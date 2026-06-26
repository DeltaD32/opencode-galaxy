#!/usr/bin/env python3
# /// script
# requires-python = ">=3.8"
# dependencies = ["rich>=13.0.0"]
# ///
"""
Complete workspace verification script
Verifies workspace setup including proxy, uv, git, and project tools
Usage: uv run scripts/verify-workspace.py
"""

import os
import shutil
import socket
import subprocess
import sys
from pathlib import Path

from rich.console import Console

console = Console()


def check_proxy():
    """Check proxy configuration."""
    console.print("[bold cyan]1. Checking Proxy Configuration...[/bold cyan]")

    # Extract port from environment variable if set, otherwise try common ports
    http_proxy = os.environ.get("HTTP_PROXY", "")
    https_proxy = os.environ.get("HTTPS_PROXY", "")

    ports_to_check = [3128, 48157, 8080]  # Common proxy ports

    # Extract port from proxy URL if available
    if http_proxy:
        import re

        match = re.search(r":(\d+)", http_proxy)
        if match:
            configured_port = int(match.group(1))
            if configured_port not in ports_to_check:
                ports_to_check.insert(0, configured_port)

    proxy_found = False
    for port in ports_to_check:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(2)
                result = sock.connect_ex(("localhost", port))
                if result == 0:
                    console.print(
                        f"   [green]:white_check_mark: Proxy detected on port {port}[/green]"
                    )
                    proxy_found = True
                    break
        except (socket.error, OSError):
            continue

    if not proxy_found:
        console.print(f"   [red]:x: No proxy detected on common ports: {ports_to_check}[/red]")

    http_proxy_display = http_proxy if http_proxy else "Not set"
    https_proxy_display = https_proxy if https_proxy else "Not set"

    console.print(f"   HTTP_PROXY: {http_proxy_display}")
    console.print(f"   HTTPS_PROXY: {https_proxy_display}")
    console.print()


def check_uv():
    """Check UV (Python package manager)."""
    console.print("[bold cyan]2. Checking UV (Python Package Manager)...[/bold cyan]")

    uv_path = shutil.which("uv")
    if uv_path:
        try:
            result = subprocess.run(["uv", "--version"], capture_output=True, text=True)
            console.print(
                f"   [green]:white_check_mark: uv is installed:[/green] {result.stdout.strip()}"
            )
        except subprocess.SubprocessError:
            console.print(f"   [green]:white_check_mark: uv is installed at:[/green] {uv_path}")
    else:
        console.print("   [red]:x: uv is not installed[/red]")
    console.print()


def check_git():
    """Check Git configuration."""
    console.print("[bold cyan]3. Checking Git Configuration...[/bold cyan]")

    git_path = shutil.which("git")
    if git_path:
        try:
            version = subprocess.run(["git", "--version"], capture_output=True, text=True)
            console.print(
                f"   [green]:white_check_mark: Git is installed:[/green] {version.stdout.strip()}"
            )

            try:
                user_name = subprocess.run(
                    ["git", "config", "user.name"], capture_output=True, text=True
                )
                name = user_name.stdout.strip() if user_name.returncode == 0 else "Not configured"
                console.print(f"   User name: {name}")
            except subprocess.SubprocessError:
                console.print("   User name: Not configured")

            try:
                user_email = subprocess.run(
                    ["git", "config", "user.email"], capture_output=True, text=True
                )
                email = (
                    user_email.stdout.strip() if user_email.returncode == 0 else "Not configured"
                )
                console.print(f"   User email: {email}")
            except subprocess.SubprocessError:
                console.print("   User email: Not configured")
        except subprocess.SubprocessError:
            console.print(f"   [green]:white_check_mark: Git is installed at:[/green] {git_path}")
    else:
        console.print("   [red]:x: Git is not installed[/red]")
    console.print()


def check_project_tools():
    """Check project tools configuration."""
    console.print("[bold cyan]4. Checking Project Tools Configuration...[/bold cyan]")

    project_tools_path = Path(".ttt/config/project-tools.md")
    config_dir = Path(".ttt/config")

    if project_tools_path.exists():
        console.print("   [green]:white_check_mark: Project tools configuration exists[/green]")
    elif config_dir.exists():
        console.print(
            "   [yellow]:warning: .ttt/config exists but project-tools.md not found[/yellow]"
        )
    else:
        console.print(
            "   [blue]:information: No .ttt/config directory (may be intentional for new projects)[/blue]"
        )
    console.print()


def main():
    from rich.panel import Panel

    console.print()
    console.print(Panel("[bold]Workspace Setup Verification[/bold]", style="cyan", width=70))
    console.print()

    check_proxy()
    check_uv()
    check_git()
    check_project_tools()

    console.print(Panel("[bold green]Verification Complete[/bold green]", style="green", width=70))
    console.print()
    console.print("[bold]For detailed setup instructions, see:[/bold]")
    console.print("  [blue]:open_book:[/blue] Proxy: setup/basic-environment/proxy-setup.md")
    console.print("  [blue]:open_book:[/blue] UV: setup/basic-environment/uv-setup.md")
    console.print(
        "  [blue]:open_book:[/blue] Project Tools Template: setup/template/project-tools.md"
    )
    console.print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
