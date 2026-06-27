# Change Order 004 — Memory architecture: scalable, local-first, cloud-fallback

**Audience:** an implementing coding agent (programming-expert) or a human dev.
**Repo:** `opencode-galaxy`. Touches `skills/agent-memory/`, `skills/memory-semantic-search/`, a new `skills/memory-daemon/`, and `memory-schema.md`.
**Branch:** `feat/memory-v2`.
**Companions:** `CHANGE-ORDER-003` (per-project binding — folded in here), `CHANGE-ORDER-001` (blackboard / opencode.db), `JARVIS-ORCHESTRATION-MODEL.md`.
**Grounded in:** `skills/agent-memory/agent_memory.py` (memory.jsonl shape), `skills/memory-semantic-search/memory_semantic_search.py` (hnswlib + BMW embeddings), `memory-schema.md` (entity/relation/observation conventions), `skills/projects/projects.py` (opencode.db blackboard DDL).

Goal: keep **every** current capability, make memory **scale** (bounded hot/warm working set, unbounded cold history), and make it **local-first with an opt-in cloud fallback**. Placement becomes deterministic (project-derived), schema compliance becomes code-enforced, and the vector index can never drift out of sync with the data.

---

## The shape of the change (one paragraph)

Move semantic memory off `memory.jsonl` onto **SQLite + the `sqlite-vec` extension** (vectors live in the same DB as the entities → no index drift; row-level ACID writes → no full-file rewrite, no lock gap). Make embeddings **local by default** (bge-small / MiniLM via `fastembed`) with the **BMW LLM API as a swappable fallback**. Add a **three-tier model (hot / warm / cold)** where the existing **decay score becomes a controller** that migrates cold entities to a consolidated archive, keeping the searched surface bounded as lifetime knowledge grows. Wrap it all in a **local memory daemon** exposing two verbs — `remember(handoff, …)` and `recall(project, query, agent)` — that key off the HANDOFF v1 `project` field, so agents never choose *where* to store. Add **libSQL/Turso** as the opt-in durability/cross-machine fallback, with a `local_only` split so sensitive entities never replicate.

---

## Hard invariants

1. **Local-first, private by default.** Embeddings and search run on-device with no network. Cloud (BMW embeddings, Turso sync) is opt-in config, never required.
2. **`local_only` entities never leave the box.** Enforced structurally (separate non-synced attached DB), not by policy.
3. **One embedding engine per database.** Vector dimension is fixed at table creation; switching engines = full re-embed. Pick per deployment.
4. **Working memory vs semantic memory stay separable.** Blackboard (opencode.db, local task state) and knowledge (memory.db, durable) are **different files** so cloud sync can replicate knowledge without replicating live task state. Soft-link via a nullable `blackboard_id` column, no cross-file FK.
5. **Placement is computed, not chosen.** Canonical entity is resolved from `handoff.project` via an alias table. Agents pass content, never `entity_name`/`entityType`.
6. **No `read_graph` equivalent.** All retrieval is SQL + vector KNN over bounded tiers.
7. **Backwards-safe migration.** Keep `memory.jsonl` as a read-only backup until the SQLite store is validated.

---

## Preflight

```bash
# Python deps for the daemon (into the memory venv)
pip install sqlite-vec fastembed numpy fastapi "uvicorn[standard]"
# Optional cloud fallback:
pip install libsql-experimental   # Turso/libSQL embedded replica
# Verify sqlite-vec loads:
python -c "import sqlite_vec, sqlite3; db=sqlite3.connect(':memory:'); db.enable_load_extension(True); sqlite_vec.load(db); print('sqlite-vec OK')"
```
- `fastembed` ships `BAAI/bge-small-en-v1.5` (384-dim, CPU, offline) — the default local engine.
- Confirm the current `memory.jsonl` path (via `MEMORY_FILE_PATH` or the npx glob in `agent_memory.py`) before migration.

---

## Target schema (`memory.db`)

```
                 ┌──────────────┐        ┌────────────────┐
                 │   entities   │◄───────│ entity_aliases │   (canonical resolver, CO-003)
                 └──────┬───────┘ 1     n└────────────────┘
        1 ┌────────────┼───────────────┐ 1
          ▼            ▼               ▼
 ┌────────────┐ ┌────────────┐  ┌────────────────┐
 │observations│ │ relations  │  │ entity_vectors │  (sqlite-vec virtual table)
 └────────────┘ └────────────┘  └────────────────┘
   (rows, not a blob)  (graph edges, both-way indexed)   (1 vec / entity, same DB)
```

```sql
-- One row per knowledge node
CREATE TABLE entities (
  id                 TEXT PRIMARY KEY,                 -- uuid
  name               TEXT NOT NULL,                    -- canonical display name
  entity_type        TEXT NOT NULL,                    -- AgentLearnings | ArchitectureDecision | DesignSystem | TechnicalFact | …
  project            TEXT,                             -- canonical project key from handoff.project; NULL = global
  tier               TEXT NOT NULL DEFAULT 'warm',     -- hot | warm | cold
  decay_score        REAL NOT NULL DEFAULT 1.0,
  half_life_days     REAL NOT NULL DEFAULT 30,         -- PATTERN entities get 2× (matches current decay design)
  local_only         INTEGER NOT NULL DEFAULT 0,       -- 1 = never replicate
  blackboard_id      TEXT,                             -- soft link into opencode.db (no enforced FK across files)
  created_at         TEXT NOT NULL,
  updated_at         TEXT NOT NULL,
  last_reinforced_at TEXT
);
CREATE UNIQUE INDEX idx_entities_name    ON entities(name);
CREATE INDEX        idx_entities_project ON entities(project);
CREATE INDEX        idx_entities_type    ON entities(entity_type);
CREATE INDEX        idx_entities_tier    ON entities(tier);

-- Canonical resolver: every known name/variant points to one entity (kills duplicate-entity anti-pattern)
CREATE TABLE entity_aliases (
  alias      TEXT PRIMARY KEY,                         -- normalized: lowercased, trimmed, punctuation-collapsed
  entity_id  TEXT NOT NULL REFERENCES entities(id) ON DELETE CASCADE
);

-- One row per observation (was a JSON blob string) → enables per-obs decay, dedup, singleton semantics in SQL
CREATE TABLE observations (
  id            TEXT PRIMARY KEY,
  entity_id     TEXT NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
  tag           TEXT,                                  -- WORKED | AVOID | PATTERN | DECISION | BUG FIX | BUILT | SESSION | NULL
  domain        TEXT,                                  -- normalized topic
  body          TEXT NOT NULL,
  singleton_key TEXT,                                  -- e.g. 'status' → replaces prior obs with same key on this entity
  observed_at   TEXT NOT NULL,                         -- YYYY-MM-DD
  decay_score   REAL NOT NULL DEFAULT 1.0
);
CREATE INDEX idx_obs_entity ON observations(entity_id);
CREATE INDEX idx_obs_tag    ON observations(tag);
-- Singleton enforcement: at most one 'status' (etc.) obs per entity — fixes the "NOT STARTED + COMPLETE" anti-pattern
CREATE UNIQUE INDEX idx_obs_singleton ON observations(entity_id, singleton_key) WHERE singleton_key IS NOT NULL;
-- Dedup: identical (tag,domain,body) on an entity can't be inserted twice
CREATE UNIQUE INDEX idx_obs_dedup ON observations(entity_id, tag, domain, body);

-- Graph edges, queryable both directions
CREATE TABLE relations (
  id         TEXT PRIMARY KEY,
  from_id    TEXT NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
  to_id      TEXT NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
  rel_type   TEXT NOT NULL,                            -- contains | implements | fixes | uses-design-system | …
  created_at TEXT NOT NULL
);
CREATE INDEX        idx_rel_from   ON relations(from_id);
CREATE INDEX        idx_rel_to     ON relations(to_id);
CREATE UNIQUE INDEX idx_rel_unique ON relations(from_id, to_id, rel_type);

-- Vectors in the SAME db (cannot drift from the data). Dim = chosen engine's dim (384 local / 1536 BMW).
CREATE VIRTUAL TABLE entity_vectors USING vec0(
  entity_id TEXT PRIMARY KEY,
  embedding float[384]
);
```

Run with WAL: `PRAGMA journal_mode=WAL;` (concurrent reads while the daemon writes).

---

## PHASE M0 — Stand up the store

### Task M0.1 — Create `memory.db` + schema + sqlite-vec loader
- **Files:** new `skills/memory-daemon/db.py`.
- **Change:** open `memory.db`, `enable_load_extension`, `sqlite_vec.load(db)`, apply the DDL above, set WAL. Provide `connect()` returning a configured connection. Default path `~/.opencode/memory/memory.db` (env `MEMORY_DB_PATH`).
- **Acceptance:** fresh DB initializes; `INSERT`/KNN round-trips on `entity_vectors`; `PRAGMA integrity_check` clean.
- **Commit:** `feat(memory): sqlite + sqlite-vec store with schema`

---

## PHASE M1 — Embedding engine (local-first, cloud fallback)

### Task M1.1 — `EmbeddingEngine` interface + local default + BMW fallback
- **Files:** `skills/memory-daemon/embeddings.py`.
- **Change:** `class EmbeddingEngine: def embed(self, texts: list[str]) -> np.ndarray` and `dim: int`.
  - `LocalEmbeddingEngine` — `fastembed` `BAAI/bge-small-en-v1.5` (dim 384), offline.
  - `BmwEmbeddingEngine` — existing BMW `openai/text-embedding-3-small` path lifted from `memory_semantic_search.py` (dim 1536), used only when `EMBED_ENGINE=bmw`.
  - Select via `EMBED_ENGINE=local|bmw`. **The `entity_vectors` dim must match the engine** (invariant 3) — record the active engine/dim in a `meta` table and refuse to start if it disagrees with the table dim (forces an explicit re-embed instead of silent corruption).
- **Acceptance:** `EMBED_ENGINE=local` embeds with no network; `=bmw` matches today's vectors; dim-mismatch start is rejected with a clear message.
- **Commit:** `feat(memory): pluggable embedding engine (local bge-small default, BMW fallback)`

---

## PHASE M2 — The daemon API (deterministic placement + enforcement)

> Folds in CO-003: project resolver, context pack, write-time schema enforcement — now transactional.

### Task M2.1 — `remember(handoff, …)`
- **Files:** `skills/memory-daemon/api.py`.
- **Change:** single transaction:
  1. **Resolve** canonical entity from `handoff.project` via `entity_aliases` (normalize → lookup; create once if absent, seeding the alias). Agents pass `project`, never `entity_name`.
  2. **Upsert** the entity; set/refresh `updated_at`, `project`, `local_only`, optional `blackboard_id` from the handoff.
  3. **Merge observations** with dedup (the unique index) and **singleton replace** (e.g. `Status:` → `singleton_key='status'`, delete-then-insert). Derive `tag`/`domain` from the helper used.
  4. **Relations**: require ≥1 (anti-pattern #3) — supply a default `contains` to the project entity if none given.
  5. **Embed** (local) name + top observations; upsert `entity_vectors`.
  6. **Reinforce** decay (reset clock) on the touched entity.
  - Enforce ≥1 dated observation (anti-pattern #4). Keep the `scribe_*` helpers (`scribe_design_decision` → `DesignSystem`/`ArchitectureDecision` + `informed`/`uses-design-system`; `scribe_bug_fix` → `TechnicalFact` + `fixes`) so **type + relations are derived, never hand-typed**.
- **Acceptance:** two `remember()` calls for the same project never create a second project entity; a `Status:` update replaces the prior; a duplicate observation is a no-op; every new entity ends with ≥1 relation and ≥1 dated obs; the vector is written in the same transaction.
- **Commit:** `feat(memory): remember() — project-bound, enforcing, transactional dual-write`

### Task M2.2 — `recall(project, query, agent)`
- **Change:** returns a **context pack** in one call:
  - Project entities where `project=?` and `tier IN ('hot','warm')`, plus their relations (1-hop).
  - The agent's own learnings (`<agent>::learnings`) sorted by `decay_score`.
  - A vector KNN over warm tier for `query`; **search cold only on a warm miss**.
  - **Hybrid rank:** `similarity × decay_score × project_proximity` (proximity = relation distance to the active project entity).
- **Acceptance:** one call returns project context + agent learnings + semantic hits with no query-composition by the agent; cold tier is touched only when warm is insufficient; recent writes (M2.1) are immediately findable (no stale index).
- **Commit:** `feat(memory): recall() — deterministic project context pack + hybrid semantic ranking`

### Task M2.3 — Retire direct file I/O; point agents at the daemon
- **Files:** `skills/agent-memory/agent_memory.py` (shim), agent `.md` scribe blocks, `AGENTS.md` Rules 13/14.
- **Change:** reimplement `learn()`/`recall()`/`summarise_learnings()` as thin wrappers calling the daemon (keep signatures for compatibility). Update `scribe` to call `remember()`. Remove the full-file `_save_graph()` rewrite path. Update the search-protocol doc: `read_graph` → "structurally N/A"; keep "specific query / cache in session / GPT fetch-once."
- **Acceptance:** existing agent scribe/recall snippets work unchanged through the shim; no code writes `memory.jsonl` anymore.
- **Commit:** `refactor(memory): route agent-memory + scribe through the daemon`

---

## PHASE M3 — Decay-driven tiering + gardener (the scale mechanism)

### Task M3.1 — Decay recompute + hot/warm/cold migration
- **Files:** `skills/memory-daemon/gardener.py`.
- **Change:** a job (cron / on idle / on project-done) that recomputes `decay_score = 0.5^(age_days/half_life_days)` per entity and observation (PATTERN half-life ×2, matching today). `reinforce()` resets the clock. Migration rules:
  - `hot` = entities of the **active** project (set by `recall`/`load_project_context`); everything else demotes to `warm` on project switch.
  - `warm → cold` when `decay_score < COLD_THRESHOLD` and not reinforced within N days.
- **Acceptance:** an untouched entity's score decays over time; reinforcing resets it; crossing the threshold flips `tier` to `cold`; the warm working set size stays bounded as total entities grow.
- **Commit:** `feat(memory): decay-driven hot/warm/cold tiering`

### Task M3.2 — Cold consolidation (generalized `distil_project`)
- **Change:** when entities migrate to `cold`, LLM-consolidate their raw observations into a small number of durable `PATTERN` / `ArchitectureDecision` entities (BMW sonnet, as `distil_project()` already does), then soft-delete the raw rows (keep a pointer). Runs off the hot path.
- **Acceptance:** a finished project's dozens of raw observations collapse into a few high-value consolidated entities; retrieval cost for old projects drops; nothing the consolidation captured is lost.
- **Commit:** `feat(memory): cold-tier consolidation of stale observations`

### Task M3.3 — Stats surface for the galaxy
- **Change:** `get_stats()` → tier counts, decay histogram, recent writes, per-project entity counts. Replaces/extends `get_decay_stats()`. Expose via the daemon for the galaxy memory layer.
- **Acceptance:** the galaxy can render memory health (tier distribution, what was just learned) from one call.
- **Commit:** `feat(memory): stats endpoint for galaxy memory layer`

---

## PHASE M4 — Migration: `memory.jsonl` → `memory.db`

> Grounded in the **actual** JSONL shape from `agent_memory.py`: lines are `{"type":"entity","name","entityType","observations":[str]}` and `{"type":"relation","from","to","relationType"}`. AgentLearnings observations are `"[TAG] domain | note | YYYY-MM-DD"`.

### Mapping

| JSONL source | → memory.db |
|---|---|
| `entity` line, name endswith `::learnings` | `entities` row, `entity_type='AgentLearnings'`, `project=NULL` (agent-global), `half_life_days` ×2 for PATTERN-heavy agents optional |
| its `observations[]` `"[TAG] domain \| note \| date"` | one `observations` row each: parse `tag`, `domain` (normalized), `body=note`, `observed_at=date`; `decay_score` from date |
| other `entity` line | `entities` row, `entity_type=<entityType>`, `project` inferred from name (`JARVIS …` → `jarvis-galaxy`; `<X> Project` → `normalize(X)`; else `NULL`) |
| its observations with prefix `[DECISION]`/`[BUG FIX]`/`[BUILT]`/`[SESSION]` | `observations` rows with matching `tag`; `Status: …` → `singleton_key='status'`; trailing `YYYY-MM-DD` → `observed_at` else file-date |
| `relation` line `{from,to,relationType}` | `relations` row, resolving `from`/`to` names → entity ids via the alias map; **skip dangling** (log them) |
| (none) | seed `entity_aliases` with `normalize(name)` for every entity, plus known variants |

### Task M4.1 — Importer with duplicate-merge
- **Files:** `skills/memory-daemon/migrate_jsonl.py`.
- **Change:** read the JSONL, build entities/observations/relations per the mapping, **embed every entity** (chosen engine) into `entity_vectors`. **Execute the documented dedup during import:** merge the three known duplicates (`JARVIS Frontend Project`, `JARVIS Project`, `JARVIS Web Frontend`) into one canonical entity (e.g. `JARVIS Galaxy`) with the other two names as **aliases**; union their observations/relations. Generalize with a fuzzy-name pass that flags likely dupes for merge (auto-merge above a high threshold, else log for review).
- **Acceptance:** entity/observation/relation counts reconcile (minus intentional merges); zero duplicate canonical names; the three JARVIS dupes resolve to one entity with two aliases; every entity has a vector; dangling relations are logged, not silently dropped.
- **Commit:** `feat(memory): jsonl→sqlite importer with canonical dedup-merge`

### Task M4.2 — Retire hnswlib overlay
- **Files:** `skills/memory-semantic-search/` (deprecate), its cache (`memory.bin`, `entities.jsonl`, `meta.json`).
- **Change:** `sqlite-vec` supersedes the separate ANN index — rebuilt from `entity_vectors` during M4.1, so no drift. Keep the old skill as a read-only fallback for one release, then remove. **Note the dim change** if moving from BMW 1536 → local 384: the importer re-embeds everything, so this is handled by M4.1 (no partial/mixed index).
- **Acceptance:** semantic search runs through `sqlite-vec`; the old `.bin` index is no longer consulted; results match or beat the old overlay.
- **Commit:** `refactor(memory): replace hnswlib overlay with in-db sqlite-vec`

### Task M4.3 — Cutover + backup
- **Change:** flip `MEMORY_BACKEND=sqlite`; keep `memory.jsonl` **read-only** as a backup until a validation window passes; provide a `verify` command (counts, orphan check, dup-name check, vector coverage). Document rollback (point back at JSONL) until cutover is confirmed.
- **Acceptance:** the system runs fully on SQLite; `verify` passes; rollback path documented and tested once.
- **Commit:** `chore(memory): cut over to sqlite backend, keep jsonl backup`

---

## PHASE M5 — Cloud fallback (opt-in durability / cross-machine)

### Task M5.1 — libSQL embedded replica
- **Change:** swap `db.py`'s opener for **libSQL** when `MEMORY_SYNC_URL` + token are set: local replica stays authoritative (matches blackboard-as-truth), remote is durable backup + cross-machine continuity. Default (no env) = plain local SQLite, no network. `sqlite-vec` and all SQL are unchanged (libSQL is SQLite-compatible).
- **Acceptance:** with no env, fully local; with a Turso URL, writes replicate and a second machine sees them after sync; pulling the network keeps the local replica fully functional.
- **Commit:** `feat(memory): optional libSQL/Turso sync (local replica authoritative)`

### Task M5.2 — `local_only` never replicates (structural)
- **Change:** libSQL embedded replica syncs the **whole** DB, so per-row exclusion isn't possible in one file. Put `local_only=1` entities in a separate **non-synced** `memory_local.db`, `ATTACH`ed at connect; `remember()` routes by the flag; `recall()` queries across both via the attached schema. Only `memory.db` is given a sync URL.
- **Acceptance:** an entity written with `local_only=1` lands in `memory_local.db` and is **never** present in the remote; cross-file `recall()` still returns it locally; replicated `memory.db` contains only shareable knowledge.
- **Commit:** `feat(memory): local_only split — sensitive entities never sync`

---

## Capability preservation (nothing lost)

| Today | In v2 |
|---|---|
| `memory.jsonl` two layers | SQLite tables (+ cold archive); same two layers |
| `scribe()` dual-write | `remember()` — transactional, enforcing, project-bound |
| `learn()`/`recall()`/`summarise_learnings()` | Same signatures, daemon-backed (shim) |
| decay + `reinforce()` | Same — and now **drives tiering**, not just ranking |
| hnswlib + BMW embeddings | `sqlite-vec` (same DB) + **local** embeddings, BMW fallback |
| search protocol (no `read_graph`) | SQL + KNN over bounded tiers; `read_graph` structurally N/A |
| `memory-schema.md` conventions | Enforced in code (alias table, singleton index, type-from-helper) |
| `prune_report()` (manual) | Continuous **gardener** (M3) |
| `distil_project()` | Generalized cold **consolidation** (M3.2) |
| per-project binding (CO-003) | Alias/resolver table — first-class |
| `get_decay_stats()` | `get_stats()` for the galaxy (M3.3) |
| blackboard (opencode.db) | Untouched; soft-linked via `blackboard_id` |

---

## Fast track — recommended order

| # | Task | Effort | Why |
|---|---|---|---|
| 1 | M0.1 store + schema | small | Foundation. |
| 2 | M1.1 local embeddings | small | Removes the cloud dependency immediately. |
| 3 | M4.1 importer (+ dedup-merge) | medium | Migrate real data early; validates the schema against reality. |
| 4 | M2.1 `remember()` | medium | Deterministic, enforcing writes. |
| 5 | M2.2 `recall()` | medium | Deterministic project context. |
| 6 | M4.2 / M4.3 retire hnswlib + cutover | small | Single index, no drift. |
| 7 | M2.3 route agents through daemon | small | Retire file I/O. |
| 8 | M3.1–M3.3 tiering + gardener + stats | medium | The scale mechanism + galaxy surface. |
| 9 | M5.1 / M5.2 cloud fallback + local_only | medium | Opt-in durability, kept private. |

## Suggested PR breakdown

| PR | Contains | Risk |
|---|---|---|
| PR1 | M0 + M1 | low — additive store + local embeddings |
| PR2 | M4.1 importer (run against a **copy** of memory.jsonl) | medium — data migration; reversible |
| PR3 | M2 (remember/recall + shim) | medium — write/read path |
| PR4 | M4.2 + M4.3 cutover | medium — flips the backend |
| PR5 | M3 tiering/gardener/stats | medium — background jobs |
| PR6 | M5 libSQL + local_only | higher — optional, behind env |

Land PR1–PR4 to get a faster, private, drift-free local store with your data migrated and duplicates merged. PR5 is the scale headroom; PR6 is the cloud fallback when you want it.

---

## Two things to verify in `scribe.py` (not in the repo)

These shape M2.1/M2.3 and couldn't be confirmed from the repo:
- Whether `scribe()` already reindexes the semantic store on write (if so, that logic moves into `remember()`'s same-transaction embed).
- The exact helper→entity-type/relation mappings in `scribe_design_decision()` / `scribe_bug_fix()` / `scribe_jarvis_feature()` so M2.1 preserves them verbatim.
