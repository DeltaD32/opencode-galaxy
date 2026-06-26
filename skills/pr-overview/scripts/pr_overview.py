#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "rich>=13.7.0",
# ]
# ///

"""
Pull Request Overview Tool

Displays comprehensive PR status including CI checks, reviews, dependencies,
and reviewer assignments for GitHub repositories.
"""

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from rich import box
from rich.console import Console
from rich.table import Table

console = Console()


class CIStatus(Enum):
    """CI check status."""

    PASS = ("✅ Pass", "green")
    FAIL = ("❌ Fail", "red")
    PENDING = ("⏳ Pending", "yellow")
    NONE = ("⚪ None", "dim")

    def __init__(self, display: str, color: str):
        self.display = display
        self.color = color


class ReviewStatus(Enum):
    """Review decision status."""

    APPROVED = ("✅ Approved", "green")
    CHANGES_REQUESTED = ("📝 Changes", "red")
    COMMENTED = ("💬 Comments", "yellow")
    PENDING = ("⏳ Pending", "dim")

    def __init__(self, display: str, color: str):
        self.display = display
        self.color = color


@dataclass
class PRInfo:
    """Pull request information."""

    number: int
    title: str
    author: str
    state: str
    url: str
    updated_at: str
    ci_status: CIStatus
    review_status: ReviewStatus
    reviewers: list[str]
    threads_resolved: int
    threads_total: int
    dependencies: list[int]
    is_draft: bool
    mergeable: str


class PROverview:
    """Fetch and display pull request overview."""

    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path).resolve()
        self.repo_owner: Optional[str] = None
        self.repo_name: Optional[str] = None
        self.gh_host: Optional[str] = None
        self._detect_repository()

    def _detect_repository(self) -> None:
        """Detect repository owner and name from git remote."""
        try:
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True,
            )
            remote_url = result.stdout.strip()

            # Parse various git URL formats
            # SSH: git@github.com:owner/repo.git or git@bmw.ghe.com:owner/repo.git
            # HTTPS: https://github.com/owner/repo.git or https://bmw.ghe.com/owner/repo.git

            # Extract host from URL
            host_match = re.search(r"^(?:https?://|git@)([^/:]+)", remote_url)
            if host_match:
                self.gh_host = host_match.group(1)

            # Extract owner and repo name
            match = re.search(r"[:/]([^/]+)/([^/]+?)(\.git)?$", remote_url)
            if match:
                self.repo_owner = match.group(1)
                self.repo_name = match.group(2)
            else:
                raise ValueError(f"Could not parse repository from URL: {remote_url}")

        except subprocess.CalledProcessError as e:
            console.print("[red]Error: Not in a git repository or no remote 'origin' found[/red]")
            console.print(f"[dim]{e}[/dim]")
            sys.exit(1)

    def _run_gh_command(self, args: list[str]) -> str:
        """Run gh CLI command and return output."""
        try:
            # Set up environment with correct GH_HOST
            env = os.environ.copy()
            if self.gh_host:
                env["GH_HOST"] = self.gh_host

            result = subprocess.run(
                ["gh"] + args,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True,
                env=env,
            )
            return result.stdout.strip()
        except FileNotFoundError:
            console.print("[red]Error: gh CLI not found. Please install it:[/red]")
            console.print("  https://cli.github.com/")
            sys.exit(1)
        except subprocess.CalledProcessError as e:
            console.print(f"[red]Error running gh command:[/red] {e}")
            if e.stderr:
                console.print(f"[dim]{e.stderr}[/dim]")
            sys.exit(1)

    def _get_current_user(self) -> str:
        """Get current authenticated GitHub user."""
        output = self._run_gh_command(["api", "user", "--jq", ".login"])
        return output

    def _fetch_pr_data(
        self,
        state: str = "open",
        author: Optional[str] = None,
        pr_number: Optional[int] = None,
    ) -> list[dict[str, Any]]:
        """Fetch PR data using gh CLI with GraphQL."""

        if pr_number:
            # Fetch specific PR
            query = """
            query($owner: String!, $repo: String!, $number: Int!) {
              repository(owner: $owner, name: $repo) {
                pullRequest(number: $number) {
                  number
                  title
                  author { login }
                  state
                  url
                  updatedAt
                  isDraft
                  mergeable
                  body
                  reviewDecision
                  reviewRequests(first: 10) {
                    nodes {
                      requestedReviewer {
                        ... on User { login }
                        ... on Team { name }
                      }
                    }
                  }
                  latestReviews(first: 50) {
                    nodes {
                      author { login }
                      state
                    }
                  }
                  reviewThreads(first: 100) {
                    totalCount
                    nodes {
                      isResolved
                    }
                  }
                  commits(last: 1) {
                    nodes {
                      commit {
                        statusCheckRollup {
                          state
                        }
                      }
                    }
                  }
                }
              }
            }
            """
        else:
            # Fetch multiple PRs
            search_query = f"repo:{self.repo_owner}/{self.repo_name} is:pr state:{state}"
            if author:
                search_query += f" author:{author}"

            query = """
            query($searchQuery: String!, $first: Int!) {
              search(query: $searchQuery, type: ISSUE, first: $first) {
                nodes {
                  ... on PullRequest {
                    number
                    title
                    author { login }
                    state
                    url
                    updatedAt
                    isDraft
                    mergeable
                    body
                    reviewDecision
                    reviewRequests(first: 10) {
                      nodes {
                        requestedReviewer {
                          ... on User { login }
                          ... on Team { name }
                        }
                      }
                    }
                    latestReviews(first: 50) {
                      nodes {
                        author { login }
                        state
                      }
                    }
                    reviewThreads(first: 100) {
                      totalCount
                      nodes {
                        isResolved
                      }
                    }
                    commits(last: 1) {
                      nodes {
                        commit {
                          statusCheckRollup {
                            state
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
            """
            variables = {
                "searchQuery": search_query,
                "first": 100,
            }

        # Build gh command with proper variable flags
        cmd = ["api", "graphql"]

        # Add variables based on which query we're using
        if pr_number:
            cmd.extend(
                [
                    "-f",
                    f"query={query}",
                    "-f",
                    f"owner={self.repo_owner}",
                    "-f",
                    f"repo={self.repo_name}",
                    "-F",
                    f"number={pr_number}",
                ]
            )
        else:
            cmd.extend(
                [
                    "-f",
                    f"query={query}",
                    "-f",
                    f"searchQuery={variables['searchQuery']}",
                    "-F",
                    f"first={variables['first']}",
                ]
            )

        result = self._run_gh_command(cmd)

        data = json.loads(result)

        if pr_number:
            pr = data.get("data", {}).get("repository", {}).get("pullRequest")
            return [pr] if pr else []
        else:
            return data.get("data", {}).get("search", {}).get("nodes", [])

    def _parse_dependencies(self, body: str) -> list[int]:
        """Parse Depends-On: #123 patterns from PR body."""
        if not body:
            return []

        # Match patterns like "Depends-On: #123" or "Depends-On: #123, #456"
        # Find all lines containing "Depends-On:"
        depends_lines = re.findall(r"Depends-On:([^\n]+)", body, re.IGNORECASE)
        deps = []
        for line in depends_lines:
            # Find all #<number> occurrences in the line
            pr_numbers = re.findall(r"#(\d+)", line)
            deps.extend(int(num) for num in pr_numbers)

        return deps

    def _determine_ci_status(self, pr_data: dict[str, Any]) -> CIStatus:
        """Determine CI status from PR data."""
        commits = pr_data.get("commits", {}).get("nodes", [])
        if not commits:
            return CIStatus.NONE

        rollup = commits[0].get("commit", {}).get("statusCheckRollup")
        if not rollup:
            return CIStatus.NONE

        state = rollup.get("state", "").upper()

        status_map = {
            "SUCCESS": CIStatus.PASS,
            "FAILURE": CIStatus.FAIL,
            "ERROR": CIStatus.FAIL,
            "PENDING": CIStatus.PENDING,
            "EXPECTED": CIStatus.PENDING,
        }

        return status_map.get(state, CIStatus.NONE)

    def _determine_review_status(self, pr_data: dict[str, Any]) -> ReviewStatus:
        """Determine review status from PR data."""
        decision = pr_data.get("reviewDecision")

        if decision == "APPROVED":
            return ReviewStatus.APPROVED
        elif decision == "CHANGES_REQUESTED":
            return ReviewStatus.CHANGES_REQUESTED
        elif decision == "REVIEW_REQUIRED":
            return ReviewStatus.PENDING

        # Check if there are any comments
        reviews = pr_data.get("latestReviews", {}).get("nodes", [])
        if reviews:
            return ReviewStatus.COMMENTED

        return ReviewStatus.PENDING

    def _get_reviewers(self, pr_data: dict[str, Any]) -> list[str]:
        """Get list of assigned reviewers."""
        reviewers = []

        # Get requested reviewers
        requests = pr_data.get("reviewRequests", {}).get("nodes", [])
        for request in requests:
            reviewer = request.get("requestedReviewer", {})
            if "login" in reviewer:
                reviewers.append(reviewer["login"])
            elif "name" in reviewer:
                reviewers.append(f"team:{reviewer['name']}")

        # Get reviewers who have already reviewed
        reviews = pr_data.get("latestReviews", {}).get("nodes", [])
        for review in reviews:
            author = review.get("author", {}).get("login")
            if author and author not in reviewers:
                reviewers.append(author)

        return reviewers

    def _get_thread_counts(self, pr_data: dict[str, Any]) -> tuple[int, int]:
        """Get resolved and total thread counts."""
        threads = pr_data.get("reviewThreads", {})
        total = threads.get("totalCount", 0)

        nodes = threads.get("nodes", [])
        resolved = sum(1 for node in nodes if node.get("isResolved", False))

        return resolved, total

    def _days_since_update(self, updated_at: str) -> str:
        """Calculate days since last update."""
        updated = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        delta = now - updated

        days = delta.days
        hours = delta.seconds // 3600

        if days == 0:
            if hours == 0:
                return "just now"
            return f"{hours}h ago"
        elif days == 1:
            return "1 day ago"
        else:
            return f"{days} days ago"

    def _parse_pr(self, pr_data: dict[str, Any]) -> PRInfo:
        """Parse PR data into PRInfo object."""
        resolved, total = self._get_thread_counts(pr_data)

        return PRInfo(
            number=pr_data["number"],
            title=pr_data["title"],
            author=pr_data.get("author", {}).get("login", "unknown"),
            state=pr_data["state"],
            url=pr_data["url"],
            updated_at=self._days_since_update(pr_data["updatedAt"]),
            ci_status=self._determine_ci_status(pr_data),
            review_status=self._determine_review_status(pr_data),
            reviewers=self._get_reviewers(pr_data),
            threads_resolved=resolved,
            threads_total=total,
            dependencies=self._parse_dependencies(pr_data.get("body", "")),
            is_draft=pr_data.get("isDraft", False),
            mergeable=pr_data.get("mergeable", "UNKNOWN"),
        )

    def _check_dependency_status(self, pr_number: int) -> tuple[str, bool]:
        """Check if a dependency PR is ready to merge."""
        try:
            pr_data = self._fetch_pr_data(pr_number=pr_number)
            if not pr_data:
                return "not found", False

            pr = self._parse_pr(pr_data[0])

            is_ready = (
                pr.state == "OPEN"
                and not pr.is_draft
                and pr.ci_status == CIStatus.PASS
                and pr.review_status == ReviewStatus.APPROVED
            )

            return pr.state.lower(), is_ready
        except Exception as e:
            return f"error: {e}", False

    def display_overview(
        self,
        state: str = "open",
        author: Optional[str] = None,
        show_all: bool = False,
        pr_number: Optional[int] = None,
    ) -> None:
        """Display PR overview table."""

        # Determine filter
        if pr_number:
            filter_desc = f"PR #{pr_number}"
        elif show_all:
            filter_desc = f"All {state} PRs"
            author = None
        else:
            if not author:
                author = self._get_current_user()
            filter_desc = f"{author}'s {state} PRs"

        console.print(
            f"\n[bold]Pull Request Overview for {self.repo_owner}/{self.repo_name}[/bold]"
        )
        console.print(f"[dim]{filter_desc}[/dim]\n")

        # Fetch PR data
        with console.status("Fetching PR data..."):
            pr_data_list = self._fetch_pr_data(state=state, author=author, pr_number=pr_number)

        if not pr_data_list:
            console.print("[yellow]No pull requests found.[/yellow]")
            return

        # Parse PRs
        prs = [self._parse_pr(pr_data) for pr_data in pr_data_list]

        # Create table
        table = Table(box=box.ROUNDED, show_header=True, header_style="bold cyan")
        table.add_column("PR", style="cyan", no_wrap=True)
        table.add_column("Title", style="white")
        table.add_column("CI Status", no_wrap=True)
        table.add_column("Review", no_wrap=True)
        table.add_column("Updated", no_wrap=True)
        table.add_column("Reviewers", no_wrap=True)
        table.add_column("Threads", no_wrap=True)

        # Track dependencies
        all_dependencies: dict[int, list[int]] = {}

        for pr in prs:
            # Format reviewers
            if pr.reviewers:
                reviewers_display = f"✅ {', '.join(pr.reviewers[:2])}"
                if len(pr.reviewers) > 2:
                    reviewers_display += f" +{len(pr.reviewers) - 2}"
            else:
                reviewers_display = "⚠️  none"

            # Format threads
            if pr.threads_total == 0:
                threads_display = "—"
            else:
                all_resolved = pr.threads_resolved == pr.threads_total
                symbol = "✅" if all_resolved else "⏳"
                threads_display = f"{pr.threads_resolved}/{pr.threads_total} {symbol}"

            # Format title (truncate if too long, add draft indicator)
            title = pr.title
            if pr.is_draft:
                title = f"[dim]DRAFT:[/dim] {title}"
            if len(title) > 40:
                title = title[:37] + "..."

            table.add_row(
                f"#{pr.number}",
                title,
                f"[{pr.ci_status.color}]{pr.ci_status.display}[/{pr.ci_status.color}]",
                f"[{pr.review_status.color}]{pr.review_status.display}[/{pr.review_status.color}]",
                pr.updated_at,
                reviewers_display,
                threads_display,
            )

            if pr.dependencies:
                all_dependencies[pr.number] = pr.dependencies

        console.print(table)

        # Display dependency information
        if all_dependencies:
            console.print("\n[bold]Dependencies:[/bold]")
            all_ready = True

            for pr_num, deps in all_dependencies.items():
                for dep in deps:
                    with console.status(f"Checking PR #{dep}..."):
                        state, is_ready = self._check_dependency_status(dep)

                    status_symbol = "✅" if is_ready else "⚠️"
                    status_text = "ready to merge" if is_ready else f"{state}"
                    console.print(
                        f"  PR #{pr_num} → Depends on: #{dep} ({status_symbol} {status_text})"
                    )

                    if not is_ready:
                        all_ready = False

            if all_ready:
                console.print("\n[green]✅ All dependencies are ready to merge[/green]")
            else:
                console.print("\n[yellow]⚠️  Some dependencies are not ready[/yellow]")

        # Display summary
        console.print("\n[bold]Summary:[/bold]")
        ready = sum(
            1
            for pr in prs
            if pr.ci_status == CIStatus.PASS
            and pr.review_status == ReviewStatus.APPROVED
            and not pr.is_draft
        )
        needs_changes = sum(1 for pr in prs if pr.review_status == ReviewStatus.CHANGES_REQUESTED)
        pending_review = sum(1 for pr in prs if pr.review_status == ReviewStatus.PENDING)
        failing_ci = sum(1 for pr in prs if pr.ci_status == CIStatus.FAIL)

        if ready > 0:
            console.print(f"  • {ready} PR(s) ready to merge")
        if needs_changes > 0:
            console.print(f"  • {needs_changes} PR(s) need changes")
        if pending_review > 0:
            console.print(f"  • {pending_review} PR(s) awaiting review")
        if failing_ci > 0:
            console.print(f"  • {failing_ci} PR(s) with failing CI")

        if all_dependencies and all(
            self._check_dependency_status(dep)[1]
            for deps in all_dependencies.values()
            for dep in deps
        ):
            console.print("  • All dependencies resolved ✅")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Display comprehensive pull request overview",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Show your open PRs
  %(prog)s

  # Show all open PRs in the repository
  %(prog)s --all

  # Show PRs by specific user
  %(prog)s --user alice

  # Check specific PR with dependencies
  %(prog)s --pr 42

  # Include closed PRs
  %(prog)s --state all
        """,
    )

    parser.add_argument(
        "--repo",
        default=".",
        help="Path to git repository (default: current directory)",
    )
    parser.add_argument(
        "--user",
        help="Filter PRs by author (default: current authenticated user)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Show all PRs in repository (ignores --user)",
    )
    parser.add_argument(
        "--pr",
        type=int,
        help="Show specific PR by number",
    )
    parser.add_argument(
        "--state",
        choices=["open", "closed", "all"],
        default="open",
        help="Filter PRs by state (default: open)",
    )

    args = parser.parse_args()

    overview = PROverview(repo_path=args.repo)
    overview.display_overview(
        state=args.state,
        author=args.user,
        show_all=args.all,
        pr_number=args.pr,
    )


if __name__ == "__main__":
    main()
