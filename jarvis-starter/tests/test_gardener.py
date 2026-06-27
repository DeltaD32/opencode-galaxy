"""Gardener tests (CO-004 M3): decay tiering + stats — offline HashEngine."""
import sys, pathlib, datetime
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from jarvis.memory import MemoryStore
from jarvis.memory.embeddings import HashEngine
from jarvis.memory import gardener as G


def _age_days(store, eid, days):
    ts = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days)).isoformat()
    store.conn.execute("UPDATE entities SET last_reinforced_at=? WHERE id=?", (ts, eid))
    store.conn.commit()


def test_tiering_and_stats():
    store = MemoryStore.open(":memory:", engine=HashEngine(dim=256))
    try:
        # half_life defaults to 30d → 0d≈hot(1.0), 60d≈warm(0.25), 400d≈cold(~0)
        hot = store._upsert_entity("fresh", "Entity");  _age_days(store, hot, 0)
        warm = store._upsert_entity("aging", "Entity"); _age_days(store, warm, 60)
        cold = store._upsert_entity("stale", "Entity"); _age_days(store, cold, 400)

        counts = G.run(store)
        assert counts == {"hot": 1, "warm": 1, "cold": 1}, counts

        tiers = {r["name"]: r["tier"] for r in
                 store.conn.execute("SELECT name, tier FROM entities")}
        assert tiers == {"fresh": "hot", "aging": "warm", "stale": "cold"}, tiers

        stats = G.get_stats(store)
        assert stats["tiers"] == {"hot": 1, "warm": 1, "cold": 1}, stats
        assert stats["total_entities"] == 3, stats

        # cold consolidation is a no-op without an llm
        assert G.consolidate_cold(store, llm_complete=None) == 0
    finally:
        store.close()  # release the handle before cleanup (Windows)
    print("  ✓ gardener: decay → hot/warm/cold tiers + stats; consolidate no-op offline")


if __name__ == "__main__":
    test_tiering_and_stats()
    print("\nGARDENER (M3) TESTS PASSED ✅")
