"""Memory tests — deterministic HashEngine, no network/model download."""
import sys, pathlib, sqlite3, time
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from jarvis.memory import MemoryStore
from jarvis.memory.embeddings import HashEngine


def fresh() -> MemoryStore:
    return MemoryStore.open(":memory:", engine=HashEngine(dim=256))


def test_project_binding_dedup():
    m = fresh()
    # two writes for the SAME project via different name variants → ONE project entity
    m.remember(project="JARVIS Galaxy", observations=[{"body": "uses Three.js"}])
    m.add_alias("JARVIS Galaxy", "jarvis-galaxy")
    m.remember(project="jarvis-galaxy", observations=[{"body": "uses Three.js"}])  # dup obs + alias
    n_proj = m.conn.execute("SELECT COUNT(*) c FROM entities WHERE entity_type='Project'").fetchone()["c"]
    n_obs = m.conn.execute("SELECT COUNT(*) c FROM observations").fetchone()["c"]
    assert n_proj == 1, f"expected 1 project entity, got {n_proj}"
    assert n_obs == 1, f"duplicate observation was not de-duped (got {n_obs})"
    print("  ✓ project binding: variants resolve to one entity; duplicate observation de-duped")


def test_singleton_replace():
    m = fresh()
    m.remember(project="proj", observations=[{"body": "Status: NOT STARTED", "singleton_key": "status"}])
    m.remember(project="proj", observations=[{"body": "Status: COMPLETE", "singleton_key": "status"}])
    rows = m.conn.execute("SELECT body FROM observations WHERE singleton_key='status'").fetchall()
    assert len(rows) == 1 and "COMPLETE" in rows[0]["body"], [r["body"] for r in rows]
    print("  ✓ singleton: Status replaced, not accumulated (no NOT STARTED + COMPLETE)")


def test_agent_learnings_recall():
    m = fresh()
    m.learn("programming-expert", "WORKED", "vite", "use ResizeObserver not window.resize")
    m.learn("programming-expert", "AVOID", "vite", "window.resize misses CSS-transform opens")
    r = m.recall(agent="programming-expert", k=5)
    joined = " ".join(r["agent_learnings"])
    assert "ResizeObserver" in joined and "AVOID" in joined, r["agent_learnings"]
    print("  ✓ agent learnings recall (WORKED/AVOID), most-relevant first")


def test_semantic_knn():
    m = fresh()
    m.remember(project="p", entity_name="GalaxyView", entity_type="Component",
               observations=[{"body": "Three.js orbital scene with lit tethers"}])
    m.remember(project="p", entity_name="VoiceController", entity_type="Component",
               observations=[{"body": "speech to text and TTS pipeline"}])
    hits = m.recall(project="p", query="three js orbital galaxy rendering", k=2)["semantic"]
    names = [h["name"] for h in hits]
    assert names and names[0] == "GalaxyView", names
    print("  ✓ semantic KNN: query retrieves the most relevant entity first")


def test_project_context_pack():
    m = fresh()
    m.remember(project="p", entity_name="db-reader", entity_type="Module",
               observations=[{"body": "converts blackboard to graph"}],
               relations=[("p", "part-of")])
    pack = m.recall(project="p", agent=None)["project_context"]
    names = [c["name"] for c in pack]
    assert "p" in names and "db-reader" in names, names
    print("  ✓ project context pack returns the project entity + related entities")


def test_recall_text_block():
    m = fresh()
    m.learn("design-expert", "PATTERN", "ui", "amber = needs human decision")
    txt = m.recall_text(agent="design-expert", project=None, query="")
    assert "amber" in txt and "learned before" in txt
    print("  ✓ recall_text renders an injectable context block")


def test_dim_mismatch_guard():
    import tempfile, os
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "m.db")
        s = MemoryStore.open(p, engine=HashEngine(dim=256))       # creates dim=256
        try:
            MemoryStore.open(p, engine=HashEngine(dim=128))       # mismatch
            assert False, "dim mismatch not caught"
        except RuntimeError as e:
            assert "dim mismatch" in str(e)
        s.close()  # release the handle before the temp dir is removed (Windows)
    print("  ✓ embedding dim mismatch is refused (no silent corruption)")


if __name__ == "__main__":
    test_project_binding_dedup()
    test_singleton_replace()
    test_agent_learnings_recall()
    test_semantic_knn()
    test_project_context_pack()
    test_recall_text_block()
    test_dim_mismatch_guard()
    print("\nMEMORY TESTS PASSED ✅")
