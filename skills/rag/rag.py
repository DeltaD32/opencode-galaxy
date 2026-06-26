"""
rag.py
======
Lightweight RAG (Retrieval-Augmented Generation) using BMW LLM API only.

- Embeds documents with openai/text-embedding-3-small
- Stores vectors in-memory with numpy cosine similarity (no external DB)
- Optionally reranks with cohere/rerank-3-5
- Generates answers with claude-haiku-4-5

Extracted from ~/.opencode/skills/rag/SKILL.md — single source of truth.
Import this module directly; do not regenerate this code inline.

Usage:
    import sys, pathlib
    sys.path.insert(0, str(pathlib.Path.home() / ".opencode/skills/rag"))
    from rag import RagIndex, rag_query

    index = RagIndex()
    index.add_documents([{"content": "...", "source": "doc.txt"}],
                        base_url=base_url, api_key=api_key, token=token, ca_cert=ca_cert)
    result = rag_query("What is the return policy?", index,
                       base_url, api_key, token, ca_cert)
    print(result["answer"])
"""

from __future__ import annotations

import asyncio
import json
import os
import pathlib
import ssl
import urllib.request
from typing import Any

import numpy as np

# ─────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────
EMBED_MODEL    = "openai/text-embedding-3-small"
RERANK_MODEL   = "cohere/rerank-3-5"
GENERATE_MODEL = "claude-haiku-4-5"
CHUNK_SIZE     = 400   # words approx — split on whitespace
CHUNK_OVERLAP  = 40
EMBED_BATCH    = 100   # max texts per embedding API call
_EMBED_SEM     = asyncio.Semaphore(4)  # max 4 concurrent embed batches

_DEFAULT_CA = str(
    pathlib.Path.home() / ".opencode/plugins/clipjoint/BMW_Trusted_Certificates_Latest.pem"
)


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────
def _ssl_ctx(ca_cert: str) -> ssl.SSLContext | None:
    if pathlib.Path(ca_cert).exists():
        return ssl.create_default_context(cafile=ca_cert)
    return None


def _post(url: str, payload: dict, api_key: str, token: str,
          ca_cert: str, timeout: int = 30) -> dict:
    body = json.dumps(payload).encode()
    req = urllib.request.Request(
        url, data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "x-apikey":      api_key,
            "Content-Type":  "application/json",
        },
        method="POST",
    )
    ctx = _ssl_ctx(ca_cert)
    kw = {"context": ctx} if ctx else {}
    with urllib.request.urlopen(req, **kw, timeout=timeout) as r:
        return json.loads(r.read().decode())


# ─────────────────────────────────────────────
# 1. Chunking
# ─────────────────────────────────────────────
def chunk_text(text: str, chunk_size: int = CHUNK_SIZE,
               overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split text into overlapping word-count chunks."""
    words = text.split()
    chunks, i = [], 0
    while i < len(words):
        chunk = " ".join(words[i: i + chunk_size])
        chunks.append(chunk)
        i += chunk_size - overlap
    return [c for c in chunks if c.strip()]


# ─────────────────────────────────────────────
# 2. Embedding
# ─────────────────────────────────────────────
def embed_texts(texts: list[str], base_url: str, api_key: str,
                token: str, ca_cert: str) -> np.ndarray:
    """Embed a list of texts synchronously. Returns float32 (N, 1536)."""
    resp = _post(
        f"{base_url}/v1/embeddings",
        {"model": EMBED_MODEL, "input": texts},
        api_key, token, ca_cert,
    )
    return np.array([item["embedding"] for item in resp["data"]], dtype=np.float32)


async def _embed_batch_async(batch: list[str], base_url: str, api_key: str,
                              token: str, ca_cert: str,
                              loop: asyncio.AbstractEventLoop) -> np.ndarray:
    """Embed one batch concurrently, semaphore-guarded."""
    async with _EMBED_SEM:
        resp = await loop.run_in_executor(
            None,
            lambda: _post(f"{base_url}/v1/embeddings",
                          {"model": EMBED_MODEL, "input": batch},
                          api_key, token, ca_cert)
        )
    return np.array([item["embedding"] for item in resp["data"]], dtype=np.float32)


async def embed_texts_async(texts: list[str], base_url: str, api_key: str,
                             token: str, ca_cert: str) -> np.ndarray:
    """
    Async drop-in for embed_texts(). Fires all batches concurrently
    (up to 4 in-flight). ~3× faster than sequential for large corpora.
    Returns float32 (N, 1536).
    """
    loop = asyncio.get_running_loop()
    batches = [texts[i: i + EMBED_BATCH] for i in range(0, len(texts), EMBED_BATCH)]
    matrices = await asyncio.gather(
        *[_embed_batch_async(b, base_url, api_key, token, ca_cert, loop) for b in batches]
    )
    return np.vstack(matrices)


# ─────────────────────────────────────────────
# 3. In-memory index
# ─────────────────────────────────────────────
class RagIndex:
    """Lightweight in-memory vector store. No external DB required."""

    def __init__(self) -> None:
        self.chunks:   list[str]        = []
        self.metadata: list[dict]       = []
        self.matrix:   np.ndarray | None = None   # shape (N, 1536)

    def add_documents(self, documents: list[dict], base_url: str,
                      api_key: str, token: str, ca_cert: str) -> None:
        """
        Chunk, embed, and index a list of documents.

        documents: list of {"content": str, "source": str (optional)}
        """
        new_chunks, new_meta = [], []
        for doc in documents:
            for chunk in chunk_text(doc["content"]):
                new_chunks.append(chunk)
                new_meta.append({"source": doc.get("source", "unknown")})
        if not new_chunks:
            return

        vectors = []
        for i in range(0, len(new_chunks), EMBED_BATCH):
            vectors.append(embed_texts(new_chunks[i: i + EMBED_BATCH],
                                       base_url, api_key, token, ca_cert))
        new_matrix = np.vstack(vectors)

        self.chunks.extend(new_chunks)
        self.metadata.extend(new_meta)
        self.matrix = (np.vstack([self.matrix, new_matrix])
                       if self.matrix is not None else new_matrix)

    async def add_documents_async(self, documents: list[dict], base_url: str,
                                   api_key: str, token: str, ca_cert: str) -> None:
        """
        Async version of add_documents(). Embeds all batches concurrently.
        Typically ~3× faster for large corpora.
        """
        new_chunks, new_meta = [], []
        for doc in documents:
            for chunk in chunk_text(doc["content"]):
                new_chunks.append(chunk)
                new_meta.append({"source": doc.get("source", "unknown")})
        if not new_chunks:
            return
        new_matrix = await embed_texts_async(new_chunks, base_url, api_key, token, ca_cert)
        self.chunks.extend(new_chunks)
        self.metadata.extend(new_meta)
        self.matrix = (np.vstack([self.matrix, new_matrix])
                       if self.matrix is not None else new_matrix)

    def search(self, query_vec: np.ndarray, top_k: int = 10) -> list[tuple[int, float]]:
        """Cosine similarity search. Returns [(index, score), ...] sorted desc."""
        if self.matrix is None or not self.chunks:
            return []
        q = query_vec / (np.linalg.norm(query_vec) + 1e-10)
        norms  = np.linalg.norm(self.matrix, axis=1, keepdims=True) + 1e-10
        normed = self.matrix / norms
        scores = normed @ q
        top_idx = np.argsort(scores)[::-1][:top_k]
        return [(int(i), float(scores[i])) for i in top_idx]


# ─────────────────────────────────────────────
# 4. Reranking (optional)
# ─────────────────────────────────────────────
def rerank(query: str, candidates: list[str], base_url: str,
           api_key: str, token: str, ca_cert: str,
           top_n: int = 5) -> list[tuple[int, float]]:
    """
    Rerank candidates with cohere/rerank-3-5.
    Returns [(original_index, relevance_score), ...] sorted desc.
    Cost: ~$0.000004/call.
    """
    resp = _post(
        f"{base_url}/v1/rerank",
        {"model": RERANK_MODEL, "query": query,
         "documents": candidates, "top_n": top_n},
        api_key, token, ca_cert,
    )
    return [(r["index"], r["relevance_score"]) for r in resp["results"]]


# ─────────────────────────────────────────────
# 5. Generation
# ─────────────────────────────────────────────
def generate_answer(question: str, context_chunks: list[str],
                    base_url: str, api_key: str, token: str, ca_cert: str,
                    model: str = GENERATE_MODEL) -> str:
    """RAG generation step — answers question grounded in context_chunks."""
    context = "\n\n---\n\n".join(context_chunks)
    resp = _post(
        f"{base_url}/v1/chat/completions",
        {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a helpful assistant. Answer the user's question "
                        "using ONLY the provided context. If the context does not "
                        "contain enough information, say so clearly.\n\n"
                        f"CONTEXT:\n{context}"
                    ),
                },
                {"role": "user", "content": question},
            ],
            "max_completion_tokens": 1024,
        },
        api_key, token, ca_cert, timeout=60,
    )
    return resp["choices"][0]["message"]["content"]


# ─────────────────────────────────────────────
# 6. Full pipeline (convenience wrapper)
# ─────────────────────────────────────────────
def rag_query(
    question: str,
    index: RagIndex,
    base_url: str,
    api_key: str,
    token: str,
    ca_cert: str,
    top_k_embed: int = 20,
    top_n_rerank: int = 5,
    use_rerank: bool = True,
    generate_model: str = GENERATE_MODEL,
) -> dict[str, Any]:
    """
    Full pipeline: embed query → cosine search → (optional) rerank → generate.

    Returns:
        {
            "answer":  str,
            "sources": [{"chunk": str, "source": str, "score": float}, ...],
        }
    """
    q_vec = embed_texts([question], base_url, api_key, token, ca_cert)[0]
    hits  = index.search(q_vec, top_k=top_k_embed)
    if not hits:
        return {"answer": "No documents in index.", "sources": []}

    candidate_chunks = [index.chunks[i]    for i, _ in hits]
    candidate_meta   = [index.metadata[i]  for i, _ in hits]

    if use_rerank and len(candidate_chunks) > top_n_rerank:
        reranked      = rerank(question, candidate_chunks, base_url,
                               api_key, token, ca_cert, top_n=top_n_rerank)
        final_chunks  = [candidate_chunks[i] for i, _ in reranked]
        final_scores  = [s for _, s in reranked]
        final_meta    = [candidate_meta[i]   for i, _ in reranked]
    else:
        final_chunks  = candidate_chunks[:top_n_rerank]
        final_scores  = [s for _, s in hits[:top_n_rerank]]
        final_meta    = candidate_meta[:top_n_rerank]

    answer = generate_answer(question, final_chunks, base_url,
                             api_key, token, ca_cert, model=generate_model)
    sources = [
        {"chunk": c, "source": m["source"], "score": round(s, 4)}
        for c, m, s in zip(final_chunks, final_meta, final_scores)
    ]
    return {"answer": answer, "sources": sources}
