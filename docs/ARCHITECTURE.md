# Agent System Architecture

> **Status:** `feat/specialist-subagents` — PR #4 open  
> **Last updated:** 2026-06-25  
> **Decisions captured from sessions:** 2026-06-24 / 2026-06-25

---

## Overview

The OpenCode agent system is a **layered routing architecture** with a stateless
fast-path orchestrator, a reasoning-capable routing oracle (secretary), nine
specialist subagents, and a mechanical executor (worker — planned). Future phases
extend the secretary into a full project coordinator backed by `opencode.db`.

```
User request
     │
     ▼
request-orchestrator  (claude-haiku-4-5 — routing only, P0–P4)
     │
     ├── P0:   Prompt / slash command match → suggest to user
     ├── P0.5: Routing cache hit (≥0.82) → load skill directly
     ├── P1:   Trivial → answer inline
     ├── P2:   Specialist match → delegate
     │           └── P2.5: Ambiguous → secretary resolves first
     ├── P3:   Installed skill → load + execute
     ├── P3.5: GAIA app match → auto-call or suggest
     └── P4:   TTT discovery
```

---

## Agent Roster

| Agent | Model | Role | Mode |
|---|---|---|---|
| `request-orchestrator` | `claude-haiku-4-5` | Default router — P0–P4 routing, P2.5 secretary delegation | `primary` |
| `secretary` | `claude-sonnet-4-6` | Routing oracle + project coordinator (Phase 2+) | `subagent` |
| `programming-expert` | `gpt-5.1` | Full-stack dev: Angular, React, Python, embedded C/C++, BMW LLM API agents | `subagent` |
| `design-expert` | `claude-sonnet-4-6` | BMW Density system, Figma, UX/accessibility, WCAG 2.1 AA | `subagent` |
| `project-manager` | `o4-mini` | Jira, Confluence, sprint health, PI planning, DoR, release notes | `subagent` |
| `oracle-apex-expert` | `gpt-5.1` | Oracle APEX development, PL/SQL, live docs.oracle.com fetch | `subagent` |
| `jirri-data-analyst` | `o3-mini` | JIRRI RPA cost-savings auditor, Python/stdlib script expert | `subagent` |
| `opencode-dev-expert` | `gpt-5.2` | OpenCode upgrades, wrapper, skill/plugin lifecycle, MCP, config repo | `subagent` |
| `uipath-rpa-expert` | `claude-sonnet-4-6` | UiPath Dispatcher/Worker documentation, XAML analyser | `subagent` |
| `worker` *(planned)* | `claude-haiku-4-5` | Mechanical executor — only agent with unrestricted bash/edit/write | `subagent` |

### Model selection rationale

| Model | Why assigned |
|---|---|
| `claude-haiku-4-5` | Orchestrator: routing only, 3× cost saving vs Sonnet. Worker: cheap mechanical tool calls |
| `claude-sonnet-4-6` | Secretary: infrequent but needs nuanced multi-signal reasoning. Design + UiPath: subjective domain |
| `gpt-5.1` | Programming + APEX: strong code generation, 272K context |
| `gpt-5.2` | OpenCode-dev: 922K context for large config repo diffs |
| `o4-mini` | Project manager: structured reasoning over Jira/sprint data |
| `o3-mini` | JIRRI analyst: heavy Python/math reasoning, cost-sensitive |

---

## The Secretary

### Current role (Phase 1 — live)

Stateless routing oracle. Fires **only** when the orchestrator cannot resolve a
request to a single specialist — keywords match 2+ domains, or P1 vs P2 is unclear.

**Output contract (strict 4-line format):**
```
ROUTE TO: <agent-name | none>
REASON: <one sentence>
CONFIDENCE: <high | medium | low>
CLARIFYING QUESTION: <one question | none>
```

**Constraints:**
- No tools, no skills, no `task` calls — pure reasoning
- Never executes work — only recommends routing
- `ROUTE TO: none` = orchestrator handles as P1 or falls to P3

### Future role (Phase 2+ — planned)

Stateful **project coordinator** backed by `opencode.db`. See `PROJECTS-DB.md` for
the full design. New responsibilities:

| Capability | Description |
|---|---|
| Blackboard lifecycle manager | Creates, tracks status, archives blackboards |
| Cross-task memory | Enforces prior decisions across sessions ("we chose signals not NgRx in task-003") |
| Conflict resolver | Consults decisions table when specialists disagree on a blackboard |
| Progress reporter | Answers "where are we?" on any active project |
| Dependency gatekeeper | Blocks execution until prerequisites complete |
| Session continuity | Picks up from last session without re-explaining context |

**New tool grant (Phase 2):** `bash` restricted to `sqlite3` + read blackboard files.
No code file writes — those stay with the worker agent only.

---

## The Routing Enforcer Plugin

**File:** `~/.config/opencode/plugins/routing-enforcer.ts`

**Problem it solves:** `claude-haiku-4-5` can drop routing rules mid-session as
context grows, causing direct responses instead of delegation.

**How it works:**
- Hook: `experimental.chat.system.transform`
- Fires: every LLM turn in any session
- Detection: identifies orchestrator by model ID `claude-haiku-4-5`
- Action: injects a compact routing enforcement block into the system prompt
- Also hooks `tool.execute.before` on `task` to append a JSONL entry to
  `~/.local/share/opencode/delegation.jsonl` for audit trail

**Detection approach:** Uses `input.model` ID matching (not `input.agent` which is
unconfirmed in the v1.17.5 binary). Handles `string | {id} | {modelID} | {name}`
shapes defensively.

---

## Blackboard Architecture (Phase 1 — planned)

A **shared working file** pattern for multi-agent coordination. Named after the
classical Blackboard Architecture from 1970s AI research.

### When it activates

| Condition | Blackboard? |
|---|---|
| 2+ specialist domains involved | Yes |
| High-stakes / multi-file change | Yes |
| User requests dry-run / plan-first | Yes |
| Simple, single-specialist, clear domain | No — fast path only |

### Blackboard file structure

```markdown
# Task: <description>
**ID:** task-YYYYMMDD-NNN
**Status:** deliberating | awaiting-approval | executing | done | blocked
**Requested:** <ISO timestamp>

## Context
(written by orchestrator — repo, files, error, branch)

## Programming Analysis
(written by programming-expert — root cause, confidence, files to change)

## Design Constraints
(written by design-expert — or "None" if not applicable)

## Proposed Changes
(MUST be exact unified diffs or complete code blocks — prose rejected)

## Execution Plan
(written by orchestrator after reviewing all sections)

## Execution Result
(written by worker after execution — pass/fail, test output)
```

**Hard rule:** Specialists MUST produce machine-executable artifacts in
`## Proposed Changes` — exact diffs, not summaries. Prose causes worker
hallucination and is a protocol violation.

### Flow

```
orchestrator creates blackboard (/tmp/opencode/task-{id}.md)
    │
    ├──► programming-expert reads + writes ## Programming Analysis + ## Proposed Changes
    ├──► design-expert reads + writes ## Design Constraints
    │    (parallel where possible)
    │
orchestrator reads completed blackboard
    │  resolves conflicts via secretary if present
    │  writes ## Execution Plan
    │  sets Status: awaiting-approval (if approval gate enabled)
    │
user approves (or auto-proceeds for low-risk)
    │
worker reads ## Execution Plan → executes → writes ## Execution Result
    │
secretary records to opencode.db (Phase 2)
```

### Worker agent

- **Only agent** with unrestricted `bash` + `edit` + `write`
- Reads `## Execution Plan` — executes mechanically, zero domain reasoning
- Writes pass/fail + test output to `## Execution Result`
- Model: `claude-haiku-4-5` — optimised for tool calls, not reasoning
- Does **not** second-guess the plan — if the plan is wrong, that's the specialist's fault

---

## Build Phases

| Phase | Deliverables | Status |
|---|---|---|
| **0 — Foundation** | `request-orchestrator.md`, agent template, Rules 1–9 | Done |
| **1a — Specialists** | `programming-expert`, `design-expert`, `project-manager` | Done |
| **1b — Secretary** | `secretary.md`, P2.5 tier in orchestrator | Done |
| **1c — Model optimisation** | All 9 agents on optimal models, routing-enforcer plugin | Done |
| **2 — Blackboard** | `blackboard.py` skill + `worker.md` agent | Planned |
| **3 — Projects DB** | `opencode.db` schema extension, secretary gets sqlite3 | Planned |
| **4 — Full coordination** | Secretary as project coordinator, approval gate, conflict resolution | Planned |
| **5 — Galaxy integration** | Projects visible in memory galaxy force graph | Planned |

---

## Key Constraints (Never Violate)

1. `mode: primary` for `request-orchestrator` only — all others `mode: subagent`
2. All models must be `llm-api/*` or `ollama/*` — never provider-direct
3. Secretary never calls `task` — it reasons and returns, orchestrator delegates
4. Worker is the only agent with unrestricted file write tools
5. Specialists write exact diffs to blackboard, not prose
6. Secretary is the only agent with `sqlite3` access to `opencode.db` project tables
