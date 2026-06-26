---
name: memory-semantic-search
description: Semantic search overlay for the memory MCP. Embeds entity names+observations with text-embedding-3-small, stores an hnswlib ANN index, and returns entity names for targeted memory_open_nodes lookups. Use instead of read_graph or broad memory_search_nodes calls.
---

## How to use

```python
import sys, pathlib
sys.path.insert(0, str(pathlib.Path.home() / ".opencode/skills/memory-semantic-search"))
from memory_semantic_search import semantic_search, sync_from_graph, index_stats

# Find relevant entity names (fast ANN search)
names = semantic_search("JARVIS galaxy 3D view frontend")
# → ['Memory Galaxy Web Frontend', 'JARVIS Project', 'GalaxyView Component']

# Fetch only those entities from the MCP (targeted, not full graph)
# Then call: memory_open_nodes(names)

# Sync new entities into the index after graph updates
added = sync_from_graph(new_entities)

# Check index health
print(index_stats())
```

## When to use

- Any time you would call `read_graph` — use `semantic_search` instead
- When `memory_search_nodes` returns too many or too few results
- GPT-model agents: call `semantic_search` once at session start with your task description to pre-load relevant context
