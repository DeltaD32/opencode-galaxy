"""Decomposer + end-to-end orchestration tests (mock LLM, no network)."""
import json, sys, types, pathlib, tempfile
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from jarvis import db, decomposer
from jarvis.decomposer import parse_plan, PlanError
from jarvis import orchestrator


def msg(content=None, tool_calls=None):
    return types.SimpleNamespace(content=content, tool_calls=tool_calls)


def make_plan_json(repo):
    return json.dumps({
        "project_name": "demo",
        "task_description": "build two independent files then combine",
        "tasks": [
            {"id": "a", "agent": "programming-expert", "description": "write a.py",
             "depends_on": [], "file_scope": ["a.py"]},
            {"id": "b", "agent": "design-expert", "description": "write b.md",
             "depends_on": [], "file_scope": ["b.md"]},
            {"id": "c", "agent": "programming-expert", "description": "combine",
             "depends_on": ["a", "b"], "file_scope": ["combined.py"]},
        ],
    })


AGENTS = ["programming-expert", "design-expert", "data-analyst"]


def test_parse_valid():
    with tempfile.TemporaryDirectory() as d:
        plan = parse_plan(make_plan_json(d), AGENTS, d)
        assert len(plan.tasks) == 3
        scope0 = pathlib.Path(plan.tasks[0].file_scope[0])
        assert scope0.is_absolute() and scope0.name == "a.py"  # normalised to abs under repo (OS-agnostic)
    print("  ✓ valid plan parses and file_scope normalises under repo_root")


def test_reject_cycle():
    with tempfile.TemporaryDirectory() as d:
        bad = json.dumps({"project_name": "x", "task_description": "y", "tasks": [
            {"id": "a", "agent": "programming-expert", "description": "", "depends_on": ["b"], "file_scope": []},
            {"id": "b", "agent": "programming-expert", "description": "", "depends_on": ["a"], "file_scope": []},
        ]})
        try:
            parse_plan(bad, AGENTS, d); assert False, "cycle not caught"
        except PlanError as e:
            assert "cycle" in str(e)
    print("  ✓ dependency cycle is rejected")


def test_reject_bad_dep_and_escape():
    with tempfile.TemporaryDirectory() as d:
        bad_dep = json.dumps({"project_name": "x", "task_description": "y", "tasks": [
            {"id": "a", "agent": "programming-expert", "description": "", "depends_on": ["ghost"], "file_scope": []}]})
        try:
            parse_plan(bad_dep, AGENTS, d); assert False
        except PlanError as e:
            assert "unknown task" in str(e)
        escape = json.dumps({"project_name": "x", "task_description": "y", "tasks": [
            {"id": "a", "agent": "programming-expert", "description": "", "depends_on": [], "file_scope": ["../etc/passwd"]}]})
        try:
            parse_plan(escape, AGENTS, d); assert False
        except PlanError as e:
            assert "escapes repo_root" in str(e)
    print("  ✓ bad dependency ref and file_scope escape are rejected")


def test_end_to_end():
    """request -> decompose -> seed -> approve -> concurrent run -> all done."""
    with tempfile.TemporaryDirectory() as d:
        ran_order = []

        def llm(messages, tools=None, model=None):
            sys_prompt = messages[0]["content"]
            if "JARVIS planner" in sys_prompt:
                return msg(content=make_plan_json(d))     # planner call
            ran_order.append(messages[1]["content"])       # agent task call
            return msg(content="done")

        # point the DB at a temp file
        import os
        os.environ["JARVIS_DB_PATH"] = str(pathlib.Path(d) / "state.db")
        res = orchestrator.handle_request("build the thing", d, llm,
                                          auto_approve=True, concurrency=3)
        assert res["status"] == "complete", res
        statuses = {t["id"]: t["status"] for t in res["tasks"]}
        assert statuses == {"a": "done", "b": "done", "c": "done"}, statuses
        # c depends on a and b -> its task call must come after both
        def idx(tid):
            return next(i for i, m in enumerate(ran_order) if f":: {tid}" in m)
        assert idx("c") > idx("a") and idx("c") > idx("b"), ran_order
    print("  ✓ end-to-end: request -> DAG -> approve -> concurrent run -> all tasks done")


def test_awaiting_approval_by_default():
    with tempfile.TemporaryDirectory() as d:
        import os
        os.environ["JARVIS_DB_PATH"] = str(pathlib.Path(d) / "state2.db")
        def llm(messages, tools=None, model=None):
            return msg(content=make_plan_json(d))
        res = orchestrator.handle_request("build", d, llm, auto_approve=False)
        assert res["status"] == "awaiting-approval"
        assert len(res["tasks"]) == 3
    print("  ✓ without auto_approve, the gate holds (awaiting-approval) — nothing executes")


if __name__ == "__main__":
    test_parse_valid()
    test_reject_cycle()
    test_reject_bad_dep_and_escape()
    test_end_to_end()
    test_awaiting_approval_by_default()
    print("\nDECOMPOSER + ORCHESTRATION TESTS PASSED ✅")
