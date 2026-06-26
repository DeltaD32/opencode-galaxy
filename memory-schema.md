# Memory Schema — OpenCode Knowledge Graph Conventions

This document defines naming rules and entity type conventions for `memory.jsonl`.
Following this schema prevents the manual cleanup problem: without it, entities
accumulate with inconsistent names, duplicate coverage, and no relations.

## The Two Memory Layers

| Layer | File | Who writes | What it stores |
|---|---|---|---|
| **agent_memory** | `memory.jsonl` (entity type `AgentLearnings`) | All agents via `scribe()` | WORKED/AVOID/PATTERN tagged strings per agent, decay-scored |
| **knowledge graph** | `memory.jsonl` (all other entity types) | `scribe()` + orchestrator MCP tools | Typed entities + relations — facts, decisions, design systems, project state |

Both layers share the same `memory.jsonl` file. The memory MCP server serves
the knowledge graph; `agent_memory.py` reads/writes the `AgentLearnings` entities directly.

---

## Entity Naming Rules

### Rule 1 — Agent learnings (AUTO — never create manually)
```
<agent-name>::learnings
```
Examples: `programming-expert::learnings`, `worker::learnings`
Created automatically by `agent_memory.learn()`. Do NOT create these via MCP tools.

### Rule 2 — JARVIS project entities
```
JARVIS <Component> — <Aspect>
```
Examples:
- `JARVIS Galaxy Design System — Color Tokens`
- `JARVIS Galaxy Design System — Themes`
- `JARVIS Phase J3`
- `JARVIS Known Gotchas`
- `JARVIS Current Branch State`

### Rule 3 — Project groups
```
<ProjectName> Project
```
Examples: `apex-fixer Project`, `JIRRI Project`, `PPT Style Registry Project`
Child entities are linked via `[contains]` relations.

### Rule 4 — Reusable technique collections
```
<Technology> Patterns
```
Examples: `Angular Signals Patterns`, `BMW LLM API Patterns`, `Three.js Galaxy Patterns`

### Rule 5 — Architecture decisions
Use the decision topic as the name, no prefix required.
Examples: `Blackboard Architecture Decision`, `Worker Agent Design Decision`
Type: `ArchitectureDecision`

### Rule 6 — Session notes (rarely needed — prefer agent_memory for ephemeral notes)
```
<AgentName> Session Notes
```
Only for high-value cross-session context that benefits from graph relations.

---

## Entity Types

| Type | When to use |
|---|---|
| `AgentLearnings` | Auto-created by agent_memory — do not use manually |
| `ArchitectureDecision` | A decision that was made and its rationale |
| `DesignSystem` | Colors, tokens, themes, scene configs, interaction patterns |
| `TechnicalFact` | Bug fixes, gotchas, environment facts, version constraints |
| `ImplementationPhase` | A completed development phase (JARVIS J1/J2/J3 etc.) |
| `Project` | A standalone project (apex-fixer, JIRRI, etc.) |
| `ProjectState` | Current live state snapshot of a project |
| `Component` | A specific UI or system component |
| `Feature` | A planned or in-progress feature |
| `Artifact` | A produced file, document, or report |
| `KnowledgeBase` | A curated catalog of information (Confluence spaces, etc.) |
| `Review` | A formal review session (Opus review, code review, etc.) |
| `SessionNote` | Free-form session summary (use sparingly) |

---

## Observation Conventions

### agent_memory observations (tagged strings)
```
[WORKED]  <domain> | <what worked>   | YYYY-MM-DD
[AVOID]   <domain> | <what to avoid> | YYYY-MM-DD
[PATTERN] <domain> | <technique>     | YYYY-MM-DD
```

### Knowledge graph observations (free-form but consistent)
Use a prefix tag for structured observations written by `scribe()`:

```
[DECISION] <decision> | Rationale: <why> | YYYY-MM-DD
[BUG FIX]  <bug> → <fix> | YYYY-MM-DD
[BUILT]    <what was built> | YYYY-MM-DD
[SESSION]  <agent> | <summary> | YYYY-MM-DD
```

Plain observations (no prefix) are fine for factual notes:
```
Branch: feat/web-frontend
Stack: React 18 + TypeScript + Vite 5 + Three.js
```

---

## Relation Types

Use active voice, lowercase-hyphen:

| Relation | Meaning |
|---|---|
| `contains` | Parent → child (project → feature) |
| `implements` | Component implements a design spec |
| `uses-design-system` | Project → design token entity |
| `extends` | Builds on another entity |
| `fixes` | Bug fix → gotcha entity |
| `resolved-by` | Problem → solution entity |
| `produced` | Process → artifact |
| `uses` | Entity depends on another |
| `builds-on` | Extends/layers on top of |
| `integrates` | Connects two systems |
| `has-reference` | Points to a reference document/file |
| `informed` | One decision influenced another |
| `proposes-extension-of` | Future idea for an existing system |

---

## Quarterly Prune Process

Run this at the start of a new quarter to surface stale entities for review:

```python
import sys, pathlib
sys.path.insert(0, str(pathlib.Path.home() / ".opencode/skills/scribe"))
from scribe import prune_report

stale = prune_report(stale_days=180)
print(f"{len(stale)} entities flagged for review:")
for e in stale:
    print(f"  [{e['entityType']}] {e['name']} — {e['obs_count']} obs, newest: {e['newest_date']} ({e['reason']})")
```

**prune_report() flags entities that are:**
- Orphaned (no relations) AND
- Have no dated observations, or all observations are older than `stale_days`

**It never deletes anything** — it returns a list for human review.
Delete via `memory_delete_entities` MCP tool only after confirming the entity is truly obsolete.

---

## Anti-patterns (what caused the last cleanup)

| Anti-pattern | Rule to follow instead |
|---|---|
| Three entities for the same project (JARVIS Frontend Project, JARVIS Project, JARVIS Web Frontend) | One canonical entity per project — update in place |
| "Status: NOT STARTED" and "Status: COMPLETE" in the same entity | Delete the stale status obs when the new one is added |
| Orphaned entities with no relations | Every new entity gets at least one relation on creation |
| Creating entities manually without dated observations | Always include at least one `YYYY-MM-DD` observation |
| Skipping `scribe()` at task-end | `scribe()` is mandatory — same weight as worker gate check |
