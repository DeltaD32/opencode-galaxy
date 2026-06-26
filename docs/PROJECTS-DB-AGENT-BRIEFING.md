# Projects DB — Agent Briefing

> **Purpose:** Quick-reference answers to the three most commonly misunderstood
> facts about `opencode.db` for any agent working with the blackboard / projects
> coordination system. Read this before touching `projects.py`, `blackboard.py`,
> or any DB query involving these tables.
>
> **Full reference:** `docs/PROJECTS-DB.md`  
> **Source files:** `~/.opencode/skills/projects/projects.py`, `~/.opencode/skills/blackboard/blackboard.py`

---

## 1. `opencode.db` — Table Schema

Database location: `~/.local/share/opencode/opencode.db`

Six tables are owned by the coordination system. All are additive — OpenCode's
own tables are untouched. Phase 4 and 4.6 columns are added via idempotent
`ALTER TABLE ADD COLUMN` migrations that run on every `_connect()` call.

### `projects`

```
id                 TEXT  PK   UUID4
name               TEXT  NOT NULL
description        TEXT
status             TEXT  NOT NULL  DEFAULT 'active'
                         → 'active' | 'paused' | 'complete' | 'archived'
created_at         TEXT  NOT NULL  ISO 8601 UTC
updated_at         TEXT  NOT NULL  ISO 8601 UTC
distillation_ready INTEGER NOT NULL DEFAULT 0   ← Phase 4.6 (ALTER ADD)
                         1 = project complete, distillation not yet run
distilled_at       TEXT                          ← Phase 4.6 (ALTER ADD)
                         ISO 8601, set when distil_project() finishes
```

### `blackboards`

```
id                 TEXT  PK   UUID4
project_id         TEXT  FK → projects.id  (NULL = standalone task)
task_description   TEXT  NOT NULL
status             TEXT  NOT NULL  DEFAULT 'deliberating'
                         → 'deliberating' | 'awaiting-approval' | 'executing'
                            | 'done' | 'blocked'
file_path          TEXT  NOT NULL  e.g. /tmp/opencode/task-20260626-001.md
created_at         TEXT  NOT NULL  ISO 8601 UTC
updated_at         TEXT  NOT NULL  ISO 8601 UTC
depends_on         TEXT            ← Phase 4 (ALTER ADD)
                         JSON array of blackboard UUIDs, e.g. '["uuid-a"]'
                         NULL = no dependencies
approval_required  INTEGER NOT NULL DEFAULT 0  ← Phase 4 (ALTER ADD)
                         1 = worker blocked until approve_blackboard() called
approved_by        TEXT            ← Phase 4 (ALTER ADD)
                         'user' | 'auto' | NULL (not yet approved)
approved_at        TEXT            ← Phase 4 (ALTER ADD)
                         ISO 8601 timestamp of approval
```

### `sections`

```
id             TEXT  PK   UUID4
blackboard_id  TEXT  NOT NULL  FK → blackboards.id
agent          TEXT  NOT NULL  e.g. 'programming-expert', 'request-orchestrator'
section_name   TEXT  NOT NULL  e.g. 'Programming Analysis', 'Execution Plan'
content        TEXT  NOT NULL  markdown body (metadata lines already stripped)
written_at     TEXT  NOT NULL  ISO 8601
compressed     INTEGER NOT NULL DEFAULT 0  ← Phase 4.6 (ALTER ADD)
               0 = visible  |  1 = soft-deleted (content kept, hidden from normal queries)
```

### `decisions`

```
id             TEXT  PK   UUID4
blackboard_id  TEXT  NOT NULL  FK → blackboards.id
made_by        TEXT  NOT NULL  agent name or 'user'
decision       TEXT  NOT NULL  short label e.g. 'use signals not NgRx'
rationale      TEXT            why (optional)
timestamp      TEXT  NOT NULL  ISO 8601
influenced     TEXT            JSON array of future blackboard UUIDs, or NULL
```

### `conflicts`

```
id             TEXT  PK   UUID4
blackboard_id  TEXT  NOT NULL  FK → blackboards.id
agent_a        TEXT  NOT NULL
agent_b        TEXT  NOT NULL
description    TEXT  NOT NULL  what they disagreed on
resolved       INTEGER NOT NULL DEFAULT 0  0 = open  |  1 = resolved
resolution     TEXT            how it was resolved
               (may contain suffix: [enforced-decision:<uuid>])
resolved_by    TEXT            'secretary' | 'user'
resolved_at    TEXT            ISO 8601
```

### `specialist_queue`

```
id             TEXT  PK   UUID4
blackboard_id  TEXT  NOT NULL  FK → blackboards.id
agent          TEXT  NOT NULL
status         TEXT  NOT NULL  DEFAULT 'pending'
               → 'pending' | 'active' | 'done' | 'skipped'
queued_at      TEXT  NOT NULL  ISO 8601
started_at     TEXT            set when status → 'active'
completed_at   TEXT            set when status → 'done'
```

---

## 2. Exact Status Strings

All status values are enforced by `frozenset` constants. Passing anything else
raises `ValueError` immediately — no silent truncation or fallback.

### Blackboard status (`blackboards.status`)

Defined in **two places** (must match):
- `projects.py` → `BLACKBOARD_STATUSES`
- `blackboard.py` → `VALID_STATUSES`

| String | What it means |
|---|---|
| `'deliberating'` | Default. Specialists are writing sections. Work in progress. |
| `'awaiting-approval'` | Execution Plan is written. Waiting for explicit user confirmation before worker runs. |
| `'executing'` | User approved (or auto-approved). Worker is actively executing the plan. |
| `'done'` | Worker finished successfully. Triggers `compress_sections()` + `auto_archive_if_done()`. |
| `'blocked'` | Worker failed, or a dependency is unresolved. Human intervention needed. |

**Status transition map:**

```
deliberating  ──────────────────────────────► awaiting-approval
    │                (request_approval())            │
    │                                               │ (user approves)
    ├──────────────────────────────────────────────►─┤
    │          (low-risk auto-proceed)               │
    │                                           executing
    │                                               │
    │                                    ┌──────────┴──────────┐
    │                                  done               blocked
    │
    └──────────────────────────────────────────────► blocked
               (dependency unresolved)
```

**Key function behaviours:**

- **`request_approval(file_path, reason)`** — always sets status to `'awaiting-approval'`
  and appends an `## Approval Request` section. Never sets `'executing'` or `'blocked'`.

- **`mark_status(file_path, status)`** — updates the `**Status:**` line in the `.md` file.
  Must be called separately from `update_blackboard_status()` in `projects.py` to keep the
  DB record in sync with the file.

- **`is_gate_open(file_path)`** — returns `True` **only** when status is exactly
  `'executing'`. The worker calls this as a hard gate in Step 0. Any other status
  (including `'awaiting-approval'`) returns `False` and halts the worker.

### Project status (`projects.status`)

Defined in `projects.py` → `PROJECT_STATUSES`.

| String | What it means |
|---|---|
| `'active'` | Work is ongoing. Default. |
| `'paused'` | Temporarily on hold. |
| `'complete'` | All work done. **Automatically calls `mark_distillation_ready()`** — sets `distillation_ready=1` so the orchestrator prompts the user at next session start. |
| `'archived'` | Historical record. No further work expected. |

### Queue status (`specialist_queue.status`)

Defined in `projects.py` → `QUEUE_STATUSES`.

| String | What it means |
|---|---|
| `'pending'` | Queued but not yet active. |
| `'active'` | Currently the specialist being delegated to. `started_at` is set. |
| `'done'` | Specialist finished. `completed_at` is set. |
| `'skipped'` | Specialist bypassed (e.g. not needed for this task). |

---

## 3. Does `sections` Get One Row Per Specialist Turn?

**No. One row per section name.**

The `sections` table is a **current-state store**, not an append-only log.

### How `append_section()` works (from `blackboard.py`)

```python
# If section with this name already exists in the .md file → replace it
if pattern.search(existing):
    updated = pattern.sub(new_block.lstrip("\n"), existing)
# Otherwise → append it
else:
    updated = existing.rstrip("\n") + "\n" + new_block
```

### How `sync_blackboard_sections()` works (from `projects.py`)

```python
# Explicit upsert: DELETE the old row first, then INSERT the new one
conn.execute(
    "DELETE FROM sections WHERE blackboard_id = ? AND section_name = ?",
    (blackboard_id, section_name),
)
conn.execute(
    "INSERT INTO sections (id, blackboard_id, agent, section_name, content, written_at) ...",
)
```

There is no `ON CONFLICT` clause and no append. The result is always exactly one
row per `(blackboard_id, section_name)` pair.

### Consequence table

| Scenario | Rows in `sections` |
|---|---|
| `programming-expert` writes `## Programming Analysis` | 1 row |
| `programming-expert` re-writes `## Programming Analysis` | Still 1 row — fresh `written_at`, same `section_name` |
| `programming-expert` writes `## Analysis`, `design-expert` writes `## Design Constraints` | 2 rows — different names |
| Both agents write `## Proposed Changes` | 1 row — the later write wins; `agent` = second writer |
| `programming-expert` writes analysis, then `design-expert` writes a section with the *same* name | 1 row — `agent` column now shows `design-expert` |

### There is no edit history in the DB

If you need to audit who wrote what and when, read the `.md` file on disk.
`append_section()` always stamps a `**Written:** <ISO timestamp>` line in the
file body. The DB reflects only the latest version.

### Which sections survive Phase 4.6 compression?

When a blackboard reaches status `'done'`, `compress_sections()` is called
automatically. It sets `compressed=1` on all sections **except**:

```python
_KEEP_SECTIONS = frozenset({"Execution Plan", "Execution Result"})
```

Raw specialist analysis (e.g. `## Programming Analysis`, `## Proposed Changes`)
is soft-deleted — content is preserved in the DB but hidden from normal queries.

---

## Quick Reference: Function → Status Side Effects

| Function | Status it sets | Where |
|---|---|---|
| `blackboard.create()` | `'deliberating'` | `.md` file header |
| `request_approval(file, reason)` | `'awaiting-approval'` | `.md` file via `mark_status()` |
| `mark_status(file, 'executing')` | `'executing'` | `.md` file |
| `mark_status(file, 'done')` | `'done'` → also triggers compress + archive | `.md` file |
| `mark_status(file, 'blocked')` | `'blocked'` | `.md` file |
| `update_blackboard_status(bid, status)` | mirrors any valid status to DB | `opencode.db` |
| `update_project_status(pid, 'complete')` | `'complete'` → also calls `mark_distillation_ready()` | `opencode.db` |
| `approve_blackboard(bid, 'user'/'auto')` | sets `approved_by` + `approved_at` (no status change) | `opencode.db` |

> **Important:** `mark_status()` only updates the `.md` file.  
> `update_blackboard_status()` only updates the DB.  
> Both must be called to keep the two in sync — the orchestrator is responsible
> for calling both after any status transition.
