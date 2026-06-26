# agent-memory — Per-Agent Self-Learning Memory

Per-agent structured learnings stored in the memory MCP knowledge graph.
Each agent maintains its own namespace (`<agent-name>::learnings`) with
observations tagged as `WORKED`, `AVOID`, or `PATTERN`.

Learnings survive session resets — agents can clear context between tasks
and reconstruct their personal "best practices" from memory on next invocation.

## When to use

- **Start of task:** call `recall()` to surface relevant tips before starting work
- **End of task:** call `learn()` to record what worked and what to avoid
- **Debugging:** call `summarise_learnings()` to inspect an agent's accumulated knowledge

## How to use

```python
import sys, pathlib
sys.path.insert(0, str(pathlib.Path.home() / ".opencode/skills/agent-memory"))
from agent_memory import recall, learn, summarise_learnings
```

<!-- skill-lint: ignore -->
```python
# At START of task — recall relevant learnings (illustrative, not executable here)
tips = recall("programming-expert", domain="Angular routing", limit=5)
# → ["[WORKED] Angular routing | Use @defer for lazy routes | 2026-06-25", ...]

# At END of task — record what worked / what to avoid
learn("programming-expert", "WORKED",   "Angular routing", "<what worked>")
learn("programming-expert", "AVOID",    "Angular routing", "<what to avoid>")
learn("programming-expert", "PATTERN",  "BMW LLM API",     "<reusable technique>")

# Human-readable summary (for display or logging)
print(summarise_learnings("programming-expert", limit=5))
```

## Observation format

Each observation is stored as a single string:
```
[WORKED]  <domain> | <note> | <YYYY-MM-DD>
[AVOID]   <domain> | <note> | <YYYY-MM-DD>
[PATTERN] <domain> | <note> | <YYYY-MM-DD>
```

## Namespace isolation

Each agent has its own entity: `<agent-name>::learnings`.
Agents cannot read or write each other's namespaces unless explicitly passing
the other agent's name to `recall()`.

Agents with cross-cutting learnings (e.g. secretary, orchestrator) use the
`shared::learnings` namespace.

## Functions

| Function | Purpose |
|---|---|
| `learn(agent, tag, domain, note)` | Record one learning. Deduplicates automatically. |
| `recall(agent, domain="", tag=None, limit=10)` | Retrieve learnings, filtered by domain/tag. |
| `summarise_learnings(agent, limit=5)` | Compact markdown summary for prepending to task context. |
| `get_all_agents_with_learnings()` | List all agents that have at least one learning. |
| `clear_learnings(agent)` | Remove all learnings for an agent. Use deliberately. |

## Storage

Reads/writes `memory.jsonl` directly (same file as memory MCP server).
Path auto-detected from npx cache or `MEMORY_FILE_PATH` env var.
Changes are visible to the memory MCP on next query (live file sharing).

## Session-clearing safety

Because learnings are persisted in `memory.jsonl` (not context), an agent
can have its conversation context fully cleared and still recall all its
accumulated learnings on the next invocation by calling `recall()` at task start.

This enables the **session-clearing pattern** for long-running projects:
1. Specialist completes task → writes learnings → hands back to orchestrator
2. Orchestrator clears specialist's context (new session)
3. On next invocation, specialist calls `recall()` → full history restored
