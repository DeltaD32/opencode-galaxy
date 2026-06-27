"""Decomposer: turn a natural-language request into a validated task DAG and
seed it into the blackboard. This is the missing link between 'a request' and
'concurrent multi-agent execution'.

The planner is an LLM call that returns JSON (no tools). We validate hard:
- unique task ids
- depends_on references exist
- the graph is acyclic
- file_scope paths resolve under repo_root
Invalid plans are rejected (caller can retry) — we never seed a broken DAG.
"""
from __future__ import annotations
import json, pathlib
from dataclasses import dataclass, field
from . import db

PLANNER_SYSTEM = """You are the JARVIS planner. Decompose the user's request into a
minimal DAG of specialist tasks. Return ONLY JSON, no prose, matching:
{
  "project_name": "short name",
  "task_description": "one sentence",
  "tasks": [
    {"id":"t1","agent":"<one of the available agents>","description":"what to do",
     "depends_on":[], "file_scope":["relative/or/abs/path"]}
  ]
}
Rules: ids unique; depends_on lists task ids that must finish first; file_scope lists
the files/dirs a task will touch (used to run independent tasks in parallel safely —
tasks that share a path will be serialized, so keep scopes disjoint when possible)."""


@dataclass
class PlannedTask:
    id: str
    agent: str
    description: str
    depends_on: list[str] = field(default_factory=list)
    file_scope: list[str] = field(default_factory=list)


@dataclass
class Plan:
    project_name: str
    task_description: str
    tasks: list[PlannedTask]


class PlanError(ValueError):
    pass


def _strip_fences(s: str) -> str:
    s = s.strip()
    if s.startswith("```"):
        s = s.split("\n", 1)[1] if "\n" in s else s
        if s.endswith("```"):
            s = s[: -3]
        if s.lstrip().startswith("json"):
            s = s.lstrip()[4:]
    return s.strip()


def _is_acyclic(tasks: list[PlannedTask]) -> bool:
    deps = {t.id: set(t.depends_on) for t in tasks}
    # Kahn's algorithm
    no_incoming = [tid for tid, d in deps.items() if not d]
    removed = 0
    while no_incoming:
        n = no_incoming.pop()
        removed += 1
        for tid, d in deps.items():
            if n in d:
                d.discard(n)
                if not d:
                    no_incoming.append(tid)
    return removed == len(tasks)


def parse_plan(raw: str, available_agents: list[str], repo_root: str) -> Plan:
    data = json.loads(_strip_fences(raw))
    tasks = [PlannedTask(**t) for t in data["tasks"]]
    if not tasks:
        raise PlanError("plan has no tasks")
    ids = [t.id for t in tasks]
    if len(ids) != len(set(ids)):
        raise PlanError("duplicate task ids")
    idset = set(ids)
    root = pathlib.Path(repo_root).resolve()
    for t in tasks:
        if available_agents and t.agent not in available_agents:
            raise PlanError(f"unknown agent '{t.agent}' (have {available_agents})")
        for d in t.depends_on:
            if d not in idset:
                raise PlanError(f"task {t.id} depends on unknown task '{d}'")
        # normalise file_scope to absolute paths under repo_root
        norm = []
        for p in t.file_scope:
            pp = pathlib.Path(p)
            pp = (root / pp).resolve() if not pp.is_absolute() else pp.resolve()
            # Component-wise containment (Path.is_relative_to) — cross-platform.
            # A `str(pp).startswith(str(root) + "/")` check is POSIX-only and
            # mis-rejects legitimate paths on Windows (back-slash separators).
            if not (pp == root or pp.is_relative_to(root)):
                raise PlanError(f"file_scope '{p}' escapes repo_root")
            norm.append(str(pp))
        t.file_scope = norm
    if not _is_acyclic(tasks):
        raise PlanError("dependency cycle detected")
    return Plan(data["project_name"], data["task_description"], tasks)


def decompose(request: str, repo_root: str, llm_complete, available_agents: list[str]) -> Plan:
    msgs = [
        {"role": "system", "content": PLANNER_SYSTEM},
        {"role": "user", "content":
            f"Available agents: {available_agents}\nRepo root: {repo_root}\n\nRequest:\n{request}"},
    ]
    msg = llm_complete(msgs, tools=None)
    return parse_plan(msg.content or "", available_agents, repo_root)


def seed_plan(conn, plan: Plan, *, approve: bool = False) -> tuple[str, str, list[str]]:
    """Write the plan into projects/blackboards/tasks. Returns (project_id, bb_id, task_ids).
    If approve=True the blackboard starts 'executing' (gate open); else 'awaiting-approval'."""
    pid, bid = db.new_id("proj_"), db.new_id("bb_")
    conn.execute("INSERT INTO projects (id,name,status,created_at,updated_at) VALUES (?,?,?,?,?)",
                 (pid, plan.project_name, "active", db.now(), db.now()))
    bb_status = "executing" if approve else "awaiting-approval"
    conn.execute("INSERT INTO blackboards (id,project_id,task_description,status,created_at,updated_at)"
                 " VALUES (?,?,?,?,?,?)",
                 (bid, pid, plan.task_description, bb_status, db.now(), db.now()))
    db.log_status(conn, blackboard_id=bid, to_status=bb_status)
    ids = []
    for t in plan.tasks:
        conn.execute(
            "INSERT INTO tasks (id,blackboard_id,agent,status,depends_on,file_scope,queued_at)"
            " VALUES (?,?,?,?,?,?,?)",
            (t.id, bid, t.agent, "pending", json.dumps(t.depends_on),
             json.dumps(t.file_scope), db.now()))
        ids.append(t.id)
    conn.commit()
    return pid, bid, ids
