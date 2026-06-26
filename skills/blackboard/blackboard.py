"""
blackboard.py — Shared working file coordination for multi-agent tasks.

Creates and manages blackboard files in /tmp/opencode/ where specialist agents
write analysis and proposed changes. The worker agent then executes the resulting
plan. Designed to feed opencode.db in Phase 3 (see PROJECTS-DB.md).

Runtime: ~/.opencode/plugins/clipjoint/.venv/bin/python3
Dependencies: stdlib only
"""

from __future__ import annotations

import os
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ─── Directory constants ──────────────────────────────────────────────────────

ACTIVE_DIR = Path("/tmp/opencode")
ARCHIVE_DIR = Path.home() / ".local/share/opencode/blackboards/archive"

# Status values defined in ARCHITECTURE.md
VALID_STATUSES = frozenset(
    {"deliberating", "awaiting-approval", "executing", "done", "blocked"}
)


# ─── Internal helpers ─────────────────────────────────────────────────────────


def _ensure_dirs() -> None:
    """Create active and archive directories if they don't exist."""
    ACTIVE_DIR.mkdir(parents=True, exist_ok=True)
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)


def _next_task_id() -> str:
    """
    Return the next sequential task ID for today, e.g. 'task-20260625-003'.
    Scans existing files in ACTIVE_DIR and ARCHIVE_DIR to find the highest
    sequence number used today, then increments.
    """
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    prefix = f"task-{today}-"
    max_seq = 0

    for search_dir in (ACTIVE_DIR, ARCHIVE_DIR):
        if not search_dir.exists():
            continue
        for p in search_dir.glob(f"task-{today}-*.md"):
            stem = p.stem  # e.g. 'task-20260625-003'
            parts = stem.split("-")
            if len(parts) == 3 and parts[2].isdigit():
                max_seq = max(max_seq, int(parts[2]))

    return f"{prefix}{max_seq + 1:03d}"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _parse_header(content: str) -> dict:
    """
    Extract structured fields from the blackboard header block.
    Returns dict with keys: task, id, status, created, project.
    Returns empty dict if the file doesn't match expected format.
    """
    result: dict = {}
    # Title line: # Task: <description>
    title_match = re.search(r"^# Task: (.+)$", content, re.MULTILINE)
    if title_match:
        result["task"] = title_match.group(1).strip()
    # **ID:** task-YYYYMMDD-NNN
    id_match = re.search(r"^\*\*ID:\*\* (.+)$", content, re.MULTILINE)
    if id_match:
        result["id"] = id_match.group(1).strip()
    # **Status:** <value>
    status_match = re.search(r"^\*\*Status:\*\* (.+)$", content, re.MULTILINE)
    if status_match:
        result["status"] = status_match.group(1).strip()
    # **Created:** <ISO timestamp>
    created_match = re.search(r"^\*\*Created:\*\* (.+)$", content, re.MULTILINE)
    if created_match:
        result["created"] = created_match.group(1).strip()
    # **Project:** <project_id or "standalone">
    project_match = re.search(r"^\*\*Project:\*\* (.+)$", content, re.MULTILINE)
    if project_match:
        result["project"] = project_match.group(1).strip()
    return result


def _section_pattern(section_name: str) -> re.Pattern:
    """
    Return a compiled regex that matches the full section block including
    its Author/Written metadata and content, up to the next ## heading or EOF.
    """
    escaped = re.escape(section_name)
    # Match ## <section_name>\n...up to next ## heading or end of string
    return re.compile(
        rf"## {escaped}\n.*?(?=\n## |\Z)",
        re.DOTALL,
    )


def _build_section_block(agent: str, section_name: str, content: str) -> str:
    """Return a fully formatted section block string."""
    return (
        f"\n## {section_name}\n"
        f"**Author:** {agent}\n"
        f"**Written:** {_now_iso()}\n\n"
        f"{content.strip()}\n"
    )


# ─── Public API ───────────────────────────────────────────────────────────────


def create(
    task_description: str,
    context: str,
    project_id: Optional[str] = None,
) -> str:
    """
    Create a new blackboard file in /tmp/opencode/.

    Parameters
    ----------
    task_description : str
        Human-readable summary of the task (appears in the # Task: header).
    context : str
        Initial context written by the orchestrator — repo, files, error, branch.
    project_id : str or None
        Optional project grouping ID. If None, written as 'standalone'.

    Returns
    -------
    str
        Absolute path to the new blackboard file.

    Raises
    ------
    ValueError
        If task_description is empty.
    """
    if not task_description.strip():
        raise ValueError("task_description must not be empty")

    _ensure_dirs()

    task_id = _next_task_id()
    project_label = project_id if project_id else "standalone"
    now = _now_iso()

    content = (
        f"# Task: {task_description}\n"
        f"**ID:** {task_id}\n"
        f"**Status:** deliberating\n"
        f"**Created:** {now}\n"
        f"**Project:** {project_label}\n"
        f"\n"
        f"## Context\n"
        f"{context.strip()}\n"
    )

    file_path = ACTIVE_DIR / f"{task_id}.md"
    file_path.write_text(content, encoding="utf-8")
    return str(file_path)


def append_section(
    file_path: str,
    agent: str,
    section_name: str,
    content: str,
) -> None:
    """
    Append (or replace) a named section in an existing blackboard.

    Idempotent: if a section with the same name already exists, it is replaced
    with the new content and a fresh **Written:** timestamp. This makes re-runs
    safe — a specialist agent can refine its analysis without duplicating sections.

    Parameters
    ----------
    file_path : str
        Absolute path to the blackboard file.
    agent : str
        Name of the agent writing the section (e.g. 'programming-expert').
    section_name : str
        Display name for the section (e.g. 'Programming Analysis').
    content : str
        Markdown content for the section body.

    Raises
    ------
    FileNotFoundError
        If file_path does not exist.
    ValueError
        If section_name or content is empty.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Blackboard not found: {file_path}")
    if not section_name.strip():
        raise ValueError("section_name must not be empty")
    if not content.strip():
        raise ValueError("content must not be empty")

    existing = path.read_text(encoding="utf-8")
    new_block = _build_section_block(agent, section_name, content)
    pattern = _section_pattern(section_name)

    if pattern.search(existing):
        # Replace existing section
        updated = pattern.sub(new_block.lstrip("\n"), existing)
    else:
        # Append new section (ensure trailing newline before block)
        updated = existing.rstrip("\n") + "\n" + new_block

    path.write_text(updated, encoding="utf-8")


def read(file_path: str) -> str:
    """
    Read and return the full blackboard content.

    Parameters
    ----------
    file_path : str
        Absolute path to the blackboard file.

    Returns
    -------
    str
        Full markdown content of the blackboard.

    Raises
    ------
    FileNotFoundError
        If file_path does not exist.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Blackboard not found: {file_path}")
    return path.read_text(encoding="utf-8")


def get_section(file_path: str, section_name: str) -> Optional[str]:
    """
    Extract a specific section's content.

    Returns only the body text of the section (strips the ## heading,
    **Author:**, and **Written:** metadata lines).

    Parameters
    ----------
    file_path : str
        Absolute path to the blackboard file.
    section_name : str
        Exact name of the section to retrieve.

    Returns
    -------
    str or None
        The section body content, or None if the section is not present.

    Raises
    ------
    FileNotFoundError
        If file_path does not exist.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Blackboard not found: {file_path}")

    content = path.read_text(encoding="utf-8")
    pattern = _section_pattern(section_name)
    match = pattern.search(content)
    if not match:
        return None

    block = match.group(0)
    # Strip the heading line
    lines = block.split("\n")
    # Skip: "## <section_name>", "**Author:** ...", "**Written:** ...", blank line
    body_lines = []
    skip_count = 0
    for line in lines:
        if skip_count < 1 and line.startswith(f"## {section_name}"):
            skip_count += 1
            continue
        if skip_count == 1 and line.startswith("**Author:**"):
            continue
        if skip_count == 1 and line.startswith("**Written:**"):
            continue
        body_lines.append(line)

    return "\n".join(body_lines).strip() or None


def mark_status(file_path: str, status: str) -> None:
    """
    Update the **Status:** line in the blackboard header.

    Parameters
    ----------
    file_path : str
        Absolute path to the blackboard file.
    status : str
        New status value. Must be one of:
        deliberating | awaiting-approval | executing | done | blocked

    Raises
    ------
    FileNotFoundError
        If file_path does not exist.
    ValueError
        If status is not a valid value.
    """
    if status not in VALID_STATUSES:
        raise ValueError(
            f"Invalid status '{status}'. "
            f"Must be one of: {', '.join(sorted(VALID_STATUSES))}"
        )
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Blackboard not found: {file_path}")

    content = path.read_text(encoding="utf-8")
    updated = re.sub(
        r"^\*\*Status:\*\* .+$",
        f"**Status:** {status}",
        content,
        count=1,
        flags=re.MULTILINE,
    )
    path.write_text(updated, encoding="utf-8")


def list_sections(file_path: str) -> list[str]:
    """
    Return the list of section names that have been written to the blackboard.

    The ## Context section created by `create()` is always first.
    Returns sections in document order.

    Parameters
    ----------
    file_path : str
        Absolute path to the blackboard file.

    Returns
    -------
    list[str]
        Section names in document order (e.g. ['Context', 'Programming Analysis']).

    Raises
    ------
    FileNotFoundError
        If file_path does not exist.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Blackboard not found: {file_path}")

    content = path.read_text(encoding="utf-8")
    # Match all ## headings (but not ### or deeper)
    return re.findall(r"^## (.+)$", content, re.MULTILINE)


def is_ready_for_execution(file_path: str) -> bool:
    """
    Return True if the blackboard has a non-empty ## Proposed Changes section.

    The worker agent requires a ## Proposed Changes section with substantive
    content before it will execute. This function checks that condition.

    Parameters
    ----------
    file_path : str
        Absolute path to the blackboard file.

    Returns
    -------
    bool
        True if ## Proposed Changes exists and is non-empty.

    Raises
    ------
    FileNotFoundError
        If file_path does not exist.
    """
    section_content = get_section(file_path, "Proposed Changes")
    return bool(section_content and section_content.strip())


def archive(file_path: str) -> str:
    """
    Move a completed blackboard to the archive directory.

    The archive directory is: ~/.local/share/opencode/blackboards/archive/
    The filename is preserved. If a file with the same name already exists
    in the archive, it is overwritten (assumed to be a re-archive of the
    same task after an update).

    Parameters
    ----------
    file_path : str
        Absolute path to the active blackboard file.

    Returns
    -------
    str
        Absolute path to the archived file.

    Raises
    ------
    FileNotFoundError
        If file_path does not exist.
    """
    src = Path(file_path)
    if not src.exists():
        raise FileNotFoundError(f"Blackboard not found: {file_path}")

    _ensure_dirs()
    dest = ARCHIVE_DIR / src.name
    shutil.move(str(src), str(dest))
    return str(dest)


def get_active_blackboards() -> list[dict]:
    """
    List all active blackboard files in /tmp/opencode/.

    Scans ACTIVE_DIR for files matching the task-YYYYMMDD-NNN.md pattern
    and parses their headers.

    Returns
    -------
    list[dict]
        List of dicts with keys: path, task, status, created, project.
        Files that cannot be parsed are skipped silently.
    """
    _ensure_dirs()
    results = []
    for p in sorted(ACTIVE_DIR.glob("task-*.md")):
        try:
            content = p.read_text(encoding="utf-8")
            header = _parse_header(content)
            results.append(
                {
                    "path": str(p),
                    "task": header.get("task", "(unknown)"),
                    "status": header.get("status", "(unknown)"),
                    "created": header.get("created", "(unknown)"),
                    "project": header.get("project", "standalone"),
                }
            )
        except Exception:
            # Skip unreadable/corrupt files rather than crashing the whole list
            continue
    return results
