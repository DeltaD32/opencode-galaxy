---
name: rag
description: Lightweight RAG (Retrieval-Augmented Generation) using BMW LLM API only. Embeds documents with text-embedding-3-small, stores vectors in-memory with numpy cosine similarity, optionally reranks with cohere/rerank-3-5, and answers with claude-haiku-4-5. No external vector DB — stdlib + numpy only.
metadata:
  version: "1.1.0"
---

# Skill: Lightweight RAG

In-memory RAG using BMW LLM API exclusively. The module is pre-installed at
`~/.opencode/skills/rag/rag.py` — **no code generation needed**.

## Python path

```python
import sys, pathlib
sys.path.insert(0, str(pathlib.Path.home() / ".opencode/skills/rag"))
from rag import RagIndex, rag_query
```

Use the clipjoint venv: `~/.opencode/plugins/clipjoint/.venv/bin/python3`

## Models

| Step | Model | Cost |
|---|---|---|
| Embed | `openai/text-embedding-3-small` | $0.022/M tokens |
| Rerank | `cohere/rerank-3-5` | $0.000004/query |
| Generate | `claude-haiku-4-5` | $1.10/M input |

## API

```python
# Sync (small corpus)
index = RagIndex()
index.add_documents(
    [{"content": "...", "source": "doc.txt"}],
    base_url=base_url, api_key=api_key, token=token, ca_cert=ca_cert,
)
result = rag_query("What is the return policy?", index,
                   base_url, api_key, token, ca_cert)
print(result["answer"])
for s in result["sources"]:
    print(f"  [{s['score']:.3f}] {s['source']}: {s['chunk'][:80]}…")

# Async (large corpus — ~3× faster embedding)
import asyncio
async def build():
    await index.add_documents_async([...], base_url, api_key, token, ca_cert)
asyncio.run(build())
```

## Credentials

| Variable | Description |
|---|---|
| `LLM_API_BASE_URL` | `https://api.gcp.cloud.bmw/llmapi` (note: no `/v1` suffix) |
| `LLM_API_BEARER_TOKEN` | OAuth2 token (auto-refreshed by `opencode-bmw`) |
| `LLM_API_KEY` | BMW API gateway key |
| `BMW_CA_BUNDLE` | Path to BMW CA cert (optional; defaults to clipjoint pem) |

## Key details

- **No external DB** — index lives in RAM; `pickle.dump(index, open("index.pkl","wb"))` to persist
- **Batch embedding** — chunks sent in batches of 100 (API limit-safe)
- **Rerank optional** — pass `use_rerank=False` to `rag_query()` to skip (saves $0.000004)
- **Chunk size** — 400 words / 40 overlap; tune `CHUNK_SIZE` / `CHUNK_OVERLAP` constants in `rag.py`

## rag_query() return shape

```python
{
    "answer":  str,                              # LLM-grounded answer
    "sources": [{"chunk": str, "source": str, "score": float}, ...]
}
```

## Error handling

| Error | Action |
|---|---|
| Embed API fails | Raises `urllib.error.HTTPError` — caller should retry |
| Empty corpus | `search()` returns `[]`; `rag_query()` returns `"No documents in index."` |
| Rerank API fails | Pass `use_rerank=False` to fall back to cosine-only ranking |
