"""
routing_cache.py — Semantic routing cache for the OpenCode orchestrator.

Self-learning loop:
  1. On each session start, scan opencode.db for new (prompt → skill) pairs.
  2. Embed any new pairs and append to the on-disk numpy index.
  3. On new request, embed the prompt and cosine-search the index.
  4. If best match score >= THRESHOLD, return the cached skill immediately.
  5. After a routing decision is made (any path), call record_routing() to
     persist the new pair so future sessions can learn from it.

Storage layout (~/.opencode/skills/routing-cache/cache/):
  index.npy      — float32 matrix (N, 1536) of embedded prompts
  routing.bin    — hnswlib index (ANN) built from index.npy (preferred)
  records.jsonl  — newline-delimited JSON: {prompt, skill, source, ts}
  meta.json      — {version, count, last_updated}
"""

import asyncio
import json
import os
import pathlib
import sqlite3
import ssl
import time
import urllib.request
from datetime import datetime
from typing import Optional, Tuple

import numpy as np

# Optional ANN acceleration.
try:
    import hnswlib  # type: ignore
except Exception:  # pragma: no cover
    hnswlib = None

# ── Config ────────────────────────────────────────────────────────────────────
EMBED_MODEL   = "openai/text-embedding-3-small"
THRESHOLD     = 0.82      # cosine similarity required for a cache hit
MIN_PROMPT_LEN = 12       # ignore single-word / noise prompts
CACHE_DIR     = pathlib.Path.home() / ".opencode/skills/routing-cache/cache"
INDEX_FILE    = CACHE_DIR / "index.npy"
HNSW_FILE     = CACHE_DIR / "routing.bin"
RECORDS_FILE  = CACHE_DIR / "records.jsonl"
META_FILE     = CACHE_DIR / "meta.json"
DB_PATH       = pathlib.Path.home() / ".local/share/opencode/opencode.db"
VERSION       = 1

# HNSW parameters (cosine space)
HNSW_M = 16
HNSW_EF_CONSTRUCTION = 200
HNSW_EF_SEARCH = 64

# Module-level state to avoid cold-loading on every query.
_RECORDS: Optional[list[dict]] = None
_MATRIX: Optional[np.ndarray] = None
_HNSW: Optional[object] = None

# ── BMW LLM API helpers ───────────────────────────────────────────────────────
def _ssl_ctx() -> Optional[ssl.SSLContext]:
    ca = (
        os.environ.get("BMW_CA_BUNDLE")
        or str(pathlib.Path.home() / ".opencode/plugins/clipjoint/BMW_Trusted_Certificates_Latest.pem")
    )
    if pathlib.Path(ca).exists():
        return ssl.create_default_context(cafile=ca)
    return None


def _embed(texts: list[str]) -> np.ndarray:
    """Embed a list of texts synchronously. Returns float32 (N, 1536)."""
    base = os.environ.get("LLM_API_BASE_URL", "https://api.gcp.cloud.bmw/llmapi/v1")
    base = base.rstrip("/").removesuffix("/v1")
    api_key = os.environ["LLM_API_KEY"]
    token   = os.environ["LLM_API_BEARER_TOKEN"]

    body = json.dumps({"model": EMBED_MODEL, "input": texts}).encode()
    req  = urllib.request.Request(
        f"{base}/v1/embeddings", data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "x-apikey":      api_key,
            "Content-Type":  "application/json",
        },
        method="POST",
    )
    ctx = _ssl_ctx()
    with urllib.request.urlopen(req, **({"context": ctx} if ctx else {}), timeout=30) as r:
        resp = json.loads(r.read().decode())
    return np.array([item["embedding"] for item in resp["data"]], dtype=np.float32)


# ── Cache I/O ─────────────────────────────────────────────────────────────────
def _ensure_cache_dir() -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _normalize(v: np.ndarray) -> np.ndarray:
    """L2-normalize a vector or matrix along last axis."""
    denom = np.linalg.norm(v, axis=-1, keepdims=True) + 1e-10
    return (v / denom).astype(np.float32, copy=False)


def _load_records() -> list[dict]:
    global _RECORDS
    if _RECORDS is not None:
        return _RECORDS
    if RECORDS_FILE.exists():
        _RECORDS = [json.loads(l) for l in RECORDS_FILE.read_text().splitlines() if l.strip()]
    else:
        _RECORDS = []
    return _RECORDS


def _load_matrix() -> np.ndarray:
    global _MATRIX
    if _MATRIX is not None:
        return _MATRIX
    if INDEX_FILE.exists():
        _MATRIX = np.load(str(INDEX_FILE))
    else:
        _MATRIX = np.empty((0, 1536), dtype=np.float32)
    return _MATRIX


def _hnsw_available() -> bool:
    return hnswlib is not None


def _hnsw_build_from_matrix(matrix: np.ndarray) -> object:
    """Build a fresh HNSW index from embeddings matrix and persist it."""
    _ensure_cache_dir()
    dim = int(matrix.shape[1]) if matrix.ndim == 2 else 1536
    idx = hnswlib.Index(space="cosine", dim=dim)  # type: ignore[union-attr]
    count = int(matrix.shape[0])
    max_elements = max(1024, count + 1024)
    idx.init_index(max_elements=max_elements, ef_construction=HNSW_EF_CONSTRUCTION, M=HNSW_M)
    idx.set_ef(HNSW_EF_SEARCH)
    if count:
        ids = np.arange(count, dtype=np.int64)
        idx.add_items(_normalize(matrix), ids)
    idx.save_index(str(HNSW_FILE))
    return idx


def _hnsw_load_or_migrate() -> Optional[object]:
    """Load HNSW index if present; otherwise migrate from index.npy if possible."""
    global _HNSW
    if _HNSW is not None:
        return _HNSW
    if not _hnsw_available():
        return None

    records = _load_records()
    count = len(records)

    if HNSW_FILE.exists():
        idx = hnswlib.Index(space="cosine", dim=1536)  # type: ignore[union-attr]
        idx.load_index(str(HNSW_FILE), max_elements=max(1024, count + 1024))
        idx.set_ef(HNSW_EF_SEARCH)
        _HNSW = idx
        return _HNSW

    # Migration path: build from existing .npy if it matches records.
    if INDEX_FILE.exists() and count:
        matrix = _load_matrix()
        if matrix.shape[0] == count:
            _HNSW = _hnsw_build_from_matrix(matrix)
            return _HNSW

    return None


def _load_index() -> tuple[np.ndarray, list[dict]]:
    """Legacy helper for the numpy fallback path."""
    return _load_matrix(), _load_records()


def _save_index(matrix: np.ndarray, records: list[dict]) -> None:
    _ensure_cache_dir()
    np.save(str(INDEX_FILE), matrix)
    RECORDS_FILE.write_text("\n".join(json.dumps(r) for r in records) + "\n")
    META_FILE.write_text(json.dumps({
        "version":      VERSION,
        "count":        len(records),
        "last_updated": datetime.utcnow().isoformat(),
    }, indent=2))

    # Keep module cache coherent.
    global _MATRIX, _RECORDS
    _MATRIX = matrix
    _RECORDS = records


def _hnsw_ensure_capacity(idx: object, needed_count: int) -> None:
    """Resize HNSW index if out of capacity."""
    cur_max = int(idx.get_max_elements())  # type: ignore[attr-defined]
    if needed_count <= cur_max:
        return
    idx.resize_index(max(needed_count, cur_max * 2))  # type: ignore[attr-defined]


def _cosine_search(
    query_vec: np.ndarray,
    matrix: np.ndarray,
) -> tuple[int, float]:
    """Return (best_index, best_score). Returns (-1, 0.0) on empty matrix."""
    if matrix.shape[0] == 0:
        return -1, 0.0
    q = _normalize(query_vec)
    normed = _normalize(matrix)
    scores = normed @ q
    best   = int(np.argmax(scores))
    return best, float(scores[best])


def _ann_search(query_vec: np.ndarray, k: int = 1) -> Tuple[int, float]:
    """Return (best_index, best_score) using HNSW; (-1, 0.0) if unavailable."""
    idx = _hnsw_load_or_migrate()
    if idx is None:
        return -1, 0.0
    if len(_load_records()) == 0:
        return -1, 0.0
    q = _normalize(query_vec.reshape(1, -1))
    labels, distances = idx.knn_query(q, k=k)  # type: ignore[attr-defined]
    best_label = int(labels[0][0])
    best_dist = float(distances[0][0])
    return best_label, 1.0 - best_dist


# ── DB extraction ─────────────────────────────────────────────────────────────
def extract_db_pairs(known_prompts: set[str] | None = None) -> list[dict]:
    """
    Scan opencode.db for (prompt, skill) pairs not yet in the cache.
    Returns list of {prompt, skill, source, ts} dicts.
    """
    if not DB_PATH.exists():
        return []

    known_prompts = known_prompts or set()
    pairs = []

    conn = sqlite3.connect(str(DB_PATH))
    try:
        # Find sessions where a skill tool was called, paired with the
        # first user text part in the same session.
        skill_rows = conn.execute("""
            SELECT
                s.id          AS session_id,
                s.agent       AS agent,
                s.title       AS title,
                s.time_created AS ts,
                json_extract(p.data, '$.state.input.name') AS skill_name
            FROM part p
            JOIN message m ON p.message_id = m.id
            JOIN session s ON m.session_id = s.id
            WHERE json_extract(p.data, '$.type') = 'tool'
              AND json_extract(p.data, '$.tool')  = 'skill'
              AND json_extract(p.data, '$.state.input.name') IS NOT NULL
            ORDER BY s.time_created ASC
        """).fetchall()

        for session_id, agent, title, ts, skill_name in skill_rows:
            # Get the first user text part in this session
            user_part = conn.execute("""
                SELECT json_extract(p.data, '$.text')
                FROM part p
                JOIN message m ON p.message_id = m.id
                WHERE m.session_id = ?
                  AND json_extract(p.data, '$.type') = 'text'
                  AND json_extract(m.data, '$.role') = 'user'
                ORDER BY p.time_created ASC
                LIMIT 1
            """, (session_id,)).fetchone()

            if not user_part or not user_part[0]:
                continue

            prompt = user_part[0].strip()
            if len(prompt) < MIN_PROMPT_LEN:
                continue
            if prompt in known_prompts:
                continue

            pairs.append({
                "prompt": prompt,
                "skill":  skill_name,
                "source": f"db:{session_id[:20]}",
                "ts":     ts,
            })
            known_prompts.add(prompt)

    finally:
        conn.close()

    return pairs


# ── Public API ────────────────────────────────────────────────────────────────
def sync_from_db() -> int:
    """
    Extract new (prompt → skill) pairs from opencode.db and append to index.
    Returns the number of new pairs added.
    Call once per session start (fast if nothing new).
    """
    _ensure_cache_dir()
    records = _load_records()
    known = {r["prompt"] for r in records}

    new_pairs = extract_db_pairs(known)
    if not new_pairs:
        return 0

    new_texts   = [p["prompt"] for p in new_pairs]
    new_vectors = _embed(new_texts)

    # Persist to numpy fallback storage.
    matrix = _load_matrix()
    matrix = np.vstack([matrix, new_vectors]) if matrix.shape[0] > 0 else new_vectors
    records.extend(new_pairs)
    _save_index(matrix, records)

    # Update HNSW (if available).
    idx = _hnsw_load_or_migrate()
    if idx is not None:
        start = matrix.shape[0] - new_vectors.shape[0]
        ids = np.arange(start, start + new_vectors.shape[0], dtype=np.int64)
        _hnsw_ensure_capacity(idx, int(ids[-1]) + 1)
        idx.add_items(_normalize(new_vectors), ids)  # type: ignore[attr-defined]
        idx.save_index(str(HNSW_FILE))  # type: ignore[attr-defined]
    return len(new_pairs)


def route_cached(prompt: str) -> Optional[dict]:
    """
    Look up a prompt in the semantic cache.

    Returns:
        {skill, score, matched_prompt}  if score >= THRESHOLD
        None                             if no confident match
    """
    if len(prompt.strip()) < MIN_PROMPT_LEN:
        return None

    q_vec = _embed([prompt])[0]
    records = _load_records()

    # Prefer ANN; gracefully fall back to numpy.
    idx, score = _ann_search(q_vec)
    if idx == -1:
        matrix = _load_matrix()
        if matrix.shape[0] == 0:
            return None
        idx, score = _cosine_search(q_vec, matrix)

    if score >= THRESHOLD:
        rec = records[idx]
        return {
            "skill":          rec["skill"],
            "score":          round(score, 4),
            "matched_prompt": rec["prompt"][:120],
        }
    return None


def record_routing(prompt: str, skill: str, source: str = "live") -> None:
    """
    Persist a new (prompt → skill) routing decision to the cache.
    Call after every routing decision so the cache grows automatically.
    Deduplicates by exact prompt match.
    """
    if len(prompt.strip()) < MIN_PROMPT_LEN:
        return

    _ensure_cache_dir()
    records = _load_records()
    known = {r["prompt"] for r in records}

    if prompt in known:
        return  # already indexed

    vec = _embed([prompt])[0]
    matrix = _load_matrix()
    new_id = int(matrix.shape[0])
    matrix = np.vstack([matrix, vec[np.newaxis]]) if matrix.shape[0] > 0 else vec[np.newaxis]
    records.append({
        "prompt": prompt,
        "skill":  skill,
        "source": source,
        "ts":     int(time.time() * 1000),
    })
    _save_index(matrix, records)

    # Update ANN index too (persist after each addition).
    idx = _hnsw_load_or_migrate()
    if idx is not None:
        _hnsw_ensure_capacity(idx, new_id + 1)
        idx.add_items(_normalize(vec.reshape(1, -1)), np.array([new_id], dtype=np.int64))  # type: ignore[attr-defined]
        idx.save_index(str(HNSW_FILE))  # type: ignore[attr-defined]


def cache_stats() -> dict:
    """Return cache statistics."""
    if META_FILE.exists():
        meta = json.loads(META_FILE.read_text())
    else:
        meta = {"version": VERSION, "count": 0, "last_updated": "never"}
    meta.update({
        "hnsw_available": _hnsw_available(),
        "hnsw_file": str(HNSW_FILE),
        "hnsw_present": HNSW_FILE.exists(),
    })
    return meta
