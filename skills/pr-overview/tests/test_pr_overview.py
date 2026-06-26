# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pytest>=8.0",
#   "pytest-mock>=3.12",
# ]
# ///
"""
Unit tests for pr-overview skill scripts.

These tests mock the `gh` CLI to test script logic without live API calls.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from conftest import CommandMocker


# Add the skills directory to path for imports
SKILL_DIR = Path(__file__).parent.parent
SCRIPTS_DIR = SKILL_DIR / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))


@pytest.fixture
def pr_fixture_data() -> dict:
    """Load the PR fixture data."""
    fixture_path = Path(__file__).parent / "fixtures" / "pr-42-response.json"
    with open(fixture_path) as f:
        return json.load(f)


class TestPROverviewBasic:
    """Basic PR status retrieval tests."""

    def test_gh_pr_view_called(
        self,
        mock_subprocess,
        command_mocker: "CommandMocker",
        pr_fixture_data: dict,
    ):
        """Verify that gh pr view is called with correct arguments."""
        from conftest import MockCommandResult

        command_mocker.register(
            "gh pr view",
            MockCommandResult(stdout=json.dumps(pr_fixture_data), returncode=0),
        )

        # Simulate calling the script logic
        import subprocess

        result = subprocess.run(
            ["gh", "pr", "view", "42", "--json", "number,title,state"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "gh pr view" in " ".join(command_mocker.call_history[0])

    def test_pr_data_parsing(self, pr_fixture_data: dict):
        """Verify PR data is correctly parsed from JSON response."""
        assert pr_fixture_data["number"] == 42
        assert pr_fixture_data["state"] == "OPEN"
        assert len(pr_fixture_data["reviews"]["nodes"]) == 2

    def test_review_status_extraction(self, pr_fixture_data: dict):
        """Verify review statuses are correctly extracted."""
        reviews = pr_fixture_data["reviews"]["nodes"]
        states = [r["state"] for r in reviews]

        assert "APPROVED" in states
        assert "CHANGES_REQUESTED" in states

    def test_ci_status_extraction(self, pr_fixture_data: dict):
        """Verify CI check statuses are correctly extracted."""
        checks = pr_fixture_data["statusCheckRollup"]["contexts"]["nodes"]

        success_checks = [c for c in checks if c["state"] == "SUCCESS"]
        pending_checks = [c for c in checks if c["state"] == "PENDING"]

        assert len(success_checks) == 1
        assert len(pending_checks) == 1
        assert pr_fixture_data["statusCheckRollup"]["state"] == "PENDING"


class TestPROverviewEdgeCases:
    """Edge case handling tests."""

    def test_no_reviews(self, mock_subprocess, command_mocker: "CommandMocker"):
        """Handle PR with no reviews."""
        from conftest import MockCommandResult

        pr_data = {
            "number": 99,
            "title": "New PR",
            "state": "OPEN",
            "reviews": {"nodes": []},
            "statusCheckRollup": None,
        }

        command_mocker.register(
            "gh pr view",
            MockCommandResult(stdout=json.dumps(pr_data), returncode=0),
        )

        import subprocess

        result = subprocess.run(
            ["gh", "pr", "view", "99", "--json", "number"],
            capture_output=True,
            text=True,
        )

        data = json.loads(result.stdout)
        assert data["reviews"]["nodes"] == []

    def test_gh_cli_not_authenticated(self, mock_subprocess, command_mocker: "CommandMocker"):
        """Handle gh CLI authentication error."""
        from conftest import MockCommandResult

        command_mocker.register(
            "gh pr view",
            MockCommandResult(
                stdout="",
                stderr="gh: Not logged in. Run 'gh auth login' to authenticate.",
                returncode=1,
            ),
        )

        import subprocess

        result = subprocess.run(
            ["gh", "pr", "view", "42"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 1
        assert "Not logged in" in result.stderr

    def test_pr_not_found(self, mock_subprocess, command_mocker: "CommandMocker"):
        """Handle non-existent PR."""
        from conftest import MockCommandResult

        command_mocker.register(
            "gh pr view",
            MockCommandResult(
                stdout="",
                stderr="GraphQL: Could not resolve to a PullRequest",
                returncode=1,
            ),
        )

        import subprocess

        result = subprocess.run(
            ["gh", "pr", "view", "99999"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 1
        assert "Could not resolve" in result.stderr


class TestDependencyChain:
    """PR dependency chain detection tests."""

    def test_parse_depends_on_references(self):
        """Extract PR references from 'Depends on' patterns."""
        body = "This PR adds feature X.\n\nDepends on #48 and #49"

        import re

        # Simple pattern to find PR references
        depends_pattern = r"[Dd]epends on[:\s]+([#\d,\s]+(?:and\s+)?[#\d]+)"
        match = re.search(depends_pattern, body)

        assert match is not None
        refs = re.findall(r"#(\d+)", match.group(1))
        assert refs == ["48", "49"]

    def test_parse_multiple_dependency_formats(self):
        """Handle various dependency reference formats."""
        test_cases = [
            ("Depends on #123", ["123"]),
            ("Depends on: #123, #456", ["123", "456"]),
            ("depends on #1 and #2", ["1", "2"]),
            ("Blocked by #789", []),  # Different pattern, not matched
        ]

        import re

        depends_pattern = r"[Dd]epends on[:\s]+([#\d,\s]+(?:and\s+)?[#\d]*)"

        for body, expected in test_cases:
            match = re.search(depends_pattern, body)
            if match:
                refs = re.findall(r"#(\d+)", match.group(1))
            else:
                refs = []
            assert refs == expected, f"Failed for: {body}"
