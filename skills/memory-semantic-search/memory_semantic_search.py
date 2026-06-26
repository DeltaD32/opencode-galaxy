"""memory_semantic_search.py — Semantic overlay for the memory MCP.

Purpose
-------
The upstream memory MCP keyword-searches entities and `read_graph` serialises the
entire graph. This module provides a tiny, local ANN index over entity text so
agents can:

  semantic_search(query) -> [entity_name, ...] -> memory_open_nodes(names)

Storage
-------
~/.opencode/skills/memory-semantic-search/cache/
  memory.bin        hnswlib ANN index (cosine)
  entities.jsonl    newline-delimited JSON: {id, name, entityType, text_hash}
  meta.json         {count, last_updated, embed_model, dim}

Notes
-----
- Embeddings use BMW LLM API (text-embedding-3-small) via /v1/embeddings.
- If hnswlib is missing or index not present, semantic_search() returns [].
"""

from __future__ import annotations

import hashlib
import json
import os
import pathlib
import ssl
import time
import urllib.request
from datetime import datetime
from typing import Any

import numpy as np

# Optional ANN acceleration.
try:
    import hnswlib  # type: ignore
except Exception:  # pragma: no cover
    hnswlib = None


# ── Config ─────────────────────────────────────────────────────────────────────

# BMW gateway expects OpenAI-compatible model IDs.
EMBED_MODEL = "openai/text-embedding-3-small"

# HNSW parameters (cosine space) — match routing-cache defaults.
HNSW_M = 16
HNSW_EF_CONSTRUCTION = 200
HNSW_EF_SEARCH = 64

CACHE_DIR = pathlib.Path.home() / ".opencode/skills/memory-semantic-search/cache"
INDEX_FILE = CACHE_DIR / "memory.bin"
ENTITIES_FILE = CACHE_DIR / "entities.jsonl"
META_FILE = CACHE_DIR / "meta.json"

_IDX: Any | None = None
_META: dict[str, Any] | None = None
_NAME_TO_ID: dict[str, int] | None = None


def _ensure_cache_dir() -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _hnsw_available() -> bool:
    return hnswlib is not None


def _ssl_ctx() -> ssl.SSLContext | None:
    # Same CA-bundle lookup pattern as routing-cache.
    ca = (
        os.environ.get("BMW_CA_BUNDLE")
        or str(pathlib.Path.home() / ".opencode/plugins/clipjoint/BMW_Trusted_Certificates_Latest.pem")
    )
    if pathlib.Path(ca).exists():
        return ssl.create_default_context(cafile=ca)
    return None


def _base_url() -> str:
    base = os.environ.get("LLM_API_BASE_URL", "https://api.gcp.cloud.bmw/llmapi/v1")
    base = base.rstrip("/").removesuffix("/v1")
    return f"{base}/v1"


def _embed(texts: list[str]) -> np.ndarray:
    """Embed texts synchronously. Returns float32 (N, dim)."""
    token = os.environ.get("LLM_API_BEARER_TOKEN")
    api_key = os.environ.get("LLM_API_KEY")
    if not token or not api_key:
        raise RuntimeError("Missing LLM_API_BEARER_TOKEN or LLM_API_KEY in env")

    body = json.dumps({"model": EMBED_MODEL, "input": texts}).encode()
    req = urllib.request.Request(
        f"{_base_url()}/embeddings",
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "x-apikey": api_key,
            "Content-Type": "application/json",
        },
        method="POST",
    )

    ctx = _ssl_ctx()
    with urllib.request.urlopen(req, **({"context": ctx} if ctx else {}), timeout=30) as r:
        resp = json.loads(r.read().decode())

    vectors = np.array([item["embedding"] for item in resp["data"]], dtype=np.float32)
    return vectors


def _normalize(v: np.ndarray) -> np.ndarray:
    denom = np.linalg.norm(v, axis=-1, keepdims=True) + 1e-10
    return (v / denom).astype(np.float32, copy=False)


def _entity_text(entity: dict) -> str:
    obs = entity.get("observations") or []
    if not isinstance(obs, list):
        obs = [str(obs)]
    obs_s = " ".join(str(x) for x in obs)
    return f"{entity.get('name','')} {entity.get('entityType','')} {obs_s}".strip()


def _text_hash(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _load_entities() -> list[dict[str, Any]]:
    if not ENTITIES_FILE.exists():
        return []
    out: list[dict[str, Any]] = []
    for line in ENTITIES_FILE.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        out.append(json.loads(line))
    return out


def _write_entities(rows: list[dict[str, Any]]) -> None:
    _ensure_cache_dir()
    ENTITIES_FILE.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n")


def _write_meta(count: int, dim: int) -> None:
    _ensure_cache_dir()
    META_FILE.write_text(
        json.dumps(
            {
                "count": count,
                "dim": dim,
                "embed_model": EMBED_MODEL,
                "last_updated": datetime.utcnow().isoformat(),
            },
            indent=2,
        )
        + "\n"
    )


def _load_meta() -> dict[str, Any] | None:
    if not META_FILE.exists():
        return None
    try:
        return json.loads(META_FILE.read_text())
    except Exception:
        return None


def _load_index_if_present() -> Any | None:
    """Load persisted ANN index. Returns None if unavailable."""
    global _IDX, _META, _NAME_TO_ID
    if _IDX is not None:
        return _IDX
    if not _hnsw_available():
        return None
    if not INDEX_FILE.exists() or not ENTITIES_FILE.exists():
        return None

    meta = _load_meta() or {}
    dim = int(meta.get("dim") or 1536)

    idx = hnswlib.Index(space="cosine", dim=dim)  # type: ignore[union-attr]

    entities = _load_entities()
    count = len(entities)
    idx.load_index(str(INDEX_FILE), max_elements=max(1024, count + 1024))
    idx.set_ef(HNSW_EF_SEARCH)

    _IDX = idx
    _META = meta
    _NAME_TO_ID = {e["name"]: int(e["id"]) for e in entities if "name" in e and "id" in e}
    return _IDX


def build_index(entities: list[dict]) -> None:
    """Build a fresh index from entities and persist it.

    For each entity, build text:
      f"{name} {entityType} {' '.join(observations)}"

    Embeds with text-embedding-3-small via BMW LLM API.
    Persists ANN index + entity map to cache/.
    """
    if not _hnsw_available():
        # Still persist entities.jsonl + meta to enable admin inspection,
        # but semantic_search will remain a no-op.
        _ensure_cache_dir()

    texts: list[str] = []
    rows: list[dict[str, Any]] = []
    for i, e in enumerate(entities):
        t = _entity_text(e)
        texts.append(t)
        rows.append(
            {
                "id": i,
                "name": e.get("name"),
                "entityType": e.get("entityType"),
                "text_hash": _text_hash(t),
            }
        )

    _write_entities(rows)

    if not texts:
        _write_meta(count=0, dim=1536)
        return

    vectors = _embed(texts)
    dim = int(vectors.shape[1])

    if _hnsw_available():
        idx = hnswlib.Index(space="cosine", dim=dim)  # type: ignore[union-attr]
        idx.init_index(
            max_elements=max(1024, len(texts) + 1024),
            ef_construction=HNSW_EF_CONSTRUCTION,
            M=HNSW_M,
        )
        idx.set_ef(HNSW_EF_SEARCH)
        ids = np.arange(len(texts), dtype=np.int64)
        idx.add_items(_normalize(vectors), ids)
        idx.save_index(str(INDEX_FILE))

        # Keep module caches coherent.
        global _IDX
        _IDX = idx

    _write_meta(count=len(texts), dim=dim)

    # Reset in-memory name mapping (reload from entities file).
    global _META, _NAME_TO_ID
    _META = _load_meta() or {}
    _NAME_TO_ID = {r["name"]: int(r["id"]) for r in rows if r.get("name") is not None}


def sync_from_graph(entities: list[dict]) -> int:
    """Incrementally sync: embed only entities not already in the index.

    Uses entity name as the stable key. If an entity exists but its text_hash
    changed, we currently treat it as unchanged (no in-place update) because
    HNSW deletes are expensive and the memory graph is small.
    """
    if not _hnsw_available():
        return 0

    idx = _load_index_if_present()
    if idx is None:
        # No index yet: build fresh.
        build_index(entities)
        return len(entities)

    existing = _load_entities()
    name_to_id = {e["name"]: int(e["id"]) for e in existing if "name" in e and "id" in e}
    next_id = (max(name_to_id.values()) + 1) if name_to_id else 0

    new_entities = [e for e in entities if e.get("name") and e.get("name") not in name_to_id]
    if not new_entities:
        return 0

    new_texts = [_entity_text(e) for e in new_entities]
    new_vecs = _embed(new_texts)

    ids = np.arange(next_id, next_id + len(new_entities), dtype=np.int64)
    needed = int(ids[-1]) + 1
    if needed > int(idx.get_max_elements()):  # type: ignore[attr-defined]
        idx.resize_index(max(needed, int(idx.get_max_elements()) * 2))  # type: ignore[attr-defined]

    idx.add_items(_normalize(new_vecs), ids)  # type: ignore[attr-defined]
    idx.save_index(str(INDEX_FILE))  # type: ignore[attr-defined]

    # Append entity map rows.
    for i, e in enumerate(new_entities):
        t = new_texts[i]
        existing.append(
            {
                "id": int(ids[i]),
                "name": e.get("name"),
                "entityType": e.get("entityType"),
                "text_hash": _text_hash(t),
            }
        )
    _write_entities(existing)

    # Update meta.
    dim = int(new_vecs.shape[1])
    _write_meta(count=len(existing), dim=dim)

    # Refresh caches.
    global _NAME_TO_ID, _META
    _NAME_TO_ID = {e["name"]: int(e["id"]) for e in existing if "name" in e and "id" in e}
    _META = _load_meta() or {}
    return len(new_entities)


def semantic_search(query: str, top_k: int = 5) -> list[str]:
    """Semantic search returning entity *names*.

    Returns [] if index is missing or hnswlib is not importable.
    """
    if not query.strip():
        return []
    if not _hnsw_available():
        return []

    idx = _load_index_if_present()
    if idx is None:
        return []

    entities = _load_entities()
    if not entities:
        return []

    # Avoid raising if env vars are missing; treat as no-results.
    try:
        q_vec = _embed([query])[0]
    except Exception:
        return []

    k = max(1, int(top_k))
    labels, _distances = idx.knn_query(_normalize(q_vec.reshape(1, -1)), k=k)  # type: ignore[attr-defined]
    ids = [int(x) for x in labels[0]]

    id_to_name = {int(e["id"]): str(e["name"]) for e in entities if "id" in e and "name" in e}
    out: list[str] = []
    for i in ids:
        n = id_to_name.get(i)
        if n and n not in out:
            out.append(n)
    return out


def index_stats() -> dict[str, Any]:
    """Return basic health/stats for the local index."""
    meta = _load_meta()
    count = int(meta.get("count")) if meta and "count" in meta else 0
    last = meta.get("last_updated") if meta else None
    return {
        "count": count,
        "index_present": bool(INDEX_FILE.exists() and ENTITIES_FILE.exists()),
        "last_updated": last,
        "hnsw_available": _hnsw_available(),
    }
