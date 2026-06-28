"""Importer tests (CO-004 M4): dedup-merge, learnings, relations, verify — offline HashEngine."""
import sys, pathlib, json, tempfile
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from jarvis.memory import MemoryStore
from jarvis.memory.embeddings import HashEngine
from jarvis.memory import migrate_jsonl as M


def test_parse_learning_obs():
    tag, domain, note, date = M.parse_learning_obs("[WORKED] vite | use ResizeObserver not window.resize | 2026-06-02")
    assert (tag, domain, note, date) == ("WORKED", "vite", "use ResizeObserver not window.resize", "2026-06-02")
    print("  ✓ learning observation '[TAG] domain | note | date' parses")


def test_import_dedup_and_verify():
    with tempfile.TemporaryDirectory() as d:
        jf = pathlib.Path(d) / "memory.jsonl"
        lines = [
            {"type": "entity", "name": "JARVIS Galaxy", "entityType": "Project",
             "observations": ["[BUILT] orbital view shipped | 2026-06-01", "Status: in progress"]},
            {"type": "entity", "name": "JARVIS Web Frontend", "entityType": "Project",  # dup → merges
             "observations": ["[DECISION] iframe galaxy panel | 2026-06-02"]},
            {"type": "entity", "name": "GalaxyView", "entityType": "Component",
             "observations": ["Three.js orbital scene with lit tethers"]},
            {"type": "entity", "name": "programming-expert::learnings", "entityType": "AgentLearnings",
             "observations": ["[WORKED] vite | use ResizeObserver not window.resize | 2026-06-02"]},
            {"type": "relation", "from": "JARVIS Web Frontend", "to": "GalaxyView", "relationType": "has-component"},
            {"type": "relation", "from": "Ghost", "to": "Nowhere", "relationType": "x"},  # dangling
        ]
        jf.write_text("\n".join(json.dumps(l) for l in lines), encoding="utf-8")

        store = MemoryStore.open(":memory:", engine=HashEngine(dim=256))
        try:
            stats = M.import_jsonl(store, str(jf))  # uses DEFAULT_MERGES
            proj = {r["name"]: r["id"] for r in
                    store.conn.execute("SELECT id,name FROM entities WHERE entity_type='Project'")}
            assert "JARVIS Galaxy" in proj and "JARVIS Web Frontend" not in proj, proj
            assert store._resolve("JARVIS Web Frontend") == proj["JARVIS Galaxy"], "alias must resolve to canonical"
            assert stats["merged"] == 1, stats

            learned = store.recall(agent="programming-expert", k=5)["agent_learnings"]
            assert any("ResizeObserver" in x for x in learned), learned

            assert stats["relations"] == 1 and len(stats["dangling"]) == 1, stats

            report = M.verify(store)
            assert report["ok"], report
            assert report["orphan_relations"] == 0 and not report["duplicate_names"], report
            assert report["vectors_complete"], report
        finally:
            store.close()  # release the handle before the temp dir is removed (Windows)
    print("  ✓ import: dedup-merge to one canonical, learnings, relations, verify clean")


if __name__ == "__main__":
    test_parse_learning_obs()
    test_import_dedup_and_verify()
    print("\nMIGRATE (M4) TESTS PASSED ✅")
