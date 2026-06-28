"""Embedding engines (local-first, swappable).

- HashEngine  : deterministic, dependency-free, offline. Default for tests + when no
                model is installed. Good for exact/near-text recall; not deeply semantic.
- LocalEngine : fastembed BAAI/bge-small-en-v1.5 (384-d), offline, real semantics. PROD default.
- BmwEngine   : BMW gateway openai/text-embedding-3-small (1536-d). Optional fallback.

Vector DIM is fixed at table creation (invariant): switching engines => re-embed.
All engines return L2-normalized vectors so sqlite-vec L2 ordering ≈ cosine.
"""
from __future__ import annotations
import os, math, hashlib


def _l2norm(v: list[float]) -> list[float]:
    n = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / n for x in v]


class HashEngine:
    name = "hash"
    def __init__(self, dim: int = 256):
        self.dim = dim
    def embed(self, texts: list[str]) -> list[list[float]]:
        out = []
        for t in texts:
            vec = [0.0] * self.dim
            toks = [w for w in ''.join(c.lower() if c.isalnum() else ' ' for c in t).split() if w]
            for w in toks:
                h = int(hashlib.md5(w.encode()).hexdigest(), 16)
                vec[h % self.dim] += 1.0
            out.append(_l2norm(vec))
        return out


class LocalEngine:
    name = "local"
    def __init__(self, model: str = "BAAI/bge-small-en-v1.5"):
        from fastembed import TextEmbedding  # lazy import
        self._m = TextEmbedding(model_name=model)
        self.dim = 384
    def embed(self, texts: list[str]) -> list[list[float]]:
        return [_l2norm(list(map(float, e))) for e in self._m.embed(texts)]


class BmwEngine:
    name = "bmw"
    dim = 1536
    def __init__(self, model: str = "openai/text-embedding-3-small"):
        from openai import OpenAI
        self._c = OpenAI(base_url=os.environ.get("LLM_API_BASE_URL"),
                         api_key=os.environ.get("LLM_API_KEY", "unused"),
                         default_headers={"Authorization": f"Bearer {os.environ.get('LLM_API_BEARER_TOKEN','')}"})
        self._model = model
    def embed(self, texts: list[str]) -> list[list[float]]:
        r = self._c.embeddings.create(model=self._model, input=texts)
        return [_l2norm(d.embedding) for d in r.data]


def from_env() -> object:
    """Select engine via JARVIS_EMBED_ENGINE (default 'local' in prod, 'hash' if fastembed absent)."""
    choice = os.environ.get("JARVIS_EMBED_ENGINE", "local")
    from ..profile import enforce_embed
    enforce_embed(choice)  # home mode: refuse the cloud (bmw) embedding engine
    if choice == "hash":
        return HashEngine()
    if choice == "bmw":
        return BmwEngine()
    try:
        return LocalEngine()
    except Exception:
        return HashEngine()   # graceful fallback if fastembed/model unavailable
