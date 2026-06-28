"""Memory gardener (CO-004 M3): decay-driven tiering + stats.

Recomputes each entity's decay score from `last_reinforced_at` / `half_life_days`
and migrates entities into hot / warm / cold tiers. This is the scale mechanism:
hot stays cheap to query, cold is a candidate for consolidation (M3.2). Runs off
the hot path (call it periodically), never during a request.

The `tier` column is added with a guarded ALTER inside this module so the unit is
self-contained and does not edit `schema/memory.sql`.
"""
from __future__ import annotations
from .store import MemoryStore, _decay, _now, _new_id

# Decay-score thresholds for tier membership.
HOT_MIN = 0.5
WARM_MIN = 0.1


def _ensure_tier_column(conn):
    cols = [r["name"] for r in conn.execute("PRAGMA table_info(entities)")]
    if "tier" not in cols:
        conn.execute("ALTER TABLE entities ADD COLUMN tier TEXT NOT NULL DEFAULT 'hot'")
        conn.commit()


def _tier_for(score: float) -> str:
    if score >= HOT_MIN:
        return "hot"
    if score >= WARM_MIN:
        return "warm"
    return "cold"


def run(store: MemoryStore) -> dict:
    """Recompute decay scores and (re)assign tiers for every entity.

    Returns the per-tier counts after the pass.
    """
    _ensure_tier_column(store.conn)
    counts = {"hot": 0, "warm": 0, "cold": 0}
    rows = store.conn.execute(
        "SELECT id, last_reinforced_at, half_life_days FROM entities").fetchall()
    for r in rows:
        score = _decay(r["last_reinforced_at"], r["half_life_days"] or 30.0)
        tier = _tier_for(score)
        store.conn.execute("UPDATE entities SET decay_score=?, tier=? WHERE id=?",
                           (score, tier, r["id"]))
        counts[tier] += 1
    store.conn.commit()
    return counts


def get_stats(store: MemoryStore) -> dict:
    """Tier counts + corpus size — the surface a galaxy stats panel reads (M3.3)."""
    _ensure_tier_column(store.conn)
    c = store.conn
    per_tier = {r["tier"]: r["c"] for r in
                c.execute("SELECT tier, COUNT(*) c FROM entities GROUP BY tier")}
    total_obs = c.execute("SELECT COUNT(*) n FROM observations").fetchone()["n"]
    span = c.execute("SELECT MIN(created_at) lo, MAX(created_at) hi FROM entities").fetchone()
    return {
        "tiers": {t: per_tier.get(t, 0) for t in ("hot", "warm", "cold")},
        "total_entities": sum(per_tier.values()),
        "total_observations": total_obs,
        "oldest": span["lo"], "newest": span["hi"],
    }


def consolidate_cold(store: MemoryStore, llm_complete=None, *, max_entities: int = 20) -> int:
    """M3.2 — collapse cold entities' raw observations into one durable PATTERN note.

    Off the hot path. Requires an injected `llm_complete(messages)->msg`; without one
    this is a safe no-op (returns 0) so the gardener runs offline. Returns the number
    of entities consolidated.
    """
    if llm_complete is None:
        return 0
    _ensure_tier_column(store.conn)
    cold = store.conn.execute(
        "SELECT id, name FROM entities WHERE tier='cold' LIMIT ?", (max_entities,)).fetchall()
    done = 0
    for e in cold:
        obs = [o["body"] for o in store.conn.execute(
            "SELECT body FROM observations WHERE entity_id=? ORDER BY observed_at", (e["id"],)).fetchall()]
        if len(obs) < 2:
            continue
        msg = llm_complete([
            {"role": "system", "content": "Consolidate these notes into one durable PATTERN sentence."},
            {"role": "user", "content": f"Entity {e['name']}:\n- " + "\n- ".join(obs)},
        ])
        summary = (getattr(msg, "content", None) or "").strip()
        if not summary:
            continue
        store.conn.execute("DELETE FROM observations WHERE entity_id=?", (e["id"],))
        store.conn.execute(
            "INSERT INTO observations (id,entity_id,tag,domain,body,singleton_key,observed_at)"
            " VALUES (?,?,?,?,?,?,?)",
            (_new_id("obs_"), e["id"], "PATTERN", "", summary, None, _now()))
        done += 1
    store.conn.commit()
    return done


def main(argv=None):
    import argparse, json
    ap = argparse.ArgumentParser(description="Run the memory gardener (decay tiering + stats).")
    ap.add_argument("--db", default=None)
    args = ap.parse_args(argv)
    store = MemoryStore.open(args.db)
    try:
        counts = run(store)
        stats = get_stats(store)
    finally:
        store.close()
    print("tiering:", json.dumps(counts))
    print("stats:", json.dumps(stats, indent=2))
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
