# Projects DB — opencode.db Extension Design

> **Status:** Phases 3–4.6 complete  
> **Last updated:** 2026-06-25  
> **Depends on:** Blackboard Architecture (Phase 2), see `ARCHITECTURE.md`

---

## Decision Summary

Extend `opencode.db` with new project-tracking tables rather than creating a
separate database or mirroring to the memory MCP.

**Rejected alternatives:**

| Option | Why rejected |
|---|---|
| Mirror to memory MCP | Two sources of truth; sync drift risk; memory MCP schema is flat (entities + relations only, no rich fields) |
| Separate `projects.db` + local REST API | Extra process to manage; separate file; operational overhead; galaxy needs a merge layer |
| **opencode.db extension (chosen)** | Single source of truth; no sync; galaxy already has access to this file; secretary and galaxy both in same process context |

---

## Database Location

```
~/.local/share/opencode/opencode.db
```

The existing file used by OpenCode for sessions, messages, and routing cache pairs.
New tables are additive — existing tables are untouched.

---

## Schema

```sql
-- A named project grouping related blackboard tasks
CREATE TABLE IF NOT EXISTS projects (
    id          TEXT PRIMARY KEY,          -- task-YYYYMMDD-NNN style or UUID
    name        TEXT NOT NULL,
    description TEXT,
    status      TEXT NOT NULL DEFAULT 'active',  -- active | paused | complete | archived
    created_at  TEXT NOT NULL,             -- ISO 8601
    updated_at  TEXT NOT NULL,
    -- Phase 4.6 additions (applied via _apply_phase46_migrations):
    distillation_ready  INTEGER DEFAULT 0, -- 1 = project complete, pending user-prompted distillation
    distilled_at        TEXT               -- ISO 8601 timestamp when distil_project() ran
);

-- A single task blackboard within a project
CREATE TABLE IF NOT EXISTS blackboards (
    id               TEXT PRIMARY KEY,
    project_id       TEXT REFERENCES projects(id),
    task_description TEXT NOT NULL,
    status           TEXT NOT NULL DEFAULT 'deliberating',
    -- deliberating | awaiting-approval | executing | done | blocked
    file_path        TEXT NOT NULL,         -- /tmp/opencode/task-{id}.md
    created_at       TEXT NOT NULL,
    updated_at       TEXT NOT NULL,
    -- Phase 4 additions (applied via _apply_phase4_migrations):
    depends_on       TEXT,                  -- JSON array of blackboard IDs that must be 'done' first
    approval_required INTEGER DEFAULT 0,   -- 1 = requires explicit user approval before worker runs
    approved_by      TEXT,                  -- 'user' | 'auto' | NULL (not yet approved)
    approved_at      TEXT                   -- ISO 8601 timestamp of approval
);

-- Individual specialist contributions to a blackboard
CREATE TABLE IF NOT EXISTS sections (
    id              TEXT PRIMARY KEY,
    blackboard_id   TEXT NOT NULL REFERENCES blackboards(id),
    agent           TEXT NOT NULL,         -- programming-expert, design-expert, etc.
    section_name    TEXT NOT NULL,         -- Programming Analysis, Design Constraints, etc.
    content         TEXT NOT NULL,         -- full markdown content of the section
    written_at      TEXT NOT NULL,
    -- Phase 4.6 addition (applied via _apply_phase46_migrations):
    compressed      INTEGER DEFAULT 0      -- 1 = soft-deleted after blackboard done (raw analysis compressed)
);

-- Decisions made during or as a result of a blackboard task
CREATE TABLE IF NOT EXISTS decisions (
    id              TEXT PRIMARY KEY,
    blackboard_id   TEXT NOT NULL REFERENCES blackboards(id),
    made_by         TEXT NOT NULL,         -- agent name or "user"
    decision        TEXT NOT NULL,         -- short label: "use signals not NgRx"
    rationale       TEXT,                  -- why this was chosen
    timestamp       TEXT NOT NULL,
    -- cross-task influence: which future blackboard_ids this decision affected
    influenced      TEXT                   -- JSON array of blackboard_ids
);

-- Conflicts between specialist recommendations on a blackboard
CREATE TABLE IF NOT EXISTS conflicts (
    id              TEXT PRIMARY KEY,
    blackboard_id   TEXT NOT NULL REFERENCES blackboards(id),
    agent_a         TEXT NOT NULL,
    agent_b         TEXT NOT NULL,
    description     TEXT NOT NULL,         -- what they disagreed on
    resolved        INTEGER NOT NULL DEFAULT 0,  -- 0=open, 1=resolved
    resolution      TEXT,                  -- how it was resolved
    resolved_by     TEXT,                  -- "secretary" or "user"
    resolved_at     TEXT
);

-- Sequential handoff queue (one row per specialist per blackboard)
-- Added Phase 3: task tool cannot spawn agents in parallel, so fan-out is sequential.
-- The queue table is the single source of truth for which specialist is active.
CREATE TABLE IF NOT EXISTS specialist_queue (
    id            TEXT PRIMARY KEY,
    blackboard_id TEXT NOT NULL REFERENCES blackboards(id),
    agent         TEXT NOT NULL,
    status        TEXT NOT NULL DEFAULT 'pending',
    -- pending | active | done | skipped
    queued_at     TEXT NOT NULL,
    started_at    TEXT,
    completed_at  TEXT
);

-- Indexes for common access patterns
CREATE INDEX IF NOT EXISTS idx_blackboards_project   ON blackboards(project_id);
CREATE INDEX IF NOT EXISTS idx_blackboards_status    ON blackboards(status);
CREATE INDEX IF NOT EXISTS idx_sections_blackboard   ON sections(blackboard_id);
CREATE INDEX IF NOT EXISTS idx_decisions_blackboard  ON decisions(blackboard_id);
CREATE INDEX IF NOT EXISTS idx_conflicts_blackboard  ON conflicts(blackboard_id);
CREATE INDEX IF NOT EXISTS idx_conflicts_resolved    ON conflicts(resolved);
CREATE INDEX IF NOT EXISTS idx_queue_blackboard      ON specialist_queue(blackboard_id);
CREATE INDEX IF NOT EXISTS idx_queue_status          ON specialist_queue(status);
```

---

## Access Pattern

### Secretary (write + read)

The secretary is the **only agent** that writes to these tables. It uses `sqlite3`
via the clipjoint venv `bash` tool — restricted to DB operations and blackboard
file reads only.

```bash
# Secretary pattern — create a blackboard record
~/.opencode/plugins/clipjoint/.venv/bin/python3 - << 'EOF'
import sqlite3, json, uuid
from datetime import datetime, timezone

db = sqlite3.connect("/Users/QTE2362/.local/share/opencode/opencode.db")
now = datetime.now(timezone.utc).isoformat()
db.execute("""
    INSERT INTO blackboards (id, project_id, task_description, status, file_path, created_at, updated_at)
    VALUES (?, ?, ?, 'deliberating', ?, ?, ?)
""", [str(uuid.uuid4()), project_id, task_description, file_path, now, now])
db.commit()
db.close()
EOF
```

### Galaxy / Web Frontend (read only)

**Confirmed (2026-06-25):** The galaxy is a **separate Vite dev server process**
(`localhost:3000`) — not an embedded webview. It communicates with the OpenCode
TUI (`localhost:4096`) via HTTP REST and SSE. It has no direct browser access to
the filesystem.

**The access pattern is the Vite `bypass()` proxy** — already used for `/__memory`
(reads `memory.jsonl`) and `/__agents` (reads agent `.md` files). The same pattern
is extended to `/__db` for `opencode.db`. `better-sqlite3` runs in the **Vite/Node
process** (has filesystem access), not in the browser.

```typescript
// vite.config.ts — add /__db alongside existing /__memory and /__agents
import Database from "better-sqlite3";

"/__db": {
  target: "http://localhost:3000",
  bypass(_req, res) {
    const db = new Database(
      "/Users/QTE2362/.local/share/opencode/opencode.db",
      { readonly: true }
    );
    try {
      const projects  = db.prepare("SELECT * FROM projects WHERE status = 'active'").all();
      const boards    = db.prepare("SELECT * FROM blackboards").all();
      const decisions = db.prepare("SELECT * FROM decisions").all();
      const conflicts = db.prepare("SELECT * FROM conflicts").all();
      res.setHeader("Content-Type", "application/json");
      res.end(JSON.stringify({ projects, boards, decisions, conflicts }));
    } finally {
      db.close();
    }
    return false;
  },
},
```

```typescript
// web/src/lib/db-reader.ts — browser-side fetch (same pattern as fetchMemoryGraph)
export async function fetchProjectsGraph(): Promise<ProjectsGraphData> {
  const resp = await fetch("/__db");
  const data = await resp.json();
  return toForceGraphNodes(data);
}
```

**No Express/FastAPI bridge needed.** The existing Vite bypass hook is the bridge.

**Tauri Phase 4 note:** When the Vite dev server is replaced by Tauri (already in
the `feat/web-frontend` roadmap), `better-sqlite3` is swapped for `tauri-plugin-sql`.
The browser-side `fetch("/__db")` calls become `invoke("db_query", {...})` Tauri
commands. Pattern is identical; only the runtime changes.

---

## Data Flow

```
User: "Let's continue work on the login overhaul"
          │
          ▼
secretary queries projects table
  → finds project: "login-overhaul", status: active, 3 blackboards
  → finds blackboard task-003: done, blackboard task-004: blocked
  → loads decisions from task-003 (architectural choices still in force)
  → reports status to orchestrator
          │
          ▼
orchestrator: "Task-004 is blocked on design sign-off — route to design-expert"
          │
          ▼
design-expert reads blackboard file task-004.md
  → writes ## Design Constraints section
  → secretary updates blackboard status: deliberating → awaiting-approval
          │
          ▼
user approves → worker executes → secretary records result
  → blackboard status: done
  → project progress: 4/5 tasks complete
```

---

## Galaxy Visual Representation

Projects in `opencode.db` appear in the memory galaxy as a distinct node cluster.
See `ARCHITECTURE.md` for the full visual encoding, but the key mappings are:

| DB concept | Galaxy node | Visual |
|---|---|---|
| `projects` row | Project node | Large BMW blue sphere with ring, high mass |
| `blackboards` row | Blackboard node | Medium octahedron, colour = status |
| `decisions` row | Decision node | Small purple diamond |
| `conflicts` row (unresolved) | Conflict node | Small orange/red spiky |
| Agent names in `sections` | Edge to agent node | Directed edge: agent → blackboard |
| `decisions.influenced` | Cross-task edge | Decision node → influenced blackboard |

**The cross-task decision edge is the most valuable visual feature.** When a
decision made in task-003 is still shaping task-008, you see a visible arc between
them — invisible in any list-based PM tool.

### Status colour encoding (blackboard nodes)

| Status | Colour | Animation |
|---|---|---|
| `deliberating` | Yellow | Slow pulse |
| `awaiting-approval` | Amber | Steady glow |
| `executing` | Bright white/blue | Fast pulse |
| `blocked` | Dim red | Slight red tint, no pulse |
| `done` | Faded green | Solid, no animation |

---

## Secretary Queries (Reference)

Common queries the secretary will run:

```sql
-- Find all active projects
SELECT id, name, status, created_at FROM projects WHERE status = 'active';

-- Get blackboard status summary for a project
SELECT b.id, b.task_description, b.status, b.updated_at
FROM blackboards b WHERE b.project_id = ? ORDER BY b.created_at;

-- Get all decisions for a project (for cross-task enforcement)
SELECT d.decision, d.rationale, d.made_by, b.task_description
FROM decisions d
JOIN blackboards b ON d.blackboard_id = b.id
WHERE b.project_id = ?
ORDER BY d.timestamp;

-- Find unresolved conflicts on active blackboards
SELECT c.*, b.task_description
FROM conflicts c
JOIN blackboards b ON c.blackboard_id = b.id
WHERE c.resolved = 0 AND b.status NOT IN ('done', 'archived');

-- Which decisions influenced a specific blackboard?
SELECT d.decision, d.rationale, d.made_by
FROM decisions d
WHERE json_extract(d.influenced, '$') LIKE '%' || ? || '%';
```

---

## Migration Strategy

Schema is applied on first secretary activation in Phase 3 via:

```python
# secretary runs this once on startup if tables don't exist
db.executescript(SCHEMA_SQL)
db.commit()
```

The `IF NOT EXISTS` guards make this idempotent — safe to run on every secretary
invocation. No destructive migrations in Phase 3 — tables are additive only.

---

## Phase Checklist

- [x] **Phase 2 prerequisite:** `blackboard.py` skill + `worker.md` agent created
- [x] **Phase 3 start:** Confirm galaxy access pattern — **separate Vite process, use `/__db` bypass proxy with `better-sqlite3` in Node. No Express bridge needed.**
- [x] **Phase 3 start:** Apply schema migration on `opencode.db`
- [x] **Phase 3:** Update `secretary.md` with DB access tools + project coordinator role
- [x] **Phase 3:** Update `request-orchestrator.md` to invoke secretary for project context
- [x] **Phase 4:** Add approval gate (`status: awaiting-approval`) to orchestrator flow — `request_approval()`, `is_gate_open()`, `get_approval_summary()` in `blackboard.py`; hard gate in `worker.md` Step 0
- [x] **Phase 4:** Add dependency tracking (`depends_on` column to `blackboards`) — `set_dependency()`, `check_dependencies()`, `get_next_ready_blackboard()` in `projects.py`
- [x] **Phase 4:** Add formal conflict resolution — secretary Mode 6; `record_conflict_resolution()` in `projects.py`; tiebreaker rules: prior-decision → simpler-wins → domain-authority → user-escalation
- [x] **Phase 4.5:** Add per-agent self-learning memory — `agent-memory` skill; `agent_memory.py` wraps `memory.jsonl`; `WORKED`/`AVOID`/`PATTERN` tags; session-clearing safe; all specialists + worker + secretary + orchestrator updated
- [x] **Phase 4.6:** Memory lifecycle — decay scoring (`0.5^(days/half_life)`; PATTERN half-life 2× WORKED/AVOID); `reinforce()` resets decay clock; `get_decay_stats()` for galaxy; `recall()` sorted by decay score; `compress_sections()` soft-deletes raw specialist sections on blackboard done (keeps Execution Plan + Result); `mark_distillation_ready()` auto-fires on `update_project_status("complete")`; `distil_project()` calls BMW LLM API (sonnet), writes PATTERN obs to agent-memory; `auto_archive_if_done()` moves done blackboard files to archive; all hooks wired into `update_blackboard_status("done")` and `update_project_status("complete")`; user-prompted distillation at session start
- [ ] **Phase 5:** Galaxy reads project tables + renders solar system node cluster
- [ ] **Phase 5:** Cross-task decision edges visible in force graph
- [ ] **Phase 5:** Agent-memory learnings visualised as node annotations in galaxy view
