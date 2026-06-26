#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pygithub>=2.1.1",
#   "pyyaml>=6.0",
#   "rich>=13.0.0",
# ]
# ///

"""
PR Creation Helper Script

Analyzes changes, validates against PR template, detects scope creep,
and helps create well-structured pull requests.

Usage:
    python pr_helper.py                    # Interactive mode
    python pr_helper.py --ticket PROJ-123  # With ticket validation
    python pr_helper.py --auto             # Auto-generate and create PR
"""

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

console = Console()


@dataclass
class PRTemplate:
    """Represents a parsed PR template."""

    path: Path
    content: str
    sections: list[str]
    checklist_items: list[str]


@dataclass
class ChangeAnalysis:
    """Analysis of changes in the current branch."""

    files_changed: list[str]
    commits: list[dict[str, str]]
    diff_stats: dict[str, int]
    directories: list[str]
    concerns: list[str]  # Detected areas of concern


def run_command(cmd: list[str], capture=True, check=True) -> str | None:
    """Run a shell command and return output."""
    try:
        if capture:
            result = subprocess.run(cmd, capture_output=True, text=True, check=check)
            return result.stdout.strip()
        else:
            subprocess.run(cmd, check=check)
            return None
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Command failed:[/red] {' '.join(cmd)}")
        if capture and e.stderr:
            console.print(f"[red]Error:[/red] {e.stderr}")
        return None
    except FileNotFoundError:
        console.print(f"[red]Command not found:[/red] {cmd[0]}")
        return None


def check_prerequisites() -> bool:
    """Verify required tools are available."""
    # Check gh CLI
    gh_version = run_command(["gh", "--version"])
    if not gh_version:
        console.print("[red]✗[/red] GitHub CLI (gh) not found. Install: https://cli.github.com/")
        return False
    console.print(f"[green]✓[/green] GitHub CLI: {gh_version.split()[2]}")

    # Check gh auth status
    auth_status = run_command(["gh", "auth", "status"], check=False)
    if not auth_status or "Logged in" not in auth_status:
        console.print("[red]✗[/red] Not authenticated. Run: gh auth login")
        return False
    console.print("[green]✓[/green] Authenticated with GitHub")

    # Check we're in a git repo
    is_repo = run_command(["git", "rev-parse", "--git-dir"], check=False)
    if not is_repo:
        console.print("[red]✗[/red] Not in a git repository")
        return False
    console.print("[green]✓[/green] Git repository detected")

    return True


def get_current_branch() -> str | None:
    """Get the current git branch name."""
    return run_command(["git", "branch", "--show-current"])


def get_default_branch() -> str:
    """Get the default branch (main/master)."""
    # Try to get from remote
    default = run_command(["git", "symbolic-ref", "refs/remotes/origin/HEAD"], check=False)
    if default:
        return default.split("/")[-1]

    # Fallback: check if main or master exists
    for branch in ["main", "master"]:
        exists = run_command(["git", "rev-parse", "--verify", branch], check=False)
        if exists:
            return branch

    return "main"


def analyze_changes(base_branch: str) -> ChangeAnalysis:
    """Analyze changes between current branch and base."""
    # Get list of changed files
    files = run_command(["git", "diff", "--name-only", base_branch])
    files_list = files.split("\n") if files else []

    # Get commit history
    commits_raw = run_command(
        ["git", "log", f"{base_branch}..HEAD", "--pretty=format:%H|%s|%an|%ar"]
    )
    commits = []
    if commits_raw:
        for line in commits_raw.split("\n"):
            parts = line.split("|")
            if len(parts) == 4:
                commits.append(
                    {
                        "hash": parts[0][:7],
                        "message": parts[1],
                        "author": parts[2],
                        "date": parts[3],
                    }
                )

    # Get diff stats
    stats_raw = run_command(["git", "diff", "--stat", base_branch])
    stats = {"files": len(files_list), "insertions": 0, "deletions": 0}
    if stats_raw:
        insertions_match = re.search(r"(\d+) insertion", stats_raw)
        deletions_match = re.search(r"(\d+) deletion", stats_raw)
        if insertions_match:
            stats["insertions"] = int(insertions_match.group(1))
        if deletions_match:
            stats["deletions"] = int(deletions_match.group(2))

    # Extract directories (exclude root-level files)
    directories = list(
        set(str(Path(f).parts[0]) for f in files_list if f and "/" in f and len(Path(f).parts) > 1)
    )

    # Detect concerns (simplified heuristic)
    concerns = []
    dir_count = len(directories)
    if dir_count > 3:
        concerns.append(f"Changes span {dir_count} directories")

    commit_prefixes = set(commit["message"].split(":")[0].split("(")[0] for commit in commits)
    if len(commit_prefixes) > 2:
        concerns.append(f"Multiple commit types: {', '.join(commit_prefixes)}")

    return ChangeAnalysis(
        files_changed=files_list,
        commits=commits,
        diff_stats=stats,
        directories=directories,
        concerns=concerns,
    )


def find_pr_template() -> PRTemplate | None:
    """Find and parse PR template."""
    possible_paths = [
        Path(".github/pull_request_template.md"),
        Path(".github/PULL_REQUEST_TEMPLATE.md"),
        Path("pull_request_template.md"),
        Path("PULL_REQUEST_TEMPLATE.md"),
    ]

    for path in possible_paths:
        if path.exists():
            content = path.read_text()

            # Extract sections
            sections = re.findall(r"^##\s+(.+)$", content, re.MULTILINE)

            # Extract checklist items
            checklist = re.findall(r"^\s*-\s+\[\s*\]\s+(.+)$", content, re.MULTILINE)

            console.print(f"[green]✓[/green] Found PR template: {path}")
            return PRTemplate(
                path=path, content=content, sections=sections, checklist_items=checklist
            )

    console.print("[yellow]![/yellow] No PR template found")
    return None


def _update_checklist_items(body: str, analysis: ChangeAnalysis) -> str:
    """Intelligently update checklist items based on actual changes.

    Only checks items that can be verified from the analysis.
    Leaves uncertain items unchecked for manual review.
    """
    # Check if tests were added/updated
    test_files = [f for f in analysis.files_changed if "test" in f.lower() or "spec" in f.lower()]
    if test_files:
        body = re.sub(
            r"(-\s+\[\s+\]\s+.*?(?:test|testing).*?)$",
            r"- [x] \1".replace("- [ ]", "").strip(),
            body,
            flags=re.IGNORECASE | re.MULTILINE,
        )

    # Check if documentation was updated
    doc_files = [
        f
        for f in analysis.files_changed
        if any(ext in f.lower() for ext in [".md", "readme", "doc", "changelog"])
    ]
    if doc_files:
        body = re.sub(
            r"(-\s+\[\s+\]\s+.*?(?:documentation|docs|readme).*?)$",
            r"- [x] \1".replace("- [ ]", "").strip(),
            body,
            flags=re.IGNORECASE | re.MULTILINE,
        )

    return body


def generate_pr_body(analysis: ChangeAnalysis, template: PRTemplate | None, title: str) -> str:
    """Generate PR body based on analysis and template."""

    # Build summary
    summary = f"{title}\n\nThis PR includes {len(analysis.files_changed)} file(s) "
    summary += f"with {analysis.diff_stats['insertions']}+ / {analysis.diff_stats['deletions']}- lines changed."

    # Build what changed section
    what_changed = []
    for commit in analysis.commits:
        # Clean up commit message
        msg = commit["message"]
        if ":" in msg:
            msg = msg.split(":", 1)[1].strip()
        what_changed.append(f"- {msg}")

    # Build testing section
    testing = [
        "1. Clone the repository and checkout this branch",
        "2. Verify the changes work as expected",
        "3. Run existing tests to ensure no regressions",
    ]

    # Build body
    if template:
        body = template.content

        # Fill in summary
        body = re.sub(
            r"##\s+Summary\s*\n\n.*?(?=##|\Z)",
            f"## Summary\n\n{summary}\n\n",
            body,
            flags=re.DOTALL,
        )

        # Fill in what changed
        changes_text = "\n".join(what_changed)
        body = re.sub(
            r"(##\s+What changed\s*\n\n).*?(?=##|\Z)",
            f"\\1{changes_text}\n\n",
            body,
            flags=re.DOTALL,
        )

        # Fill in testing
        testing_text = "\n".join(testing)
        body = re.sub(
            r"(##\s+How to test\s*\n\n).*?(?=##|\Z)",
            f"\\1{testing_text}\n\n",
            body,
            flags=re.DOTALL,
        )

        # Update checklist items based on actual changes
        body = _update_checklist_items(body, analysis)

    else:
        # Create basic template
        body = f"""## Summary

{summary}

## What changed

{chr(10).join(what_changed)}

## How to test

{chr(10).join(testing)}
"""

    return body


def detect_ticket_from_branch(branch_name: str) -> str | None:
    """Extract ticket number from branch name."""
    # Common patterns: feature/PROJ-123, bugfix/TEAM-456-description
    patterns = [
        r"([A-Z]+-\d+)",
        r"([A-Z]+\d+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, branch_name, re.IGNORECASE)
        if match:
            return match.group(1).upper()

    return None


def read_ticket_from_memory() -> tuple[str, dict[str, str]] | None:
    """Read current ticket from memory file.

    Returns:
        A tuple (ticket_id: str, ticket_info: dict[str, str]) if the file exists and is valid,
        or None if the file doesn't exist or is invalid.
    """
    memory_file = Path(".ttt/memory/current-ticket.md")

    if not memory_file.exists():
        return None

    try:
        content = memory_file.read_text().strip()
        if not content:
            return None

        # Extract ticket ID (first line or heading)
        lines = content.split("\n")
        first_line = lines[0].strip()

        # Try to extract from heading: "# Current Ticket: PROJ-123"
        heading_match = re.search(
            r"#\s*Current Ticket:\s*([A-Z]+-?\d+|#\d+)", first_line, re.IGNORECASE
        )
        if heading_match:
            ticket_id = heading_match.group(1)
        else:
            # Assume first line is ticket ID
            ticket_id = first_line

        # Parse additional info if available
        ticket_info = {"id": ticket_id}

        # Extract title
        title_match = re.search(r"\*\*Title:\*\*\s*(.+)", content)
        if title_match:
            ticket_info["title"] = title_match.group(1).strip()

        # Extract link
        link_match = re.search(r"\*\*Link:\*\*\s*(.+)", content)
        if link_match:
            ticket_info["link"] = link_match.group(1).strip()

        # Extract status
        status_match = re.search(r"\*\*Status:\*\*\s*(.+)", content)
        if status_match:
            ticket_info["status"] = status_match.group(1).strip()

        console.print(f"[cyan]Found ticket in memory:[/cyan] {ticket_id}")
        return (ticket_id, ticket_info)

    except Exception as e:
        console.print(f"[yellow]Warning: Could not read ticket memory:[/yellow] {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description="PR Creation Helper")
    parser.add_argument("--ticket", help="Ticket/issue number for validation")
    parser.add_argument("--base", help="Base branch (default: main)")
    parser.add_argument("--auto", action="store_true", help="Auto-create PR")
    parser.add_argument("--title", help="PR title")
    args = parser.parse_args()

    console.print(Panel.fit("🚀 PR Creation Helper", style="bold blue"))

    # Check prerequisites
    if not check_prerequisites():
        sys.exit(1)

    # Get branches
    current_branch = get_current_branch()
    if not current_branch:
        console.print("[red]Failed to get current branch[/red]")
        sys.exit(1)

    base_branch = args.base or get_default_branch()
    console.print(f"\n[cyan]Current branch:[/cyan] {current_branch}")
    console.print(f"[cyan]Base branch:[/cyan] {base_branch}")

    # Check for ticket in memory first (unless explicitly provided)
    ticket = args.ticket
    ticket_info = {}

    if not ticket:
        # Try to read from memory
        memory_result = read_ticket_from_memory()
        if memory_result:
            memory_ticket_id, ticket_info = memory_result

            # Ask user to confirm
            if not args.auto:
                ticket_display = memory_ticket_id
                if "title" in ticket_info:
                    ticket_display = f"{memory_ticket_id} ({ticket_info['title']})"

                if Confirm.ask(
                    f"Found ticket [cyan]{ticket_display}[/cyan] in memory. Is this the right ticket for this PR?"
                ):
                    ticket = memory_ticket_id
                    console.print(f"[green]✓[/green] Using ticket {memory_ticket_id}")
                else:
                    # Ask for different ticket
                    new_ticket = Prompt.ask("Enter ticket ID (or press Enter to skip)", default="")
                    if new_ticket:
                        ticket = new_ticket
            else:
                # Auto mode: use memory ticket
                ticket = memory_ticket_id

        # If still no ticket, try to detect from branch
        if not ticket:
            ticket = detect_ticket_from_branch(current_branch)
            if ticket:
                console.print(f"[cyan]Detected ticket from branch:[/cyan] {ticket}")

    if ticket and not ticket_info:
        console.print(f"[cyan]Using ticket:[/cyan] {ticket}")

    # Analyze changes
    console.print("\n[bold]Analyzing changes...[/bold]")
    analysis = analyze_changes(base_branch)

    console.print(f"  Files changed: {len(analysis.files_changed)}")
    console.print(f"  Commits: {len(analysis.commits)}")
    console.print(f"  Directories: {', '.join(analysis.directories[:5])}")

    if analysis.concerns:
        console.print("\n[yellow]⚠ Potential scope concerns:[/yellow]")
        for concern in analysis.concerns:
            console.print(f"  • {concern}")

        if not args.auto:
            if not Confirm.ask("Continue with PR creation?"):
                console.print("[yellow]Aborted[/yellow]")
                sys.exit(0)

    # Find PR template
    template = find_pr_template()

    # Generate title
    if args.title:
        title = args.title
    elif analysis.commits:
        # Use first commit message as title
        title = analysis.commits[0]["message"]
    else:
        title = Prompt.ask("\n[cyan]Enter PR title[/cyan]")

    # Generate body
    body = generate_pr_body(analysis, template, title)

    # Show preview
    if not args.auto:
        console.print("\n[bold]PR Preview:[/bold]")
        console.print(Panel(Markdown(f"# {title}\n\n{body}"), expand=False))

        if not Confirm.ask("\nCreate PR?"):
            console.print("[yellow]Aborted[/yellow]")
            sys.exit(0)

    # Push branch if needed
    console.print("\n[bold]Pushing branch...[/bold]")
    push_result = run_command(["git", "push", "-u", "origin", current_branch], check=False)

    if push_result is None:
        console.print("[red]Failed to push branch[/red]")
        sys.exit(1)

    # Create PR
    console.print("[bold]Creating pull request...[/bold]")
    pr_cmd = [
        "gh",
        "pr",
        "create",
        "--title",
        title,
        "--body",
        body,
        "--base",
        base_branch,
    ]

    pr_url = run_command(pr_cmd)

    if pr_url:
        console.print("\n[green]✓ Pull request created![/green]")
        console.print(f"[cyan]URL:[/cyan] {pr_url}")
    else:
        console.print("[red]Failed to create PR[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
