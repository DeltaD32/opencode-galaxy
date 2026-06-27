"""Routing cache (Module D / build-guide Phase 7).

Every routing decision is embedded and cached; a future request that is highly
similar to a past one reuses its agent — routing gets faster and more consistent
the more the system runs (it learns from itself). Backed by sqlite + sqlite-vec
so there is no separate index to drift.

Embeddings are L2-normalized, so sqlite-vec's L2 distance d maps to cosine
similarity s = 1 - d²/2.
"""
from __future__ import annotations
import os, sqlite3, pathlib
import sqlite_vec
from .memory import embeddings

DEFAULT_PATH = str(pathlib.Path.home() / ".jarvis" / "routing.db")
DEFAULT_THRESHOLD = 0.85


def _cosine_from_l2(distance: float) -> float:
    """For unit vectors: ||a-b||² = 2(1 - cos) → cos = 1 - d²/2."""
    return 1.0 - (distance * distance) / 2.0


class RoutingCache:
    def __init__(self, conn: sqlite3.Connection, engine):
        self.conn = conn
        self.engine = engine

    @classmethod
    def open(cls, path: str | None = None, engine=None):
        p = path or os.environ.get("JARVIS_ROUTING_PATH", DEFAULT_PATH)
        if p != ":memory:":
            pathlib.Path(p).parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(p)
        conn.row_factory = sqlite3.Row
        conn.enable_load_extension(True)
        sqlite_vec.load(conn)
        conn.enable_load_extension(False)
        cache = cls(conn, engine or embeddings.from_env())
        cache.init()
        return cache

    def init(self):
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS routes ("
            " id INTEGER PRIMARY KEY, request TEXT NOT NULL, agent TEXT NOT NULL, hits INTEGER NOT NULL DEFAULT 0)")
        self.conn.execute(
            f"CREATE VIRTUAL TABLE IF NOT EXISTS route_vectors USING vec0("
            f"route_id INTEGER PRIMARY KEY, embedding float[{self.engine.dim}])")
        self.conn.commit()

    def record(self, request_text: str, chosen_agent: str) -> int:
        """Cache a routing decision (request → agent) with its embedding."""
        vec = self.engine.embed([request_text])[0]
        cur = self.conn.execute("INSERT INTO routes (request, agent) VALUES (?,?)",
                                (request_text, chosen_agent))
        rid = cur.lastrowid
        self.conn.execute("INSERT INTO route_vectors (route_id, embedding) VALUES (?,?)",
                          (rid, sqlite_vec.serialize_float32(vec)))
        self.conn.commit()
        return rid

    def lookup(self, request_text: str, threshold: float = DEFAULT_THRESHOLD):
        """Return the cached agent for the most-similar past request if its cosine
        similarity ≥ threshold (a cache HIT), else None (a MISS)."""
        hit = self.lookup_detailed(request_text)
        if hit and hit["similarity"] >= threshold:
            self.conn.execute("UPDATE routes SET hits = hits + 1 WHERE id=?", (hit["route_id"],))
            self.conn.commit()
            return hit["agent"]
        return None

    def lookup_detailed(self, request_text: str):
        """Nearest cached route with its similarity, or None if the cache is empty."""
        qv = sqlite_vec.serialize_float32(self.engine.embed([request_text])[0])
        row = self.conn.execute(
            "SELECT route_id, distance FROM route_vectors WHERE embedding MATCH ? ORDER BY distance LIMIT 1",
            (qv,)).fetchone()
        if not row:
            return None
        r = self.conn.execute("SELECT agent FROM routes WHERE id=?", (row["route_id"],)).fetchone()
        if not r:
            return None
        return {"route_id": row["route_id"], "agent": r["agent"],
                "similarity": round(_cosine_from_l2(row["distance"]), 4)}

    def close(self):
        self.conn.close()
