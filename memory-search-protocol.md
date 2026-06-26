# Memory Search Protocol (BMW OpenCode)

This protocol defines **how every agent must use the `memory` MCP** (`@modelcontextprotocol/server-memory`).
Goal: minimise latency + token cost (especially for GPT models, which have **no prompt caching**).

## The 4 Rules (ENFORCING)

1. **Never call `read_graph`.**
   - It serialises the entire knowledge graph on every call.
   - Use `memory_search_nodes` or `memory_open_nodes` instead.

2. **Be specific with search queries.**
   - Prefer entity names or unique observation keywords.
   - Bad: `memory_search_nodes("project")`
   - Good: `memory_search_nodes("JARVIS Galaxy frontend")`

3. **Cache in context for the session.**
   - If you fetched an entity (or search results) this turn, do **not** fetch it again.
   - Keep the relevant entity JSON in your working context and reuse it.

4. **GPT-model agents: fetch once at session start.**
   - Call memory once with the most relevant query at the beginning of the session.
   - Hold the results and avoid per-turn memory calls.

## Preferred Call Hierarchy (fastest → slowest)

1. `memory_open_nodes(["Exact Entity Name", ...])`
   - O(1) fetch by exact name.
   - Use after you already know the names (from UI context, prior turns, or semantic search).

2. `memory_search_nodes("specific phrase")`
   - O(n) keyword scan, but returns a subset.
   - Use a 2–6 word phrase that uniquely identifies the target.

3. `memory_search_nodes("broad term")`
   - Avoid unless necessary.
   - Broad terms return noisy results and usually lead to repeated follow-up calls.

4. `read_graph`
   - **NEVER** (except explicit admin/maintenance tasks).

## Recommended Workflow (keyword-only)

1. Start with a specific query:
   - `hits = memory_search_nodes("<unique phrase>")`
2. Extract exact entity names from `hits`.
3. Fetch only what you need:
   - `entities = memory_open_nodes(["Name A", "Name B"])`
4. Cache the fetched entity JSON in your context for the remainder of the session.

## Semantic Overlay (Tier 2) — Preferred

If the `memory-semantic-search` skill is available, use it as a drop-in upgrade:

1. Semantic search returns **entity names**:
   - `names = semantic_search("your task description")`
2. Fetch targeted entities:
   - `memory_open_nodes(names)`

This avoids broad keyword scans and avoids `read_graph` while still finding the right nodes.

### GPT agents (semantic overlay)

- At session start:
  1) `names = semantic_search("<task description>")`
  2) `entities = memory_open_nodes(names)`
  3) Cache entities in context and proceed without further memory calls.
