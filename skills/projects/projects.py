"""
projects.py — Persistent project and blackboard coordination via opencode.db.

Tracks projects, blackboard lifecycle, specialist handoff queues, decisions, and
conflicts across sessions. Used by the secretary agent to maintain project state.
Pairs with the blackboard skill for full multi-agent coordination.

Runtime: ~/.opencode/plugins/clipjoint/.venv/bin/python3
Dependencies: stdlib + sqlite3 only — no external packages required.

DB: ~/.local/share/opencode/opencode.db  (additive tables — existing tables untouched)
"""

from __future__ import annotations

import json
import re
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ─── Constants ────────────────────────────────────────────────────────────────

DB_PATH = Path.home() / ".local/share/opencode/opencode.db"

# Valid status values for projects
PROJECT_STATUSES = frozenset({"active", "paused", "complete", "archived"})

# Valid status values for blackboards (mirrors blackboard.py VALID_STATUSES)
BLACKBOARD_STATUSES = frozenset(
    {"deliberating", "awaiting-approval", "executing", "done", "blocked"}
)

# Valid status values for specialist queue entries
QUEUE_STATUSES = frozenset({"pending", "active", "done", "skipped"})

# ─── Schema ───────────────────────────────────────────────────────────────────

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS projects (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    description TEXT,
    status      TEXT NOT NULL DEFAULT 'active',
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS blackboards (
    id               TEXT PRIMARY KEY,
    project_id       TEXT REFERENCES projects(id),
    task_description TEXT NOT NULL,
    status           TEXT NOT NULL DEFAULT 'deliberating',
    file_path        TEXT NOT NULL,
    created_at       TEXT NOT NULL,
    updated_at       TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sections (
    id            TEXT PRIMARY KEY,
    blackboard_id TEXT NOT NULL REFERENCES blackboards(id),
    agent         TEXT NOT NULL,
    section_name  TEXT NOT NULL,
    content       TEXT NOT NULL,
    written_at    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS decisions (
    id            TEXT PRIMARY KEY,
    blackboard_id TEXT NOT NULL REFERENCES blackboards(id),
    made_by       TEXT NOT NULL,
    decision      TEXT NOT NULL,
    rationale     TEXT,
    timestamp     TEXT NOT NULL,
    influenced    TEXT
);

CREATE TABLE IF NOT EXISTS conflicts (
    id            TEXT PRIMARY KEY,
    blackboard_id TEXT NOT NULL REFERENCES blackboards(id),
    agent_a       TEXT NOT NULL,
    agent_b       TEXT NOT NULL,
    description   TEXT NOT NULL,
    resolved      INTEGER NOT NULL DEFAULT 0,
    resolution    TEXT,
    resolved_by   TEXT,
    resolved_at   TEXT
);

CREATE TABLE IF NOT EXISTS specialist_queue (
    id            TEXT PRIMARY KEY,
    blackboard_id TEXT NOT NULL REFERENCES blackboards(id),
    agent         TEXT NOT NULL,
    status        TEXT NOT NULL DEFAULT 'pending',
    queued_at     TEXT NOT NULL,
    started_at    TEXT,
    completed_at  TEXT
);

CREATE INDEX IF NOT EXISTS idx_blackboards_project   ON blackboards(project_id);
CREATE INDEX IF NOT EXISTS idx_blackboards_status    ON blackboards(status);
CREATE INDEX IF NOT EXISTS idx_sections_blackboard   ON sections(blackboard_id);
CREATE INDEX IF NOT EXISTS idx_decisions_blackboard  ON decisions(blackboard_id);
CREATE INDEX IF NOT EXISTS idx_conflicts_blackboard  ON conflicts(blackboard_id);
CREATE INDEX IF NOT EXISTS idx_conflicts_resolved    ON conflicts(resolved);
CREATE INDEX IF NOT EXISTS idx_queue_blackboard      ON specialist_queue(blackboard_id);
CREATE INDEX IF NOT EXISTS idx_queue_status          ON specialist_queue(status);
"""


# ─── Internal helpers ─────────────────────────────────────────────────────────


def _now_iso() -> str:
    """Return current UTC timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _new_id() -> str:
    """Return a fresh UUID4 string."""
    return str(uuid.uuid4())


def _connect() -> sqlite3.Connection:
    """
    Open a connection to opencode.db with WAL journal mode and row factory.
    Applies the schema migration (idempotent — IF NOT EXISTS guards throughout).
    """
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript(_SCHEMA_SQL)
    conn.commit()
    return conn


def _row_to_dict(row: sqlite3.Row) -> dict:
    """Convert a sqlite3.Row to a plain dict."""
    return dict(row)


def _rows_to_dicts(rows: list[sqlite3.Row]) -> list[dict]:
    """Convert a list of sqlite3.Row objects to plain dicts."""
    return [dict(r) for r in rows]


# ─── Project functions ────────────────────────────────────────────────────────


def create_project(name: str, description: str = "") -> str:
    """
    Create a new project.

    Parameters
    ----------
    name : str
        Short human-readable project name (e.g. 'login-overhaul').
    description : str
        Longer description of the project's scope. Optional.

    Returns
    -------
    str
        The new project's ID (UUID4).

    Raises
    ------
    ValueError
        If name is empty.
    """
    if not name.strip():
        raise ValueError("name must not be empty")

    now = _now_iso()
    project_id = _new_id()

    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO projects (id, name, description, status, created_at, updated_at)
            VALUES (?, ?, ?, 'active', ?, ?)
            """,
            (project_id, name.strip(), description.strip(), now, now),
        )
    return project_id


def get_project(project_id: str) -> Optional[dict]:
    """
    Get a project by ID.

    Parameters
    ----------
    project_id : str
        The project UUID.

    Returns
    -------
    dict or None
        Project row as dict, or None if not found.
    """
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM projects WHERE id = ?", (project_id,)
        ).fetchone()
    return _row_to_dict(row) if row else None


def list_projects(status: str = "active") -> list[dict]:
    """
    List projects filtered by status.

    Parameters
    ----------
    status : str
        One of: active | paused | complete | archived. Default: 'active'.

    Returns
    -------
    list[dict]
        List of project rows, ordered by created_at descending.
    """
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM projects WHERE status = ? ORDER BY created_at DESC",
            (status,),
        ).fetchall()
    return _rows_to_dicts(rows)


def update_project_status(project_id: str, status: str) -> None:
    """
    Update a project's status.

    Parameters
    ----------
    project_id : str
        The project UUID.
    status : str
        New status: active | paused | complete | archived.

    Raises
    ------
    ValueError
        If status is not a valid project status value.
    """
    if status not in PROJECT_STATUSES:
        raise ValueError(
            f"Invalid project status '{status}'. "
            f"Must be one of: {', '.join(sorted(PROJECT_STATUSES))}"
        )
    now = _now_iso()
    with _connect() as conn:
        conn.execute(
            "UPDATE projects SET status = ?, updated_at = ? WHERE id = ?",
            (status, now, project_id),
        )


# ─── Blackboard functions ─────────────────────────────────────────────────────


def register_blackboard(
    blackboard_path: str,
    project_id: Optional[str],
    task_description: str,
) -> str:
    """
    Register a blackboard file in the database.

    Call this immediately after ``blackboard.create()`` to link the blackboard
    to a project and make it visible to the secretary's coordination queries.

    Parameters
    ----------
    blackboard_path : str
        Absolute path to the blackboard file (e.g. '/tmp/opencode/task-20260625-001.md').
    project_id : str or None
        Project UUID to link this blackboard to. Pass None for standalone tasks.
    task_description : str
        One-line task summary — copied from blackboard header.

    Returns
    -------
    str
        The new blackboard DB record ID (UUID4).

    Raises
    ------
    ValueError
        If task_description is empty.
    """
    if not task_description.strip():
        raise ValueError("task_description must not be empty")

    now = _now_iso()
    blackboard_id = _new_id()

    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO blackboards
                (id, project_id, task_description, status, file_path, created_at, updated_at)
            VALUES (?, ?, ?, 'deliberating', ?, ?, ?)
            """,
            (blackboard_id, project_id, task_description.strip(),
             blackboard_path, now, now),
        )
        # If linked to a project, update the project's updated_at
        if project_id:
            conn.execute(
                "UPDATE projects SET updated_at = ? WHERE id = ?",
                (now, project_id),
            )
    return blackboard_id


def update_blackboard_status(blackboard_id: str, status: str) -> None:
    """
    Update a blackboard's status in the database.

    Call this whenever the blackboard file's **Status:** line changes, to keep
    the DB record in sync with the filesystem state.

    Parameters
    ----------
    blackboard_id : str
        The blackboard DB record UUID.
    status : str
        New status: deliberating | awaiting-approval | executing | done | blocked.

    Raises
    ------
    ValueError
        If status is not a valid blackboard status value.
    """
    if status not in BLACKBOARD_STATUSES:
        raise ValueError(
            f"Invalid blackboard status '{status}'. "
            f"Must be one of: {', '.join(sorted(BLACKBOARD_STATUSES))}"
        )
    now = _now_iso()
    with _connect() as conn:
        conn.execute(
            "UPDATE blackboards SET status = ?, updated_at = ? WHERE id = ?",
            (status, now, blackboard_id),
        )


def sync_blackboard_sections(blackboard_path: str, blackboard_id: str) -> int:
    """
    Parse a blackboard file and upsert all its sections into the ``sections`` table.

    Reads every ``## <section_name>`` block from the blackboard markdown file,
    extracts the **Author:** and content, and upserts each into the DB. Existing
    rows for the same (blackboard_id, section_name) are replaced so this is safe
    to call repeatedly after each specialist writes their section.

    Parameters
    ----------
    blackboard_path : str
        Absolute path to the blackboard file.
    blackboard_id : str
        The blackboard DB record UUID.

    Returns
    -------
    int
        Number of sections upserted.

    Raises
    ------
    FileNotFoundError
        If the blackboard file does not exist.
    """
    path = Path(blackboard_path)
    if not path.exists():
        raise FileNotFoundError(f"Blackboard not found: {blackboard_path}")

    content = path.read_text(encoding="utf-8")
    now = _now_iso()

    # Split into section blocks at "## " headings
    # Pattern captures the heading name and everything up to next heading or EOF
    section_pattern = re.compile(r"^## (.+)$", re.MULTILINE)
    headings = list(section_pattern.finditer(content))

    count = 0
    with _connect() as conn:
        for i, match in enumerate(headings):
            section_name = match.group(1).strip()
            start = match.end()
            end = headings[i + 1].start() if i + 1 < len(headings) else len(content)
            body = content[start:end].strip()

            # Extract author from **Author:** line if present
            author_match = re.search(r"^\*\*Author:\*\*\s*(.+)$", body, re.MULTILINE)
            agent = author_match.group(1).strip() if author_match else "unknown"

            # Extract written_at from **Written:** line if present
            written_match = re.search(r"^\*\*Written:\*\*\s*(.+)$", body, re.MULTILINE)
            written_at = written_match.group(1).strip() if written_match else now

            # Remove metadata lines from content
            body_clean = re.sub(r"^\*\*(Author|Written):\*\*.*$\n?", "", body,
                                flags=re.MULTILINE).strip()

            # Upsert: delete existing row for same blackboard+section_name, then insert
            conn.execute(
                """
                DELETE FROM sections
                WHERE blackboard_id = ? AND section_name = ?
                """,
                (blackboard_id, section_name),
            )
            conn.execute(
                """
                INSERT INTO sections (id, blackboard_id, agent, section_name, content, written_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (_new_id(), blackboard_id, agent, section_name, body_clean, written_at),
            )
            count += 1

    return count


# ─── Decision functions ───────────────────────────────────────────────────────


def record_decision(
    blackboard_id: str,
    made_by: str,
    decision: str,
    rationale: str = "",
    influenced: Optional[list[str]] = None,
) -> str:
    """
    Record an architectural or technical decision made during a blackboard task.

    Decisions are queryable across tasks via ``get_prior_decisions()`` — this is
    how the secretary enforces consistency across sessions ("we chose signals not
    NgRx in task-003").

    Parameters
    ----------
    blackboard_id : str
        The blackboard DB record UUID this decision belongs to.
    made_by : str
        Agent name or 'user'.
    decision : str
        Short decision label: e.g. 'use signals not NgRx'.
    rationale : str
        Why this was chosen. Optional.
    influenced : list[str] or None
        List of future blackboard_ids this decision will affect. Optional.

    Returns
    -------
    str
        The new decision ID (UUID4).
    """
    now = _now_iso()
    decision_id = _new_id()
    influenced_json = json.dumps(influenced) if influenced else None

    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO decisions
                (id, blackboard_id, made_by, decision, rationale, timestamp, influenced)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (decision_id, blackboard_id, made_by, decision.strip(),
             rationale.strip(), now, influenced_json),
        )
    return decision_id


def get_prior_decisions(project_id: str) -> list[dict]:
    """
    Get all decisions for a project ordered by timestamp — for cross-task enforcement.

    Use this at the start of a new blackboard task to load the project's standing
    decisions and pass them to specialist agents as context ("these architectural
    choices are still in force").

    Parameters
    ----------
    project_id : str
        The project UUID.

    Returns
    -------
    list[dict]
        Decision rows with extra field ``task_description`` from the parent blackboard.
        Ordered by ``timestamp`` ascending (oldest first).
    """
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT d.id, d.blackboard_id, d.made_by, d.decision, d.rationale,
                   d.timestamp, d.influenced, b.task_description
            FROM decisions d
            JOIN blackboards b ON d.blackboard_id = b.id
            WHERE b.project_id = ?
            ORDER BY d.timestamp ASC
            """,
            (project_id,),
        ).fetchall()
    return _rows_to_dicts(rows)


# ─── Conflict functions ───────────────────────────────────────────────────────


def record_conflict(
    blackboard_id: str,
    agent_a: str,
    agent_b: str,
    description: str,
) -> str:
    """
    Record a conflict between two specialist agents on a blackboard.

    Parameters
    ----------
    blackboard_id : str
        The blackboard DB record UUID.
    agent_a : str
        First agent (e.g. 'programming-expert').
    agent_b : str
        Second agent (e.g. 'design-expert').
    description : str
        What the agents disagreed on.

    Returns
    -------
    str
        The new conflict ID (UUID4).
    """
    conflict_id = _new_id()

    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO conflicts
                (id, blackboard_id, agent_a, agent_b, description, resolved)
            VALUES (?, ?, ?, ?, ?, 0)
            """,
            (conflict_id, blackboard_id, agent_a, agent_b, description.strip()),
        )
    return conflict_id


def resolve_conflict(conflict_id: str, resolution: str, resolved_by: str) -> None:
    """
    Mark a conflict as resolved.

    Parameters
    ----------
    conflict_id : str
        The conflict UUID.
    resolution : str
        Description of how the conflict was resolved.
    resolved_by : str
        Who resolved it: 'secretary' or 'user'.
    """
    now = _now_iso()
    with _connect() as conn:
        conn.execute(
            """
            UPDATE conflicts
            SET resolved = 1, resolution = ?, resolved_by = ?, resolved_at = ?
            WHERE id = ?
            """,
            (resolution.strip(), resolved_by, now, conflict_id),
        )


# ─── Project status aggregation ───────────────────────────────────────────────


def get_project_status(project_id: str) -> dict:
    """
    Return full project status: project row + blackboard list + open conflicts +
    recent decisions.

    This is the primary query the secretary runs when the user asks
    "where are we?" or "project status".

    Parameters
    ----------
    project_id : str
        The project UUID.

    Returns
    -------
    dict
        Keys:
        - ``project``: dict of project row fields (or empty dict if not found)
        - ``blackboards``: list of blackboard dicts for this project
        - ``open_conflicts``: list of unresolved conflict dicts
        - ``decisions``: list of decision dicts (all, ordered by timestamp)
        - ``queue``: list of queue entry dicts for the most-recent active blackboard
    """
    with _connect() as conn:
        # Project row
        project_row = conn.execute(
            "SELECT * FROM projects WHERE id = ?", (project_id,)
        ).fetchone()
        project = _row_to_dict(project_row) if project_row else {}

        # Blackboards for this project
        blackboard_rows = conn.execute(
            """
            SELECT * FROM blackboards WHERE project_id = ?
            ORDER BY created_at ASC
            """,
            (project_id,),
        ).fetchall()
        blackboards = _rows_to_dicts(blackboard_rows)

        # Collect blackboard IDs for subsequent queries
        bb_ids = [b["id"] for b in blackboards]

        # Open conflicts across all project blackboards
        open_conflicts: list[dict] = []
        if bb_ids:
            placeholders = ",".join("?" * len(bb_ids))
            conflict_rows = conn.execute(
                f"""
                SELECT c.*, b.task_description
                FROM conflicts c
                JOIN blackboards b ON c.blackboard_id = b.id
                WHERE c.blackboard_id IN ({placeholders}) AND c.resolved = 0
                ORDER BY b.created_at ASC
                """,
                bb_ids,
            ).fetchall()
            open_conflicts = _rows_to_dicts(conflict_rows)

        # All decisions for this project
        decision_rows = conn.execute(
            """
            SELECT d.*, b.task_description
            FROM decisions d
            JOIN blackboards b ON d.blackboard_id = b.id
            WHERE b.project_id = ?
            ORDER BY d.timestamp ASC
            """,
            (project_id,),
        ).fetchall()
        decisions = _rows_to_dicts(decision_rows)

        # Queue for the most-recent non-done blackboard
        queue: list[dict] = []
        active_bbs = [b for b in blackboards if b["status"] not in ("done", "blocked")]
        if active_bbs:
            latest_bb_id = active_bbs[-1]["id"]
            queue_rows = conn.execute(
                """
                SELECT * FROM specialist_queue
                WHERE blackboard_id = ?
                ORDER BY queued_at ASC
                """,
                (latest_bb_id,),
            ).fetchall()
            queue = _rows_to_dicts(queue_rows)

    return {
        "project": project,
        "blackboards": blackboards,
        "open_conflicts": open_conflicts,
        "decisions": decisions,
        "queue": queue,
    }


# ─── Specialist queue functions ───────────────────────────────────────────────


def enqueue_specialists(blackboard_id: str, agents: list[str]) -> None:
    """
    Add specialists to the handoff queue for a blackboard.

    Inserts one row per agent in ``pending`` status. If an agent is already
    queued for this blackboard, it is skipped (idempotent).

    Call this after creating a blackboard and registering it, before delegating
    to the first specialist. The queue drives sequential fan-out.

    Parameters
    ----------
    blackboard_id : str
        The blackboard DB record UUID.
    agents : list[str]
        Ordered list of agent names (e.g. ['programming-expert', 'design-expert']).

    Raises
    ------
    ValueError
        If agents is empty.
    """
    if not agents:
        raise ValueError("agents list must not be empty")

    now = _now_iso()
    with _connect() as conn:
        for agent in agents:
            # Check if already queued
            existing = conn.execute(
                """
                SELECT id FROM specialist_queue
                WHERE blackboard_id = ? AND agent = ?
                """,
                (blackboard_id, agent),
            ).fetchone()
            if existing:
                continue  # Already queued — skip
            conn.execute(
                """
                INSERT INTO specialist_queue
                    (id, blackboard_id, agent, status, queued_at)
                VALUES (?, ?, ?, 'pending', ?)
                """,
                (_new_id(), blackboard_id, agent, now),
            )


def advance_queue(blackboard_id: str) -> Optional[dict]:
    """
    Mark the currently active specialist done and activate the next pending one.

    Transitions:
    1. Find the ``active`` row (if any) → mark it ``done`` with ``completed_at`` now
    2. Find the first ``pending`` row → mark it ``active`` with ``started_at`` now
    3. Return the newly activated row as a dict, or None if queue is complete

    If there is no ``active`` row but there is a ``pending`` row, activates the
    first pending one directly (handles the first call — "start the queue").

    Parameters
    ----------
    blackboard_id : str
        The blackboard DB record UUID.

    Returns
    -------
    dict or None
        The newly activated queue entry dict (includes agent, status, etc.),
        or None if all specialists are done or skipped.
    """
    now = _now_iso()
    with _connect() as conn:
        # Mark current active as done
        active = conn.execute(
            """
            SELECT * FROM specialist_queue
            WHERE blackboard_id = ? AND status = 'active'
            ORDER BY queued_at ASC LIMIT 1
            """,
            (blackboard_id,),
        ).fetchone()
        if active:
            conn.execute(
                """
                UPDATE specialist_queue
                SET status = 'done', completed_at = ?
                WHERE id = ?
                """,
                (now, active["id"]),
            )

        # Activate the next pending specialist
        next_pending = conn.execute(
            """
            SELECT * FROM specialist_queue
            WHERE blackboard_id = ? AND status = 'pending'
            ORDER BY queued_at ASC LIMIT 1
            """,
            (blackboard_id,),
        ).fetchone()
        if not next_pending:
            return None  # Queue complete

        conn.execute(
            """
            UPDATE specialist_queue
            SET status = 'active', started_at = ?
            WHERE id = ?
            """,
            (now, next_pending["id"]),
        )

        # Re-fetch to get updated row
        updated = conn.execute(
            "SELECT * FROM specialist_queue WHERE id = ?",
            (next_pending["id"],),
        ).fetchone()
    return _row_to_dict(updated) if updated else None


def get_queue_status(blackboard_id: str) -> list[dict]:
    """
    Return the full handoff queue for a blackboard.

    Parameters
    ----------
    blackboard_id : str
        The blackboard DB record UUID.

    Returns
    -------
    list[dict]
        Queue entries in ``queued_at`` order. Each dict has:
        id, blackboard_id, agent, status, queued_at, started_at, completed_at.
    """
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT * FROM specialist_queue
            WHERE blackboard_id = ?
            ORDER BY queued_at ASC
            """,
            (blackboard_id,),
        ).fetchall()
    return _rows_to_dicts(rows)


# ─── Project discovery ────────────────────────────────────────────────────────


def find_project_for_task(task_description: str) -> Optional[dict]:
    """
    Fuzzy-match a task description against active project names and descriptions.

    Uses simple word-overlap scoring: counts how many normalised words from
    ``task_description`` appear in the project's name or description. Returns
    the project with the highest score, or None if no meaningful overlap is found
    (threshold: at least 2 matching words, or 1 if the project name is very short).

    Parameters
    ----------
    task_description : str
        The task text to match (e.g. 'fix the login iOS bug').

    Returns
    -------
    dict or None
        Best-matching active project row, or None if no match above threshold.
    """
    if not task_description.strip():
        return None

    # Normalise task words: lowercase, strip punctuation, remove stop words
    _stop_words = frozenset({
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
        "of", "with", "is", "it", "this", "that", "my", "our", "their", "we",
        "i", "you", "fix", "add", "update", "create", "build", "make", "help",
        "me", "please", "can", "will", "need", "want", "get", "set", "new",
        "old", "use", "via", "from", "into", "its", "be", "do", "has", "have",
    })

    def _tokenise(text: str) -> set[str]:
        words = re.findall(r"[a-z0-9]+", text.lower())
        return {w for w in words if w not in _stop_words and len(w) > 1}

    task_words = _tokenise(task_description)
    if not task_words:
        return None

    projects = list_projects(status="active")
    best_project: Optional[dict] = None
    best_score = 0

    for project in projects:
        # Score against combined name + description text
        project_text = f"{project['name']} {project.get('description', '')}"
        project_words = _tokenise(project_text)
        overlap = len(task_words & project_words)

        # Threshold: use name-only token count so a long description doesn't
        # artificially inflate the minimum overlap required.
        name_words = _tokenise(project["name"])
        min_threshold = 1 if len(name_words) <= 2 else 2

        if overlap >= min_threshold and overlap > best_score:
            best_score = overlap
            best_project = project

    return best_project
