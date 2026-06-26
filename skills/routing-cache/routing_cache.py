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
from typing import Optional

import numpy as np

# ── Config ────────────────────────────────────────────────────────────────────
EMBED_MODEL   = "openai/text-embedding-3-small"
THRESHOLD     = 0.82      # cosine similarity required for a cache hit
MIN_PROMPT_LEN = 12       # ignore single-word / noise prompts
CACHE_DIR     = pathlib.Path.home() / ".opencode/skills/routing-cache/cache"
INDEX_FILE    = CACHE_DIR / "index.npy"
RECORDS_FILE  = CACHE_DIR / "records.jsonl"
META_FILE     = CACHE_DIR / "meta.json"
DB_PATH       = pathlib.Path.home() / ".local/share/opencode/opencode.db"
VERSION       = 1

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


def _load_index() -> tuple[np.ndarray, list[dict]]:
    """Load the on-disk index. Returns (matrix, records). Both empty if cold cache."""
    if INDEX_FILE.exists() and RECORDS_FILE.exists():
        matrix  = np.load(str(INDEX_FILE))
        records = [json.loads(l) for l in RECORDS_FILE.read_text().splitlines() if l.strip()]
        return matrix, records
    return np.empty((0, 1536), dtype=np.float32), []


def _save_index(matrix: np.ndarray, records: list[dict]) -> None:
    _ensure_cache_dir()
    np.save(str(INDEX_FILE), matrix)
    RECORDS_FILE.write_text("\n".join(json.dumps(r) for r in records) + "\n")
    META_FILE.write_text(json.dumps({
        "version":      VERSION,
        "count":        len(records),
        "last_updated": datetime.utcnow().isoformat(),
    }, indent=2))


def _cosine_search(
    query_vec: np.ndarray,
    matrix: np.ndarray,
) -> tuple[int, float]:
    """Return (best_index, best_score). Returns (-1, 0.0) on empty matrix."""
    if matrix.shape[0] == 0:
        return -1, 0.0
    q = query_vec / (np.linalg.norm(query_vec) + 1e-10)
    norms  = np.linalg.norm(matrix, axis=1, keepdims=True) + 1e-10
    normed = matrix / norms
    scores = normed @ q
    best   = int(np.argmax(scores))
    return best, float(scores[best])


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
    matrix, records = _load_index()
    known = {r["prompt"] for r in records}

    new_pairs = extract_db_pairs(known)
    if not new_pairs:
        return 0

    new_texts   = [p["prompt"] for p in new_pairs]
    new_vectors = _embed(new_texts)

    matrix  = np.vstack([matrix, new_vectors]) if matrix.shape[0] > 0 else new_vectors
    records = records + new_pairs
    _save_index(matrix, records)
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

    matrix, records = _load_index()
    if matrix.shape[0] == 0:
        return None

    q_vec = _embed([prompt])[0]
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
    matrix, records = _load_index()
    known = {r["prompt"] for r in records}

    if prompt in known:
        return  # already indexed

    vec    = _embed([prompt])[0]
    matrix = np.vstack([matrix, vec[np.newaxis]]) if matrix.shape[0] > 0 else vec[np.newaxis]
    records.append({
        "prompt": prompt,
        "skill":  skill,
        "source": source,
        "ts":     int(time.time() * 1000),
    })
    _save_index(matrix, records)


def cache_stats() -> dict:
    """Return cache statistics."""
    if META_FILE.exists():
        meta = json.loads(META_FILE.read_text())
    else:
        meta = {"version": VERSION, "count": 0, "last_updated": "never"}
    return meta
