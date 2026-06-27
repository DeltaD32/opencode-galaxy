"""Control plane: schedule a task DAG with concurrency, file-lease safety,
governance gate, and retry. Blackboard is the source of truth; a restart
re-derives state from it.
"""
from __future__ import annotations
import json, datetime
from concurrent.futures import ThreadPoolExecutor
from . import db
from .runtime import TaskSpec, run_task

LEASE_TTL_SECONDS = 120


def _expired(ts: str | None) -> bool:
    if not ts:
        return True
    return datetime.datetime.fromisoformat(ts) < datetime.datetime.now(datetime.timezone.utc)


def _deps_done(conn, depends_on: list[str]) -> bool:
    if not depends_on:
        return True
    q = ",".join("?" * len(depends_on))
    rows = conn.execute(f"SELECT status FROM tasks WHERE id IN ({q})", depends_on).fetchall()
    return all(r["status"] == "done" for r in rows) and len(rows) == len(depends_on)


def _scope_free(conn, file_scope: list[str], task_id: str) -> bool:
    """True if no other live task holds an overlapping path lease."""
    for path in file_scope:
        row = conn.execute("SELECT task_id, expires_at FROM file_leases WHERE path=?", (path,)).fetchone()
        if row and row["task_id"] != task_id and not _expired(row["expires_at"]):
            return False
    return True


def _acquire_leases(conn, file_scope, task_id, bb_id):
    exp = (datetime.datetime.now(datetime.timezone.utc)
           + datetime.timedelta(seconds=LEASE_TTL_SECONDS)).isoformat()
    for path in file_scope:
        conn.execute("INSERT OR REPLACE INTO file_leases (path, task_id, blackboard_id, acquired_at, expires_at)"
                     " VALUES (?,?,?,?,?)", (path, task_id, bb_id, db.now(), exp))
    conn.commit()


def _release_leases(conn, task_id):
    conn.execute("DELETE FROM file_leases WHERE task_id=?", (task_id,))
    conn.commit()


def _set_status(conn, task, to, **extra):
    db.log_status(conn, blackboard_id=task["blackboard_id"], task_id=task["id"],
                  handoff_id=task["handoff_id"], agent=task["agent"],
                  from_status=task["status"], to_status=to)
    cols = ", ".join(f"{k}=?" for k in extra)
    sql = f"UPDATE tasks SET status=?{', ' + cols if extra else ''} WHERE id=?"
    conn.execute(sql, (to, *extra.values(), task["id"]))
    conn.commit()


def reap_stale(conn):
    """Reset crashed/abandoned active tasks whose lease expired."""
    for t in conn.execute("SELECT * FROM tasks WHERE status='active'").fetchall():
        if _expired(t["lease_expires_at"]):
            _release_leases(conn, t["id"])
            nxt = "retrying" if t["attempts"] < t["max_attempts"] else "failed"
            _set_status(conn, t, nxt, lease_owner=None, lease_expires_at=None)


def _blackboard_executing(conn, bb_id) -> bool:
    r = conn.execute("SELECT status FROM blackboards WHERE id=?", (bb_id,)).fetchone()
    return r and r["status"] == "executing"


def tick(conn, build_spec, llm_complete, concurrency=3, require_gate=True):
    """One scheduling pass. Returns number of tasks dispatched this tick."""
    reap_stale(conn)
    candidates = conn.execute(
        "SELECT * FROM tasks WHERE status IN ('pending','retrying') ORDER BY queued_at").fetchall()
    ready = []
    claimed: set[str] = set()          # paths claimed by earlier tasks IN THIS tick
    for t in candidates:
        deps = json.loads(t["depends_on"])
        scope = json.loads(t["file_scope"])
        if not _deps_done(conn, deps):
            continue
        # Governance: a task may not execute unless its blackboard is approved/executing.
        if require_gate and not _blackboard_executing(conn, t["blackboard_id"]):
            continue
        if not _scope_free(conn, scope, t["id"]):
            continue          # overlapping a held lease → serialize (defer)
        if any(p in claimed for p in scope):
            continue          # overlapping another task picked THIS tick → serialize
        claimed.update(scope)
        ready.append(t)
        if len(ready) >= concurrency:
            break

    dispatched = []
    for t in ready:
        scope = json.loads(t["file_scope"])
        _acquire_leases(conn, scope, t["id"], t["blackboard_id"])
        _set_status(conn, t, "active", lease_owner="sched-1",
                    lease_expires_at=(datetime.datetime.now(datetime.timezone.utc)
                                      + datetime.timedelta(seconds=LEASE_TTL_SECONDS)).isoformat(),
                    attempts=t["attempts"] + 1, started_at=db.now())
        dispatched.append(t)

    # Build specs on the MAIN thread (DB/memory reads are not thread-safe),
    # then run only the LLM execution concurrently.
    specs = [(t, build_spec(t)) for t in dispatched]

    def _run(pair):
        t, spec = pair
        return t, run_task(spec, llm_complete)

    if dispatched:
        with ThreadPoolExecutor(max_workers=concurrency) as pool:
            for t, res in pool.map(_run, specs):
                # re-fetch row for fresh status fields
                row = conn.execute("SELECT * FROM tasks WHERE id=?", (t["id"],)).fetchone()
                _release_leases(conn, t["id"])
                if res.status == "done":
                    _set_status(conn, row, "done", result=res.final_text, completed_at=db.now())
                else:
                    nxt = "retrying" if row["attempts"] < row["max_attempts"] else "failed"
                    _set_status(conn, row, nxt, last_error=res.error)
    return len(dispatched)


def run_until_idle(conn, build_spec, llm_complete, concurrency=3, require_gate=True, max_ticks=100):
    for _ in range(max_ticks):
        live = conn.execute(
            "SELECT COUNT(*) c FROM tasks WHERE status IN ('pending','ready','active','retrying')"
        ).fetchone()["c"]
        if live == 0:
            return
        tick(conn, build_spec, llm_complete, concurrency, require_gate)
