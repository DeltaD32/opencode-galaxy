#!/usr/bin/env python3
# /// script
# requires-python = ">=3.8"
# dependencies = ["rich>=13.0.0"]
# ///
"""
Token Tom's Toolbelt self-update script.

This script automates the update process for an existing token-toms-toolbelt
installation. It performs prerequisite checks, executes the update command,
and verifies the installation.

Usage:
    uv run scripts/self-update-script.py [--branch BRANCH] [--repository REPO] [--check-only]

Options:
    --branch BRANCH      Update to a specific branch instead of default
    --repository REPO    Update from specific repository (URL or local path)
    --check-only         Only check if update is needed, don't perform update
    --force              Force update even if checks suggest it's current
    --help               Show this help message
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

try:
    from rich.panel import Panel
    from rich.prompt import Confirm
    from utils import (
        console,
        log_error,
        log_info,
        log_step,
        log_warn,
        print_script_header,
    )
except ImportError:
    print("Error: This script requires the 'rich' package and utils.py")
    print("Install rich with: pip install rich")
    sys.exit(1)

# Constants
DEFAULT_REPO_URL = "https://bmw.ghe.com/DX/token-toms-toolbelt.git"
SETUP_COMMAND = "token-toms-toolbelt-setup"
TTT_DIR = Path(".ttt")
CONFIG_FILE = TTT_DIR / "config.yaml"


def read_setup_config() -> dict:
    """Read setup configuration from .ttt/config.yaml.

    Returns:
        Dictionary with config values (branch, repository, etc.)
        Returns empty dict if config file doesn't exist or can't be read.
    """
    if not CONFIG_FILE.exists():
        return {}

    try:
        import re

        config = {}
        content = CONFIG_FILE.read_text(encoding="utf-8")

        # Simple YAML parsing for our specific format
        for line in content.split("\n"):
            if line.strip().startswith("#") or not line.strip():
                continue

            match = re.match(r"^(\w+):\s*['\"]?([^'\"]+)['\"]?\s*$", line)
            if match:
                key, value = match.groups()
                config[key] = value.strip()

        return config
    except Exception as e:
        log_warn(f"Could not read config file: {e}")
        return {}


def check_installation() -> bool:
    """Check if token-toms-toolbelt is already installed.

    Returns:
        True if installation exists, False otherwise
    """
    log_step("Checking current installation...")

    if not TTT_DIR.exists():
        log_error(f"{TTT_DIR} directory not found")
        console.print(
            "  This script should be run from a project with token-toms-toolbelt already installed."
        )
        console.print(
            "  For initial setup, use: uvx --from git+https://bmw.ghe.com/DX/token-toms-toolbelt.git token-toms-toolbelt-setup"
        )
        return False

    log_info(f"Found {TTT_DIR} directory")

    # Check for expected subdirectories
    subdirs = ["flows", "setup", "scripts"]
    missing_dirs = []
    for subdir in subdirs:
        subdir_path = TTT_DIR / subdir
        if subdir_path.exists():
            log_info(f"Found {subdir_path}/")
        else:
            missing_dirs.append(subdir)
            log_warn(f"Missing {subdir_path}/")

    if missing_dirs:
        log_warn(f"Some expected directories are missing: {', '.join(missing_dirs)}")
        console.print("  Update will restore these directories.")

    console.print()
    return True


def check_prerequisites() -> bool:
    """Check prerequisites for update.

    Returns:
        True if all prerequisites are met, False otherwise
    """
    log_step("Checking prerequisites...")

    # Check for uvx
    uvx_path = shutil.which("uvx")
    if not uvx_path:
        log_error("uvx is not installed or not in PATH")
        console.print("  Install uv with: curl -LsSf https://astral.sh/uv/install.sh | sh")
        console.print("  See: setup/basic-environment/uv-setup.md")
        return False

    log_info(f"uvx found at: {uvx_path}")

    # Check for git (needed for git+ URL)
    git_path = shutil.which("git")
    if not git_path:
        log_error("git is not installed or not in PATH")
        console.print("  Install git: sudo apt install git (Linux) or brew install git (macOS)")
        return False

    log_info(f"git found at: {git_path}")
    console.print()
    return True


def check_directory_permissions() -> bool:
    """Check if .ttt directory is writable.

    Returns:
        True if directory is writable, False otherwise
    """
    log_step("Checking directory permissions...")

    if not TTT_DIR.exists():
        log_warn(f"{TTT_DIR} does not exist (will be created)")
        console.print()
        return True

    if not os.access(TTT_DIR, os.W_OK):
        log_error(f"{TTT_DIR} is not writable")
        console.print(f"  Fix with: chmod -R u+w {TTT_DIR}")
        return False

    log_info(f"{TTT_DIR} is writable")
    console.print()
    return True


def run_update(
    branch: str | None = None, repository: str | None = None, config: dict | None = None
) -> bool:
    """Execute the update command.

    Args:
        branch: Optional branch name to update from (overrides config)
        repository: Optional repository URL or path (overrides config)
        config: Configuration dict from .ttt/config.yaml

    Returns:
        True if update succeeded, False otherwise
    """
    log_step("Running update command...")
    console.print()

    # Determine which branch and repository to use
    stored_branch = config.get("branch") if config else None
    stored_repository = config.get("repository") if config else None
    effective_branch = branch if branch else stored_branch
    effective_repository = repository if repository else (stored_repository or DEFAULT_REPO_URL)
    repo_path = None

    # Check if repository is a local path
    is_local = not effective_repository.startswith(
        ("http://", "https://", "git://", "ssh://", "git@")
    )

    if is_local:
        repo_path = Path(effective_repository).expanduser().resolve()
        if not repo_path.exists():
            log_error(f"Local repository path does not exist: {repo_path}")
            return False
        effective_repository = str(repo_path)
        log_info(f"Updating from local path: {effective_repository}")
    else:
        log_info(f"Updating from repository: {effective_repository}")

    # Warn if using non-main branch (only relevant for git repos)
    if not is_local and effective_branch and effective_branch not in ["main", "HEAD"]:
        console.print(
            Panel(
                f"[bold yellow]⚠ You are updating from branch: {effective_branch}[/bold yellow]\n\n"
                f"This is not the main branch. You will receive updates from this branch.\n"
                f"To switch to the main branch, run:\n"
                f"  uv run .ttt/scripts/self-update-script.py --branch main",
                style="yellow",
                width=70,
            )
        )
        console.print()

    # Build command based on whether it's local or remote
    if is_local and repo_path and repo_path.exists():
        # For local paths, use python directly
        setup_script = repo_path / "src" / "token_toms_toolbelt" / "setup.py"
        if not setup_script.exists():
            log_error(f"Setup script not found: {setup_script}")
            return False

        cmd = [
            "python3",
            str(setup_script),
            "--repository",
            effective_repository,
            "--force",
            "--non-interactive",
        ]
    else:
        # For remote repos, use uvx
        repo_url = (
            f"git+{effective_repository}"
            if not effective_repository.startswith("git+")
            else effective_repository
        )
        cmd = ["uvx", "--from", repo_url, SETUP_COMMAND, "--force", "--non-interactive"]

    if effective_branch:
        cmd.extend(["--branch", effective_branch])
        if not is_local:
            log_info(f"Updating from branch: {effective_branch}")
    else:
        if not is_local:
            log_info("Updating from default branch")

    # For remote repos, add repository parameter to ensure it's saved in config
    if not is_local:
        cmd.extend(["--repository", effective_repository])

    # Display command
    console.print("[dim]$ " + " ".join(cmd) + "[/dim]")
    console.print()

    try:
        subprocess.run(
            cmd,
            check=True,
            capture_output=False,  # Show output in real-time
            text=True,
        )
        console.print()
        log_info("Update command completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        console.print()
        log_error(f"Update command failed with exit code {e.returncode}")
        return False
    except FileNotFoundError:
        log_error("uvx command not found")
        return False


def verify_update() -> bool:
    """Verify that the update was successful.

    Returns:
        True if verification passed, False otherwise
    """
    log_step("Verifying update...")

    # Check that .ttt directory exists
    if not TTT_DIR.exists():
        log_error(f"{TTT_DIR} directory not found after update")
        return False

    # Check for expected subdirectories
    subdirs = ["flows", "setup", "scripts", "agents", "knowledge"]
    all_present = True
    for subdir in subdirs:
        subdir_path = TTT_DIR / subdir
        if subdir_path.exists():
            log_info(f"Verified {subdir_path}/")
        else:
            log_error(f"Missing {subdir_path}/ after update")
            all_present = False

    console.print()
    return all_present


def print_summary(success: bool):
    """Print update summary.

    Args:
        success: Whether the update was successful
    """
    console.print()
    console.print("=" * 70)
    if success:
        log_info("Update completed successfully!")
        console.print()
        console.print("[bold]What was updated:[/bold]")
        console.print("  • Flow templates in .ttt/flows/")
        console.print("  • Setup guides in .ttt/setup/")
        console.print("  • Automation scripts in .ttt/scripts/")
        console.print("  • Agent configurations in .ttt/agents/")
        console.print("  • Knowledge base in .ttt/knowledge/")
    else:
        log_error("Update failed")
        console.print()
        console.print("[bold]Troubleshooting:[/bold]")
        console.print("  • Check directory permissions: ls -ld .ttt/")
        console.print("  • Clear uv cache: uv cache clean")
        console.print("  • Check proxy settings: echo $HTTP_PROXY")
    console.print()


def main():
    """Main entry point."""
    # Parse arguments
    parser = argparse.ArgumentParser(
        description="Update Token Tom's Toolbelt to the latest version",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--branch", help="Update to a specific branch instead of default")
    parser.add_argument(
        "--repository",
        help="Update from specific repository URL or local path (overrides config)",
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Only check if update is needed, don't perform update",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force update even if checks suggest it's current",
    )

    args = parser.parse_args()

    print_script_header(
        "Token Tom's Toolbelt - Self-Update",
        "Automated update process",
    )

    # Read stored configuration
    config = read_setup_config()
    stored_branch = config.get("branch")
    stored_repository = config.get("repository")

    # Show current configuration
    if stored_repository:
        is_local = not stored_repository.startswith(
            ("http://", "https://", "git://", "ssh://", "git@")
        )
        is_default = stored_repository == DEFAULT_REPO_URL

        if is_local:
            log_info("Current configured source: Local path")
            console.print(f"  Repository: {stored_repository}")
        elif is_default:
            log_info("Current configured source: Default repository")
        else:
            log_info("Current configured source: Custom repository")
            console.print(f"  Repository: {stored_repository}")
        console.print()

    if stored_branch:
        log_info(f"Current configured branch: {stored_branch}")
        if stored_branch not in ["main", "HEAD"] and not args.branch:
            console.print(f"[yellow]  You are on branch '{stored_branch}' (not main)[/yellow]")
            console.print("[yellow]  To switch to main, use: --branch main[/yellow]")
        console.print()

    # Run checks
    if not check_installation():
        sys.exit(1)

    if not check_prerequisites():
        sys.exit(1)

    if not check_directory_permissions():
        sys.exit(1)

    # Check-only mode
    if args.check_only:
        log_info("Check-only mode: All prerequisite checks passed")
        console.print()
        console.print("[bold]To perform the update, run:[/bold]")
        console.print(f"  uv run {__file__}")
        console.print()
        sys.exit(0)

    # Confirm before proceeding (unless force flag is set)
    if not args.force:
        console.print(
            "[bold yellow]This will update Token Tom's Toolbelt to the latest version.[/bold yellow]"
        )
        console.print()
        if not Confirm.ask("Do you want to proceed?", default=True):
            log_info("Update cancelled by user")
            sys.exit(0)
        console.print()

    # Run update
    if not run_update(args.branch, args.repository, config):
        print_summary(False)
        sys.exit(1)

    # Verify update
    if not verify_update():
        print_summary(False)
        sys.exit(1)

    print_summary(True)
    sys.exit(0)


if __name__ == "__main__":
    main()
