"""SQLite state store: connect, apply schema, small helpers."""
from __future__ import annotations
import os, sqlite3, uuid, datetime, pathlib

DEFAULT_DB_PATH = str(pathlib.Path.home() / ".jarvis" / "state.db")
SCHEMA = pathlib.Path(__file__).resolve().parent.parent / "schema" / "state.sql"


def _db_path(path: str | None) -> str:
    # resolved at call time so JARVIS_DB_PATH set after import still applies
    return path or os.environ.get("JARVIS_DB_PATH", DEFAULT_DB_PATH)


def now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def new_id(prefix: str = "") -> str:
    return f"{prefix}{uuid.uuid4().hex[:12]}"


def connect(path: str | None = None) -> sqlite3.Connection:
    p = _db_path(path)
    pathlib.Path(p).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(p)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA.read_text())
    conn.commit()


def log_status(conn, *, blackboard_id, to_status, from_status=None,
               task_id=None, handoff_id=None, agent=None) -> None:
    conn.execute(
        "INSERT INTO status_events (id, blackboard_id, task_id, handoff_id, agent, from_status, to_status, event_at)"
        " VALUES (?,?,?,?,?,?,?,?)",
        (new_id("ev_"), blackboard_id, task_id, handoff_id, agent, from_status, to_status, now()),
    )
    conn.commit()
