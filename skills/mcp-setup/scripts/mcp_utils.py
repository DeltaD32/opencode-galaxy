#!/usr/bin/env python3
# /// script
# requires-python = ">=3.14"
# dependencies = [
# ]
# ///
"""
MCP-specific utilities for MCP server setup scripts.

This module provides MCP-specific functionality for:
- MCP configuration file management
- Docker image handling for MCP servers
- Instance/environment selection prompts

General-purpose utilities (console output, prerequisite checking, etc.)
are imported from utils.py.
"""

import json
import os
import platform
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import general-purpose utilities from utils.py
from utils import (
    # Setup completion
    ManualStep,
    # Prerequisite checking
    PrerequisiteCheck,
    PrerequisiteCheckResult,
    SetupResult,
    check_command,
    check_docker_daemon_running,
    check_docker_installed,
    check_node_installed,
    check_npx_installed,
    check_python_installed,
    check_uvx_installed,
    # Console output
    console,
    create_prerequisite_checker,
    # Environment & validation
    is_wsl,
    log_error,
    log_info,
    log_manual,
    log_prompt,
    log_step,
    log_warn,
    print_script_header,
    print_setup_complete,
    prompt_selection,
    run_prerequisite_checks,
    validate_json_file,
)

# Re-export general utilities for backward compatibility
__all__ = [
    # Console output
    "console",
    "print_script_header",
    "log_info",
    "log_warn",
    "log_error",
    "log_manual",
    "log_step",
    "log_prompt",
    "prompt_selection",
    # Prerequisite checking
    "PrerequisiteCheck",
    "PrerequisiteCheckResult",
    "check_command",
    "check_python_installed",
    "check_node_installed",
    "check_npx_installed",
    "check_docker_daemon_running",
    "check_uvx_installed",
    "check_docker_installed",
    "run_prerequisite_checks",
    "create_prerequisite_checker",
    # Setup completion
    "ManualStep",
    "SetupResult",
    "print_setup_complete",
    # Environment & validation
    "is_wsl",
    "validate_json_file",
    # MCP-specific functions (defined below)
    "get_mcp_config_path",
    "create_mcp_config_dir",
    "backup_mcp_config",
    "merge_mcp_config",
    "write_mcp_config",
    "pull_docker_image",
    "check_docker_image_exists",
    "prompt_instance_selection",
]


# ============================================================================
# MCP Configuration Management
# ============================================================================


def get_mcp_config_path(scope: str = "global") -> Path:
    """Get the path to the MCP configuration file.

    Args:
        scope: Either 'global' for user-wide config or 'project' for workspace config

    Returns:
        Path to the MCP configuration file

    Raises:
        ValueError: If scope is not 'global' or 'project'
    """
    if scope not in ["global", "project"]:
        raise ValueError(f"Invalid scope: {scope}. Must be 'global' or 'project'")

    if scope == "project":
        # Project-specific configuration in .vscode/mcp.json
        # Resolution order:
        # 1) Explicit MCP_PROJECT_ROOT env var
        # 2) Git repository root (if available)
        # 3) Workspace root inferred from .github/skills/mcp-setup path
        # 4) Current working directory
        configured_root = os.environ.get("MCP_PROJECT_ROOT")
        if configured_root:
            root = Path(configured_root).expanduser().resolve()
            return root / ".vscode" / "mcp.json"

        try:
            git_root = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            if git_root:
                return Path(git_root).resolve() / ".vscode" / "mcp.json"
        except (subprocess.SubprocessError, FileNotFoundError):
            pass

        # If this script lives under <workspace>/.github/skills/mcp-setup/scripts,
        # prefer that workspace root.
        module_path = Path(__file__).resolve()
        for parent in module_path.parents:
            if parent.name == ".github":
                return parent.parent / ".vscode" / "mcp.json"

        return Path.cwd() / ".vscode" / "mcp.json"
    else:
        # Global configuration
        if platform.system() == "Windows":
            base_path = Path(os.environ.get("APPDATA", ""))
        else:
            base_path = Path.home() / ".config"

    return base_path / "Code" / "User" / "globalStorage" / "mcp.json"


def create_mcp_config_dir(config_path: Path) -> None:
    """Create MCP configuration directory if it doesn't exist.

    Args:
        config_path: Path to the MCP configuration file
    """
    config_dir = config_path.parent
    config_dir.mkdir(parents=True, exist_ok=True)

    if config_dir.exists():
        log_info(f"Directory ready: {config_dir}")


def backup_mcp_config(config_path: Path) -> Optional[Path]:
    """Create a timestamped backup of the MCP configuration file.

    Args:
        config_path: Path to the MCP configuration file

    Returns:
        Path to the backup file, or None if no backup was created
    """
    if not config_path.exists():
        return None

    backup_path = config_path.with_suffix(f".backup.{int(time.time())}.json")
    shutil.copy(config_path, backup_path)
    log_info(f"Backed up existing config to: {backup_path}")

    return backup_path


def merge_mcp_config(
    config_path: Path, new_servers: Dict[str, Any], new_inputs: Optional[List] = None
) -> Dict[str, Any]:
    """Merge new MCP server configurations with existing config.

    Args:
        config_path: Path to the MCP configuration file
        new_servers: Dictionary of new server configurations to add/update
        new_inputs: Optional list of input variable definitions to add/update

    Returns:
        The merged configuration dictionary
    """
    config: Dict[str, Any] = {"servers": new_servers}
    if new_inputs:
        config["inputs"] = new_inputs

    if config_path.exists():
        log_info("Existing MCP config found - merging configurations...")

        # Backup existing config
        backup_mcp_config(config_path)

        # Load and merge
        try:
            with open(config_path, "r") as f:
                existing_config = json.load(f)

            if "servers" not in existing_config:
                existing_config["servers"] = {}

            existing_config["servers"].update(new_servers)

            # Merge inputs if provided
            if new_inputs:
                if "inputs" not in existing_config:
                    existing_config["inputs"] = []

                # Merge inputs by ID to avoid duplicates
                existing_input_ids = {inp.get("id") for inp in existing_config["inputs"]}
                for new_input in new_inputs:
                    if new_input.get("id") not in existing_input_ids:
                        existing_config["inputs"].append(new_input)

            config = existing_config
            log_info("Merged new server configurations")
        except json.JSONDecodeError:
            log_warn("Could not parse existing config - creating new config (backup saved)")
    else:
        log_info("Created new MCP configuration")

    return config


def write_mcp_config(config_path: Path, config: Dict[str, Any], secure: bool = True) -> None:
    """Write MCP configuration to file.

    Args:
        config_path: Path to the MCP configuration file
        config: Configuration dictionary to write
        secure: If True, set file permissions to 600 (owner read/write only)
    """
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)

    log_info(f"Configuration written to: {config_path}")

    if secure and platform.system() != "Windows":
        config_path.chmod(0o600)
        log_info("Set secure file permissions (600) on config file")


# ============================================================================
# Docker Utilities (MCP-specific)
# ============================================================================


def pull_docker_image(image: str) -> bool:
    """Pull a Docker image.

    Args:
        image: Docker image name (e.g., "mcp/atlassian:latest")

    Returns:
        True if successful, False otherwise
    """
    log_info(f"Pulling Docker image: {image}")

    try:
        subprocess.run(["docker", "pull", image], check=True)
        log_info(f"Docker image pulled successfully: {image}")
        return True
    except subprocess.SubprocessError:
        log_error(f"Failed to pull Docker image: {image}")
        return False


def check_docker_image_exists(image: str) -> bool:
    """Check if a Docker image exists locally.

    Args:
        image: Docker image name

    Returns:
        True if image exists, False otherwise
    """
    try:
        subprocess.run(["docker", "image", "inspect", image], capture_output=True, check=True)
        return True
    except subprocess.SubprocessError:
        return False


# ============================================================================
# Instance Selection (MCP-specific, kept for backward compatibility)
# ============================================================================


def prompt_instance_selection(
    instance_map: Dict[str, str],
    title: str = "Instance Selection",
    custom_option_label: str = "Custom URL",
    custom_prompt: str = "Enter custom URL:",
    param_instance: Optional[str] = None,
) -> str:
    """Prompt user to select from a map of instances or enter a custom URL.

    DEPRECATED: Use prompt_selection() for more flexibility.
    This function is kept for backward compatibility with MCP scripts.

    Args:
        instance_map: Dictionary mapping instance names to URLs
        title: Title for the selection menu
        custom_option_label: Label for the custom URL option
        custom_prompt: Prompt message for custom URL input
        param_instance: Pre-selected instance name or URL (skips prompt)

    Returns:
        Selected URL (either from map or custom)

    Example:
        instance_map = {
            "ito": "https://ito-ci.bmwgroup.net/sonar",
            "oto": "https://oto-ci.bmwgroup.net/sonar",
        }
        url = prompt_instance_selection(
            instance_map,
            title="BMW SonarQube Instances",
            param_instance=args.instance
        )
    """

    def url_validator(value: str) -> str:
        """Accept URLs as-is."""
        if value.startswith("http://") or value.startswith("https://"):
            return value
        return value.lower()

    return prompt_selection(
        options=instance_map,
        title=title,
        display_format="{idx}) {key:<10} - {value}",
        allow_custom=True,
        custom_option_label=custom_option_label,
        custom_prompt=custom_prompt,
        custom_validator=url_validator,
        param_value=param_instance,
    )
