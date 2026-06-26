#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "rich>=13.0.0",
#   "pyyaml>=6.0",
# ]
# ///

"""Unified MCP Server Setup Script

Reads server configuration from YAML reference files and performs
automated setup for any MCP server. This script is the single entry
point that replaces the individual setup-*-mcp.py scripts.

The YAML files in references/ contain a `server_definition` section
that provides all machine-readable config needed for setup.

Usage:
  uv run scripts/setup-mcp.py --server <name> [--scope <global|project>] [--instance <name>]

Examples:
  uv run scripts/setup-mcp.py --server fetch
  uv run scripts/setup-mcp.py --server github --instance ghe
  uv run scripts/setup-mcp.py --server sonarqube --instance ito
  uv run scripts/setup-mcp.py --server figma --scope project
  uv run scripts/setup-mcp.py --server jira --instance atc
  uv run scripts/setup-mcp.py --list
"""

from __future__ import annotations

import argparse
import copy
import os
import socket
import sys
from pathlib import Path

import yaml

# Ensure scripts/ is on the import path
sys.path.insert(0, str(Path(__file__).parent))

from mcp_utils import (
    create_mcp_config_dir,
    get_mcp_config_path,
    merge_mcp_config,
    prompt_instance_selection,
    pull_docker_image,
    write_mcp_config,
)
from utils import (
    ManualStep,
    SetupResult,
    check_docker_daemon_running,
    check_docker_installed,
    check_node_installed,
    check_npx_installed,
    check_python_installed,
    check_uv_installed,
    check_uvx_installed,
    is_wsl,
    log_error,
    log_info,
    log_step,
    log_warn,
    print_script_header,
    print_setup_complete,
    run_prerequisite_checks,
    validate_json_file,
)

# ============================================================================
# Prerequisite check registry
# ============================================================================

PREREQUISITE_MAP = {
    "python": check_python_installed,
    "uv": check_uv_installed,
    "node": check_node_installed,
    "npx": check_npx_installed,
    "docker": check_docker_installed,
    "docker_daemon": check_docker_daemon_running,
    "uvx": check_uvx_installed,
}


# ============================================================================
# YAML loading
# ============================================================================


def get_references_dir() -> Path:
    """Return the references/ directory path."""
    return Path(__file__).parent.parent / "references"


def list_available_servers() -> list[str]:
    """List all available MCP server names from YAML files."""
    refs = get_references_dir()
    return sorted(
        p.stem.removeprefix("setup-").removesuffix("-mcp") for p in refs.glob("setup-*-mcp.yaml")
    )


def find_yaml_file(server_name: str) -> Path:
    """Find the YAML reference file for a server."""
    yaml_path = get_references_dir() / f"setup-{server_name}-mcp.yaml"
    if not yaml_path.exists():
        log_error(f"No YAML reference found for server '{server_name}'")
        available = list_available_servers()
        log_info(f"Available servers: {', '.join(available)}")
        sys.exit(1)
    return yaml_path


def load_yaml(yaml_path: Path) -> dict:
    """Load YAML file and return parsed data."""
    with open(yaml_path, "r") as f:
        return yaml.safe_load(f)


def get_server_definition(yaml_data: dict, yaml_path: Path) -> dict:
    """Extract server_definition from YAML data."""
    server_def = yaml_data.get("server_definition")
    if not server_def:
        log_error(f"No server_definition found in {yaml_path.name}")
        log_info("This YAML file has not been updated for the unified setup script.")
        sys.exit(1)
    return server_def


# ============================================================================
# Proxy detection
# ============================================================================


def detect_proxy() -> dict:
    """Detect proxy configuration (Proxydetox or environment variables).

    Returns:
        Dict with 'detected' bool and 'env' dict of proxy env vars.
    """
    proxy: dict = {"detected": False, "env": {}}

    # Check Proxydetox on port 3128
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex(("localhost", 3128))
        sock.close()
        if result == 0:
            proxy["detected"] = True
            proxy["env"] = {
                "HTTP_PROXY": "http://localhost:3128",
                "HTTPS_PROXY": "http://localhost:3128",
                "NO_PROXY": "127.0.0.1,localhost,.bmwgroup.net,.cloud.bmw,.bmw.cloud",
            }
            log_info("Proxydetox detected on port 3128")
            return proxy
    except OSError:
        pass

    # Fall back to environment variables
    http_proxy = os.environ.get("HTTP_PROXY") or os.environ.get("http_proxy")
    https_proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
    no_proxy = os.environ.get("NO_PROXY") or os.environ.get("no_proxy")

    if http_proxy or https_proxy:
        proxy["detected"] = True
        if http_proxy:
            proxy["env"]["HTTP_PROXY"] = http_proxy
        if https_proxy:
            proxy["env"]["HTTPS_PROXY"] = https_proxy
        if no_proxy:
            proxy["env"]["NO_PROXY"] = no_proxy
        log_info(f"Proxy detected from environment: {http_proxy or https_proxy}")
    else:
        log_info("No proxy detected")

    return proxy


# ============================================================================
# Instance resolution
# ============================================================================


def resolve_instance(server_def: dict, instance_arg: str | None) -> tuple[dict, str | None]:
    """Resolve instance selection and return (effective_config, instance_url).

    For multi-instance servers (instances dict), returns the selected instance config.
    For servers with instance_selection, returns (server_def, selected_url).
    For simple servers, returns (server_def, None).
    """
    instances = server_def.get("instances")
    instance_selection = server_def.get("instance_selection")

    if instances:
        # Multi-instance: each instance has its own full config
        if not instance_arg:
            log_error("This server requires --instance argument")
            log_info(f"Available instances: {', '.join(instances.keys())}")
            sys.exit(1)

        if instance_arg not in instances:
            log_error(f"Unknown instance: {instance_arg}")
            log_info(f"Available instances: {', '.join(instances.keys())}")
            sys.exit(1)

        return instances[instance_arg], None

    if instance_selection:
        # Single config with URL placeholder replacement
        options = instance_selection.get("options", {})
        prompt_text = instance_selection.get("prompt", "Select instance")

        url = prompt_instance_selection(
            instance_map=options,
            title=prompt_text,
            param_instance=instance_arg,
        )

        return server_def, url

    return server_def, None


# ============================================================================
# Placeholder replacement
# ============================================================================


def replace_placeholders(obj: object, placeholder: str, value: str) -> object:
    """Deep-replace a placeholder string in a nested dict/list/str structure."""
    if isinstance(obj, str):
        return obj.replace(placeholder, value)
    if isinstance(obj, dict):
        return {k: replace_placeholders(v, placeholder, value) for k, v in obj.items()}
    if isinstance(obj, list):
        return [replace_placeholders(item, placeholder, value) for item in obj]
    return obj


# ============================================================================
# WSL detection and config adjustment
# ============================================================================


def apply_wsl_adjustment(mcp_config: dict) -> dict:
    """Adjust Docker config for WSL2 environment.

    Wraps the Docker command in 'wsl' and adds --add-host for host gateway.
    """
    if mcp_config.get("command") != "docker":
        return mcp_config

    log_info("WSL2 environment detected — adjusting Docker config for WSL")

    original_args = mcp_config.get("args", [])
    new_args = ["docker"]

    # Insert --add-host after the initial "run", "--rm", "-i" flags
    host_added = False
    for arg in original_args:
        new_args.append(arg)
        if arg == "-i" and not host_added:
            new_args.extend(["--add-host", "host.docker.internal:host-gateway"])
            host_added = True

    mcp_config = dict(mcp_config)
    mcp_config["command"] = "wsl"
    mcp_config["args"] = new_args
    return mcp_config


# ============================================================================
# Core setup logic
# ============================================================================


def run_prerequisites(effective_config: dict, server_def: dict) -> bool:
    """Run prerequisite checks. Returns True if all pass."""
    prereq_names = effective_config.get("prerequisites", server_def.get("prerequisites", []))
    if not prereq_names:
        return True

    check_funcs = []
    for name in prereq_names:
        func = PREREQUISITE_MAP.get(name)
        if func:
            check_funcs.append(func)
        else:
            log_warn(f"Unknown prerequisite check: {name}")

    if not check_funcs:
        return True

    log_step("Checking prerequisites...")
    checks = [func() for func in check_funcs]
    result = run_prerequisite_checks(checks, title="Prerequisites")
    return result


def build_mcp_config(
    server_def: dict,
    effective_config: dict,
    instance_url: str | None,
) -> tuple[str, dict, list | None]:
    """Build the MCP server config dict from YAML data.

    Returns:
        (server_key, server_config, inputs)
    """
    server_key = effective_config.get("server_key", server_def.get("server_key"))
    mcp_config = copy.deepcopy(effective_config.get("mcp_config", server_def.get("mcp_config", {})))
    inputs = effective_config.get("inputs", server_def.get("inputs"))

    if not server_key or not mcp_config:
        log_error("Missing server_key or mcp_config in server definition")
        sys.exit(1)

    # Replace instance URL placeholder if applicable
    instance_selection = server_def.get("instance_selection")
    if instance_url and instance_selection:
        placeholder = instance_selection.get("placeholder", "{{instance_url}}")
        mcp_config = replace_placeholders(mcp_config, placeholder, instance_url)

    # Apply feature hooks
    features = effective_config.get("features", server_def.get("features", []))

    # Proxy detection
    if "proxy_detection" in features:
        proxy = detect_proxy()
        if proxy["detected"]:
            env = mcp_config.get("env", {})
            env.update(proxy["env"])
            mcp_config["env"] = env

    # WSL detection
    if "wsl_detection" in features and is_wsl():
        mcp_config = apply_wsl_adjustment(mcp_config)

    return server_key, mcp_config, inputs


def run_setup(
    yaml_data: dict,
    server_def: dict,
    effective_config: dict,
    scope: str,
    instance_url: str | None,
) -> int:
    """Execute the full setup pipeline. Returns exit code."""

    # 1. Prerequisites
    if not run_prerequisites(effective_config, server_def):
        return 1

    # 2. Config path
    config_path = get_mcp_config_path(scope)
    create_mcp_config_dir(config_path)

    # 3. Docker image pull
    docker_image = effective_config.get("docker_image", server_def.get("docker_image"))
    if docker_image:
        log_step(f"Pulling Docker image: {docker_image}")
        if not pull_docker_image(docker_image):
            log_warn("Docker image pull failed — setup will continue, but server may not start")

    # 4. Build config
    server_key, mcp_config, inputs = build_mcp_config(server_def, effective_config, instance_url)

    # 5. Write config
    log_step("Generating MCP configuration...")
    new_servers = {server_key: mcp_config}
    config = merge_mcp_config(config_path, new_servers, inputs)
    write_mcp_config(config_path, config)

    # 6. Validate
    log_step("Validating setup...")
    if not config_path.exists():
        log_error(f"Config file not found at: {config_path}")
        return 1
    if not validate_json_file(config_path):
        log_error(f"Config file contains invalid JSON: {config_path}")
        return 1
    log_info("Configuration file validated successfully")

    # 7. Print results
    print_results(yaml_data, server_def, effective_config, config_path, server_key)
    return 0


# ============================================================================
# Result output
# ============================================================================


def print_results(
    yaml_data: dict,
    server_def: dict,
    effective_config: dict,
    config_path: Path,
    server_key: str,
) -> None:
    """Print setup completion with next steps."""
    name = yaml_data.get("name", server_key)

    manual_steps = []

    # Optional server-specific runtime/manual steps from YAML.
    # Expected shape:
    # manual_steps:
    #   - "1. Do this"
    #   - "2. Do that"
    extra_manual_steps = yaml_data.get("manual_steps", [])
    if isinstance(extra_manual_steps, list) and all(
        isinstance(step, str) for step in extra_manual_steps
    ):
        manual_steps.append(
            ManualStep(
                title="Server Runtime Steps",
                instructions=extra_manual_steps,
            )
        )

    manual_steps.extend(
        [
            ManualStep(
                title=f"Start {name}",
                instructions=[
                    "1. Open VS Code Command Palette (Ctrl+Shift+P or Cmd+Shift+P)",
                    "2. Run: 'MCP: Open User Configuration'",
                    f"3. Find '{server_key}' server in the list",
                    "4. Click 'Start' button",
                    "5. If prompted, provide required values",
                    "6. Wait for status to show 'Running'",
                ],
            ),
            ManualStep(
                title="Verify Setup",
                instructions=[
                    "Test in GitHub Copilot Chat:",
                    f"  @{server_key} help",
                    "",
                    "Expected: List of available commands",
                ],
            ),
        ]
    )

    completed_steps = [
        "Prerequisite checks passed",
        "Generated MCP server configuration",
        f"Server key: {server_key}",
    ]

    docker_image = effective_config.get("docker_image", server_def.get("docker_image"))
    if docker_image:
        completed_steps.append(f"Docker image pulled: {docker_image}")

    result = SetupResult(
        title=name,
        config_path=config_path,
        completed_steps=completed_steps,
        manual_steps=manual_steps,
    )

    print_setup_complete(result)


# ============================================================================
# CLI
# ============================================================================


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Unified MCP Server Setup — reads YAML references and generates config",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  uv run scripts/setup-mcp.py --server fetch
  uv run scripts/setup-mcp.py --server github --instance ghe
  uv run scripts/setup-mcp.py --server sonarqube --instance ito --scope project
  uv run scripts/setup-mcp.py --server figma
  uv run scripts/setup-mcp.py --list
        """,
    )
    parser.add_argument(
        "--server",
        "-s",
        help="MCP server name (e.g., 'fetch', 'github', 'sonarqube')",
    )
    parser.add_argument(
        "--scope",
        choices=["global", "project"],
        default=None,
        help="Configuration scope (default: from YAML server_definition)",
    )
    parser.add_argument(
        "--instance",
        "-i",
        default=None,
        help="Instance name for multi-instance servers (e.g., 'ghe', 'atc', 'ito')",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all available MCP servers and exit",
    )
    args = parser.parse_args()

    # List mode
    if args.list:
        servers = list_available_servers()
        print("Available MCP servers:")
        for s in servers:
            print(f"  - {s}")
        return 0

    if not args.server:
        parser.error("--server is required (or use --list to see available servers)")

    # Load YAML
    yaml_path = find_yaml_file(args.server)
    yaml_data = load_yaml(yaml_path)
    server_def = get_server_definition(yaml_data, yaml_path)

    # Determine scope
    scope = args.scope or server_def.get("default_scope", "global")

    # Print header
    server_name = yaml_data.get("name", args.server)
    print_script_header(f"{server_name}", width=64)
    log_info(f"Server: {args.server}")
    log_info(f"Scope: {scope}")
    if args.instance:
        log_info(f"Instance: {args.instance}")
    print()

    # Resolve instance
    effective_config, instance_url = resolve_instance(server_def, args.instance)

    # Run setup
    return run_setup(yaml_data, server_def, effective_config, scope, instance_url)


if __name__ == "__main__":
    sys.exit(main())
