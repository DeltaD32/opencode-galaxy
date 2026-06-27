"""Smoke test: foundation works end-to-end with a mock LLM (no network)."""
import json, sys, types, pathlib, tempfile, os
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from jarvis import db
from jarvis.runtime import TaskSpec, run_task
from jarvis import scheduler


# ---- a mock LLM message + complete() --------------------------------------
def make_msg(content=None, tool_calls=None):
    tc_objs = None
    if tool_calls:
        tc_objs = []
        for i, (name, args) in enumerate(tool_calls):
            tc_objs.append(types.SimpleNamespace(
                id=f"call_{i}", type="function",
                function=types.SimpleNamespace(name=name, arguments=json.dumps(args))))
    return types.SimpleNamespace(content=content, tool_calls=tc_objs)


def mock_complete_writes_file(messages, tools=None, model=None):
    # First call: ask to write a file. Second call (after tool result): finish.
    has_tool_result = any(m.get("role") == "tool" for m in messages)
    if not has_tool_result:
        return make_msg(tool_calls=[("write_file", {"path": "out.txt", "content": "hello from agent"})])
    return make_msg(content="Done: wrote out.txt with a greeting.")


def test_agent_loop():
    with tempfile.TemporaryDirectory() as d:
        spec = TaskSpec(task_id="t1", agent="programming-expert",
                        system_prompt="You write files.", user_prompt="write out.txt",
                        repo_root=d, file_scope=[d], allowed_tools=["write_file", "read_file"])
        res = run_task(spec, mock_complete_writes_file)
        assert res.status == "done", res
        assert (pathlib.Path(d) / "out.txt").read_text() == "hello from agent"
        assert any(s["tool"] == "write_file" for s in res.transcript)
    print("  ✓ agent loop runs tool-use cycle and writes within file_scope")


def test_file_scope_enforced():
    with tempfile.TemporaryDirectory() as d:
        # scope allows only subdir 'allowed'; agent tries to write outside it
        allowed = pathlib.Path(d) / "allowed"; allowed.mkdir()
        def complete(messages, tools=None, model=None):
            if not any(m.get("role") == "tool" for m in messages):
                return make_msg(tool_calls=[("write_file", {"path": "../secret.txt", "content": "x"})])
            return make_msg(content="done")
        spec = TaskSpec(task_id="t2", agent="a", system_prompt="s", user_prompt="u",
                        repo_root=str(allowed), file_scope=[str(allowed)], allowed_tools=["write_file"])
        res = run_task(spec, complete)
        assert not (pathlib.Path(d) / "secret.txt").exists(), "escaped file_scope!"
        assert any("outside this task's file_scope" in s["result"] for s in res.transcript)
    print("  ✓ file_scope sandbox blocks out-of-scope writes")


def _seed_project(conn, n_tasks, deps=None, scopes=None, executing=True):
    pid = db.new_id("proj_"); bid = db.new_id("bb_")
    conn.execute("INSERT INTO projects (id,name,status,created_at,updated_at) VALUES (?,?,?,?,?)",
                 (pid, "demo", "active", db.now(), db.now()))
    conn.execute("INSERT INTO blackboards (id,project_id,task_description,status,created_at,updated_at)"
                 " VALUES (?,?,?,?,?,?)",
                 (bid, pid, "demo task", "executing" if executing else "deliberating", db.now(), db.now()))
    ids = []
    for i in range(n_tasks):
        tid = f"task{i}"
        conn.execute("INSERT INTO tasks (id,blackboard_id,agent,status,depends_on,file_scope,queued_at)"
                     " VALUES (?,?,?,?,?,?,?)",
                     (tid, bid, f"agent{i}", "pending",
                      json.dumps(deps[i] if deps else []),
                      json.dumps(scopes[i] if scopes else []), db.now()))
        ids.append(tid)
    conn.commit()
    return bid, ids


def test_concurrency_and_deps():
    order = []
    def complete(messages, tools=None, model=None):
        # record which agent ran (from system prompt), finish immediately
        sysmsg = messages[0]["content"]
        order.append(sysmsg)
        return make_msg(content="ok")

    def build_spec(t):
        return TaskSpec(task_id=t["id"], agent=t["agent"], system_prompt=t["id"],
                        user_prompt="go", repo_root="/tmp", file_scope=[], allowed_tools=[])

    conn = db.connect(":memory:"); db.init_db(conn)
    # task2 depends on task0 and task1; 0 and 1 independent → run concurrently
    bid, ids = _seed_project(conn, 3, deps=[[], [], ["task0", "task1"]])
    scheduler.run_until_idle(conn, build_spec, complete, concurrency=3)
    statuses = {r["id"]: r["status"] for r in conn.execute("SELECT id,status FROM tasks")}
    assert statuses == {"task0": "done", "task1": "done", "task2": "done"}, statuses
    # task2 must have run after both deps
    assert order.index("task2") > order.index("task0")
    assert order.index("task2") > order.index("task1")
    print("  ✓ independent tasks dispatch together; dependent task waits for both")


def test_governance_gate():
    def complete(messages, tools=None, model=None):
        return make_msg(content="ok")
    def build_spec(t):
        return TaskSpec(t["id"], t["agent"], "s", "u", "/tmp", [], [])
    conn = db.connect(":memory:"); db.init_db(conn)
    bid, ids = _seed_project(conn, 1, executing=False)  # blackboard NOT executing
    scheduler.tick(conn, build_spec, complete, require_gate=True)
    st = conn.execute("SELECT status FROM tasks WHERE id='task0'").fetchone()["status"]
    assert st == "pending", f"gate failed: task ran without approval (status={st})"
    print("  ✓ governance gate: task will not run until blackboard is 'executing'")


def test_file_lease_serializes():
    ran = []
    def complete(messages, tools=None, model=None):
        ran.append(messages[0]["content"]); return make_msg(content="ok")
    def build_spec(t):
        return TaskSpec(t["id"], t["agent"], t["id"], "u", "/tmp",
                        json.loads(t["file_scope"]), [])
    conn = db.connect(":memory:"); db.init_db(conn)
    # both tasks want the SAME file → must NOT run in the same tick
    bid, ids = _seed_project(conn, 2, scopes=[["/repo/app.py"], ["/repo/app.py"]])
    n1 = scheduler.tick(conn, build_spec, complete, concurrency=3)
    n2 = scheduler.tick(conn, build_spec, complete, concurrency=3)
    assert n1 == 1 and n2 == 1, f"overlapping scope ran together (n1={n1}, n2={n2})"
    print("  ✓ overlapping file_scope serializes (no concurrent edit to same file)")


if __name__ == "__main__":
    conn = db.connect(":memory:"); db.init_db(conn)
    print("schema applies cleanly:")
    print("  ✓ tables:", [r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")])
    test_agent_loop()
    test_file_scope_enforced()
    test_concurrency_and_deps()
    test_governance_gate()
    test_file_lease_serializes()
    print("\nALL FOUNDATION TESTS PASSED ✅")
