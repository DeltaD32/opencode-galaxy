#!/usr/bin/env python3
# /// script
# requires-python = ">=3.14"
# dependencies = [
# ]
# ///
"""
Shared utilities for setup scripts.

This module provides common functionality for:
- Colored console output (Rich-based)
- Prerequisite checking (commands, Docker, etc.)
- User input prompts and selections
- Setup completion reporting
- Environment detection

These utilities are used by both MCP server setup scripts and other
setup scripts like setup-bmad.py.
"""

import json
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional

from rich.console import Console
from rich.panel import Panel

# Initialize Rich console for consistent output
console = Console()


# ============================================================================
# Console Output Utilities
# ============================================================================


def print_script_header(title: str, subtitle: Optional[str] = None, width: int = 70):
    """Print standardized script header using Rich.

    Args:
        title: Main title of the script
        subtitle: Optional subtitle for additional context
        width: Width of the header box (default: 70)
    """
    console.print()
    content = f"[bold]{title}[/bold]"
    if subtitle:
        content += f"\n{subtitle}"
    console.print(Panel(content, width=width, style="cyan"))
    console.print()


def log_info(msg: str):
    """Log an informational message in green."""
    console.print(f"[green]:heavy_check_mark: INFO[/green] {msg}")


def log_warn(msg: str):
    """Log a warning message in yellow."""
    console.print(f"[yellow]:warning: WARNING[/yellow] {msg}")


def log_error(msg: str):
    """Log an error message in red."""
    console.print(f"[red]:x: ERROR[/red] {msg}")


def log_manual(msg: str):
    """Log a manual action required message in blue."""
    console.print(f"[blue]:wrench: MANUAL STEP REQUIRED[/blue] {msg}")


def log_step(msg: str):
    """Log a step message in cyan."""
    console.print(f"[cyan]:arrow_forward: STEP[/cyan] {msg}")


def log_prompt(msg: str):
    """Log a user input prompt message in blue."""
    console.print(f"[blue]:writing_hand: INPUT[/blue] {msg}")


def prompt_selection(
    options: Dict[str, str],
    title: str = "Please Select",
    display_format: Optional[str] = None,
    allow_custom: bool = False,
    custom_option_label: str = "Custom",
    custom_prompt: str = "Enter custom value:",
    custom_validator: Optional[Callable[[str], str]] = None,
    param_value: Optional[str] = None,
) -> str:
    """Prompt user to select from a map of options or enter a custom value.

    This is a generic selection utility that can be used for any kind of
    key-value selection menu (instances, environments, profiles, etc.).

    Args:
        options: Dictionary mapping option keys to values/descriptions
        title: Title for the selection menu
        display_format: Format string for menu items. Available placeholders:
            {idx} - menu number, {key} - option key, {value} - option value
            Default: "{idx}) {key:<15} - {value}"
        allow_custom: Whether to allow custom value input
        custom_option_label: Label for the custom value option (if enabled)
        custom_prompt: Prompt message for custom value input
        custom_validator: Optional function to validate param_value or custom input.
            Should return the value itself if valid (allows normalization).
        param_value: Pre-selected key or value (skips interactive prompt)

    Returns:
        Selected value (either from options dict or custom input)

    Raises:
        SystemExit: If invalid input is provided

    Examples:
        # Simple selection (returns URL)
        sonar_instances = {
            "ito": "https://ito-ci.bmwgroup.net/sonar",
            "oto": "https://oto-ci.bmwgroup.net/sonar",
        }
        url = prompt_selection(
            sonar_instances,
            title="BMW SonarQube Instances",
            allow_custom=True,
            custom_option_label="Custom URL",
            custom_prompt="Enter custom SonarQube URL:",
            param_value=args.instance
        )
    """
    if display_format is None:
        display_format = "{idx}) {key:<15} - {value}"

    # If value is provided as parameter, resolve and return
    if param_value:
        # First check if it's a valid option key (e.g. "atc" → URL)
        value = options.get(param_value.lower())
        if value:
            log_info(f"Using: {value}")
            return value

        # Check if the param_value itself is a valid value in the dict
        if param_value in options.values():
            log_info(f"Using: {param_value}")
            return param_value

        # Then check if custom_validator can handle it (e.g. a raw URL)
        if custom_validator:
            try:
                validated = custom_validator(param_value)
                log_info(f"Using: {validated}")
                return validated
            except (ValueError, TypeError):
                pass

        # Invalid option
        log_error(f"Invalid option: {param_value}")
        log_error(f"Valid options: {', '.join(options.keys())}")
        if allow_custom:
            log_error("Or provide a custom value")
        sys.exit(1)

    # Interactive selection
    print(f"=== {title} ===")

    # Generate menu options
    for idx, (key, value) in enumerate(options.items(), start=1):
        print(display_format.format(idx=idx, key=key, value=value))

    if allow_custom:
        custom_idx = len(options) + 1
        print(f"{custom_idx}) {custom_option_label:<15} - Enter your own value")

    print()

    max_option = len(options) + (1 if allow_custom else 0)
    log_prompt(f"Select an option (1-{max_option}):")
    choice = input()

    try:
        choice_num = int(choice)
        if 1 <= choice_num <= len(options):
            # Get the selected option
            option_key = list(options.keys())[choice_num - 1]
            selected_value = options[option_key]
            log_info(f"Selected: {option_key}")
            return selected_value
        elif allow_custom and choice_num == len(options) + 1:
            log_prompt(custom_prompt)
            custom_value = input()
            if not custom_value:
                log_error("Value cannot be empty")
                sys.exit(1)

            # Validate custom input if validator provided
            if custom_validator:
                try:
                    custom_value = custom_validator(custom_value)
                except (ValueError, TypeError) as e:
                    log_error(f"Invalid value: {e}")
                    sys.exit(1)

            log_info(f"Using custom value: {custom_value}")
            return custom_value
        else:
            log_error(f"Invalid selection. Please choose 1-{max_option}.")
            sys.exit(1)
    except ValueError:
        log_error(f"Invalid input. Please enter a number between 1 and {max_option}.")
        sys.exit(1)


def prompt_multi_selection(
    options: Dict[str, str],
    title: str = "Please Select",
    display_format: Optional[str] = None,
    min_selections: int = 1,
    max_selections: Optional[int] = None,
) -> List[str]:
    """Prompt user to select multiple items with interactive keyboard navigation.

    Navigation:
        ↑/↓ or k/j: Move up/down
        Space: Toggle selection
        Enter: Confirm selections
        Escape/q: Cancel
        a: Select all
        n: Select none

    Args:
        options: Dictionary mapping option keys to values/descriptions
        title: Title for the selection menu
        display_format: Not used in interactive mode (kept for compatibility)
        min_selections: Minimum number of selections required (default: 1)
        max_selections: Maximum number of selections allowed (default: unlimited)

    Returns:
        List of selected values from the options dict

    Raises:
        SystemExit: If cancelled or invalid input

    Examples:
        # Multi-select plugins
        plugins = {
            "plugin1": "DX/ttt-plugin-testing - Testing utilities",
            "plugin2": "DX/ttt-plugin-docs - Documentation tools",
        }
        selected = prompt_multi_selection(
            plugins,
            title="Select Plugins to Install",
            min_selections=1
        )
    """
    import sys
    import termios
    import tty

    if not options:
        log_error("No options available")
        sys.exit(1)

    option_list = list(options.items())
    selected = set()
    current_index = 0

    def get_key():
        """Read a single keypress from stdin."""
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
            # Handle escape sequences (arrow keys)
            if ch == "\x1b":
                ch2 = sys.stdin.read(1)
                if ch2 == "[":
                    ch3 = sys.stdin.read(1)
                    if ch3 == "A":
                        return "UP"
                    elif ch3 == "B":
                        return "DOWN"
                return "ESC"
            return ch
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    def render_menu():
        """Render the selection menu."""
        console.clear()
        console.print(f"\n[bold cyan]{title}[/bold cyan]")
        console.print(
            "[dim]↑/↓: Navigate | Space: Select | Enter: Confirm | Esc/q: Cancel | a: All | n: None[/dim]\n"
        )

        for idx, (key, value) in enumerate(option_list):
            checkbox = "[green]☑[/green]" if idx in selected else "☐"
            cursor = "[bold yellow]→[/bold yellow]" if idx == current_index else " "
            console.print(f"{cursor} {checkbox} {value}")

        console.print()
        sel_count = len(selected)

        # Show status and warnings
        status_parts = []
        if max_selections:
            status_parts.append(f"Selected: {sel_count} / {max_selections}")
            if sel_count >= max_selections:
                status_parts.append("[yellow](Maximum reached)[/yellow]")
        else:
            status_parts.append(f"Selected: {sel_count}")

        if sel_count < min_selections:
            status_parts.append(f"[yellow](Need at least {min_selections})[/yellow]")

        console.print(f"[dim]{' '.join(status_parts)}[/dim]")

    # Initial render
    render_menu()

    # Main interaction loop
    while True:
        try:
            key = get_key()

            if key == "UP" or key == "k":
                current_index = (current_index - 1) % len(option_list)
                render_menu()

            elif key == "DOWN" or key == "j":
                current_index = (current_index + 1) % len(option_list)
                render_menu()

            elif key == " ":
                # Toggle selection
                if current_index in selected:
                    selected.remove(current_index)
                    render_menu()
                else:
                    if max_selections and len(selected) >= max_selections:
                        # Show warning in the status area instead of separate message
                        pass  # Warning will be shown in next render
                    else:
                        selected.add(current_index)
                    render_menu()

            elif key == "a":
                # Select all (up to max)
                if max_selections:
                    selected = set(range(min(len(option_list), max_selections)))
                else:
                    selected = set(range(len(option_list)))
                render_menu()

            elif key == "n":
                # Select none
                selected.clear()
                render_menu()

            elif key == "\r" or key == "\n":
                # Confirm selection
                if len(selected) < min_selections:
                    # Warning will be shown in status line, just re-render
                    render_menu()
                else:
                    break

            elif key == "ESC" or key == "q":
                console.print("\n[yellow]Selection cancelled[/yellow]")
                sys.exit(0)

        except KeyboardInterrupt:
            console.print("\n[yellow]Selection cancelled[/yellow]")
            sys.exit(0)

    # Get selected values
    selected_values = [option_list[idx][1] for idx in sorted(selected)]

    console.print()
    log_info(f"Selected {len(selected_values)} option(s):")
    for idx in sorted(selected):
        key = option_list[idx][0]
        console.print(f"  [green]✓[/green] {key}")
    console.print()

    return selected_values


# ============================================================================
# Prerequisite Checking - Data Structures
# ============================================================================


@dataclass
class PrerequisiteCheck:
    """Represents the result of a prerequisite check.

    Attributes:
        name: Display name of the prerequisite being checked
        success: Whether the check passed
        path: Optional path to the checked resource (command, file, etc.)
        version: Optional version information
        message: Optional additional message
        help_text: Optional help text shown on failure
    """

    name: str
    success: bool
    path: Optional[str] = None
    version: Optional[str] = None
    message: Optional[str] = None
    help_text: List[str] = field(default_factory=list)

    def print_result(self) -> None:
        """Print the check result in standardized format."""
        console.print(f"[cyan][CHECK][/cyan] {self.name}...")

        if self.success:
            console.print(f"  [green]:white_check_mark: {self.name} OK[/green]")
            if self.path:
                console.print(f"     Path: {self.path}")
            if self.version:
                console.print(f"     Version: {self.version}")
            if self.message:
                console.print(f"     {self.message}")
        else:
            console.print(f"  [red]:x: {self.name} check failed[/red]")
            if self.message:
                console.print(f"     {self.message}")
            if self.help_text:
                for line in self.help_text:
                    console.print(f"     {line}")


@dataclass
class PrerequisiteCheckResult:
    """Aggregated result of multiple prerequisite checks.

    Attributes:
        checks: List of individual prerequisite checks
        all_passed: Whether all checks passed
    """

    checks: List[PrerequisiteCheck]

    @property
    def all_passed(self) -> bool:
        """Check if all prerequisites passed."""
        return all(check.success for check in self.checks)

    def print_summary(self) -> None:
        """Print summary of all checks."""
        console.print()
        for check in self.checks:
            check.print_result()
            console.print()

        console.rule(style="cyan")
        if self.all_passed:
            console.print("[bold green]✓ All prerequisite checks passed[/bold green]")
        else:
            console.print("[bold red]✗ Some prerequisite checks failed[/bold red]")
            console.print("[yellow]Please resolve the issues above before continuing.[/yellow]")
        console.rule(style="cyan")
        console.print()


# ============================================================================
# Prerequisite Checking - Core Functions
# ============================================================================


def check_command(
    command: str,
    display_name: Optional[str] = None,
    help_text: Optional[List[str]] = None,
) -> PrerequisiteCheck:
    """Check if a command exists in the system PATH.

    Args:
        command: Command name to check
        display_name: Optional display name (defaults to command)
        help_text: Optional help text shown on failure

    Returns:
        PrerequisiteCheck object with results
    """
    name = display_name or command
    cmd_path = shutil.which(command)

    if not cmd_path:
        return PrerequisiteCheck(
            name=name,
            success=False,
            message=f"{command} is not installed or not in PATH",
            help_text=help_text or [],
        )

    # Try to get version (use resolved cmd_path for Windows .cmd/.bat compatibility)
    version = None
    try:
        result = subprocess.run([cmd_path, "--version"], capture_output=True, text=True, timeout=5)
        version_output = result.stdout.strip() or result.stderr.strip()
        # Get just the first line for cleaner output
        if version_output:
            version = version_output.split("\n")[0]
    except (subprocess.SubprocessError, subprocess.TimeoutExpired, FileNotFoundError):
        pass

    return PrerequisiteCheck(name=name, success=True, path=cmd_path, version=version)


def check_python_installed() -> PrerequisiteCheck:
    """Check if Python is installed.

    Returns:
        PrerequisiteCheck object with results
    """
    return check_command(
        "python3",
        display_name="Python 3",
        help_text=[
            "📖 Install Python: https://www.python.org/downloads/",
            "📦 For Linux: sudo apt install python3 python3-pip",
            "📦 For macOS: brew install python3",
        ],
    )


def check_node_installed() -> PrerequisiteCheck:
    """Check if Node.js is installed.

    Returns:
        PrerequisiteCheck object with results
    """
    return check_command(
        "node",
        display_name="Node.js",
        help_text=[
            "📖 Install Node.js: https://nodejs.org/",
            "📦 For Linux: sudo apt install nodejs npm",
            "📦 For macOS: brew install node",
        ],
    )


def check_npx_installed() -> PrerequisiteCheck:
    """Check if npx is installed.

    Returns:
        PrerequisiteCheck object with results
    """
    return check_command(
        "npx",
        display_name="npx (Node Package Runner)",
        help_text=[
            "npx is included with npm (Node.js package manager)",
            "📖 Install Node.js: https://nodejs.org/",
            "📦 For Linux: sudo apt install nodejs npm",
            "📦 For macOS: brew install node",
        ],
    )


def check_docker_daemon_running() -> PrerequisiteCheck:
    """Check if Docker daemon is running.

    Returns:
        PrerequisiteCheck object with results
    """
    try:
        subprocess.run(["docker", "info"], capture_output=True, check=True, timeout=5)
        return PrerequisiteCheck(
            name="Docker daemon", success=True, message="Docker daemon is running"
        )
    except (subprocess.SubprocessError, subprocess.TimeoutExpired):
        return PrerequisiteCheck(
            name="Docker daemon",
            success=False,
            message="Docker daemon is not running",
            help_text=[
                "Start Docker:",
                "  • Docker Desktop: Start the application",
                "  • Linux: sudo systemctl start docker",
            ],
        )


def check_uvx_installed() -> PrerequisiteCheck:
    """Check if uvx is installed.

    Returns:
        PrerequisiteCheck object with results
    """
    return check_command(
        "uvx",
        display_name="uvx (Python package manager)",
        help_text=[
            "📖 Installation guide: setup/basic-environment/uv-setup.md",
            "📦 Quick install for Linux/macOS:",
            "   curl -LsSf https://astral.sh/uv/install.sh | sh",
            "",
            "After installation:",
            "  1. Restart terminal or run: source ~/.zshrc",
            "  2. Re-run this script",
        ],
    )


def check_uv_installed() -> PrerequisiteCheck:
    """Check if uv is installed.

    Returns:
        PrerequisiteCheck object with results
    """
    return check_command(
        "uv",
        display_name="uv (Python package manager)",
        help_text=[
            "Install uv: https://docs.astral.sh/uv/getting-started/installation/",
            "Windows (PowerShell): irm https://astral.sh/uv/install.ps1 | iex",
            "After installation, restart terminal and re-run setup",
        ],
    )


def check_docker_installed() -> PrerequisiteCheck:
    """Check if Docker is installed.

    Returns:
        PrerequisiteCheck object with results
    """
    return check_command(
        "docker",
        display_name="Docker",
        help_text=[
            "📖 Install Docker: https://docs.docker.com/get-docker/",
            "📦 For Linux: curl -fsSL https://get.docker.com | sh",
            "📦 For macOS: brew install --cask docker",
            "📦 For Windows: Download Docker Desktop",
        ],
    )


# ============================================================================
# Prerequisite Checking - Helper Functions
# ============================================================================


def run_prerequisite_checks(
    checks: List[PrerequisiteCheck], title: str = "PREREQUISITE CHECKS"
) -> bool:
    """Run multiple prerequisite checks and print summary.

    Args:
        checks: List of PrerequisiteCheck objects
        title: Title for the check section

    Returns:
        True if all checks passed, False otherwise
    """
    console.print()
    console.print(Panel(f"[bold]{title}[/bold]", style="cyan", width=70))

    result = PrerequisiteCheckResult(checks=checks)
    result.print_summary()

    return result.all_passed


def create_prerequisite_checker(*check_funcs):
    """Create a prerequisite checker function from multiple check functions.

    Args:
        *check_funcs: Functions that return PrerequisiteCheck objects

    Returns:
        Function that runs all checks and returns True if all passed

    Example:
        check_prerequisites = create_prerequisite_checker(
            check_uvx_installed,
            check_docker_installed,
            check_docker_daemon_running
        )

        if not check_prerequisites():
            sys.exit(1)
    """

    def checker(title: str = "PREREQUISITE CHECKS") -> bool:
        """Run all prerequisite checks."""
        checks = [func() for func in check_funcs]
        return run_prerequisite_checks(checks, title=title)

    return checker


# ============================================================================
# Setup Completion Output - Data Structures
# ============================================================================


@dataclass
class ManualStep:
    """Represents a manual step that requires user action.

    Attributes:
        title: Step title (e.g., "Generate GitHub Token")
        instructions: List of instruction lines to display
        ai_guidance: Optional guidance for AI agents handling this step
    """

    title: str
    instructions: List[str]
    ai_guidance: Optional[str] = None

    def format_instructions(self) -> List[str]:
        """Format instructions with AI guidance if present."""
        lines = []
        if self.ai_guidance:
            lines.append(f"[dim]AI Guidance: {self.ai_guidance}[/dim]")
            lines.append("")
        lines.extend(self.instructions)
        return lines


@dataclass
class SetupResult:
    """Represents the result of a setup operation.

    Attributes:
        title: Setup title (e.g., "GitHub MCP Server Setup")
        config_path: Path to the configuration file
        completed_steps: List of automated actions completed
        manual_steps: List of manual steps requiring user action
        important_notes: Optional list of important notes
        documentation: Optional documentation reference
    """

    title: str
    config_path: Path
    completed_steps: List[str]
    manual_steps: List[ManualStep] = field(default_factory=list)
    important_notes: List[str] = field(default_factory=list)
    documentation: Optional[str] = None


def print_setup_complete(result: SetupResult) -> None:
    """Print standardized setup completion message.

    Args:
        result: SetupResult object containing all setup information
    """
    console.print()
    console.print(
        Panel(
            f"[bold green]{result.title} - SETUP COMPLETE[/bold green]",
            style="green",
            width=70,
        )
    )
    console.print()

    # Print completed automated actions
    console.print("[bold]AUTOMATED ACTIONS COMPLETED:[/bold]")
    for step in result.completed_steps:
        console.print(f"  [green]:white_check_mark:[/green] {step}")
    console.print(
        f"  [green]:white_check_mark:[/green] Configuration saved to: {result.config_path}"
    )
    console.print()

    # Print manual steps if any
    if result.manual_steps:
        console.rule("[bold yellow]MANUAL STEPS REQUIRED[/bold yellow]", style="yellow")
        console.print()

        for idx, step in enumerate(result.manual_steps, 1):
            console.print(f"[bold cyan]STEP {chr(64 + idx)}: {step.title}[/bold cyan]")
            console.print("[dim]" + "-" * 70 + "[/dim]")

            for line in step.format_instructions():
                console.print(f"  {line}", emoji=True)
            console.print()

    # Print important notes if any
    if result.important_notes:
        console.rule("[bold yellow]IMPORTANT NOTES[/bold yellow]", style="yellow")
        console.print()
        for note in result.important_notes:
            console.print(f"  {note}", emoji=True)
        console.print()

    # Print documentation reference if provided
    if result.documentation:
        console.rule("[bold blue]DOCUMENTATION[/bold blue]", style="blue")
        console.print()
        console.print(f"  :open_book: {result.documentation}")
        console.print()

    console.rule(style="green")
    console.print()


# ============================================================================
# Environment Detection
# ============================================================================


def is_wsl() -> bool:
    """Check if running in WSL2.

    Returns:
        True if running in WSL2, False otherwise
    """
    try:
        with open("/proc/version", "r") as f:
            return "microsoft" in f.read().lower()
    except FileNotFoundError:
        return False


# ============================================================================
# Validation Utilities
# ============================================================================


def validate_json_file(file_path: Path) -> bool:
    """Validate that a file contains valid JSON.

    Args:
        file_path: Path to the JSON file

    Returns:
        True if valid JSON, False otherwise
    """
    try:
        with open(file_path, "r") as f:
            json.load(f)
        return True
    except (json.JSONDecodeError, FileNotFoundError):
        return False
