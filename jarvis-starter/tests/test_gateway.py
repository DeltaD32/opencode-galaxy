"""Gateway daemon tests (Module C) — FastAPI TestClient, seeded temp state.db."""
import sys, pathlib, tempfile, os
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient
from jarvis import db


def _seed(path):
    os.environ["JARVIS_DB_PATH"] = path
    c = db.connect()
    db.init_db(c)
    c.execute("INSERT INTO projects (id,name,status,created_at,updated_at) VALUES ('p','demo','active',?,?)",
              (db.now(), db.now()))
    c.execute("INSERT INTO blackboards (id,project_id,task_description,status,created_at,updated_at)"
              " VALUES ('bb','p','demo task','executing',?,?)", (db.now(), db.now()))
    c.execute("INSERT INTO tasks (id,blackboard_id,agent,status,depends_on,file_scope,queued_at)"
              " VALUES ('t1','bb','programming-expert','active','[]','[]',?)", (db.now(),))
    db.log_status(c, blackboard_id="bb", to_status="executing")
    c.commit()
    c.close()


def test_gateway_endpoints():
    with tempfile.TemporaryDirectory() as d:
        _seed(os.path.join(d, "state.db"))
        from daemons.gateway.app import app
        client = TestClient(app)

        assert client.get("/health").json()["status"] == "ok"

        nodes = client.get("/api/agents").json()["nodes"]
        assert any(n["name"] == "orchestrator" and n["tier"] == 0 for n in nodes)
        assert any(n["name"] == "programming-expert" for n in nodes)

        tasks = client.get("/api/tasks").json()["tasks"]
        assert tasks and tasks[0]["id"] == "t1" and tasks[0]["active"] is True, tasks

        bbs = client.get("/api/blackboards").json()["blackboards"]
        assert bbs and bbs[0]["status"] == "executing", bbs

        ev = client.get("/api/events?max_ticks=1")
        assert ev.status_code == 200 and "status_events" in ev.text, ev.text
    print("  ✓ gateway: /health, /api/agents, /api/tasks (active), /api/blackboards, SSE tick")


if __name__ == "__main__":
    test_gateway_endpoints()
    print("\nGATEWAY (Module C) TESTS PASSED ✅")
