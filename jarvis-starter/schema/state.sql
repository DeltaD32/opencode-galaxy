-- JARVIS state plane (working memory / blackboard) — applied idempotently.
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS projects (
  id          TEXT PRIMARY KEY,
  name        TEXT NOT NULL,
  status      TEXT NOT NULL DEFAULT 'active',   -- active | paused | complete | archived
  created_at  TEXT NOT NULL,
  updated_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS blackboards (
  id               TEXT PRIMARY KEY,
  project_id       TEXT NOT NULL REFERENCES projects(id),
  task_description TEXT NOT NULL,
  status           TEXT NOT NULL DEFAULT 'deliberating', -- deliberating|awaiting-approval|executing|done|blocked
  approval_required INTEGER NOT NULL DEFAULT 0,
  created_at       TEXT NOT NULL,
  updated_at       TEXT NOT NULL
);

-- The task DAG. One row per specialist assignment.
CREATE TABLE IF NOT EXISTS tasks (
  id               TEXT PRIMARY KEY,
  blackboard_id    TEXT NOT NULL REFERENCES blackboards(id),
  agent            TEXT NOT NULL,
  handoff_id       TEXT,
  status           TEXT NOT NULL DEFAULT 'pending', -- pending|ready|active|done|skipped|failed|blocked|retrying
  depends_on       TEXT NOT NULL DEFAULT '[]',      -- JSON array of task ids
  file_scope       TEXT NOT NULL DEFAULT '[]',      -- JSON array of paths this task may touch
  runtime          TEXT NOT NULL DEFAULT 'api',     -- api | opencode | ...
  model            TEXT,
  lease_owner      TEXT,
  lease_expires_at TEXT,
  attempts         INTEGER NOT NULL DEFAULT 0,
  max_attempts     INTEGER NOT NULL DEFAULT 3,
  last_error       TEXT,
  result           TEXT,
  queued_at        TEXT NOT NULL,
  started_at       TEXT,
  completed_at     TEXT
);
CREATE INDEX IF NOT EXISTS idx_tasks_bb     ON tasks(blackboard_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);

CREATE TABLE IF NOT EXISTS sections (
  id            TEXT PRIMARY KEY,
  blackboard_id TEXT NOT NULL REFERENCES blackboards(id),
  task_id       TEXT REFERENCES tasks(id),
  agent         TEXT NOT NULL,
  section_name  TEXT NOT NULL,
  content       TEXT NOT NULL,
  handoff_id    TEXT,
  written_at    TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_sections_bb ON sections(blackboard_id);

CREATE TABLE IF NOT EXISTS decisions (
  id            TEXT PRIMARY KEY,
  blackboard_id TEXT NOT NULL REFERENCES blackboards(id),
  made_by       TEXT,
  decision      TEXT NOT NULL,
  rationale     TEXT,
  timestamp     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS conflicts (
  id            TEXT PRIMARY KEY,
  blackboard_id TEXT NOT NULL REFERENCES blackboards(id),
  agent_a       TEXT,
  agent_b       TEXT,
  description   TEXT,
  resolved      INTEGER NOT NULL DEFAULT 0,
  resolution    TEXT
);

-- Append-only audit log — powers the galaxy timeline scrubber.
CREATE TABLE IF NOT EXISTS status_events (
  id            TEXT PRIMARY KEY,
  blackboard_id TEXT NOT NULL,
  task_id       TEXT,
  handoff_id    TEXT,
  agent         TEXT,
  from_status   TEXT,
  to_status     TEXT NOT NULL,
  event_at      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_status_events_at ON status_events(event_at);

-- Concurrency safety: a path may be leased by at most one active task.
CREATE TABLE IF NOT EXISTS file_leases (
  path          TEXT PRIMARY KEY,
  task_id       TEXT NOT NULL,
  blackboard_id TEXT NOT NULL,
  acquired_at   TEXT NOT NULL,
  expires_at    TEXT NOT NULL
);
