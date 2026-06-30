# Change Order 001 — Galaxy: render fixes + live blackboard wiring

**Audience:** an implementing coding agent (e.g. Sonnet 4.6 via the programming-expert) or a human dev.
**Repo:** `opencode-galaxy`, web app under `web/`. **Branch:** create `feat/galaxy-live-wiring` off `main`.
**Read first:** `JARVIS-ORCHESTRATION-MODEL.md`, `GALAXY-VISUAL-LANGUAGE.md`, `BUILD-GAP-ANALYSIS.md` (design rationale). This doc is the *mechanical* work order; those are the *why*.

This document is self-contained: you do not need the originating conversation. Each task has a goal, exact file targets, the change to make, acceptance criteria, and a commit message. Do tasks in order — phases are dependency-ordered. Stop and report if any acceptance check fails.

---

## Hard invariants — do NOT violate

1. **Blackboard is the source of truth, not SSE.** Agent activity must derive from `opencode.db` (`specialist_queue` / `sections` / `blackboards`), never from SSE events. SSE may *trigger a re-poll*, but never *be* the state. (See MODEL §5.)
2. **The renderer stays lazy; the recorder is eager.** Do not make the Three.js scene run while the panel is closed. The always-on data capture (Phase 4) is a separate non-visual layer. (MODEL §7.)
3. **Keep the SSE EventSource a singleton.** `useSSE` already guarantees one connection; do not open a second.
4. **One STT instance.** Voice work (Phase 5) must not create a second `SpeechRecognition`/recorder. `VoiceController` owns it.
5. **Never use Web Speech STT.** It routes to Google's cloud and is blocked on BMW's network. Use the mlx-whisper sidecar only.
6. **No `localStorage`/`sessionStorage` in artifacts** is irrelevant here (real app) — but keep secrets/paths out of source; use env vars.
7. **Don't reintroduce `3d-force-graph`.** The orbital port replaced it.

---

## Preflight (run once, verify before starting)

```bash
cd web
node -v          # expect Node 18+; better-sqlite3 needs a matching ABI
npm install      # REQUIRED — without this, ~50 TS errors are all "cannot find module"
npx tsc --noEmit # after Phase 0.2 this should be clean
```

If `npm install` fails on `better-sqlite3`, the local Node version mismatches the prebuilt binary — rebuild with `npm rebuild better-sqlite3` or align Node to the project's version.

---

## Fast track — easy wins first (recommended order)

Front-loaded because each is small, low-risk, and high-value. Do these before the heavier subsystems (Phases 4–5). Each links to its full task below.

| Order | Task | Effort | Why first |
|---|---|---|---|
| 1 | **0.1** `npm install` | trivial | Nothing builds without it. |
| 2 | **0.2** archive dead `App.tsx` | trivial | Clears the typecheck. |
| 3 | **2.0** 🔴 remove `sections.compressed` filter | 1 line | Unblocks the entire live view (silently empty today). |
| 4 | **1.1** ResizeObserver | small | Fixes blank-on-open render. |
| 5 | **1.2** colour planets from data | 1 line | Big visual payoff; distinguishes roles. |
| 6 | **1.3** layer-toggle reactivity | small | Makes existing toggles work. |
| 7 | **2.1** pass live props into galaxy | small | Connects data already flowing. |
| 8 | **2.2** expose `specialist_queue` over `/__db` | small | The precise "who's working now" signal. |
| 9 | **B-DB1** add `handoff_id` columns (+ index) | small | Cheap now, refactor later. Join key for timeline + chat linking. |
| 10 | **B-DB2** add `summary` / `blockers` columns | small | Clean narration + amber source without parsing markdown. |
| 11 | **B-DB3** durable `status_events` audit log | small+ | Foundation of the scrubbable timeline; durable + gap-free. Do before Phase 4. |
| 12 | **H** housekeeping (dep removal, CSS dedupe, env vars, schema-guard warning) | trivial | No-risk cleanup. |

Then proceed to the lit-tether / brightness work (2.3–2.4), Phase 3, and the bigger subsystems. Phase 4's timeline now builds on the durable `status_events` log from **B-DB3**.

---


- **Goal:** resolve all missing modules.
- **Change:** run `npm install` in `web/`.
- **Acceptance:** `npx tsc --noEmit` no longer reports `Cannot find module 'react'` (App.tsx errors remain until 0.2).
- **Commit:** *(no code change; do with 0.2)*

### Task 0.2 — Remove dead `App.tsx`
- **Goal:** `App.tsx` is the pre-JARVIS UI; nothing imports it (`main.tsx` boots `JarvisShell`). Its TS errors block the typecheck.
- **Files:** `web/src/App.tsx`
- **Change:** verify no live import, then archive it.
  ```bash
  grep -rn "from \"./App\"\|from './App'\|import App" web/src   # expect: no matches
  mkdir -p web/src/_archive && git mv web/src/App.tsx web/src/_archive/App.tsx.bak
  ```
  Also confirm `_archive` is excluded from the build: add `"src/_archive"` to `exclude` in `web/tsconfig.json` (create the array if absent).
- **Acceptance:** `npx tsc --noEmit` is **clean** (zero errors).
- **Commit:** `chore(web): install deps + archive dead App.tsx`

---

## PHASE 1 — Make the scene render correctly

> All edits in `web/src/components/GalaxyView.tsx` unless noted. **View the file before editing** — line numbers below are anchors from the reviewed revision and may shift.

### Task 1.1 — Fix blank render (ResizeObserver)
- **Goal:** the canvas is sized to 0 when the panel opens because `window "resize"` doesn't fire on a CSS-transform drawer.
- **Change:** replace the window listener (≈ line 490) with a `ResizeObserver` on the mount element, plus a transition-matched fallback.
  - **Before:**
    ```ts
    window.addEventListener("resize", onResize);
    ```
  - **After:**
    ```ts
    const ro = new ResizeObserver(() => onResize());
    ro.observe(el);
    // Drawer slide is 360ms (PanelLayer.css transform transition) — ensure a
    // correct size once it settles, even if no further resize event fires.
    const settleTimer = window.setTimeout(onResize, 360);
    ```
  - **Cleanup (≈ line 495), before:**
    ```ts
    window.removeEventListener("resize", onResize);
    ```
  - **Cleanup, after:**
    ```ts
    ro.disconnect();
    window.clearTimeout(settleTimer);
    ```
- **Acceptance:** open the galaxy panel from a cold load → the scene fills the panel immediately (no blank/letterboxed canvas). Resize the window and the panel → canvas tracks the container.
- **Commit:** `fix(galaxy): size canvas via ResizeObserver so panel-open renders`

### Task 1.2 — Colour planets from data
- **Goal:** every planet renders identical purple because the colour is hardcoded; `agent-reader` already provides per-agent colour (BMW blue primary `#1c69d4`, purple subagent `#a855f7`).
- **Change:** in the subagent build loop, replace the hardcoded colour.
  - **Before:**
    ```ts
    const col = C.sub;
    ```
  - **After:**
    ```ts
    const col = (sa as { color?: string }).color ?? C.sub;
    ```
  - Better (typed): add `color?: string` to the `GraphNode` interface in `web/src/lib/memory-reader.ts` if not already present, so the cast isn't needed. `agent-reader.ts` already sets `color` on every node it emits.
- **Acceptance:** the primary/orchestrator-linked agent renders BMW blue; subagents render purple. No two roles are indistinguishable by colour.
- **Commit:** `fix(galaxy): colour planets from agent data, not hardcoded purple`

### Task 1.3 — Make layer toggles reactive
- **Goal:** the `[layers]` effect (≈ line 147) is an empty stub; group visibility is only set once inside `loadAndBuild` (≈ line 474), so toggles do nothing after first render.
- **Change:**
  1. Add a ref near the top of the component body:
     ```ts
     const groupsRef = useRef<Record<"agents"|"skills"|"memory"|"stars", THREE.Group> | null>(null);
     ```
  2. Inside the main effect, right after the `G` object is created and added to the scene:
     ```ts
     groupsRef.current = G;
     ```
  3. Replace the empty `[layers]` effect body:
     - **Before:**
       ```ts
       useEffect(() => {
         // ...handled below...
       }, [layers]);
       ```
     - **After:**
       ```ts
       useEffect(() => {
         const g = groupsRef.current;
         if (!g) return;
         g.agents.visible = layers?.agents ?? true;
         g.skills.visible = layers?.skills ?? true;
         g.memory.visible = layers?.memory ?? true;
       }, [layers]);
       ```
- **Acceptance:** toggling a layer prop flips that group's visibility live, both before and after the initial data load.
- **Commit:** `fix(galaxy): apply layer visibility reactively via group ref`

### Task 1.4 — Touch/pointer support + gentler zoom *(polish; may trail)*
- **Goal:** camera controls are mouse-only; wheel zoom (`e.deltaY * 0.4`) overshoots.
- **Change:** add `pointerdown/pointermove/pointerup` mirroring the mouse handlers, call `canvas.setPointerCapture(e.pointerId)` on down; add a two-pointer `touchmove` pinch that adjusts `camTo.radius`. Change wheel to proportional:
  ```ts
  const sign = Math.sign(e.deltaY);
  camTo.radius = Math.max(50, Math.min(700, camTo.radius * (1 + sign * 0.08)));
  ```
- **Acceptance:** on a touch device / trackpad, drag orbits and pinch zooms; wheel zoom no longer flies past the sun in one notch.
- **Commit:** `feat(galaxy): pointer + touch camera controls, proportional zoom`

**Phase 1 Definition of Done:** panel opens to a visible, correctly-sized, multi-coloured scene; layer toggles work; `tsc` clean.

---

## PHASE 2 — Make it live

### Task 2.0 — 🔴 CRITICAL: fix the silent `sections` query bug *(do this FIRST)*
- **Goal:** the live view is currently **dead at the source** and fails silently. The `/__db` sections query filters on a column that does not exist in the real schema, so the query throws, `safeAll` swallows it and returns `[]`, and **every agent therefore derives as idle — no tether can ever light.**
- **Evidence:** the real DDL (`skills/projects/projects.py`) is `sections(id, blackboard_id, agent, section_name, content, written_at)` — **there is no `compressed` column.** But `web/vite.config.ts` runs `... FROM sections WHERE compressed = 0 OR compressed IS NULL`. `safeAll` logs `skipping table sections: no such column: compressed` and returns `[]`. (Compression is described in the briefing doc but was never implemented in `projects.py`.)
- **Files:** `web/vite.config.ts` (`buildDbSnapshot`, the `sections` query ≈ line 159).
- **Change:**
  - **Before:**
    ```ts
    "SELECT id, blackboard_id, agent, section_name, written_at FROM sections WHERE compressed = 0 OR compressed IS NULL"
    ```
  - **After:**
    ```ts
    "SELECT id, blackboard_id, agent, section_name, written_at FROM sections"
    ```
  - *(If you implement compression later, add the `compressed` column to `projects.py`'s `sections` DDL first, then re-add the filter. Don't filter on a column that isn't there.)*
- **Acceptance:** with a non-`done` board that has sections, `curl localhost:3000/__db | jq '.sections | length'` returns > 0, and the server log no longer prints `skipping table sections`. Agent activity now derives correctly.
- **Commit:** `fix(db): remove filter on nonexistent sections.compressed column (live view was silently empty)`

### Task 2.1 — Pass live props into the galaxy
- **Goal:** `GalaxyPanel` renders `<GalaxyView />` with no props; `GalaxyView` ignores `busyAgentNames` (param is `_busyAgentNames`).
- **Files:** `web/src/jarvis/panel/GalaxyPanel.tsx`, `web/src/components/GalaxyView.tsx`
- **Change:**
  1. In `GalaxyPanel.tsx`, pull from session context and pass down. **Before:**
     ```tsx
     {isOpen && <GalaxyView />}
     ```
     **After:**
     ```tsx
     {isOpen && (
       <GalaxyView
         busyAgentNames={busyAgentNames}
         agentStatuses={agentStatuses}
       />
     )}
     ```
     Add at the top of the component: `const { busyAgentNames, agentStatuses } = useSessionContext();` (import `useSessionContext` from `../session/SessionContext`).
  2. In `GalaxyView.tsx`, stop ignoring the prop. **Before:** `busyAgentNames: _busyAgentNames,` → **After:** `busyAgentNames,`. Add `agentStatuses?: AgentStatus[]` to `GalaxyViewProps` (import `AgentStatus` from `../lib/db-reader`).
- **Acceptance:** `GalaxyView` receives a populated `busyAgentNames`/`agentStatuses` when agents are active (verify via a temporary `console.log`, then remove).
- **Commit:** `feat(galaxy): pass live agent status from session context into the scene`

### Task 2.2 — Expose `specialist_queue` over `/__db`  *(highest-value data change — G6)*
- **Goal:** the precise "who is executing right now" + queue order lives in `specialist_queue`, which `/__db` does not currently select.
- **Files:** `web/vite.config.ts` (`buildDbSnapshot`), `web/src/lib/db-reader.ts`
- **Change:**
  1. In `vite.config.ts`, add a `safeAll` query alongside the existing five (after `sections`, ≈ line 159):
     ```ts
     const specialistQueue = safeAll(
       "specialist_queue",
       "SELECT id, blackboard_id, agent, status, queued_at, started_at, completed_at FROM specialist_queue"
     );
     ```
     and include it in the return (≈ line 164):
     ```ts
     return JSON.stringify({ projects, blackboards, decisions, conflicts, sections, specialistQueue });
     ```
     Also add `specialistQueue: []` to the `empty` object near the top of `buildDbSnapshot`.
  2. In `db-reader.ts`, add the row type and extend `DbSnapshot`. **Column names verified exact against `skills/projects/projects.py` DDL** (`id, blackboard_id, agent, status, queued_at, started_at, completed_at`; `blackboard_id` and `agent` are `NOT NULL`; queue statuses are `pending | active | done | skipped`):
     ```ts
     export interface SpecialistQueueRow {
       id: string;
       blackboard_id: string;
       agent: string;
       status: "pending" | "active" | "done" | "skipped" | string;
       queued_at: string;
       started_at: string | null;
       completed_at: string | null;
     }
     ```
     Add to `DbSnapshot`: `specialistQueue: SpecialistQueueRow[];` (default to `[]` in the fetch fallbacks).
- **Acceptance:** `curl localhost:3000/__db | jq '.specialistQueue'` returns an array (empty is fine when idle; populated with a `status:"active"` row during a real delegation).
- **Commit:** `feat(db): expose specialist_queue over /__db for precise live agent state`

### Task 2.3 — Bind lit tethers to live activity
- **Goal:** a subagent's tether brightens while it is the active queue member; dims otherwise. (One at a time — execution is sequential; see MODEL §5 / invariant on async.)
- **Files:** `web/src/components/GalaxyView.tsx`
- **Change:**
  - Compute an `activeAgents: Set<string>` each frame (or on data refresh) as: agents with a `specialistQueue` row where `status === "active"`. Fallback to `agentStatuses` (`status === "active"`) if the queue array is empty.
  - For each `AgentEntry`, set the sun→planet `link` material opacity high (e.g. `0.9`) and the planet emissive intensity up when its name ∈ `activeAgents`; otherwise the dim defaults (link `0.32`, emissive `0.85`). Match the agent by the `sa.name` captured in the build loop (store it on the entry).
- **Acceptance:** trigger a real delegation → exactly the executing agent's tether is bright; when the queue advances, the bright tether moves to the next agent.
- **Commit:** `feat(galaxy): light the tether of the actively-executing agent`

### Task 2.4 — Two-tier brightness (active vs dormant)
- **Goal:** elements not in the current session render dimmed; active ones full bright. (VISUAL §2.)
- **Change:** define an `activeSet` (agents in queue or with a section on a non-`done` board; their owned skills; the active blackboards). For nodes not in `activeSet`, lower emissive intensity and glow opacity to a dormant level (e.g. ×0.25). Memory cloud stays at a low ambient level regardless.
- **Acceptance:** with one project running, only its agents/skills/board are bright; the rest of the team is visibly dimmed but present.
- **Commit:** `feat(galaxy): two-tier active/dormant brightness`

**Phase 2 Definition of Done:** during a real task, the galaxy shows the executing agent lit and the idle team dimmed, driven entirely by `opencode.db` (not SSE).

---

## PHASE 3 — Wire the blackboard into the scene

> The converter already exists and the schema is verified (`docs/PROJECTS-DB-AGENT-BRIEFING.md`). This is "call it + map statuses," not "build a data layer."

### Task 3.1 — Render the blackboard graph
- **Files:** `web/src/components/GalaxyView.tsx`, using `fetchProjectsGraph` from `web/src/lib/db-reader.ts`.
- **Change:** in `loadAndBuild`, after the agent/memory fetches, also `await fetchProjectsGraph()` and build nodes for projects / blackboards / decisions / conflicts. Place projects near the artifact tier; attach blackboards to their project; decisions/conflicts near their blackboard. Reuse the existing glow/label helpers. Put these in the `memory`/`projects` layer group so the layer toggle governs them.
- **Acceptance:** with seeded DB rows, project/blackboard/decision/conflict nodes appear and are connected; counts reported via `onCountChange` increase accordingly.
- **Commit:** `feat(galaxy): render projects/blackboards/decisions/conflicts from /__db`

### Task 3.2 — Status → visual mapping
- **Goal:** blackboard status drives colour/state. Strings already match the web (`deliberating / awaiting-approval / executing / done / blocked`).
- **Change:** map `executing`→bright (green/active), `awaiting-approval` & `deliberating`→**amber**, `blocked`→amber-red, `done`→faded/dormant. Amber is reserved for "needs your decision" (VISUAL §4).
- **Acceptance:** a board in `awaiting-approval` shows amber in the scene at the same time the approval is pending; flipping it to `executing` turns it bright.
- **Commit:** `feat(galaxy): map blackboard status to node colour/state`

### Task 3.3 — Conflict flares between agents
- **Change:** for each unresolved `conflicts` row, draw an amber line/flare between `agent_a` and `agent_b` planets (not planet-to-sun). Resolved conflicts fade to neutral.
- **Acceptance:** an open conflict shows an amber flare between exactly the two named agents; resolving it removes the flare.
- **Commit:** `feat(galaxy): amber conflict flares between disagreeing agents`

### Task 3.4 — *(optional)* Section bodies in the side-panel (G4)
- **Change:** add `content` to the `sections` `SELECT` in `vite.config.ts` (after Task 2.0 the query is clean) and to `SectionRow` in `db-reader.ts`; surface a node's section content in the existing detail/side-panel. **Note:** there is currently **no compression** in `projects.py`, so *all* section content is available in the DB — no `.md` fallback needed today. If compression is added later, completed-board history would need the `.md` at `blackboards.file_path` (a future `/__blackboard?path=` route).
- **Acceptance:** clicking a blackboard node shows its current section text.
- **Commit:** `feat(galaxy): show section content in node detail panel`

**Phase 3 Definition of Done:** the galaxy reflects real coordination state — projects, board statuses (amber when awaiting you), and live conflicts.

---

## PHASE 4 — Timeline (new subsystem — contract + criteria, not a diff)

Implement as a **non-visual, always-on recorder** plus a **scrubber** the lazy renderer reads. Do not couple capture to the panel being open.

**Contract — `useBoardRecorder` (suggested `web/src/jarvis/galaxy/recorder.ts`):**
- Starts at app boot (mount it in `JarvisShell`, not in `GalaxyView`).
- Subscribes to `useSSE` purely as a *trigger*; on relevant events, re-polls `/__db`.
- Also polls `/__db` on a low-frequency interval (e.g. 3–5s) as a safety net.
- Stores an append-only array of `{ t: ISOString, snapshot: DbSnapshot }`, capped (e.g. last N minutes or M entries) to bound memory.
- Exposes: `getLatest()`, `getAt(t)`, `getRange(from,to)`, `isLive()`.

**Renderer integration:**
- On panel open, `GalaxyView` reads history from the recorder so the timeline is immediately scrubbable.
- Add a scrubber UI (bottom of the panel). Dragging sets a "viewing time"; the scene renders the snapshot at that time.
- **Playback stays put:** when scrubbed back, new live snapshots do NOT jump the view forward. Show a `● LIVE` indicator — bright when viewing the live edge, dim+clickable when scrubbed back (click → jump to live).

**Acceptance:**
- Close the panel, let a task run, reopen → the elapsed activity is present and scrubbable (recorder ran while closed).
- Scrub to T, let new events arrive → view stays at T; `● LIVE` dims; clicking it returns to the live edge.
- Memory stays bounded over a long session (cap enforced).

**Commits:** `feat(galaxy): always-on board recorder` · `feat(galaxy): timeline scrubber with live-edge lock`

---

## PHASE 5 — Conversational intents (new — contract + criteria)

**5.1 Narration mute** — add `narrationEnabled` to `settingsStore.ts` (distinct from `ttsEnabled`; `ttsEnabled` mutes *all* speech, `narrationEnabled` mutes only proactive headlines). Wire a Settings toggle and a voice command. *Acceptance:* with narration off, JARVIS stops volunteering agent-response headlines but still answers direct questions and still speaks if `ttsEnabled`.

**5.2 Status query + thousand-foot summary** — intent recognition near `VoiceController`: "what's <agent> doing?" reads `specialist_queue`+`blackboards` and speaks a one-line status; "are we on track?" summarizes board state (counts by status, blockers, pending approvals). May spotlight the queried agent's planet. *Acceptance:* both queries answer from live DB state within ~1–2s; spotlight highlights the right planet.

**5.3 Scope amend + interrupt** — "also add Y / don't forget Z" routes an amendment to the orchestrator as a new ticket (do not freeze the plan at kickoff). Voice barge-in (user starts speaking) or a cancel keyword calls the existing `abortSession()`. *Acceptance:* an amendment appears as a new board/section mid-run; speaking over JARVIS aborts the current turn.

**Commits:** `feat(voice): narration mute` · `feat(voice): board status + summary intents` · `feat(voice): scope amend + barge-in interrupt`

---

## Backend schema additions (`skills/projects/projects.py`) — cheap now, costly later

> **Migration note for all three:** `CREATE TABLE IF NOT EXISTS` only helps *fresh* databases. The existing `opencode.db` already has these tables, so you must also run idempotent `ALTER TABLE ADD COLUMN` guarded by a column-exists check (SQLite has no `ADD COLUMN IF NOT EXISTS`). Pattern:
> ```python
> def _ensure_column(conn, table, col, decl):
>     cols = {r[1] for r in conn.execute(f"PRAGMA table_info({table})")}
>     if col not in cols:
>         conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} {decl}")
> ```
> Run these on init alongside the `CREATE TABLE` block.

### Task B-DB1 — Persist `handoff_id` (the timeline/chat join key)
- **Goal:** thread a delegation's rows together and to the chat log by the unique `handoff_id` that already exists in every envelope. (Decided — see MODEL discussion.)
- **Files:** `skills/projects/projects.py` (DDL + the `sections` and `specialist_queue` write paths), and whatever sync writes sections from the `.md`.
- **Change:**
  - Add columns:
    ```sql
    -- sections
    ALTER TABLE sections ADD COLUMN handoff_id TEXT;
    -- specialist_queue
    ALTER TABLE specialist_queue ADD COLUMN handoff_id TEXT;
    ```
  - Add an index:
    ```sql
    CREATE INDEX IF NOT EXISTS idx_sections_handoff ON sections(handoff_id);
    ```
  - Populate `handoff_id` when writing a section / enqueuing a specialist (parse it from the RESPONSE v1 / HANDOFF v1 envelope already present in the content).
  - Expose it: add `handoff_id` to the `sections` and `specialist_queue` `SELECT`s in `web/vite.config.ts` and to the row interfaces in `db-reader.ts`.
- **Acceptance:** rows from one delegation share a `handoff_id`; `SELECT * FROM sections WHERE handoff_id = ?` returns that delegation's sections.
- **Commit:** `feat(db): persist handoff_id on sections + specialist_queue for end-to-end traceability`

### Task B-DB2 — Persist RESPONSE v1 `summary` + `blockers` (narration / amber source)
- **Goal:** JARVIS narration (Phase 5.2) and node headlines should read a clean field, not parse markdown out of `content`. `blockers` drives amber/your-attention.
- **Files:** `skills/projects/projects.py` (sections DDL + write path).
- **Change:**
  ```sql
  ALTER TABLE sections ADD COLUMN summary  TEXT;   -- RESPONSE v1 summary bullets (joined)
  ALTER TABLE sections ADD COLUMN blockers TEXT;   -- RESPONSE v1 blockers (joined), null if none
  ```
  When syncing a RESPONSE v1 section, extract `summary:` and `blockers:` from the envelope and store them. Expose both via `/__db` + `db-reader` like B-DB1.
- **Acceptance:** a specialist response row has a populated `summary`; a blocked response has non-null `blockers`. The galaxy can show a one-line headline and flag amber without markdown parsing.
- **Commit:** `feat(db): persist response summary + blockers for narration and amber state`

### Task B-DB3 — Durable status-event audit log  *(DECIDED: build now)*
- **Why it's in the easy-wins batch:** your timeline is a **scrubbable audit log**. Phase 4's client-side recorder only captures state **while the app is open** — close it and you get gaps, and it can't show anything from before the feature shipped. This small append-only table makes the timeline **durable and gap-free**, and is the natural home for the lifecycle (handoff → proposed → awaiting → executing → done). Adding it later means rebuilding the timeline's data source — so it's done up front.
- **Scope:** a new table plus one insert on every status transition. Small, but it touches the status-change paths (more than a column).
- **Change:**
  ```sql
  CREATE TABLE IF NOT EXISTS status_events (
      id            TEXT PRIMARY KEY,
      blackboard_id TEXT NOT NULL REFERENCES blackboards(id),
      handoff_id    TEXT,
      agent         TEXT,
      from_status   TEXT,
      to_status     TEXT NOT NULL,
      event_at      TEXT NOT NULL
  );
  CREATE INDEX IF NOT EXISTS idx_status_events_bb ON status_events(blackboard_id);
  CREATE INDEX IF NOT EXISTS idx_status_events_at ON status_events(event_at);
  ```
  Insert one row inside `update_blackboard_status()` (and the queue-advance path) on every transition, stamping `handoff_id` from the active envelope. Expose via `/__db`; Phase 4's recorder then **prefers this server log** and falls back to polling only for the live edge.
- **Acceptance:** every status change appends a `status_events` row; querying by `blackboard_id` returns the full ordered lifecycle; closing/reopening the app preserves history.
- **Commit:** `feat(db): append-only status_events audit log for durable timeline`

### Task H — Housekeeping (trivial, no risk)
- Remove unused `3d-force-graph` from `web/package.json`.
- Env-var the hardcoded `/Users/QTE2362/...` paths in `vite.config.ts` + `memory-reader.ts` (`VITE_MEMORY_PATH`, `VITE_AGENTS_DIR`, `VITE_OPENCODE_DB`).
- Dedupe `jarvisThemeTokens.css` `:root` ≡ `observatory.css`.
- **Schema-guard (prevents the next silent bug):** in `safeAll`, when a query fails with `no such column`/`no such table`, surface it visibly (e.g. a `__dbWarnings` array in the `/__db` payload the app can log/badge) instead of only a server-side `console.warn`. The `sections.compressed` bug was invisible precisely because the failure was swallowed.
- **Commit:** `chore(web): remove dead dep, env-var paths, dedupe theme css, surface db schema warnings`

---



Schema, status vocabulary, and the governance loop are **verified at the source** (`skills/projects/projects.py`, `skills/blackboard/blackboard.py`, `agents/*.md`). Confirm these *runtime* behaviours, which are what make Phases 2–3 show real data:
- **`specialist_queue` is populated during runs** — orchestrator calls `enqueue_specialists` / `advance_queue`; a row reaches `status='active'` for the current specialist. (Verified columns: `id, blackboard_id, agent, status, queued_at, started_at, completed_at`.)
- **`sections` is synced** — sections are written to the DB (`content` included). After Task 2.0 the web reads them correctly.
- **Status vocabulary is exact** — `blackboard.py VALID_STATUSES = {deliberating, awaiting-approval, executing, done, blocked}` matches the web byte-for-byte. No action.
- **Two-write sync (G7)** — every status change should update both the `.md` and the DB. The galaxy reads the DB; drift makes it stale.

### Changes since the protocol update (2026-06-26 23:00) — reviewed, impact noted
- **HANDOFF v1 / RESPONSE v1 envelopes** (`handoff-protocol.md`) are now mandatory on every delegation. **`handoff_id` is unique per task and would be the ideal correlation key for the timeline (Phase 4) and for threading a delegation → response → execution.** But it is **not persisted to opencode.db** — it lives only in the blackboard `.md` and chat. **Opportunity G8 (backend, optional but high-value):** add a `handoff_id TEXT` column to `sections` (and/or `specialist_queue`) and write it during sync, so the galaxy can thread events by `handoff_id` instead of inferring. Without it, Phase 4 correlates by `(blackboard_id, written_at)` — workable, just coarser.
- **RESPONSE v1 `summary:` (1–5 bullets) is the natural source for JARVIS narration (Phase 5.2)** and for a node's headline. It currently lands inside a section's `content` as envelope text. If you want clean narration without parsing markdown, consider syncing `summary` (and `blockers`) to dedicated columns — otherwise Phase 5 parses it out of `content`.
- **Worker now hard-blocks on missing preconditions** — if the Execution Plan lacks `repo_root` / `workdir` / paths or a RESPONSE v1 envelope, the worker writes `BLOCKED: …` and calls `mark_status(…, "blocked")`. **Implication for the galaxy:** `blocked` is now a *common, expected* state, not an edge case — it should be a first-class amber/red visual (Task 3.2) and a prime JARVIS-narratable / your-attention event ("the worker blocked — the plan was missing file paths").
- **Scribe → MCP memory** — orchestrator/worker now call `scribe()` / `scribe_session_summary()` writing `worked/avoided/patterns` into the memory graph. The memory layer (ambient backdrop in the galaxy) will **grow during sessions**; it's a live-ish layer now, not static. No web change required, but the memory cloud will gain nodes over time.
- **`opencode.json`: `density-mcp`, `wiz`, `playwright` set to `enabled:false`** (GPT tool-cap protection). If the galaxy ever renders MCP servers as nodes, reflect `enabled:false` as dimmed/offline. Not in current scope.

---

## Suggested PR breakdown

| PR | Contains | Risk |
|---|---|---|
| PR1 | Phase 0 + Phase 1 | low — build hygiene + render fixes |
| PR2 | Phase 2 (2.1–2.4) | medium — live wiring; reviewable as a unit |
| PR3 | Phase 3 (3.1–3.3, 3.4 optional) | medium — blackboard in scene |
| PR4 | Phase 4 | higher — new subsystem |
| PR5 | Phase 5 | higher — voice/intent |

Each PR should leave the app building (`tsc` clean) and the galaxy at least as functional as before. Do not bundle phases out of order.
