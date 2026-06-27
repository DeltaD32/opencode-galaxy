"""Integration: orchestrator + memory = the learning loop.
First run records a learning; second run injects it into the agent prompt (recall)."""
import json, sys, types, pathlib, tempfile, os
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from jarvis import orchestrator
from jarvis.memory import MemoryStore
from jarvis.memory.embeddings import HashEngine


def msg(content=None, tool_calls=None):
    return types.SimpleNamespace(content=content, tool_calls=tool_calls)


def plan_json():
    return json.dumps({
        "project_name": "widget", "task_description": "build a widget",
        "tasks": [{"id": "t1", "agent": "programming-expert", "description": "build it",
                   "depends_on": [], "file_scope": ["widget.py"]}]})


def test_learning_loop():
    with tempfile.TemporaryDirectory() as d:
        os.environ["JARVIS_DB_PATH"] = os.path.join(d, "state.db")
        mem = MemoryStore.open(os.path.join(d, "memory.db"), engine=HashEngine(dim=256))

        seen_prompts = []
        def llm(messages, tools=None, model=None):
            if "JARVIS planner" in messages[0]["content"]:
                return msg(content=plan_json())
            seen_prompts.append(messages[1]["content"])   # agent task user-prompt
            return msg(content="done")

        # RUN 1 — no prior memory; should record a WORKED learning afterward.
        r1 = orchestrator.handle_request("build a widget", d, llm, auto_approve=True, memory=mem)
        assert r1["tasks"][0]["status"] == "done"
        learned = mem.recall(agent="programming-expert", k=5)["agent_learnings"]
        assert any("completed" in x for x in learned), learned
        assert "Recalled context" not in seen_prompts[0], "run 1 should have no recalled context yet"

        # RUN 2 — same agent; the prior learning should be RECALLED into the prompt.
        os.environ["JARVIS_DB_PATH"] = os.path.join(d, "state2.db")
        r2 = orchestrator.handle_request("build a widget again", d, llm, auto_approve=True, memory=mem)
        assert r2["tasks"][0]["status"] == "done"
        assert "Recalled context" in seen_prompts[-1], "run 2 should inject recalled memory"
        assert "What you've learned before" in seen_prompts[-1]
        mem.close()  # release the handle before the temp dir is removed (Windows)
    print("  ✓ learning loop: run 1 records, run 2 recalls prior learning into the agent prompt")


def test_project_knowledge_persisted():
    with tempfile.TemporaryDirectory() as d:
        os.environ["JARVIS_DB_PATH"] = os.path.join(d, "s.db")
        mem = MemoryStore.open(os.path.join(d, "m.db"), engine=HashEngine(dim=256))
        def llm(messages, tools=None, model=None):
            return msg(content=plan_json()) if "JARVIS planner" in messages[0]["content"] else msg(content="done")
        orchestrator.handle_request("build a widget", d, llm, auto_approve=True, memory=mem)
        # the project entity exists with a singleton status observation
        ctx = mem.recall(project="widget")["project_context"]
        assert any(c["name"] == "widget" for c in ctx), ctx
        status_obs = [o for c in ctx if c["name"] == "widget" for o in c["observations"]]
        assert any("done" in s for s in status_obs), status_obs
        mem.close()  # release the handle before the temp dir is removed (Windows)
    print("  ✓ project knowledge persisted (project entity + singleton status)")


if __name__ == "__main__":
    test_learning_loop()
    test_project_knowledge_persisted()
    print("\nMEMORY ↔ ORCHESTRATOR INTEGRATION PASSED ✅")
