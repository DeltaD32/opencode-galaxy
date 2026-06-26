# Memory Galaxy — Web Frontend Architecture

> **Branch:** `feat/web-frontend` (parallel to `feat/specialist-subagents` — do not merge or touch from other branches)  
> **Last updated:** 2026-06-25  
> **Status:** Phase 3.5 live — agent graph + memory graph rendering. Phase 4.6 decay/distillation data ready. Phase 5 (projects layer) planned.

---

## Process Architecture

The galaxy is a **completely separate Vite dev server** — not embedded in the OpenCode TUI.

```
Terminal A:  opencode serve --port 4096     ← OpenCode TUI + HTTP API (required)
Terminal B:  cd web && npm run dev          ← Vite dev server on :3000
Browser:     http://localhost:3000          ← React SPA (GalaxyView)
```

The TUI is a **required dependency** — without it, `/api/*` calls fail. But the two are
separate OS processes with no shared memory, no IPC, no webview embedding.

---

## File Map

```
web/
  index.html                    ← entry HTML
  vite.config.ts                ← proxy config + /__memory + /__agents bypass handlers
  src/
    main.tsx                    ← ReactDOM.createRoot
    App.tsx                     ← layout, right panel (galaxy/todos/diff/cost), busyAgentNames
    components/
      GalaxyView.tsx            ← 670 lines, main 3D force graph component
    lib/
      memory-reader.ts          ← fetches /__memory, parses JSONL, → ForceGraphData
      agent-reader.ts           ← fetches /__agents, converts to ForceGraphData + mergeGraphs()
      db-reader.ts (PLANNED)    ← will fetch /__db, convert opencode.db project rows → nodes
```

---

## Data Flow

```
Vite Node process
  ├── /__memory  → fs.readFileSync(memory.jsonl) → text/plain
  ├── /__agents  → buildAgentGraph() reads agent .md files + skill dirs → JSON
  └── /__db      → better-sqlite3 reads opencode.db (PLANNED Phase 5)

Browser (React)
  ├── fetch("/__memory") → memory-reader.ts → ForceGraphData
  ├── fetch("/__agents") → agent-reader.ts  → ForceGraphData
  ├── fetch("/__db")     → db-reader.ts     → ForceGraphData  (PLANNED)
  └── mergeGraphs() → unified ForceGraphData → 3d-force-graph → WebGL canvas

OpenCode TUI (:4096)
  ├── /api/*     → REST (sessions, messages, providers)
  └── /api/event → SSE (streaming tokens, real-time session status)
```

---

## GalaxyView.tsx — React Architecture

### Key design decisions

| Decision | Why |
|---|---|
| `graphRef` (useRef, not useState) | Storing the 3d-force-graph instance in state causes re-render loops — must be a ref |
| `dimensionsRef` (not state) | ResizeObserver fires frequently — writing to state on each resize causes cascade re-renders |
| `initTick` counter | Kicks the graph init effect once on first real ResizeObserver measurement without causing ongoing re-renders |
| `filteredData` via `useMemo` | Stable reference — only recomputes when `graphData` or `layers` change. Prevents spurious graph reinits |
| `agentMeshRegistry` module-level Set | Rotation loop needs to find all agent meshes without coupling to graph internals |
| Unmount cleanup effect (empty deps) | React StrictMode double-invoke safe — graphRef null check on remount prevents double-init |

### Kapsule pattern (confirmed in stash — important)

`3d-force-graph` uses the kapsule pattern. **Wrong usage crashes the graph silently:**

```typescript
// WRONG — the old code did this and caused sizing bugs:
const Graph = (ForceGraph3D as unknown as (el: HTMLElement) => Instance)(el);

// CORRECT — kapsule: factory first, then mount:
const Graph = (ForceGraph3D as unknown as () => Instance)();
Graph(el)  // ← mount to DOM element
  .backgroundColor(...)
  .width(initW)
  .height(initH)
  .graphData(data);
```

The stash on `feat/web-frontend` contains this fix — apply it when the stash is popped.

### Sizing strategy

```typescript
// Read live DOM dimensions at mount time — avoids stale React closure values
const rect = el.getBoundingClientRect();
const initW = rect.width > 0 ? rect.width : 800;
const initH = rect.height > 0 ? rect.height : 600;
```

ResizeObserver handles subsequent resizes by calling `.width(w).height(h)` directly
on the graph instance — no React state involved.

---

## Visual Encoding — Current State

### Node types

| Type | Shape | Colour | Size (val) | Special |
|---|---|---|---|---|
| Primary agent (`mode: primary`) | Custom `makeAgentMesh()` sphere | `#1c69d4` BMW Blue | 40 | Glow ring, emissiveIntensity=1.2, rotates at 0.005/frame |
| Subagent (`mode: subagent`) | Custom `makeAgentMesh()` sphere | `#a855f7` Purple | 22 | Glow ring, emissiveIntensity=0.7, rotates at 0.003/frame |
| Skill | `makeSkillMesh()` small sphere | `#22c55e` Green | 8 | emissiveIntensity=0.2 |
| Memory entity | Default 3d-force-graph sphere | `TYPE_COLOURS[entityType]` | proportional to observation count | — |

**TYPE_COLOURS map** (memory entity types):

| Type | Colour |
|---|---|
| `Agent` | `#1c69d4` BMW Blue |
| `Skill` | `#22c55e` Green |
| `Project` / `project` | `#f97316` Orange |
| `KnowledgeBase` | `#a855f7` Purple |
| `Offering` | `#14b8a6` Teal |
| `feature` | `#eab308` Yellow |
| `Artifact` | `#ec4899` Pink |
| `Configuration` | `#06b6d4` Cyan |
| `ProjectTracker` | `#f43f5e` Rose |
| `script` | `#84cc16` Lime |
| default | `#6b7280` Grey |

### Link types

| Relation | Colour | Width | Arrow | Particles |
|---|---|---|---|---|
| `orchestrates` (orchestrator → subagent) | `#1c69d4` BMW Blue | 5 | length=10 | 2 @ speed 0.003, width 5 |
| `uses` (agent → skill) | `#4ade80` Light green | 3.5 | length=6 | 5 @ speed 0.006, width 4 |
| Memory relations | `#374151` Dark grey | 1.5 | none | none |

- All links: `linkOpacity=0.85`, `linkCurvature=0.1`, arrows at `relPos=1`
- Bloom post-processing: `UnrealBloomPass(strength=0.8, radius=0.4, threshold=0.1)`

### Live animation

- Agent meshes rotate continuously (setInterval 16ms)
- Busy agents (`busyAgentNames` prop from App.tsx): emissive intensity pulses
  `0.8 + 0.7 * sin(Date.now() / 400)` — fast bright pulsing while processing
- Simulation settings: `d3AlphaDecay(0.012)`, `d3VelocityDecay(0.25)` — slower, organic feel

---

## Layer System

Three toggleable layers (top-right toolbar):

| Button | Controls | Default |
|---|---|---|
| Agents | `PrimaryAgent` + `Subagent` nodes + all `orchestrates`/`uses` links | On |
| Skills | `Skill` nodes | On |
| Memory | All other entity nodes + relation links | On |

---

## Pending Stash (`feat/web-frontend`)

```
stash@{0}: On feat/web-frontend: wip: web frontend galaxy changes
  web/src/App.tsx        — overflow-hidden for galaxy panel (canvas sizing fix)
  web/src/components/GalaxyView.tsx — kapsule pattern fix + live DOM rect sizing
```

Apply before starting Phase 5 work:
```bash
git checkout feat/web-frontend
git stash pop
# verify builds, then commit
```

---

## Phase 4.6 — Memory Lifecycle Data (Available for Phase 5 Visualisation)

The following data is now available from `agent_memory.py` for galaxy visualisation.
Rendering is deferred to Phase 5; the data contracts are finalised here.

### Decay score visualisation

`get_decay_stats(agent)` returns:
```python
{
  "total": int,          # total observation count
  "fresh": int,          # score >= 0.80
  "warm": int,           # 0.40 <= score < 0.80
  "stale": int,          # score < 0.40
  "mean_score": float,   # average decay score across all obs
  "by_tag": {            # breakdown by WORKED / AVOID / PATTERN
    "WORKED": {"count": int, "mean_score": float},
    "AVOID":  {"count": int, "mean_score": float},
    "PATTERN":{"count": int, "mean_score": float},
  }
}
```

**Planned galaxy encoding:**

| Decay bucket | Agent node visual change |
|---|---|
| Agent `mean_score` ≥ 0.80 (mostly fresh) | No change from default |
| Agent `mean_score` 0.40–0.79 (mixed) | Slight amber tint on glow ring |
| Agent `mean_score` < 0.40 (mostly stale) | Dim glow + grey tint — signals knowledge needs refreshing |
| Individual PATTERN obs at score < 0.20 | Faded annotation dot near agent node |

### Distillation status visualisation

`get_projects_pending_distillation()` returns projects with `distillation_ready=1` and `distilled_at IS NULL`.

**Planned galaxy encoding:**

| State | Project node visual |
|---|---|
| `distillation_ready=1`, not yet distilled | Amber pulsing ring around project sun |
| `distilled_at` set | Stable ring; no pulse |

### Section compression visualisation

`sections.compressed=1` rows are soft-deleted raw analysis. `compressed=0` rows include Execution Plan and Execution Result — the permanent record.

**Planned galaxy encoding:**

| State | Blackboard node visual |
|---|---|
| All sections compressed (blackboard done) | Grey faded octahedron |
| Has uncompressed sections (in-flight) | Full colour per status |
| `compressed=0` sections count | Small number badge on blackboard node |

---

## Phase 5 — Projects Layer (Planned)

### What gets added

A fourth node cluster representing projects/blackboards/decisions from `opencode.db`.
See `PROJECTS-DB.md` for the full schema.

### New Vite bypass route

```typescript
// vite.config.ts — add alongside /__memory and /__agents
import Database from "better-sqlite3";

"/__db": {
  target: "http://localhost:3000",
  bypass(_req, res) {
    const db = new Database(
      "/Users/QTE2362/.local/share/opencode/opencode.db",
      { readonly: true }
    );
    try {
      const projects  = db.prepare("SELECT * FROM projects WHERE status != 'archived'").all();
      const boards    = db.prepare("SELECT * FROM blackboards").all();
      const decisions = db.prepare("SELECT * FROM decisions").all();
      const conflicts = db.prepare("SELECT * FROM conflicts").all();
      res.setHeader("Content-Type", "application/json; charset=utf-8");
      res.setHeader("Access-Control-Allow-Origin", "*");
      res.end(JSON.stringify({ projects, boards, decisions, conflicts }));
    } finally {
      db.close();
    }
    return false;
  },
},
```

### New node types for projects

| DB table | Node type | Colour | Shape | Size | Animation |
|---|---|---|---|---|---|
| `projects` | Project | `#1c69d4` BMW Blue | Sphere with ring (solar system sun) | Large, high mass | Steady glow |
| `blackboards` (deliberating) | Blackboard | Yellow `#eab308` | Octahedron | Medium | Slow pulse |
| `blackboards` (awaiting-approval) | Blackboard | Amber `#f97316` | Octahedron | Medium | Steady |
| `blackboards` (executing) | Blackboard | Bright white-blue | Octahedron | Medium | Fast pulse |
| `blackboards` (blocked) | Blackboard | Dim red `#ef4444` | Octahedron | Medium | No pulse |
| `blackboards` (done) | Blackboard | Faded green | Octahedron | Medium | Solid, faded |
| `decisions` | Decision | Purple `#a855f7` | Diamond | Small | None |
| `conflicts` (unresolved) | Conflict | Orange-red `#f97316` | Spiky | Small | Faint pulse |

### New link types

| Relation | From | To | Visual |
|---|---|---|---|
| `contains` | Project | Blackboard | Medium blue, no particles |
| `deliberated-by` | Blackboard | Agent | Green, directional |
| `produced` | Blackboard | Decision | Purple, directional |
| `influenced` | Decision | Blackboard (future) | Purple dashed arc — **the killer feature** |
| `recommended-by` | Decision | Agent | Purple, thin |

### `db-reader.ts` (to be created)

```typescript
export interface ProjectsGraphData {
  nodes: GraphNode[];
  links: GraphLink[];
}

export async function fetchProjectsGraph(): Promise<ProjectsGraphData> {
  const resp = await fetch("/__db");
  if (!resp.ok) throw new Error(`/__db failed: ${resp.status}`);
  const data = await resp.json() as DbPayload;
  return toForceGraphNodes(data);
}
```

### Spatial layout

```
[Memory nodes]      [Projects cluster]      [Agent constellation]
   left zone          centre-right              right zone (fixed)

Each project = solar system:
  ☀️  Project (sun) — high mass, other nodes orbit
    🪐 Blackboard (planets) — attracted to project
      💫 Decisions (moons) — low mass, cluster near blackboard
      ⚠️  Conflicts (red moons) — unresolved = faint pulse
```

Force graph physics handles this naturally via `d3Force` charge/link strength tuning.

### Tauri Phase 4 migration

When the Vite dev server is replaced by Tauri:
- `better-sqlite3` → `tauri-plugin-sql`
- `fetch("/__db")` → `invoke("db_query", { sql: "...", params: [] })`
- Pattern is identical; only the runtime transport changes

---

## Adding a New Node Type (Pattern Reference)

When adding blackboard/decision nodes in Phase 5, follow this existing pattern:

1. **Add to `TYPE_COLOURS`** in `memory-reader.ts` (or new `db-reader.ts`)
2. **Add type guards** (`isProjectNode`, `isBlackboardNode`, etc.)
3. **Add mesh factory** (`makeProjectMesh`, `makeBlackboardMesh`) using Three.js
4. **Update `nodeThreeObject`** in GalaxyView init block
5. **Update `LEGEND_ENTRIES`** array for the legend panel
6. **Add link colour constants** for new relation types
7. **Update `linkWidth` / `linkDirectionalParticles`** in init block
8. **Add layer toggle** if the new cluster should be independently hideable
