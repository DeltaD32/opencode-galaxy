"""Orchestrator: the single hand-over entrypoint.

handle_request(request) -> decompose into a DAG -> seed the blackboard ->
(optionally auto-approve the gate) -> run the scheduler to completion ->
return a summary. This is what 'talking to JARVIS' calls.

If a MemoryStore is passed, agents RECALL relevant knowledge before acting and
the system RECORDS a learning after each task — the self-learning loop.
"""
from __future__ import annotations
import json
from . import db, agents as agentreg, decomposer, scheduler
from .runtime import TaskSpec


def _build_spec(task_row, repo_root: str, project: str | None = None, memory=None):
    """Map a tasks row -> TaskSpec using the agent registry, injecting recalled memory."""
    spec_def = agentreg.get(task_row["agent"])
    file_scope = json.loads(task_row["file_scope"])
    recalled = ""
    if memory is not None:
        recalled = memory.recall_text(project=project, agent=task_row["agent"],
                                      query=task_row["agent"])
    user = f"Task: {task_row['agent']} :: {task_row['id']}\nWork only within: {file_scope}\n"
    if recalled:
        user += f"\n--- Recalled context (from prior work) ---\n{recalled}\n--- end context ---\n"
    user += "Complete the task."
    return TaskSpec(
        task_id=task_row["id"], agent=task_row["agent"], system_prompt=spec_def["prompt"],
        user_prompt=user, repo_root=repo_root, file_scope=file_scope,
        allowed_tools=spec_def["tools"], model=spec_def.get("model"))


def handle_request(request: str, repo_root: str, llm_complete, *,
                   auto_approve: bool = False, concurrency: int = 3, memory=None) -> dict:
    conn = db.connect()
    db.init_db(conn)
    plan = decomposer.decompose(request, repo_root, llm_complete, agentreg.available())
    pid, bid, task_ids = decomposer.seed_plan(conn, plan, approve=auto_approve)

    if not auto_approve:
        conn.close()  # release the SQLite handle — Windows can't unlink an open DB file
        return {"status": "awaiting-approval", "project_id": pid, "blackboard_id": bid,
                "tasks": task_ids, "plan": plan}

    scheduler.run_until_idle(
        conn, lambda t: _build_spec(t, repo_root, plan.project_name, memory), llm_complete,
        concurrency=concurrency, require_gate=True)

    rows = conn.execute("SELECT id, agent, status, result FROM tasks WHERE blackboard_id=?",
                        (bid,)).fetchall()

    # RECORD: persist a learning per completed task + register the project knowledge.
    if memory is not None:
        for r in rows:
            if r["status"] == "done":
                memory.learn(r["agent"], "WORKED", plan.project_name,
                             f"completed '{plan.task_description}' (task {r['id']})")
        memory.remember(project=plan.project_name, blackboard_id=bid,
                        observations=[{"body": f"Status: {plan.task_description} — done",
                                       "singleton_key": "status"}])

    result = {"status": "complete", "project_id": pid, "blackboard_id": bid,
              "tasks": [dict(r) for r in rows]}
    conn.close()  # release the SQLite handle — Windows can't unlink an open DB file
    return result


def approve(conn, blackboard_id: str) -> None:
    """Open the governance gate for a blackboard (sets it 'executing')."""
    conn.execute("UPDATE blackboards SET status='executing', updated_at=? WHERE id=?",
                 (db.now(), blackboard_id))
    db.log_status(conn, blackboard_id=blackboard_id, to_status="executing",
                  from_status="awaiting-approval")
    conn.commit()
