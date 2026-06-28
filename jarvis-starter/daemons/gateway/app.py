"""Gateway daemon (Module C, step 1).

One local, read-only API the galaxy frontend talks to. It exposes snapshots of
the control plane (agents, the task DAG, blackboards) read from `state.db`, plus
an SSE stream that ticks when `status_events` grows — the "something changed"
signal the galaxy animates on. The browser stays a thin client; all truth lives
in the DB. Colour comes from data (galaxy visual language).

Run:  python -m uvicorn daemons.gateway.app:app --port 8132   (from jarvis-starter/)
"""
from __future__ import annotations
import os, json, time, sqlite3
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from jarvis import db, agents as agentreg

app = FastAPI(title="JARVIS Gateway")

# tier → colour (galaxy visual language: amber sun, purple subagents, green skills)
TIER_COLOUR = {0: "#ffb627", 1: "#9a7bff", 2: "#5be08a"}


def _query(sql: str, params=()):
    """Read-only query against state.db; tolerant of a not-yet-created schema."""
    conn = db.connect()  # path from JARVIS_DB_PATH, resolved per call
    try:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]
    except sqlite3.OperationalError:
        return []  # tables not created yet → empty snapshot
    finally:
        conn.close()


@app.get("/health")
def health():
    return {"status": "ok", "db": os.environ.get("JARVIS_DB_PATH", "default")}


@app.get("/api/agents")
def api_agents():
    """Orchestrator (sun) + subagents (planets), shaped for the orbital galaxy."""
    nodes = [{"id": "orchestrator", "name": "orchestrator", "tier": 0, "colour": TIER_COLOUR[0]}]
    for name in agentreg.available():
        nodes.append({"id": name, "name": name, "tier": 1, "colour": TIER_COLOUR[1]})
    return {"nodes": nodes}


@app.get("/api/tasks")
def api_tasks():
    """Current task DAG with statuses; `active` marks the lit-tether task."""
    rows = _query("SELECT id, blackboard_id, agent, status, depends_on FROM tasks ORDER BY queued_at")
    tasks = [{"id": r["id"], "blackboard_id": r["blackboard_id"], "agent": r["agent"],
              "status": r["status"], "depends_on": json.loads(r["depends_on"] or "[]"),
              "active": r["status"] == "active"} for r in rows]
    return {"tasks": tasks}


@app.get("/api/blackboards")
def api_blackboards():
    return {"blackboards": _query(
        "SELECT id, project_id, task_description, status FROM blackboards ORDER BY created_at")}


@app.get("/api/events")
def api_events(max_ticks: int = 0):
    """SSE: emit a tick whenever status_events grows. `max_ticks>0` bounds the
    stream (used by tests); 0 = stream until the client disconnects."""
    def gen():
        last, ticks = -1, 0
        while max_ticks == 0 or ticks < max_ticks:
            rows = _query("SELECT COUNT(*) AS n FROM status_events")
            n = rows[0]["n"] if rows else 0
            if n != last:
                last = n
                yield f"data: {json.dumps({'status_events': n})}\n\n"
            ticks += 1
            if max_ticks == 0 or ticks < max_ticks:
                time.sleep(1)
    return StreamingResponse(gen(), media_type="text/event-stream")
