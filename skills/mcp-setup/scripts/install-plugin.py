#!/usr/bin/env python3
# /// script
# requires-python = ">=3.8"
# dependencies = ["rich>=13.0.0"]
# ///
"""
TTT Plugin Installation Script

This script searches for repositories with the 'ttt-plugin' tag on BMW's GHE instance
and installs plugin files to a target project's .ttt folder.

AI Agent Instructions:
1. Execute this script to search for available TTT plugins
2. User can specify additional search terms, a URL, or owner/repo format
3. Interactive selection with keyboard navigation:
   - Arrow keys (↑/↓) or j/k: Navigate through options
   - Space: Toggle selection
   - Enter: Confirm and install selected plugins
   - Escape or q: Cancel selection
   - a: Select all
   - n: Select none
4. Plugin files are installed to .ttt/ directory in the target repository
5. After installation, prompts.yaml and mcp-servers.yaml are automatically regenerated
   to index the plugin content, making it discoverable for help and MCP setup

Usage:
    uv run scripts/install-plugin.py [search terms]
    uv run scripts/install-plugin.py --url <github-url>
    uv run scripts/install-plugin.py --repo <owner/repo>

Examples:
    # Search and select multiple plugins interactively
    uv run scripts/install-plugin.py testing

    # Select specific plugin by URL
    uv run scripts/install-plugin.py --url https://bmw.ghe.com/DX/ttt-plugin-example
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

from utils import (
    console,
    log_error,
    log_info,
    log_step,
    log_warn,
    print_script_header,
    prompt_multi_selection,
)

# ============================================================================
# GitHub CLI Integration
# ============================================================================


def check_gh_cli(hostname: str = "bmw.ghe.com") -> bool:
    """Check if gh CLI is installed and authenticated to specific hostname.

    Args:
        hostname: GitHub hostname to check authentication for

    Returns:
        True if gh is installed and authenticated to the hostname
    """
    try:
        # Check if gh is installed
        result = subprocess.run(["gh", "--version"], capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            log_error("GitHub CLI (gh) is not working properly")
            return False

        # Check authentication status (any instance is OK, we'll specify --hostname in commands)
        result = subprocess.run(
            ["gh", "auth", "status"], capture_output=True, text=True, timeout=10
        )

        # gh auth status returns non-zero if not authenticated to ANY instance
        # but we check if the specific hostname is in the output
        if hostname in result.stderr or hostname in result.stdout:
            log_info(f"GitHub CLI is authenticated to {hostname}")
            return True
        elif "Logged in to" in result.stderr or "Logged in to" in result.stdout:
            log_warn(f"GitHub CLI is authenticated, but not to {hostname}")
            log_info(f"Run: gh auth login --hostname {hostname}")
            # Still return True as gh can work with --hostname flag
            return True
        else:
            log_error("GitHub CLI is not authenticated")
            log_error(f"Run: gh auth login --hostname {hostname}")
            return False

    except FileNotFoundError:
        log_error("GitHub CLI (gh) is not installed")
        log_error("Install from: https://cli.github.com/")
        return False
    except subprocess.TimeoutExpired:
        log_error("GitHub CLI check timed out")
        return False


class GitHubClient:
    """Client for interacting with GitHub Enterprise using gh CLI."""

    def __init__(self, base_url: str = "https://bmw.ghe.com"):
        """Initialize GitHub client.

        Args:
            base_url: Base URL for GHE instance
        """
        self.base_url = base_url.rstrip("/")
        self.hostname = base_url.replace("https://", "").replace("http://", "")

    def _run_gh_command(self, args: List[str]) -> Optional[Dict]:
        """Run a gh CLI command and return JSON output.

        Args:
            args: Command arguments for gh CLI

        Returns:
            Parsed JSON response or None if failed

        Note:
            Uses GH_HOST environment variable for host selection since --hostname
            flag is not universally supported across all gh commands.
        """
        try:
            cmd = ["gh"] + args

            # Use GH_HOST environment variable for all commands
            # This is more reliable than --hostname which isn't supported by all commands
            env = os.environ.copy()
            env["GH_HOST"] = self.hostname

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, env=env)

            if result.returncode != 0:
                log_error(f"Command failed: gh {' '.join(args)}")
                if result.stderr:
                    log_error(result.stderr.strip())
                return None

            if result.stdout:
                return json.loads(result.stdout)
            return {}

        except subprocess.TimeoutExpired:
            log_error(f"Command timed out: gh {' '.join(args)}")
            return None
        except json.JSONDecodeError as e:
            log_error(f"Failed to parse JSON response: {e}")
            return None
        except Exception as e:
            log_error(f"Command failed: {e}")
            return None

    def search_repositories(self, query: str, additional_terms: Optional[str] = None) -> List[Dict]:
        """Search for repositories with specific topic/tag.

        Args:
            query: Base search query (e.g., "topic:ttt-plugin")
            additional_terms: Additional search terms to narrow results

        Returns:
            List of repository information dictionaries
        """
        search_query = query
        if additional_terms:
            search_query = f"{query} {additional_terms}"

        log_step(f"Searching GHE for: {search_query}")

        # gh search repos returns an array directly
        # Uses GH_HOST env var set by _run_gh_command
        result = self._run_gh_command(
            [
                "search",
                "repos",
                search_query,
                "--json",
                "name,owner,description,url,defaultBranch",
                "--limit",
                "100",
            ]
        )

        if result is None:
            return []

        # gh search repos returns a list directly (not wrapped in an object)
        repos = result if isinstance(result, list) else []

        log_info(f"Found {len(repos)} repository/repositories")
        return repos

    def get_repository(self, owner: str, repo: str) -> Optional[Dict]:
        """Get repository information by owner/repo.

        Args:
            owner: Repository owner
            repo: Repository name

        Returns:
            Repository information dictionary or None if not found
        """
        log_step(f"Fetching repository: {owner}/{repo}")

        # Uses GH_HOST env var set by _run_gh_command
        # Note: gh repo view uses defaultBranchRef (object), not defaultBranch (string)
        result = self._run_gh_command(
            [
                "repo",
                "view",
                f"{owner}/{repo}",
                "--json",
                "name,owner,description,url,defaultBranchRef",
            ]
        )

        if result:
            log_info(f"Found repository: {owner}/{repo}")

        return result

    def get_repository_tree(self, owner: str, repo: str, branch: str = "main") -> List[Dict]:
        """Get repository file tree using gh CLI.

        Args:
            owner: Repository owner
            repo: Repository name
            branch: Branch name (default: main)

        Returns:
            List of file/directory information
        """
        log_step(f"Fetching repository tree for {owner}/{repo}@{branch}")

        # Use gh api to get the tree
        try:
            env = os.environ.copy()
            env["GH_HOST"] = self.hostname

            result = subprocess.run(
                ["gh", "api", f"repos/{owner}/{repo}/git/trees/{branch}?recursive=1"],
                capture_output=True,
                text=True,
                timeout=30,
                env=env,
            )

            if result.returncode != 0:
                if branch == "main":
                    log_warn("Trying 'master' branch instead...")
                    return self.get_repository_tree(owner, repo, branch="master")
                log_error(f"Failed to fetch repository tree: {result.stderr}")
                return []

            data = json.loads(result.stdout)
            tree = data.get("tree", [])

            log_info(f"Found {len(tree)} files/directories")
            return tree

        except Exception as e:
            log_error(f"Failed to fetch repository tree: {e}")
            if branch == "main":
                log_warn("Trying 'master' branch instead...")
                return self.get_repository_tree(owner, repo, branch="master")
            return []

    def download_file(
        self, owner: str, repo: str, path: str, branch: str = "main"
    ) -> Optional[bytes]:
        """Download a file from a repository using gh CLI.

        Args:
            owner: Repository owner
            repo: Repository name
            path: File path in repository
            branch: Branch name (default: main)

        Returns:
            File content as bytes or None if failed
        """
        try:
            # Use gh api to download raw file content
            env = os.environ.copy()
            env["GH_HOST"] = self.hostname

            result = subprocess.run(
                [
                    "gh",
                    "api",
                    f"repos/{owner}/{repo}/contents/{path}?ref={branch}",
                    "--jq",
                    ".content",
                ],
                capture_output=True,
                text=True,
                timeout=30,
                env=env,
            )

            if result.returncode != 0:
                log_error(f"Failed to download {path}: {result.stderr}")
                return None

            # GitHub API returns base64-encoded content
            import base64

            content_base64 = result.stdout.strip().replace("\n", "")
            content = base64.b64decode(content_base64)

            return content

        except Exception as e:
            log_error(f"Failed to download {path}: {e}")
            return None


# ============================================================================
# Plugin Installation
# ============================================================================


def parse_github_url(url: str) -> Optional[Tuple[str, str]]:
    """Parse GitHub URL to extract owner and repo.

    Args:
        url: GitHub repository URL

    Returns:
        Tuple of (owner, repo) or None if parsing failed
    """
    # Handle various GitHub URL formats:
    # https://bmw.ghe.com/owner/repo
    # https://bmw.ghe.com/owner/repo.git
    # git@bmw.ghe.com:owner/repo.git

    if url.startswith("git@"):
        # SSH format: git@bmw.ghe.com:owner/repo.git
        match = re.search(r"git@[^:]+:([^/]+)/(.+?)(?:\.git)?$", url)
        if match:
            return match.group(1), match.group(2)
    else:
        # HTTPS format
        parsed = urlparse(url)
        path_parts = [p for p in parsed.path.split("/") if p]
        if len(path_parts) >= 2:
            owner = path_parts[0]
            repo = path_parts[1].replace(".git", "")
            return owner, repo

    return None


def select_repositories(repos: List[Dict]) -> List[Dict]:
    """Allow user to select multiple repositories from a list.

    Args:
        repos: List of repository information dictionaries

    Returns:
        List of selected repositories or empty list if cancelled
    """
    if not repos:
        log_error("No repositories found")
        return []

    # Build selection options - map index to repo info string
    options = {}
    repo_map = {}  # Map option strings back to repo objects

    for i, repo in enumerate(repos, 1):
        full_name = f"{repo['owner']['login']}/{repo['name']}"
        desc = repo.get("description", "No description")
        option_str = f"{full_name} - {desc}"
        options[str(i)] = option_str
        repo_map[option_str] = repo

    log_step(f"Found {len(repos)} repositories")

    try:
        selected_options = prompt_multi_selection(
            options=options,
            title="Select Plugins to Install (multiple selection supported)",
            display_format="{idx}) {value}",
            min_selections=1,
        )

        # Map selected option strings back to repo objects
        selected_repos = [repo_map[opt] for opt in selected_options]
        return selected_repos

    except (KeyboardInterrupt, EOFError):
        console.print("\n[yellow]Selection cancelled by user[/yellow]")
        return []


def get_plugin_files(tree: List[Dict]) -> List[Dict]:
    """Filter repository tree to get plugin files that should be installed.

    Args:
        tree: Repository file tree

    Returns:
        List of file entries to install
    """
    # Plugin files should be in the root or organized similar to this repo's structure
    # We'll look for common directories: flows/, agents/, knowledge/, setup/

    plugin_dirs = {"flows", "agents", "knowledge", "setup", "scripts"}
    plugin_files = []

    for item in tree:
        if item["type"] != "blob":  # Only files, not directories
            continue

        path = item["path"]
        # Check if file is in a plugin directory or is a root .md file
        parts = path.split("/")

        if len(parts) > 1 and parts[0] in plugin_dirs:
            plugin_files.append(item)
        elif len(parts) == 1 and path.endswith(".md"):
            # Root .md files might be documentation
            plugin_files.append(item)

    return plugin_files


def install_plugin_files(
    client: GitHubClient,
    owner: str,
    repo: str,
    files: List[Dict],
    target_dir: Path,
    branch: str = "main",
) -> int:
    """Install plugin files to target directory.

    Args:
        client: GitHub client
        owner: Repository owner
        repo: Repository name
        files: List of file entries to install
        target_dir: Target directory (.ttt folder)
        branch: Branch to download from

    Returns:
        Number of successfully installed files
    """
    if not files:
        log_warn("No plugin files to install")
        return 0

    installed_count = 0

    log_step(f"Installing {len(files)} plugin files to {target_dir}")

    for file_info in files:
        file_path = file_info["path"]

        # Download file content
        content = client.download_file(owner, repo, file_path, branch)
        if content is None:
            log_warn(f"Skipping {file_path} (download failed)")
            continue

        # Create target path
        target_path = target_dir / file_path
        target_path.parent.mkdir(parents=True, exist_ok=True)

        # Write file
        try:
            # Handle binary vs text files
            if file_path.endswith((".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip")):
                target_path.write_bytes(content)
            else:
                target_path.write_text(content.decode("utf-8"))

            log_info(f"Installed: {file_path}")
            installed_count += 1

        except Exception as e:
            log_error(f"Failed to write {file_path}: {e}")

    return installed_count


def regenerate_yaml_catalogs(target_dir: Path) -> bool:
    """Regenerate prompts.yaml and mcp-servers.yaml after plugin installation.

    This ensures that plugin-contributed flows, setup docs, and MCP servers
    are indexed and discoverable.

    Args:
        target_dir: Target directory (.ttt folder)

    Returns:
        True if regeneration succeeded, False otherwise
    """
    log_step("Regenerating YAML catalogs with plugin content")

    scripts_dir = target_dir / "scripts"
    success = True

    # Regenerate prompts.yaml
    prompts_script = scripts_dir / "generate_prompts_yaml.py"
    if prompts_script.exists():
        try:
            result = subprocess.run(
                ["python3", str(prompts_script)],
                cwd=target_dir.parent,  # Run from project root
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                log_info("✓ Regenerated prompts.yaml")
            else:
                log_warn(f"Failed to regenerate prompts.yaml: {result.stderr}")
                success = False
        except Exception as e:
            log_warn(f"Failed to regenerate prompts.yaml: {e}")
            success = False
    else:
        log_warn("prompts.yaml generation script not found, skipping")

    # Regenerate mcp-servers.yaml
    mcp_script = scripts_dir / "generate_mcp_servers_yaml.py"
    if mcp_script.exists():
        try:
            result = subprocess.run(
                ["python3", str(mcp_script)],
                cwd=target_dir.parent,  # Run from project root
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                log_info("✓ Regenerated mcp-servers.yaml")
            else:
                log_warn(f"Failed to regenerate mcp-servers.yaml: {result.stderr}")
                success = False
        except Exception as e:
            log_warn(f"Failed to regenerate mcp-servers.yaml: {e}")
            success = False
    else:
        log_warn("mcp-servers.yaml generation script not found, skipping")

    return success


def find_default_branch(client: GitHubClient, owner: str, repo: str) -> str:
    """Find the default branch of a repository.

    Args:
        client: GitHub client
        owner: Repository owner
        repo: Repository name

    Returns:
        Default branch name (e.g., 'main' or 'master')
    """
    repo_info = client.get_repository(owner, repo)
    if repo_info:
        # gh repo view returns defaultBranchRef as an object
        if "defaultBranchRef" in repo_info and repo_info["defaultBranchRef"]:
            return repo_info["defaultBranchRef"]["name"]
        # gh search repos returns defaultBranch as a string
        elif "defaultBranch" in repo_info:
            return repo_info["defaultBranch"]
    return "main"


# ============================================================================
# Main Script
# ============================================================================


def main():
    """Main script execution."""
    parser = argparse.ArgumentParser(
        description="Search and install TTT plugins from BMW GHE",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Search for all plugins with additional terms
  uv run scripts/install-plugin.py testing automation

  # Install from specific repository URL
  uv run scripts/install-plugin.py --url https://bmw.ghe.com/DX/ttt-plugin-example

  # Install from owner/repo format
  uv run scripts/install-plugin.py --repo DX/ttt-plugin-example

  # Install to custom directory
  uv run scripts/install-plugin.py --target /path/to/project --repo DX/ttt-plugin-example
        """,
    )

    parser.add_argument(
        "search_terms",
        nargs="*",
        help="Additional search terms to filter plugins",
    )
    parser.add_argument(
        "--url",
        help="GitHub repository URL to install from",
    )
    parser.add_argument(
        "--repo",
        help="Repository in owner/repo format",
    )
    parser.add_argument(
        "--target",
        help="Target directory (default: current directory)",
        default=".",
    )
    parser.add_argument(
        "--base-url",
        help="GitHub Enterprise base URL",
        default="https://bmw.ghe.com",
    )

    args = parser.parse_args()

    print_script_header(
        "TTT Plugin Installer",
        "Search and install Token Tom's Toolbelt plugins from BMW GHE",
    )

    # Check for gh CLI
    hostname = args.base_url.replace("https://", "").replace("http://", "")
    if not check_gh_cli(hostname):
        log_error("GitHub CLI is required for this script")
        log_info("Install: https://cli.github.com/")
        log_info(f"Authenticate: gh auth login --hostname {hostname}")
        return 1

    # Initialize GitHub client
    client = GitHubClient(base_url=args.base_url)

    # Determine target directory
    target_base = Path(args.target).resolve()
    target_dir = target_base / ".ttt"

    if not target_base.exists():
        log_error(f"Target directory does not exist: {target_base}")
        return 1

    log_info(f"Target directory: {target_dir}")

    # Determine repositories to install from
    repositories_to_install = []  # List of (owner, repo_name) tuples

    if args.url:
        # Parse URL
        result = parse_github_url(args.url)
        if result:
            owner, repo_name = result
            repositories_to_install.append((owner, repo_name))
        else:
            log_error(f"Failed to parse GitHub URL: {args.url}")
            return 1

    elif args.repo:
        # Parse owner/repo format
        parts = args.repo.split("/")
        if len(parts) == 2:
            owner, repo_name = parts
            repositories_to_install.append((owner, repo_name))
        else:
            log_error(f"Invalid repository format: {args.repo} (expected: owner/repo)")
            return 1
    else:
        # Search for plugins and allow multiple selections
        search_terms = " ".join(args.search_terms) if args.search_terms else None
        repos = client.search_repositories("topic:ttt-plugin", search_terms)

        if not repos:
            log_error("No plugins found matching search criteria")
            return 1

        # Let user select multiple repositories
        selected_repos = select_repositories(repos)
        if not selected_repos:
            log_warn("No repositories selected")
            return 0

        # Extract owner and repo names from selected repositories
        for repo in selected_repos:
            owner = repo["owner"]["login"]
            repo_name = repo["name"]
            repositories_to_install.append((owner, repo_name))

    # Process each selected repository
    total_installed = 0
    failed_repos = []

    for idx, (owner, repo_name) in enumerate(repositories_to_install, 1):
        console.print()
        log_step(
            f"[{idx}/{len(repositories_to_install)}] Processing repository: {owner}/{repo_name}"
        )

        # Find default branch
        branch = find_default_branch(client, owner, repo_name)
        log_info(f"Using branch: {branch}")

        # Get repository tree
        tree = client.get_repository_tree(owner, repo_name, branch)
        if not tree:
            log_error("Failed to fetch repository tree")
            failed_repos.append(f"{owner}/{repo_name}")
            continue

        # Filter plugin files
        plugin_files = get_plugin_files(tree)

        if not plugin_files:
            log_warn("No plugin files found in repository")
            log_info("Plugin files should be in: flows/, agents/, knowledge/, setup/, or scripts/")
            failed_repos.append(f"{owner}/{repo_name}")
            continue

        log_info(f"Found {len(plugin_files)} plugin files to install")

        # Confirm installation for this repository
        if len(repositories_to_install) > 1:
            console.print()
            console.print(
                f"[yellow]Ready to install {len(plugin_files)} files from {owner}/{repo_name} to:[/yellow]"
            )
            console.print(f"  {target_dir}")
            console.print()

            try:
                confirm = (
                    input(f"Continue with {owner}/{repo_name}? [Y/n/q to quit]: ").strip().lower()
                )
                if confirm == "q" or confirm == "quit":
                    log_warn("Installation cancelled by user")
                    break
                if confirm and confirm not in ("y", "yes"):
                    log_warn(f"Skipping {owner}/{repo_name}")
                    continue
            except (KeyboardInterrupt, EOFError):
                console.print("\n[yellow]Installation cancelled by user[/yellow]")
                break

        # Install files
        installed = install_plugin_files(client, owner, repo_name, plugin_files, target_dir, branch)

        if installed > 0:
            log_info(f"Successfully installed {installed} files from {owner}/{repo_name}")
            total_installed += installed
        else:
            log_error(f"No files were installed from {owner}/{repo_name}")
            failed_repos.append(f"{owner}/{repo_name}")

    # Final summary
    console.print()
    console.print("=" * 70)
    if total_installed > 0:
        log_info(f"Installation complete! Total files installed: {total_installed}")
        log_info(f"Plugin files are now available in: {target_dir}")

        if failed_repos:
            console.print()
            log_warn(f"Failed to install from {len(failed_repos)} repository/repositories:")
            for repo in failed_repos:
                console.print(f"  [yellow]✗[/yellow] {repo}")

        # Regenerate YAML catalogs to index plugin content
        console.print()
        if regenerate_yaml_catalogs(target_dir):
            log_info("Plugin content has been indexed and is now discoverable")
        else:
            log_warn("YAML catalog regeneration had issues, but plugin files are installed")
    else:
        log_error("No files were installed")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
