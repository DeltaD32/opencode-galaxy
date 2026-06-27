-- JARVIS semantic memory (durable knowledge). Vectors live in entity_vectors,
-- created at runtime with the embedding engine's dim (needs sqlite-vec loaded).
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT);

CREATE TABLE IF NOT EXISTS entities (
  id            TEXT PRIMARY KEY,
  name          TEXT NOT NULL UNIQUE,
  entity_type   TEXT NOT NULL,
  project       TEXT,                              -- canonical project key; NULL = global
  tier          TEXT NOT NULL DEFAULT 'warm',      -- hot | warm | cold
  decay_score   REAL NOT NULL DEFAULT 1.0,
  half_life_days REAL NOT NULL DEFAULT 30,
  local_only    INTEGER NOT NULL DEFAULT 0,        -- 1 = never replicate to cloud
  blackboard_id TEXT,
  created_at    TEXT NOT NULL,
  updated_at    TEXT NOT NULL,
  last_reinforced_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_entities_project ON entities(project);
CREATE INDEX IF NOT EXISTS idx_entities_type    ON entities(entity_type);

-- Canonical resolver: every known name/variant points to one entity.
CREATE TABLE IF NOT EXISTS entity_aliases (
  alias     TEXT PRIMARY KEY,                      -- normalized
  entity_id TEXT NOT NULL REFERENCES entities(id) ON DELETE CASCADE
);

-- One row per observation (tag/domain default '' so dedup/singleton work with the unique indexes).
CREATE TABLE IF NOT EXISTS observations (
  id            TEXT PRIMARY KEY,
  entity_id     TEXT NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
  tag           TEXT NOT NULL DEFAULT '',          -- WORKED | AVOID | PATTERN | DECISION | ''
  domain        TEXT NOT NULL DEFAULT '',
  body          TEXT NOT NULL,
  singleton_key TEXT,                              -- e.g. 'status' → replaces prior same-key obs
  observed_at   TEXT NOT NULL,
  decay_score   REAL NOT NULL DEFAULT 1.0
);
CREATE INDEX IF NOT EXISTS idx_obs_entity ON observations(entity_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_obs_singleton
  ON observations(entity_id, singleton_key) WHERE singleton_key IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS idx_obs_dedup
  ON observations(entity_id, tag, domain, body);

CREATE TABLE IF NOT EXISTS relations (
  id         TEXT PRIMARY KEY,
  from_id    TEXT NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
  to_id      TEXT NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
  rel_type   TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_rel_from ON relations(from_id);
CREATE INDEX IF NOT EXISTS idx_rel_to   ON relations(to_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_rel_unique ON relations(from_id, to_id, rel_type);
