# Build Gap Analysis — Current Repo vs. Vision

**Status:** Cross-check as of 2026-06-26 (repo @ `main`, sync `50f7080`).
**Reads against:** `JARVIS-ORCHESTRATION-MODEL.md` + `GALAXY-VISUAL-LANGUAGE.md`.
**Purpose:** Hold the target state up against what's actually built, so the work is concrete.

The headline: **you are much closer than a feature list would suggest.** The biggest pieces of the vision already exist in the data tier — they're just not wired into the scene. Most of the remaining work is *connection*, not *creation*.

Legend: ✅ done · 🟡 partial / orphaned · ❌ missing · ⛔ blocker

---

## 0. Blockers (must clear before anything renders)

| # | Item | State | Notes |
|---|---|---|---|
| B1 | `npm install` not run | ⛔ | Every dependency shows MISSING; 50+ TS errors are all cascading "cannot find module 'react'". Nothing builds until this runs. |
| B2 | `src/App.tsx` is dead code | ⛔ | Pre-JARVIS UI; nothing imports it (main.tsx boots `JarvisShell`). Its TS errors block the typecheck. Delete or move to `src/_archive/`. |

---

## 1. The coordination model (backend governance) — ALREADY BUILT

**Verified against `agents/*.md`.** The submit-for-review / conflict-check / approval-gate / blackboard-as-truth governance loop you described is **fully implemented** in the opencode agent backend. It is *not* missing — it just lives in a different role structure than first assumed.

### Who actually owns coordination (important correction)
The **project-manager agent is NOT the scrum master.** It is a *domain specialist* for Agile/Jira/sprints (PI planning, PR triage, release notes) — one expert among many. The coordinator role you described is implemented by a **trio**:

| Your described role | Actually implemented as | Evidence |
|---|---|---|
| "PM decomposes request into workable blocks" | **request-orchestrator** creates a blackboard and delegates | `request-orchestrator.md` → "Blackboard Coordination", Steps 0–2 |
| "PM assigns subagents" | **request-orchestrator** sequential delegation + **secretary** queue | `enqueue_specialists` / `advance_queue` (secretary Mode 3/4) |
| "Agents propose changes + next steps before acting" | Specialists write `## <Domain> Analysis` + `## Proposed Changes` sections | orchestrator Step 2 instructions to each specialist |
| "Submit to PM before action" | Submit to **orchestrator/secretary**; **worker** enforces it | `worker.md` Step 0 `is_gate_open()` gate check |
| "Check conflicts between tasks" | orchestrator Step 3 conflict scan + **secretary** Mode 6 | `record_conflict_resolution` |
| "Conflict → my approval" | secretary Mode 6 `BASIS: user-escalation` + Step 5 high-stakes gate waits for `approved`/`cancel` | `request_approval` / `approve_blackboard` |
| "Blackboard = source of truth" | Blackboard **.md files** (`/tmp/opencode/`) + **opencode.db** state | `blackboard.py` + `projects.py` |
| "Track project status" | **secretary** + `projects.py` over opencode.db | secretary Modes 2/5 |

So: **orchestrator = decomposer/delegator/gatekeeper, secretary = state coordinator (opencode.db), worker = mechanical executor with a hard approval gate, specialists = domain experts that post proposals.** The governance you wanted is real and enforced (the worker literally refuses to run unless status is `executing`).

| Capability | State | Evidence |
|---|---|---|
| Orchestrator + specialists + secretary + worker | ✅ | All present in `agents/`. |
| Decompose → assign → propose → review → gate → execute | ✅ | Encoded in `request-orchestrator.md` Blackboard Coordination + `worker.md` gate. |
| Submit-for-review before action | ✅ | Worker `is_gate_open()` Step 0 — unconditional, can't be skipped even in `/beast-mode`. |
| Conflict → user escalation | ✅ | secretary Mode 6 + high-stakes approval gate. |
| Blackboard durable state | ✅ | `.md` files + opencode.db via `projects.py`. |

### The web ↔ backend seam — VERIFIED against `docs/PROJECTS-DB-AGENT-BRIEFING.md`
The five seams are now checked against the real schema. Most are already correct.

| # | Gap | Verdict | Detail |
|---|---|---|---|
| G1 | Schema match | ✅ **RESOLVED — exact match** | Real tables `projects / blackboards / decisions / conflicts / sections` carry every column the web `/__db` selects. The app was built against this schema. No change needed. |
| G2 | Status vocabulary | ✅ **RESOLVED — exact match** | Real blackboard statuses are exactly `deliberating / awaiting-approval / executing / done / blocked` — hyphenated, matching `db-reader`'s `blackboardColourForStatus` and the top-bar map byte-for-byte. Amber (`awaiting-approval`/`deliberating`) and bright (`executing`) will fire correctly. No change needed. |
| G3 | `sections` populated? | ✅ **RESOLVED, with a refinement** | `sections` IS populated and **persists** (current-state upsert: one row per `(board, section_name)`, `agent` = latest writer, fresh `written_at`). So `deriveAgentStatuses` works. **But** "active" there means *"has a section on a non-done board"* — coarser than *"executing right now."* See the new finding G6. |
| G4 | Blackboard content exposed? | ✅ **MOSTLY RESOLVED** | The section **body lives in `sections.content` in opencode.db** — the web just doesn't `SELECT` it yet. Add `content` to the `/__db` sections query and the galaxy side-panel can show analysis / proposed changes / execution plan **without** reading the `.md`. Caveat: when a board hits `done`, `compress_sections()` sets `compressed=1` on everything except `Execution Plan` + `Execution Result`, so full history of a *completed* board still needs the `.md` at `file_path`. |
| G5 | Sequential vs async | ✅ **CONFIRMED** | Execution is a sequential queue (`specialist_queue`: `pending → active → done`), one `active` at a time. Galaxy should render a **baton-pass queue**, not parallel tethers, until a parallel executor replaces the `task` tool. |

### New finding from the schema — the precise "who's working now" signal
| # | Finding | Why it matters |
|---|---|---|
| G6 | **The web doesn't read `specialist_queue` at all.** | This table is the *exact* live signal: `status = 'active'` is the one specialist currently being delegated to, with `started_at` / `completed_at` and queue order. It's strictly better than deriving activity from `sections` (which only tells you who has *contributed* to an open board). **For accurate lit-tethers and the queue visual, read `specialist_queue` — add it to `/__db` (vite.config) and consume `status='active'` in the scene.** This is the single highest-value data addition for the live view. |
| G7 | **Two-write sync gotcha.** `mark_status()` updates only the `.md`; `update_blackboard_status()` updates only the DB. The orchestrator must call **both**. | The web reads the **DB**. If the two ever drift (file updated, DB not), the galaxy shows the stale DB value. Not a web bug — a backend-discipline risk worth a sanity check. |

**Bottom line on the seam:** G1 and G2 need *nothing*. G3 works as-is. The real, small, high-value work is **G6 (read `specialist_queue`)** for precise live state, and optionally **G4 (`SELECT content`)** to show section bodies in-panel.

---

## 2. JARVIS conversational behaviour

| Intent | State | Evidence / gap |
|---|---|---|
| Voice + text input | ✅ | `InputBar` (text + PTT), `VoiceController` (mlx-whisper STT, single instance, correctly avoids Web Speech). |
| TTS responses | ✅ | `TtsPipeline` / `TtsLocal` / `TtsBmw`; vite `say -o` path fixed. |
| Orb state machine (IDLE/LISTENING/THINKING/SPEAKING) | ✅ | `SessionContext` + `Canvas2DOrb` + `VoxCorona`. |
| Narrate **response headlines** | 🟡 | TTS speaks assistant text, but there's no *summarization to a headline* — it would read full responses. Need a "summarize to one line" step. |
| **Mute narration** (separate from muting all TTS) | ❌ | `settingsStore` has `ttsEnabled` (all-or-nothing) only. No distinct "narration off, but still answer my direct questions" toggle. |
| Thousand-foot status ("are we on track?") | ❌ | No intent that reads board state and produces a sprint-level summary. |
| Query an agent's live status | 🟡 | The *data* exists (`deriveAgentStatuses` → active/idle + task). No **voice intent** that maps "what's agent X doing" to a spoken board answer. |
| Amend scope mid-project ("also add Y") | ❌ | No intent to route an amendment to the PM as a new ticket. |
| Conflict → ask for your approval | 🟡 | `PermissionDialog` exists for opencode permissions (allow/deny), which is the right *mechanism*. Not yet wired to **blackboard conflicts** specifically. |
| Interrupt mid-task | 🟡 | `abortSession()` exists in the session layer. Not yet triggered by *voice barge-in* (start speaking → abort). |

**Takeaway:** the voice/orb plumbing is solid. The gap is an **intent layer** — recognizing query / amend / status / mute / interrupt and mapping them to board actions. That's new, but it sits cleanly on top of what's there.

---

## 3. The galaxy — data tier

**This is the big surprise, and it's good news.**

| Layer | State | Evidence |
|---|---|---|
| Agent + skill graph | ✅ | `agent-reader.ts` → `/__agents`; per-node colour (BMW blue / purple / green) already set. |
| MCP memory graph | ✅ | `memory-reader.ts` → `/__memory`; parsed to nodes/links. |
| **Blackboard graph (projects/tickets/decisions/conflicts)** | ✅🟡 | **`db-reader.ts` already converts the full snapshot** — including blackboard status colours and **cross-task decision edges** — into renderable graph data. **But `GalaxyView` never imports `fetchProjectsGraph`.** It's built and orphaned. |
| Per-agent active/idle from blackboard | ✅🟡 | `deriveAgentStatuses()` derives status from `sections` on non-done boards — **blackboard-as-truth, already** (schema verified). Feeds the top-bar badge, **not** the galaxy. Coarser than `specialist_queue` (see below). |
| `specialist_queue` (precise "active now" + order) | ❌ | **Not read by `/__db` at all.** The exact live signal (`status='active'`) and baton-pass order live here. Adding it (G6) is the highest-value data change for the live view. |

**Takeaway:** the single most important layer for the vision — the blackboard rendered in the scene — is **written and tested in `db-reader.ts`, schema-verified, and simply not called by `GalaxyView`.** The gap here is one import + a build step in the scene (plus reading `specialist_queue`), not a new subsystem.

---

## 4. The galaxy — rendering / visual language

This is where the real work is. `GalaxyView.tsx` is a **static, fetch-once orbital scene** today.

| Visual rule (from spec) | State | Gap |
|---|---|---|
| Orbital metaphor (sun/planets/tiers) | ✅ | Deterministic orbital layout, good port. |
| Colour by role (blue primary / purple sub) | ❌ | Hardcodes `const col = C.sub` for every planet — ignores `sa.color` from `agent-reader`. **All planets render identical purple.** |
| Two-tier brightness (active vs dormant) | ❌ | No concept of active set. Everything renders equally bright. |
| Lit tether = working | ❌ | Tethers are static low-opacity lines; no binding to agent status. |
| Tether/planet states (proposing/exec/blocked) | ❌ | Not represented. |
| Amber = pending decision | ❌ | Not represented in scene (colours exist in `db-reader` data but data isn't rendered). |
| Conflict flare between planets | 🟡 | `db-reader` emits conflict nodes + cross edges; scene doesn't draw them. |
| Blackboard tickets as travelling bodies | ❌ | Not represented (data available). |
| Live updates (reacts to SSE/board) | ❌ | Fetches once on mount; never refreshes. `refreshTrigger` prop accepted as `_refreshTrigger` (deliberately ignored). |
| Timeline scrubber | ❌ | None. |
| Playback stays put + `● LIVE` indicator | ❌ | None. |
| Spotlight on query | ❌ | None. |
| MCP memory as ambient backdrop | 🟡 | Memory nodes render, but at full brightness, not dimmed-ambient. |

### Known rendering bugs (prerequisites, from prior review)
| Bug | State | Fix |
|---|---|---|
| Blank render when panel opens | ❌ | `window.addEventListener("resize")` doesn't fire on CSS-transform open. Use `ResizeObserver` on `el` + `setTimeout(resize, 360)` matching the drawer transition. |
| Layer toggles dead after first render | ❌ | `useEffect([layers])` is empty ("handled below"); groups only set in `loadAndBuild`. Store `G` in a `useRef`, set visibility in the layers effect. |
| No touch/pointer support | ❌ | Mouse events only. Add pointer events + `setPointerCapture` + pinch. |
| Wheel zoom too aggressive | 🟡 | `e.deltaY * 0.4`; use proportional `radius*(1±0.08)`. |

---

## 5. Live wiring (the "make it JARVIS" gap)

The live nervous system exists and **stops one inch short of the galaxy.**

| Wire | State | Gap |
|---|---|---|
| SSE singleton stream | ✅ | `useSSE` — clean singleton EventSource, backoff. |
| `SessionContext` computes `busyAgentNames` + `agentStatuses` | ✅ | Already derived and fed to the top bar. |
| `GalaxyPanel` passes live props to `GalaxyView` | ❌ | Renders `<GalaxyView />` with **no props at all.** |
| `GalaxyView` consumes `busyAgentNames` | ❌ | Accepts it as `_busyAgentNames` — **deliberately ignored.** |
| `/__db` exposes `specialist_queue` | ❌ | Not selected in `buildDbSnapshot` (vite.config). The precise live signal isn't reaching the app at all (G6). |
| Always-on recorder (time-series of board snapshots) | ❌ | Doesn't exist. Needed for scrubbing while panel is closed (`MODEL.md` §7). |
| Lazy renderer reads recorder history on open | ❌ | Galaxy mounts via `{isOpen && <GalaxyView/>}` but has no history to read. |

**Takeaway:** connecting `SessionContext` → `GalaxyPanel` → `GalaxyView` (and deleting the underscores) is the **highest-leverage change in the project** — it's mostly prop-passing on top of data that's already flowing.

---

## 6. Housekeeping

| Item | State | Fix |
|---|---|---|
| `3d-force-graph` dependency | 🟡 | ~900KB, in `package.json`, unused after orbital port. Remove. |
| Hardcoded `/Users/QTE2362/...` paths | 🟡 | In `vite.config.ts` + `memory-reader.ts`. Move to env vars (`VITE_MEMORY_PATH`, `VITE_AGENTS_DIR`, `VITE_OPENCODE_DB`). |
| `jarvisThemeTokens.css` `:root` ≡ `observatory.css` | 🟡 | Byte-identical duplication. Dedupe. |
| Stale-closure deps in `GalaxyView` main effect | 🟡 | `onCountChange` / `layers` missing from deps; wrap `onCountChange` in `useCallback` upstream. |

---

## 7. Recommended sequence (next session, when usage resets)

Each step lists the **file(s)** it touches and **why it's ordered there**. Steps within a phase are safe to do in order; phases are strictly dependent (don't start a phase until the prior one renders).

### Phase 0 — Foundation *(settled, no debate — nothing builds without it)*
| # | Step | File(s) | Note |
|---|---|---|---|
| 0.1 | `npm install` | `web/` | Clears all 50+ "cannot find module" TS errors. |
| 0.2 | Delete/relocate dead `App.tsx` | `web/src/App.tsx` → `src/_archive/` or removed | `main.tsx` boots `JarvisShell`; `App.tsx` is unused and its errors block typecheck. |

### Phase 1 — Make it render correctly *(prerequisites; the scene must be visible & legible before live data means anything)*
| # | Step | File(s) | Note |
|---|---|---|---|
| 1.1 | ResizeObserver fix (blank render) | `GalaxyView.tsx` | Replace `window.addEventListener("resize")` with `ResizeObserver` on `el`; add `setTimeout(resize, 360)` to match the drawer transition. |
| 1.2 | Colour-from-data | `GalaxyView.tsx` | Read `sa.color` (BMW blue primary / purple sub) instead of hardcoded `C.sub`. This is the language that distinguishes orchestrator from subagents. |
| 1.3 | Layer-toggle reactivity | `GalaxyView.tsx` | Store `G` groups in a `useRef`; set visibility in the `[layers]` effect. |
| 1.4 | Touch/pointer + gentler zoom | `GalaxyView.tsx` | Pointer events + `setPointerCapture` + pinch; proportional wheel `radius*(1±0.08)`. *(Polish — can trail 1.1–1.3.)* |

### Phase 2 — Make it live *(the JARVIS moment — connect data that's already flowing)*
| # | Step | File(s) | Note |
|---|---|---|---|
| 2.1 | Pass live props down | `GalaxyPanel.tsx` → `GalaxyView.tsx` | `GalaxyPanel` currently renders `<GalaxyView/>` with no props. Pass `busyAgentNames` / `agentStatuses` from `SessionContext`; stop ignoring `_busyAgentNames`. |
| 2.2 | **Add `specialist_queue` to `/__db`** | `vite.config.ts` (`buildDbSnapshot`) + `db-reader.ts` | **G6 — highest-value data change.** `SELECT id, blackboard_id, agent, status, started_at, completed_at FROM specialist_queue`. Expose it in the snapshot type. This is the precise "who's executing now" + queue-order signal. |
| 2.3 | Lit-tether binding | `GalaxyView.tsx` | Tether brightness ← `specialist_queue.status === 'active'` (fallback: `deriveAgentStatuses`). One lit tether at a time (sequential — G5). |
| 2.4 | Two-tier brightness | `GalaxyView.tsx` | Active set (in queue / on an open board) bright; dormant set dimmed. |

### Phase 3 — Wire the blackboard into the scene *(easier than first thought — `db-reader` is built & schema-verified)*
| # | Step | File(s) | Note |
|---|---|---|---|
| 3.1 | Render the blackboard graph | `GalaxyView.tsx` | Call `fetchProjectsGraph()` (already in `db-reader.ts`, schema verified ✅) alongside the agent/memory fetches; build the project/blackboard/decision/conflict nodes. |
| 3.2 | Status → visual mapping | `GalaxyView.tsx` | `executing`→bright, `awaiting-approval`/`deliberating`→amber, `blocked`→amber/red, `done`→fade. Strings already match (G2). |
| 3.3 | Conflict flares between planets | `GalaxyView.tsx` | Draw `conflicts` (agent_a ↔ agent_b) as amber inter-planet flares; `db-reader` already emits the nodes/edges. |
| 3.4 | *(optional)* Section bodies in side-panel | `vite.config.ts` + `db-reader.ts` + `GalaxyView.tsx` | **G4** — add `content` to the `sections` `SELECT` to show analysis / proposed changes / execution plan in-panel. Completed-board history (post-compression) still needs the `.md` at `file_path`. |

### Phase 4 — Timeline *(the one genuinely new subsystem)*
| # | Step | File(s) | Note |
|---|---|---|---|
| 4.1 | Always-on recorder | new `useBoardRecorder` hook / store (e.g. `web/src/jarvis/galaxy/recorder.ts`) | Subscribe to SSE + poll `/__db` from app start; keep a timestamped time-series of board snapshots. Runs whether or not the panel is open (`MODEL.md` §7). |
| 4.2 | Renderer reads history + scrubber | `GalaxyView.tsx` + new scrubber component | On open, read the recorder's history so the full timeline is scrubbable; add the scrubber UI; playback-stays-put + `● LIVE` indicator. |

### Phase 5 — Conversational intents *(JARVIS as chief of staff)*
| # | Step | File(s) | Note |
|---|---|---|---|
| 5.1 | Narration mute toggle | `settingsStore.ts` (+ Settings panel + a voice command) | New flag distinct from `ttsEnabled` (which mutes *all* TTS). Mute narration but keep answering direct questions. |
| 5.2 | Status-query + thousand-foot-summary intents | voice/intent layer (near `VoiceController.tsx`) | "What's agent X doing?" / "Are we on track?" → read board (`specialist_queue` + `blackboards`) → speak. May spotlight a planet. |
| 5.3 | Scope-amend + interrupt | intent layer + `abortSession` (exists) | "Also add Y" → route to orchestrator as a new ticket; voice barge-in → `abortSession()`. |

### Phase 6 — Memory architecture *(new; depends on orchestration + blackboard contracts)*
| # | Step | File(s) | Note |
|---|---|---|---|
| 6.1 | Stand up memory v2 daemon/store | `skills/memory-daemon/` | Local-first memory store with SQLite + vector index; deterministic placement. |
| 6.2 | Route memory writes/recall through daemon | `skills/agent-memory/`, `memory-schema.md` | Keep old APIs as shims; do not let agents choose entity placement. |
| 6.3 | Add tiering + migration | `skills/memory-daemon/` | Hot/warm/cold tiers, decay, and consolidation for scale. |
| 6.4 | Add optional cloud fallback | `skills/memory-daemon/` | Make replication opt-in and preserve local-only paths structurally. |

### Backend track *(verify, in parallel — but mostly already confirmed)*
- ✅ Governance loop, schema, and status strings are **verified** (`docs/PROJECTS-DB-AGENT-BRIEFING.md`). No change needed for the galaxy to read real data.
- 🟡 **G3/G6 runtime check:** confirm the orchestrator is actually calling `sync_blackboard_sections()` *and* populating `specialist_queue` (`enqueue_specialists` / `advance_queue`) during real runs — the schema supports it; verify it's wired in live sessions.
- 🟡 **G7 sync discipline:** ensure every status transition calls **both** `mark_status()` (file) and `update_blackboard_status()` (DB), since the galaxy reads the DB.
- 🟡 **Memory path check:** if memory v2 lands, verify all scribe / recall paths are routed through the daemon and that `memory.jsonl` is only a backward-compatibility fallback during migration.

### Housekeeping *(any time)*
- Remove unused `3d-force-graph` dep · env-var the `/Users/QTE2362/...` paths · dedupe `jarvisThemeTokens.css` ≡ `observatory.css` · fix stale-closure deps in `GalaxyView`.

---

## 8. One-paragraph summary

The voice/orb/session/SSE foundation is **done and solid**, the multi-agent **governance loop is built and enforced** in the agent backend (orchestrator decomposes → specialists propose → worker executes only behind an approval gate), and the **opencode.db schema, status vocabulary, and `sections` population are all verified to match** what the web expects. The blackboard is **fully modelled in `db-reader.ts` and orphaned** — never called by `GalaxyView` — and the galaxy itself is a **static snapshot** that ignores the live props already handed to its panel. So this isn't "build the vision from scratch": it's **clear two blockers, fix a few render bugs, pass props that already exist, read one table you're not reading yet (`specialist_queue`), and call a converter that's already written.** The only genuinely new subsystems are the **always-on recorder + timeline scrubber** and the **conversational intent layer** (mute / query / amend / interrupt). Everything else is wiring what you've already built.
