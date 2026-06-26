# BMW OpenCode Config — Project Roadmap

> **BMW INTERNAL USE ONLY**  
> Branch tracking: all active work is on feature branches. See each section for the relevant branch.  
> Last updated: 2026-06-25

---

## Summary of Completion Status

| Domain | Complete | In Progress | Pending |
|--------|----------|-------------|---------|
| Core Config (auth, models, MCPs) | ✅ Done | — | — |
| Skills Library | ✅ Done (62+) | — | agent-productivity expansion |
| Multi-Agent Architecture (Phases 1–4) | ✅ Done | — | — |
| Web Frontend (Phases 1–3.5 Step 2) | ✅ Done | Step 2.5 polish | Steps 3–4, Phase 4–6 |
| Async Dispatch (Phase 6) | — | Decision made | Implementation pending |
| Windows / WSL2 Support | Planning done | — | End-to-end testing pending |

---

## Part 1 — Multi-Agent Architecture

### Phase 1 — Blackboard Architecture + Worker Agent ✅ COMPLETE
> **Commit:** `5992413`  **Branch:** `main`

The shared working-file coordination system for multi-agent tasks.

- [x] `~/.opencode/skills/blackboard/blackboard.py` — `create()`, `append_section()`, `read()`, `mark_status()`, `is_ready_for_execution()`, `request_approval()`, `get_approval_summary()`, `is_gate_open()`, `compress_sections()`, `auto_archive_if_done()`
- [x] `~/.opencode/skills/blackboard/SKILL.md` — API reference (module-import paradigm)
- [x] Worker agent (`worker` subagent type in orchestrator) — reads blackboard, executes plan mechanically
- [x] Approval gate logic — high-stakes (>3 steps, delete/migrate/production keywords) → user approval required; low-risk → auto-approve
- [x] README sync

---

### Phase 2 — Projects DB Schema ✅ COMPLETE
> **Commit:** `56cf67e`  **Branch:** `main`

`opencode.db` extension for persistent project and blackboard tracking.

- [x] `~/.opencode/skills/projects/projects.py` — 16 functions: `create_project()`, `add_blackboard()`, `get_project()`, `list_projects()`, `check_dependencies()`, `set_approval_required()`, `approve_blackboard()`, `distil_project()`, `get_projects_pending_distillation()`, etc.
- [x] `~/.opencode/skills/projects/SKILL.md` — API reference
- [x] `opencode.db` tables: `projects`, `blackboards`, `decisions`, `conflicts`, `specialist_queue`
- [x] DB confirmed live at `~/.local/share/opencode/opencode.db`

---

### Phase 3 — Secretary as Stateful Project Coordinator ✅ COMPLETE
> **Commit:** `56cf67e`  **Branch:** `main`

Secretary subagent handles 6 modes: routing oracle (P2.5), project context check, blackboard registration, queue advancement, progress reports, conflict resolution.

- [x] Secretary agent (`secretary` subagent type in orchestrator)
- [x] Mode 1: Routing oracle — resolves ambiguous requests, returns `ROUTE TO / REASON / CONFIDENCE / CLARIFYING QUESTION`
- [x] Mode 2: Project context check — returns project name, blackboard count, prior decisions
- [x] Mode 3: Blackboard registration — writes to `opencode.db`, returns `blackboard_db_id`
- [x] Mode 4: Queue advancement — tracks specialist handoff sequence
- [x] Mode 5: Progress reports — answers "where are we?" queries
- [x] Mode 6: Conflict resolution — prior decisions → domain authority → user escalation
- [x] Orchestrator updated with full blackboard flow (Steps 0–8)

---

### Phase 4 — Approval Gates + Dependency Tracking ✅ COMPLETE
> **Branch:** `main`

- [x] `set_approval_required()` / `approve_blackboard()` in `projects.py`
- [x] `check_dependencies()` — blocks execution if upstream blackboards are not done
- [x] `compress_sections()` — reduces blackboard token footprint after execution
- [x] `auto_archive_if_done()` — moves completed blackboards to `/tmp/opencode/archived/`
- [x] Distillation workflow — `distil_project()` extracts durable patterns from completed projects
- [x] Agent-memory decay — `agent-memory` skill with `recall()` / `learn()` / `summarise_learnings()` / `decay()` (`agent_memory.py`)

---

### Phase 5 — Galaxy Projects Layer (Web Frontend) ✅ COMPLETE
> **Commit:** `1a86e8a`  **Branch:** `feat/web-frontend`

`opencode.db` data surfaced as a 4th layer in the 3D galaxy view.

- [x] `web/src/lib/db-reader.ts` — `fetchProjectsGraph()` fetches `/__db`, maps projects/blackboards/decisions/conflicts to `ForceGraphData`
- [x] `web/vite.config.ts` — `/__db` Vite bypass reads `opencode.db` directly via `better-sqlite3` (readonly, graceful on missing tables)
- [x] `GalaxyView.tsx` — accepts `layers: LayerState` as prop; Projects layer toggle shows project/blackboard nodes
- [x] Side panel moved to `left-0` with `border-r` — avoids overlap with chat drawer (`z-40`) and right-panel overlays (`z-30`)
- [x] Layer state lifted to `App.tsx` — `galaxyLayers: LayerState`, `galaxyRefreshTrigger`, `galaxyCount` state
- [x] `Projects` + `↺` buttons added to toolbar
- [x] Node count badge bottom-left

---

### Phase 6 — Async Agent Dispatch 🔲 IMPLEMENTATION PENDING
> **Decision made:** 2026-06-25  **Branch:** `feat/web-frontend` (or new `feat/async-dispatch`)  
> **Decision stored in:** Memory MCP (`Async Agent Dispatch System` entity)

**Selected approach: Option E — BMW LLM API `asyncio.gather` + `Semaphore(2)`**

Rejected alternatives:
- ❌ Option A — Plugin intercept: No `task` hook exists in OpenCode v1.17.5
- ❌ Option B — `opencode.db` message queue: Polling overhead, fragile
- ❌ Option C — Multiple OpenCode sessions: Full LLM context per session, worst token cost
- ❌ Option D — `routing-enforcer.ts` extension: File never created, no hook surface

**Implementation tasks:**

- [ ] Create `~/.opencode/skills/blackboard/parallel_dispatch.py`
  - `async def dispatch_specialists(blackboard_path, specialists, semaphore=asyncio.Semaphore(2))`
  - Each specialist call uses `bmw_advisor.py` `run_agent_advised()` — executor `claude-haiku-4-5`, advisor `claude-sonnet-4-6` (high-stakes only)
  - Retry on 429: inherit `base_delay=1.0`, `max_retries=4` exponential backoff from `reranker.py`
  - Graceful fallback: failed specialist sections marked `FAILED` in blackboard
- [ ] Update `~/.opencode/skills/blackboard/SKILL.md` — add `parallel_dispatch` API reference
- [ ] Update orchestrator (`request-orchestrator.md`) blackboard fan-out — replace sequential `task(specialist)` loop with `asyncio.run(dispatch_specialists(path, [...]))`
- [ ] Integration test against live BMW LLM API with 2-specialist scenario
- [ ] Update `README.md` Performance Metrics — before/after latency for parallel vs sequential dispatch
- [ ] Commit, README sync, merge consideration

---

## Part 2 — Web Frontend (`feat/web-frontend`)

> Full implementation notes live in `web/ROADMAP.md`. This section tracks phase-level status only.

### Phase 1 — Foundation ✅ COMPLETE
Vite + React 18 + TypeScript + TailwindCSS scaffold, chat loop, streaming tokens, BMW CI.

### Phase 2 — Core UI ✅ COMPLETE
Agent/model pickers, tool call cards, permission dialog, slash command palette, diff viewer, todo panel, cost tracker. 86/86 E2E tests passing.

### Phase 3 — Galaxy View + Voice ✅ COMPLETE
3D force-directed galaxy (`GalaxyView.tsx`), memory graph visualisation, voice input (Web Speech API), TTS playback. 12 E2E tests.

### Phase 3.5 — Galaxy Mission Control

#### Step 1 — Galaxy-first layout ✅ COMPLETE (commit `d08aa13`)
Galaxy is full-screen default; chat is a sliding drawer; session sidebar collapsible.

#### Step 2 — Live agent status ✅ COMPLETE (commit `dc54612`)
Busy sessions pulse in galaxy via emissive intensity oscillation; Mission Control badge shows real-time agent/busy count.

#### Step 2.5 — Visual polish 🔲 NEXT
> **Branch:** `feat/web-frontend` — ready to implement

- [ ] ① Soft radial constraints (`d3.forceRadial`) — subagents r=80, skills r=160
  - Add `import * as d3 from "d3-force"` at top of `GalaxyView.tsx`
  - Add `d3Force()` method to `ForceGraph3DInstance` interface
  - Add `isPrimaryAgent()` helper
  - Insert `.d3Force("radial-agents", ...)` and `.d3Force("radial-skills", ...)` in init effect **before** `.nodeLabel()`
- [ ] ② Additive glow sprites (`SpriteMaterial + AdditiveBlending`)
  - Add `makeGlowSprite(hexColor, size)` helper after `makeSkillMesh()`
  - Apply to skill meshes (child sprite in `makeSkillMesh()`)
  - Apply to memory node meshes (replace empty `Object3D` with real mesh + glow)
  - Change `nodeThreeObjectExtend` to `() => false` for all nodes
- [ ] `tsc --noEmit` clean
- [ ] Commit + update `web/ROADMAP.md` + update `opencode-dev-expert.md` Part 4

#### Step 3 — Team Inbox Watcher 🔲 PENDING
- [ ] `web/server/` — `/__team` Vite proxy reads `~/.config/opencode/team_inbox/*.jsonl`
- [ ] `lib/team-reader.ts` — `useTeamInbox()` hook
- [ ] `GalaxyView.tsx` — poll `/__team` every 5s; trigger edge particle burst on new messages
- [ ] Unread badge on agent node label

#### Step 4 — Click-to-Chat 🔲 PENDING
- [ ] Click agent node → open/focus that agent's most-recent session as chat drawer
- [ ] If no session → `createSession()` with `agent` pre-filled
- [ ] Smooth camera fly-to before drawer opens

---

### Phase 4 — Tauri Desktop App 🔲 PENDING
> Effort estimate: 1 week

- [ ] `npm create tauri-app` — wraps existing React frontend (zero React code changes)
- [ ] Menu bar integration — live session cost in menu bar icon
- [ ] `Cmd+Space`-style global hotkey to summon/dismiss window
- [ ] Tauri sidecar: starts/stops `opencode serve --port 4096` automatically on app launch/quit
- [ ] Native mic via `tauri-plugin-microphone` — upgrade from Web Speech API
- [ ] Whisper STT via Tauri command (higher quality than Web Speech API)
- [ ] Wake word detection (always-on mic when backgrounded)
- [ ] Direct SQLite reads via `tauri-plugin-sql` — bypass HTTP for analytics
- [ ] macOS `.app` bundle + DMG
- [ ] Auto-update via Tauri updater (GitHub Releases)

---

### Phase 5 (Web) — Local SQLite Project Tracker 🔲 PENDING
> Effort estimate: 1 week

Persistent "mission layer" in the galaxy — projects, tasks, and agent activity alongside ephemeral session/memory data.

- [ ] `web/data/opencode-tracker.db` — schema: `projects`, `tasks`, `agent_activity`, `knowledge_links`
- [ ] `/__db` CRUD endpoints for all four tables
- [ ] New galaxy node types: Project (gold sphere), Task (cube, colour by status)
- [ ] Tasks link to assigned agent node and parent project
- [ ] Click-to-edit panel for projects and tasks
- [ ] Inline status toggle on task nodes
- [ ] Layer toggle: "Projects" (on/off)
- [ ] Activity log feeds into galaxy edge particle density

---

## Part 3 — Platform Support

### macOS ✅ FULLY SUPPORTED
All features working. Homebrew install, Keychain credential storage, OAuth2 wrapper, auto-refresh.

### Windows (WSL2) 🔲 TESTING PENDING
> See `WINDOWS-SETUP.md` for full gap analysis.

- [x] Wrapper script (`bin/opencode-bmw-wsl2`) written
- [x] Auth diagnostic (`bin/test-opencode-auth-wsl2`) written
- [x] `.env`-based credential storage pattern documented
- [x] WSL2 mirrored networking approach documented
- [ ] End-to-end test on real Windows + WSL2 machine
- [ ] Full `WINDOWS-SETUP.md` install guide verified against real environment
- [ ] Add WSL2 Quick Start to README once tested

### Windows (Native) 📋 STRETCH GOAL
PowerShell wrapper + Windows Credential Manager. Not yet started.

### Linux 📋 UNTESTED
Should work via WSL2 path. No BMW employee has tested this end-to-end.

---

## Part 4 — Skills & Agents Backlog

### Skills to add (not yet installed)

| Skill | Source | Purpose |
|-------|--------|---------|
| `aaa-ghas-remediation` | `aaa/` namespace | Required for `/security-fix` slash command (GHAS target) |
| `aaa-wiz-remediation` | `aaa/` namespace | Required for `/security-fix` slash command (Wiz target) |

> **Note:** `/security-fix` and `/security-explain` slash commands reference these skills but they are not yet installed. Install via: `ttt skills install aaa/aaa-ghas-remediation --agent-type opencode --global`

### Agents to evaluate

| Agent | Status | Notes |
|-------|--------|-------|
| `agile-master-pi-planning` | TTT-only (not a custom agent file) | Used via `task` tool delegation; no local agent file needed |
| `agile-master-catalyst-coaching` | TTT-only | Same — delegation only |
| `presentation-builder` | TTT-only | Same — delegation only |
| `dor-agent` | TTT-only | Pairs with `dor-jira-updater` skill |

---

## Part 5 — Technical Debt / Known Issues

| Item | Priority | Notes |
|------|----------|-------|
| `memory` MCP disabled | Medium | Was enabled, now disabled — knowledge graph tools not available unless re-enabled. Intentional or oversight? |
| `feat/specialist-subagents` not merged | Low | Branch exists, not merged to `main`. Check if superseded by `feat/web-frontend`. |
| `web/ROADMAP.md` Phase 3.5 Step 2.5 | High | Implementation spec is fully written; just needs execution (next session task) |
| `opencode.db` `distillation_ready` flow | Low | Distillation prompt surfaces at session start if projects pending — needs user testing |
| `feat/opencode-dev-expert-expansion` branch | Low | Branch exists; check if work was merged or abandoned |

---

## How to Continue Work

### Next immediate task (Phase 6 or Step 2.5)

**Option A — Phase 3.5 Step 2.5 (visual polish, ~2h):**
```bash
git checkout feat/web-frontend
cd ~/.config/opencode/web
# Read GalaxyView.tsx lines 340-420 for insertion point
# Apply radial constraints + glow sprites per web/ROADMAP.md spec
npx tsc --noEmit
git commit -m "feat(web): Step 2.5 — radial constraints + additive glow sprites"
```

**Option B — Phase 6 async dispatch (~4h):**
```bash
# Create parallel_dispatch.py in blackboard skill
# Test with 2 mock specialists
# Update orchestrator fan-out path
# Commit + README sync
```

### Branch strategy reminder

| Branch | Purpose | Merge target |
|--------|---------|--------------|
| `feat/web-frontend` | Web UI (Phases 1–5, Galaxy, Tauri) | `main` (after Phase 4) |
| `feat/specialist-subagents` | Specialist agent expansion | Review before merging |
| `main` | Stable config — skills, agents, orchestrator | — |

---

*This roadmap is maintained by the `request-orchestrator` and `opencode-dev-expert` agents. Update it whenever a phase completes or a new task is identified.*
