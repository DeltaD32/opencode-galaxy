---
name: routing-cache
description: >
  Semantic routing cache for the OpenCode orchestrator. Learns from past
  sessions by extracting (prompt → skill) pairs from opencode.db, embedding
  them with text-embedding-3-small, and storing a persistent numpy index on
  disk. On each new request, the orchestrator embeds the prompt and cosine-
  searches the cache — if similarity >= 0.82 it short-circuits routing and
  returns the cached skill immediately, skipping GAIA and TTT lookup.
  Grows automatically: every routing decision is written back so the cache
  improves with every session.
  Trigger: loaded automatically by the orchestrator at session start.
license: Proprietary
metadata:
  authors:
    - OpenCode Config
  version: "1.1.0"
  tags:
    - routing
    - self-learning
    - embeddings
    - cache
    - orchestrator
---

# routing-cache

Self-learning semantic routing cache. The module is pre-installed at
`~/.opencode/skills/routing-cache/routing_cache.py` — **no code generation
needed**. Import and call directly.

## Python path

```python
import sys, pathlib
sys.path.insert(0, str(pathlib.Path.home() / ".opencode/skills/routing-cache"))
from routing_cache import sync_from_db, route_cached, record_routing, cache_stats
```

Use the clipjoint venv: `~/.opencode/plugins/clipjoint/.venv/bin/python3`

## API (three functions)

| Call | When | Returns |
|---|---|---|
| `sync_from_db()` | Session start — pull new pairs from opencode.db | `int` — count of new pairs added |
| `route_cached(prompt)` | Before each request (after P0) | `{"skill", "score", "matched_prompt"}` or `None` |
| `record_routing(prompt, skill)` | After every routing decision | `None` (writes to cache) |
| `cache_stats()` | Diagnostics | `{"version", "count", "last_updated"}` |

Hit threshold: **cosine ≥ 0.82** (`text-embedding-3-small`).

## Orchestrator integration (one-liners)

**Session start:**
```bash
~/.opencode/plugins/clipjoint/.venv/bin/python3 -c "
import sys, pathlib
sys.path.insert(0, str(pathlib.Path.home() / '.opencode/skills/routing-cache'))
from routing_cache import sync_from_db, cache_stats
n = sync_from_db()
s = cache_stats()
if n: print(f'[routing-cache] +{n} pairs → {s[\"count\"]} total')
"
```

**Route check:**
```bash
~/.opencode/plugins/clipjoint/.venv/bin/python3 -c "
import sys, pathlib, json
sys.path.insert(0, str(pathlib.Path.home() / '.opencode/skills/routing-cache'))
from routing_cache import route_cached
print(json.dumps(route_cached('''PROMPT''')) or 'null')
"
```

**Record decision:**
```bash
~/.opencode/plugins/clipjoint/.venv/bin/python3 -c "
import sys, pathlib
sys.path.insert(0, str(pathlib.Path.home() / '.opencode/skills/routing-cache'))
from routing_cache import record_routing
record_routing('PROMPT', 'SKILL', source='live')
"
```

## Storage

`~/.opencode/skills/routing-cache/cache/` — `index.npy` (float32 N×1536),
`records.jsonl`, `meta.json`. Append-only, deduplicates by exact prompt.

## Troubleshooting

| Symptom | Fix |
|---|---|
| Always `None` | Run `sync_from_db()` first; check `cache_stats()` |
| `KeyError: LLM_API_KEY` | `source ~/.config/opencode/load-secrets.sh` |
