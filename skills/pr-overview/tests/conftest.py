# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pytest>=8.0",
#   "pytest-mock>=3.12",
# ]
# ///
"""
Pytest fixtures for pr-overview skill tests.

Defines fixtures locally - these duplicate the shared fixtures but avoid import issues.
For production use, consider a pytest plugin approach.
"""

from __future__ import annotations

import json
import subprocess
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import pytest


@dataclass
class MockCommandResult:
    """Represents a mocked command execution result."""

    stdout: str = ""
    stderr: str = ""
    returncode: int = 0


@dataclass
class CommandMocker:
    """Helper class to register and match mocked commands."""

    _mocks: dict[str, MockCommandResult] = field(default_factory=dict)
    _pattern_mocks: list[tuple[Callable[[list[str]], bool], MockCommandResult]] = field(
        default_factory=list
    )
    call_history: list[list[str]] = field(default_factory=list)

    def register(self, command_prefix: str, result: MockCommandResult) -> None:
        """Register a mock for commands starting with the given prefix."""
        self._mocks[command_prefix] = result

    def register_pattern(
        self, matcher: Callable[[list[str]], bool], result: MockCommandResult
    ) -> None:
        """Register a mock using a custom matcher function."""
        self._pattern_mocks.append((matcher, result))

    def get_result(self, cmd: list[str]) -> MockCommandResult | None:
        """Get the mock result for a command, or None if not mocked."""
        self.call_history.append(cmd)
        cmd_str = " ".join(cmd)

        # Check exact prefix matches first
        for prefix, result in self._mocks.items():
            if cmd_str.startswith(prefix):
                return result

        # Check pattern matchers
        for matcher, result in self._pattern_mocks:
            if matcher(cmd):
                return result

        return None


@pytest.fixture
def command_mocker() -> CommandMocker:
    """Provide a CommandMocker instance for registering mock commands."""
    return CommandMocker()


@pytest.fixture
def mock_subprocess(monkeypatch: Any, command_mocker: CommandMocker) -> None:
    """Mock subprocess.run to intercept external command calls."""

    def mock_run(
        cmd: list[str] | str,
        *args: Any,
        capture_output: bool = False,
        text: bool = False,
        check: bool = False,
        **kwargs: Any,
    ) -> subprocess.CompletedProcess[str]:
        if isinstance(cmd, str):
            cmd_list = cmd.split()
        else:
            cmd_list = list(cmd)

        result = command_mocker.get_result(cmd_list)
        if result is None:
            result = MockCommandResult()

        completed = subprocess.CompletedProcess(
            args=cmd_list,
            returncode=result.returncode,
            stdout=result.stdout if capture_output or text else None,
            stderr=result.stderr if capture_output or text else None,
        )

        if check and result.returncode != 0:
            raise subprocess.CalledProcessError(
                result.returncode, cmd_list, result.stdout, result.stderr
            )

        return completed

    monkeypatch.setattr("subprocess.run", mock_run)


@pytest.fixture
def mock_gh_pr_view(command_mocker: CommandMocker) -> Callable[[dict[str, Any]], None]:
    """Fixture to easily mock `gh pr view` responses."""

    def register_mock(pr_data: dict[str, Any]) -> None:
        command_mocker.register(
            "gh pr view",
            MockCommandResult(stdout=json.dumps(pr_data), returncode=0),
        )

    return register_mock
