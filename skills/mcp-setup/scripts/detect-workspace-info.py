#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
# ]
# ///
"""Detect if VS Code is running in a remote setup (SSH, WSL, Dev Container, Codespaces)."""

import json
import os
import subprocess
from typing import Any


def detect_bmw_instance() -> dict[str, Any]:
    """
    Detect the BMW tool instance (ATC, CC, or unknown) based on git remote.

    Returns:
        Dictionary with BMW instance information.
    """
    info: dict[str, Any] = {"bmw_instance": "unknown", "git_remote": None}

    try:
        # Get git remote URL
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        if result.returncode == 0:
            remote_url = result.stdout.strip()
            info["git_remote"] = remote_url

            # Determine instance based on remote URL
            if "cc-github" in remote_url.lower():
                info["bmw_instance"] = "CC"
            elif "atc-github" in remote_url.lower() or "bmw.ghe.com" in remote_url.lower():
                info["bmw_instance"] = "ATC"

    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        # Git not available or not in a git repository
        pass

    return info


def detect_vscode_remote() -> dict[str, Any]:
    """
    Detect if VS Code is running in a remote setup.

    Returns:
        Dictionary with remote setup information.
    """
    info: dict[str, Any] = {"is_remote": False, "remote_type": None, "details": {}}

    if os.environ.get("VSCODE_REMOTE_SERVER_PATH") or os.environ.get("VSCODE_IPC_HOOK_CLI"):
        info["is_remote"] = True

        if os.environ.get("CODESPACES"):
            info["remote_type"] = "GitHub Codespaces"
            info["details"]["codespace_name"] = os.environ.get("CODESPACE_NAME")
        elif os.environ.get("REMOTE_CONTAINERS") or os.environ.get("REMOTE_CONTAINERS_IPC"):
            info["remote_type"] = "Dev Container"
            info["details"]["container_name"] = os.environ.get("HOSTNAME")
        elif os.environ.get("WSL_DISTRO_NAME") or os.environ.get("WSL_INTEROP"):
            info["remote_type"] = "WSL"
            info["details"]["distro_name"] = os.environ.get("WSL_DISTRO_NAME")
        else:
            info["remote_type"] = "Remote-SSH"
            info["details"]["hostname"] = os.environ.get("HOSTNAME")
            info["details"]["ssh_connection"] = os.environ.get("SSH_CONNECTION")

    elif os.environ.get("SSH_CONNECTION"):
        info["details"]["ssh_session"] = True
        info["details"]["ssh_connection"] = os.environ.get("SSH_CONNECTION")
        info["details"]["note"] = "SSH session detected, but not VS Code Remote-SSH"

    return info


def main():
    """Main entry point for the script."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Detect VS Code remote setup (SSH, WSL, Dev Container, Codespaces)."
    )
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    args = parser.parse_args()

    result = detect_vscode_remote()
    bmw_info = detect_bmw_instance()

    # Merge BMW instance info into result
    result.update(bmw_info)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"  Is Remote: {result['is_remote']}")
        if result["is_remote"]:
            print(f"  Remote Type: {result['remote_type']}")
        for key, value in result["details"].items():
            if value:
                print(f"  {key}: {value}")

        # Print BMW instance info
        print(f"  BMW Instance: {result['bmw_instance']}")
        if result.get("git_remote"):
            print(f"  Git Remote: {result['git_remote']}")


if __name__ == "__main__":
    main()
