"""Routing-cache tests (Module D) — offline HashEngine (lexical bag-of-words)."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from jarvis.routing import RoutingCache
from jarvis.memory.embeddings import HashEngine


def test_record_lookup_hit_and_miss():
    cache = RoutingCache.open(":memory:", engine=HashEngine(dim=256))
    try:
        cache.record("build a fastapi web app", "programming-expert")

        # exact + reordered (same token set) → similarity 1.0 → HIT
        assert cache.lookup("build a fastapi web app") == "programming-expert"
        assert cache.lookup("a web app fastapi build") == "programming-expert"

        # unrelated request → no shared tokens → MISS
        assert cache.lookup("design a corporate logo") is None

        # partial overlap (4/5 tokens) reuses at a looser threshold
        assert cache.lookup("build a flask web app", threshold=0.6) == "programming-expert"
        # …but not at the strict default
        assert cache.lookup("build a flask web app") is None

        # hit counter advanced
        hits = cache.conn.execute("SELECT hits FROM routes WHERE agent='programming-expert'").fetchone()["hits"]
        assert hits >= 1
    finally:
        cache.close()
    print("  ✓ routing cache: similar request reuses agent; unrelated misses; hits tracked")


if __name__ == "__main__":
    test_record_lookup_hit_and_miss()
    print("\nROUTING (Module D) TESTS PASSED ✅")
