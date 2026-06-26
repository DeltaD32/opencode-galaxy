---
name: projects
description: >
  Persistent project and blackboard coordination via opencode.db. Tracks projects,
  blackboard lifecycle, specialist handoff queues, decisions, and conflicts across
  sessions. Used by the secretary agent to maintain project state. Pairs with the
  blackboard skill for full multi-agent coordination.
tags: [coordination, projects, secretary, persistence, sqlite]
license: Proprietary
metadata:
  authors:
    - OpenCode Config
  version: "1.0.0"
---

# projects

Persistent coordination layer for multi-session, multi-agent projects. Stores
project records, blackboard lifecycle, sequential specialist handoff queues,
architectural decisions, and inter-agent conflicts in `opencode.db`. The secretary
agent is the **only** agent that writes to these tables.

## Python path

```python
import sys, pathlib
sys.path.insert(0, str(pathlib.Path.home() / ".opencode/skills/projects"))
from projects import (
    create_project, get_project, list_projects, update_project_status,
    register_blackboard, update_blackboard_status, sync_blackboard_sections,
    record_decision, record_conflict, resolve_conflict,
    get_project_status, enqueue_specialists, advance_queue, get_queue_status,
    get_prior_decisions, find_project_for_task,
)
```

Use the clipjoint venv: `~/.opencode/plugins/clipjoint/.venv/bin/python3`

## Database location

`~/.local/share/opencode/opencode.db` — additive tables; existing OpenCode tables untouched.

Schema is applied automatically on first import (idempotent `IF NOT EXISTS` guards).

## Function reference

### Project management

| Function | Returns | Description |
|---|---|---|
| `create_project(name, description="")` | `str` | Create a new project. Returns project id (UUID4). |
| `get_project(project_id)` | `dict \| None` | Get project by id. Returns dict or None if not found. |
| `list_projects(status="active")` | `list[dict]` | List projects by status: active \| paused \| complete \| archived. |
| `update_project_status(project_id, status)` | `None` | Update project status. |

### Blackboard registration

| Function | Returns | Description |
|---|---|---|
| `register_blackboard(blackboard_path, project_id, task_description)` | `str` | Register a blackboard file. Returns blackboard DB id. |
| `update_blackboard_status(blackboard_id, status)` | `None` | Sync blackboard status to DB. Valid values: see Status Values below. |
| `sync_blackboard_sections(blackboard_path, blackboard_id)` | `int` | Parse blackboard file, upsert all sections to DB. Returns count synced. |

### Decisions

| Function | Returns | Description |
|---|---|---|
| `record_decision(blackboard_id, made_by, decision, rationale="", influenced=None)` | `str` | Record an architectural decision. Returns decision id. |
| `get_prior_decisions(project_id)` | `list[dict]` | All decisions for a project ordered by timestamp. Used for cross-task enforcement. |

### Conflicts

| Function | Returns | Description |
|---|---|---|
| `record_conflict(blackboard_id, agent_a, agent_b, description)` | `str` | Record a conflict between two specialists. Returns conflict id. |
| `resolve_conflict(conflict_id, resolution, resolved_by)` | `None` | Mark conflict resolved. `resolved_by`: 'secretary' or 'user'. |

### Specialist handoff queue

| Function | Returns | Description |
|---|---|---|
| `enqueue_specialists(blackboard_id, agents)` | `None` | Add specialists to the sequential handoff queue. Call after `register_blackboard`. |
| `advance_queue(blackboard_id)` | `dict \| None` | Mark current active specialist done, activate next pending. Returns next agent dict or None when queue is complete. |
| `get_queue_status(blackboard_id)` | `list[dict]` | Full queue for a blackboard: `[{agent, status, queued_at, started_at, completed_at}]`. |

### Aggregated status

| Function | Returns | Description |
|---|---|---|
| `get_project_status(project_id)` | `dict` | Full status: project + blackboards + open_conflicts + decisions + queue. |
| `find_project_for_task(task_description)` | `dict \| None` | Fuzzy-match task description against active project names/descriptions. Returns best match or None. |

## Status values

### Project status

| Status | Meaning |
|---|---|
| `active` | Project is underway (default) |
| `paused` | Temporarily on hold |
| `complete` | All tasks done |
| `archived` | Closed; kept for history |

### Blackboard status (mirrors blackboard.py)

| Status | Meaning |
|---|---|
| `deliberating` | Specialists writing their sections (default) |
| `awaiting-approval` | Execution Plan written; waiting for user sign-off |
| `executing` | Worker applying the plan |
| `done` | Worker completed successfully |
| `blocked` | A step failed; specialist must revise plan |

### Specialist queue status

| Status | Meaning |
|---|---|
| `pending` | Queued, waiting for turn |
| `active` | Currently being worked on |
| `done` | Section written, handed off |
| `skipped` | Bypassed (e.g. design not applicable) |

## Coordination flow (secretary pattern)

<!-- skill-lint: ignore -->
```python
# 1. Check for existing project context before creating a blackboard
match = find_project_for_task("Fix login button on iOS")
project_id = match["id"] if match else None

# 2. Create and register the blackboard
import sys, pathlib
sys.path.insert(0, str(pathlib.Path.home() / ".opencode/skills/blackboard"))
from blackboard import create as bb_create

bb_path = bb_create("Fix login button on iOS", "Repo: oasis-fe-mono", project_id)
bid = register_blackboard(bb_path, project_id, "Fix login button on iOS")

# 3. Queue the specialists (sequential fan-out)
enqueue_specialists(bid, ["programming-expert", "design-expert"])

# 4. Start the queue (activate first specialist)
next_agent = advance_queue(bid)
# → {"agent": "programming-expert", "status": "active", ...}

# 5. After programming-expert writes their section:
next_agent = advance_queue(bid)
# → {"agent": "design-expert", "status": "active", ...}

# 6. After design-expert writes their section:
done = advance_queue(bid)  # → None (queue complete)

# 7. Record a decision made during review
did = record_decision(bid, "programming-expert", "use signals not NgRx",
                      "signals are simpler for local UI state")

# 8. Check prior decisions before next task in this project
decisions = get_prior_decisions(project_id)

# 9. Full progress report
status = get_project_status(project_id)
# → {project: {...}, blackboards: [...], open_conflicts: [], decisions: [...], queue: []}
```

## Secretary output modes reference

The secretary uses these functions to generate each output mode:

| Output mode | Functions used |
|---|---|
| Mode 2 — Project context lookup | `find_project_for_task()`, `get_project_status()` |
| Mode 3 — Blackboard registration | `register_blackboard()`, `enqueue_specialists()` |
| Mode 4 — Queue advance | `advance_queue()`, `get_queue_status()`, `update_blackboard_status()` |
| Mode 5 — Progress report | `get_project_status()`, `get_prior_decisions()` |

## Phase 3 note

This skill implements the Phase 3 schema from `~/.config/opencode/docs/PROJECTS-DB.md`.
The `specialist_queue` table is an addition to the original schema — it tracks sequential
fan-out state because the `task` tool cannot spawn custom agents in parallel.
