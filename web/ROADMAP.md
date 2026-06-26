# BMW OpenCode Web Frontend — Roadmap

Branch: `feat/web-frontend`  
Started: 2026-06-25  
Stack: React 18 + TypeScript + Vite + CSS variables + Zustand  
Target: Tauri `.app` wrapper in Phase J4

---

## JARVIS Shell — Active Phases

> The JARVIS shell replaced the Galaxy-first layout as the primary UI.
> Galaxy becomes Panel #1 inside JARVIS in Phase J3.
> All JARVIS work lives on `feat/web-frontend`. Legacy Galaxy phases below are preserved for reference.

### Phase J1 — JARVIS Shell ✅ COMPLETE (commits 8818d3f + 8e9ecd1)

- [x] `JarvisShell.tsx` + `JarvisShell.css` — root shell with orb, chat, InputBar
- [x] 7-theme system — `themeStore.ts`, `initTheme()`, CSS `data-jarvis-theme` tokens
  - Themes: `observatory`, `cel-shade`, `blueprint`, `synthwave`, `forge`, `black-ice`, `chrome`
- [x] Orb system — `OrbContainer`, `Canvas2DOrb` (SVG gyroscope rings + Canvas 2D particle field)
  - States: `IDLE`, `LISTENING`, `THINKING`, `SPEAKING`, `ERROR`
- [x] `SessionContext.tsx` — all session/orb/message state; `sendMessage`, `setOrbState`, `abortSession`
- [x] `ActivityModal.tsx` — tool-call step display, 15s auto-dismiss, hover-pause countdown
- [x] `InputBar.tsx` — textarea + PTT mic button + send/abort; Space-PTT, ⌘⇧Space toggle
- [x] `SttBridge.ts` — Phase 1 webspeech stub (upgraded in J2)
- [x] `src/main.tsx` updated — boots `SessionProvider` + `JarvisShell`; `App.tsx` preserved as Panel #1 candidate

**Build:** 0 TS errors, 240 modules, 303 KB JS / 62 KB CSS

---

### Phase J2 — Voice Pipeline ✅ COMPLETE (commits 6e9ed7d + f1effef + 7259793)

#### TTS (JARVIS speaks back)

- [x] `TtsLocal.ts` — POST `/api/tts-local` → Vite middleware shells `say -v Daniel -r 180` → `.aiff` blob
- [x] `TtsBmw.ts` — POST `/api/audio/speech` (BMW Audio TTS API) → streaming MP3 blob
- [x] `TtsPipeline.ts` (`useTtsPipeline`) — routes ≤120 chars → TtsLocal, >120 → TtsBmw; strips markdown
- [x] `vite.config.ts` — `ttsLocalPlugin` inline middleware (`execFileSync say`, no shell injection)
- [x] `scripts/tts-server.mjs` — standalone reference copy of TTS middleware

#### STT (JARVIS listens)

> **BMW network constraint:** Web Speech API streams audio to Google's cloud endpoint
> (`wss://speech.googleapis.com`), which is **blocked on BMW corporate/VPN networks** and
> returns a browser `network` error. Web Speech is never used as a fallback on BMW network.

- [x] `SttBridge.ts` upgraded:
  - `mode: 'none'` — PTT cleanly disabled (default when no sidecar running)
  - `mode: 'mlxwhisper'` — `MediaRecorder` + WebSocket to `ws://localhost:5001/ws/transcribe`, 250 ms chunks
  - `mode: 'webspeech'` — kept for local dev only; translates raw error codes (`network`, `not-allowed`, `no-speech`) into readable messages
- [x] `scripts/whisper-sidecar.py` — FastAPI + uvicorn WebSocket STT bridge:
  - Receives WebM/Opus chunks from browser → `ffmpeg` → WAV 16 kHz → `mlx_whisper.transcribe()`
  - Runs entirely on-device (Apple Silicon MLX). Audio never leaves the machine.
  - Self-installs deps into `.venv-whisper/` on first run
  - Health endpoint: `GET http://localhost:5001/health`

#### Voice Setup (required for mic button)

```bash
# Prerequisites
brew install ffmpeg

# One-time: install mlx-whisper + FastAPI into .venv-whisper/ (~1.5 GB model download)
cd ~/.config/opencode/web
python3 scripts/whisper-sidecar.py --setup

# Start before using JARVIS voice (keep terminal open)
python3 scripts/whisper-sidecar.py
# Serving on ws://localhost:5001

# Optional: custom model
python3 scripts/whisper-sidecar.py --model mlx-community/whisper-small-mlx
```

**Startup probe behaviour:**
| State | Toast | Mic button |
|-------|-------|-----------|
| Sidecar running | ✅ "mlx-whisper active — voice stays on device" | Enabled |
| Sidecar not running | ⚠ "Voice unavailable — run: python scripts/whisper-sidecar.py" (10 s) | Disabled (greyed, tooltip with command) |

#### Orchestration & toasts

- [x] `VoiceController.tsx` — transparent provider wrapper; the ONE `useSttBridge` call in the app
  - Probes `localhost:5001/health` on mount; switches to `mlxwhisper` if reachable
  - `session.idle` SSE → speaks last assistant message via TTS pipeline
  - PTT stop → sends transcript buffer as message → orb → `THINKING`
  - New busy turn → `tts.stop()` (mid-sentence interrupt)
- [x] `SttContext.tsx` — React context publishing the single `SttBridgeResult`; prevents duplicate recognition instances
- [x] `toastStore.ts` — Zustand queue, max 4, 6 s auto-dismiss, rAF countdown, hover-pause
- [x] `ToastLayer.tsx` + `ToastLayer.css` — fixed top-right stack, level icons, progress bar, glassmorphic surface

**Build:** 0 TS errors, 248 modules, 314 KB JS / 65 KB CSS

---

### Phase J3 — Panels + Three.js Corona ✅ COMPLETE (commit c5e2b2e)

- [x] **Panel system** — `panelStore.ts` (Zustand), `PanelLayer.tsx/.css`
  - Slide-in drawer from right; backdrop blur + click-to-close; Escape key; one panel at a time
  - CSS: toggle switch, model pill selector, section labels, settings rows
- [x] **Galaxy Panel #1** — `GalaxyPanel.tsx` wraps `GalaxyView` inside PanelLayer `'galaxy'` (540 px)
  - Top-bar graph icon button → `togglePanel('galaxy')`; `.active` state on button
- [x] **Settings Panel #2** — `SettingsPanel.tsx`
  - TTS on/off toggle (Zustand `settingsStore` + localStorage persist)
  - STT model pill selector (`whisper-small-mlx` / `distil-whisper-large-v3`)
  - Active theme display; keyboard shortcuts reference
  - Top-bar settings gear button now live (was disabled in J1/J2)
- [x] **VoxCorona.tsx** — Three.js particle corona layered over Canvas2DOrb
  - 280 particles on torus (R=1.0, r=0.22); additive blending; transparent WebGL canvas
  - State-driven: IDLE=slow drift, LISTENING=scatter+rapid pulse, SPEAKING=medium pulse, THINKING=tight rotation
  - `setPixelRatio(dpr)` retina-crisp; RAF loop; full dispose on unmount
- [x] `settingsStore.ts` — TTS/STT prefs persist to `localStorage`

**Build:** 0 TS errors, 658 modules, 1.7 MB JS (Three.js + 3d-force-graph) / 70 KB CSS

---

### Phase J4 — Tauri Desktop App 🔲 Pending

- [ ] Tauri wrapper — macOS `.app` bundle
- [ ] Auto-start `opencode serve` on app launch (Tauri sidecar command)
- [ ] **Auto-start whisper sidecar on app launch** — `scripts/whisper-sidecar.py` must be
      initialized before the frontend loads so PTT is ready immediately; use Tauri's
      `tauri::async_runtime::spawn` + `tauri-plugin-shell` `sidecar()` API; probe
      `localhost:5001/health` in the frontend and retry until ready (max ~10 s) rather
      than assuming instant availability; bundle the `.venv-whisper/` env or use a
      compiled Rust binary to avoid Python startup latency
- [ ] Native mic option via `tauri-plugin-microphone` (evaluate vs keeping the sidecar WebSocket approach)

---

## Validated API Facts (do not re-research)

- OpenCode HTTP server: `opencode serve --port 4096 --hostname 127.0.0.1`
- **CORS is open by default** — no `--cors` flag needed, any localhost origin works
- `POST /session/{id}/prompt_async` → 204 immediately, response arrives via SSE
- `GET /event` → SSE stream, `Content-Type: text/event-stream`
- Memory graph file: `~/.npm/_npx/15b07286cbcc3329/node_modules/@modelcontextprotocol/server-memory/dist/memory.jsonl`
- Agent shape: `{ name, description, mode, color, hidden, model, ... }` — key is `name` not `id`
- step-finish part carries `{ tokens: { total, input, output, cache }, cost }` — live per-turn cost

### SSE Event Lifecycle (one prompt)
```
server.connected
message.part.updated        type: "text"        user message echo
session.status              { type: "busy" }
message.part.updated        type: "step-start"
message.part.updated        type: "reasoning"   internal monologue
message.part.updated        type: "tool"        tool call (build/general agent)
                            { tool, callID, state: { status, input, output, title } }
message.part.delta          delta: "<token>"    🔥 streaming token
message.part.updated        type: "text"        full snapshot
message.part.updated        type: "step-finish" { tokens, cost }
session.status              { type: "idle" }
session.idle                                    🏁 done
server.heartbeat                                keepalive
```

### Tool part shape (1.17.5)
```json
{
  "type": "tool",
  "tool": "bash",
  "callID": "toolu_...",
  "state": {
    "status": "completed",
    "input": { "command": "echo hi", "description": "Echo hi" },
    "output": "hi\n",
    "title": "Echo hi"
  }
}
```

### Two streaming strategies
- `message.part.delta` → raw token deltas (fastest, word-by-word display)
- `message.part.updated` where `part.type === "text"` → full text snapshot per token (simpler)

---

## Phase 1 — Foundation 🏗️
> Goal: Working chat in the browser, streaming tokens, BMW CI styling.  
> Effort: 1 day

- [ ] Scaffold `web/` — Vite + React 18 + TypeScript + TailwindCSS
- [ ] `lib/opencode-client.ts` — thin fetch wrapper around OpenCode REST API
- [x] `hooks/useSSE.ts` — EventSource hook with auto-reconnect + session filtering
- [x] `hooks/useSession.ts` — session CRUD (list, create, delete, update title)
- [x] `hooks/useMessages.ts` — message list + streaming assembly from SSE deltas
- [x] `components/SessionSidebar.tsx` — list sessions, create new, switch active
- [x] `components/ChatThread.tsx` — render messages + parts (text, tool calls)
- [x] `components/PromptInput.tsx` — textarea + send button + abort button
- [x] `components/StreamingText.tsx` — assembles delta stream into live text
- [x] `components/CostBadge.tsx` — per-turn cost from step-finish event
- [x] BMW CI colours + typography (Tailwind theme config)
- [x] `bin/opencode-serve` — wrapper script to start `opencode serve --port 4096`

**Entry point files:**
```
web/
  src/
    App.tsx
    main.tsx
    components/
    hooks/
    lib/
  vite.config.ts      ← no proxy needed (CORS open), but add anyway for clean URLs
  tailwind.config.ts
  tsconfig.json
  package.json
  index.html
  .env.local          ← VITE_OPENCODE_PORT=4096 (gitignored)
  .gitignore
```

**Acceptance criteria:**
- `cd web && npm run dev` → browser opens
- Can create a session, type a prompt, see tokens stream in real-time
- Session list shows all historical sessions with cost
- Abort button stops generation mid-stream

---

## Phase 2 — Core UI Features ✅ COMPLETE (2026-06-25)
> Goal: Feature parity with the TUI for daily use.  
> Effort: 3–5 days — **86/86 E2E tests passing** (98 total across Phases 1–3)

- [x] `components/AgentPicker.tsx` — dropdown from `GET /agent`, filters `mode: primary`
- [x] `components/ModelPicker.tsx` — from `GET /provider`, grouped by provider with cost
- [x] `components/ToolCallCard.tsx` — tool name, input JSON, output, status (real `type=tool` API shape)
- [x] `components/PermissionDialog.tsx` — responds to `permission.v2.asked` SSE event via POST
- [x] `components/SlashCommandPalette.tsx` — `/` triggers palette from `GET /command` (67 commands)
- [x] `components/DiffViewer.tsx` — syntax-highlighted patch from `GET /session/{id}/diff`
- [x] `components/TodoPanel.tsx` — real-time todo list from `GET /session/{id}/todo` + `EventTodoUpdated`
- [x] `components/CostTracker.tsx` — running session cost, daily total, monthly total
- [x] hooks: `useAgents`, `useProviders`, `usePermissions`, `useTodos`, `useCommands`
- [x] Keyboard shortcuts (send on Cmd+Enter, abort on Escape)
- [x] `playwright.config.ts` global timeout=120s (covers beforeAll LLM calls)
- [x] E2E: 07-agent-picker (7), 08-model-picker (8), 09-slash-commands (8), 10-right-panels (13), 11-tool-calls (4)

**Key learnings:**
- Real API emits `type: "tool"` (not `"tool-invocation"`) with `{ tool, callID, state: { status, input, output } }`
- `build` agent reliably calls bash tools; `request-orchestrator` answers prompts as text
- `test.describe.configure({ timeout })` does NOT affect `beforeAll` — must use global `timeout` in config
- `beforeAll` LLM setup: use API polling (`sendAndWaitForToolCall`) not browser UI for reliability

---

## Phase 3 — Galaxy View + Voice 🌌🎤 ✅ COMPLETE (2026-06-25)
> Goal: Memory graph visualisation + voice interaction.  
> Effort: 1 week — **12 E2E tests written (7 galaxy + 5 voice)**  
> Phase 3 commit: pending

### Memory Galaxy
- [x] Install `3d-force-graph` + `three.js`
- [x] `lib/memory-reader.ts` — reads `memory.jsonl`, parses entities + relations
- [x] `components/GalaxyView.tsx` — 3D force-directed graph
  - Entity type → node colour mapping
  - Relation type → edge colour + thickness
  - Click node → slide-in observation panel
  - Camera fly-to on search/filter
  - Auto-categorised clusters by `entityType`
- [x] Galaxy panel toggle (sidebar icon or keyboard shortcut)
- [x] Real-time update when memory changes (watch `memory.jsonl` via polling or inotify)

**Node colour map (starting point):**
```
Agent          →  BMW Blue    #1c69d4
Skill          →  Green       #22c55e
Project        →  Orange      #f97316
KnowledgeBase  →  Purple      #a855f7
Offering       →  Teal        #14b8a6
feature        →  Yellow      #eab308
Artifact       →  Pink        #ec4899
(default)      →  Grey        #6b7280
```

### Voice
- [x] `hooks/useVoice.ts` — Web Speech API STT (5 lines, works in Edge)
- [x] `components/VoiceButton.tsx` — mic button, pulse animation while listening
- [x] Transcript → PromptInput → auto-send on silence
- [x] TTS playback: pipe `session.idle` text to `POST /tts` (BMW Audio API via opencode-serve proxy)
- [x] Visual waveform during TTS playback

**Acceptance criteria:**
- Click mic → speak → transcript appears in prompt → auto-sends
- Response streams in text AND is read aloud via BMW TTS
- Galaxy view shows all 24+ entities with coloured nodes and labelled edges
- Clicking a node shows its observations in a side panel

**E2E tests:**
- `e2e/12-galaxy.spec.ts` — 7 tests (toolbar button, panel open/close, canvas, legend, refresh, close button)
- `e2e/13-voice.spec.ts` — 5 tests (exists, disabled when unsupported, aria-label, title, click-no-op)

---

## Phase 3.5 — Galaxy Mission Control 🌌🕹️
> Goal: Promote the Galaxy from side panel to primary interface — the app opens on the galaxy, chat slides in as a drawer.  
> Effort: 2–3 days

### Step 1 — Galaxy-first layout (App.tsx restructure) ✅ COMPLETE (2026-06-25)
- [x] Galaxy is full-screen by default (`<main>` is just the galaxy canvas when no drawer is open)
- [x] Session sidebar is collapsible: 240px expanded ↔ 48px icon rail collapsed
- [x] Chat opens as a sliding drawer (~480px) from the right when `activeSessionID` is set
- [x] Closing the drawer hides chat but does NOT delete the session
- [x] Right-panel overlays (todos, diff, cost) float over the galaxy
- [x] Agent/model pickers live in the drawer header (session-contextual)
- [x] Galaxy layer toggles always visible in top toolbar
- [x] "Mission Control" badge in top-left: active agent count + busy count (e.g. "3 agents · 1 busy")

### Step 2 — Live agent status ✅ COMPLETE (2026-06-25)
- [x] SSE `session.updated` events carry `properties.info.agent` → `sessionAgentMapRef: Map<string,string>` in `useMissionControl`
- [x] `busySessionIds: Set<string>` (state) driven by `session.status` SSE events; derived `busyAgentNames: Set<string>` passed as prop to `GalaxyView`
- [x] `GalaxyView`: `mesh.userData.agentName` stored during `makeAgentMesh`; rotation interval oscillates `emissiveIntensity` via `Math.sin(Date.now()/400)` for busy agents
- [x] Mission Control badge shows real-time busy count; `LEGEND_ENTRIES` dedup fix (no duplicate `Skill` key)

### Step 2.5 — Visual polish (cherry-picked from `memory-galaxy.html`) 🔲 **Next**

Two standalone changes, both in `GalaxyView.tsx` only. No architecture changes. Implement together in one commit.

#### ① Soft radial constraints (orbital feel without rewrite)

**Decision:** Use `d3.forceRadial` soft constraints instead of a full orbital rewrite.
Force-directed graph gives real topology for free; orbital metaphor requires hardcoding tier
assumptions that break as agent list grows. Soft radial = orbital feel + organic topology.

**Where to insert:** In the init effect (`useEffect`, deps `[filteredData, orchestratorId, initTick]`),
**between** `.d3VelocityDecay(0.25)` (line ~348) and `.nodeLabel(...)` — i.e. before `.graphData(filteredData)` (line 417).
Forces must be set BEFORE `.graphData()` — setting them after crashes the simulation tick.

**Exact code block to add** (after `.d3VelocityDecay(0.25)` and before `.nodeLabel(...)`:
```ts
// ① Soft radial constraints — orbital feel
.d3Force("radial-agents",
  (d3 as any).forceRadial(80, 0, 0, 0)
    .strength((n: unknown) => isAgentNode(n as GraphNode) && !isPrimaryAgent(n as GraphNode) ? 0.4 : 0)
)
.d3Force("radial-skills",
  (d3 as any).forceRadial(160, 0, 0, 0)
    .strength((n: unknown) => isSkillNode(n as GraphNode) ? 0.25 : 0)
)
```

**Helper needed** — add `isPrimaryAgent` predicate near `isAgentNode` / `isSkillNode`:
```ts
function isPrimaryAgent(n: GraphNode): boolean {
  return n.entityType === "PrimaryAgent";
}
```

**d3 import:** `d3` is NOT currently imported in `GalaxyView.tsx`. Add at top:
```ts
import * as d3 from "d3-force";
```
`d3-force` is a dependency of `3d-force-graph` so it's already in `node_modules` — no `npm install` needed.
If TypeScript complains about missing types, cast via `(d3 as any).forceRadial(...)`.

**ForceGraph3DInstance interface** — the `.d3Force()` method is NOT in the interface yet.
Add it (lines 53–140 area):
```ts
d3Force(name: string, force: unknown): ForceGraph3DInstance;
```

**Expected visual result:** Subagent spheres cluster ~80 units from origin; skill spheres orbit ~160 units out.
Primary agent (orchestrator) is unpinned but naturally centres due to high connectivity.

#### ② Additive glow sprites (cherry-picked from `memory-galaxy.html` `makeGlow()`)

**Decision:** Add a `SpriteMaterial` with `AdditiveBlending` as a child of each skill mesh and each
memory node mesh. This gives the "nebula bloom" effect without post-processing cost.

**Pattern from `memory-galaxy.html`** (6-line `makeGlow` function):
```js
function makeGlow(color, size) {
  const canvas = document.createElement("canvas");
  canvas.width = canvas.height = 128;
  const ctx = canvas.getContext("2d");
  const grad = ctx.createRadialGradient(64, 64, 0, 64, 64, 64);
  grad.addColorStop(0,   color + "ff");   // opaque centre
  grad.addColorStop(0.3, color + "88");   // mid fade
  grad.addColorStop(1,   color + "00");   // transparent edge
  ctx.fillStyle = grad;
  ctx.fillRect(0, 0, 128, 128);
  const tex = new THREE.CanvasTexture(canvas);
  const mat = new THREE.SpriteMaterial({ map: tex, blending: THREE.AdditiveBlending, depthWrite: false });
  const sprite = new THREE.Sprite(mat);
  sprite.scale.setScalar(size);
  return sprite;
}
```

**Where to apply:**

A. **`makeSkillMesh()` (lines 187–199):** Add glow sprite as child after creating the mesh:
```ts
function makeSkillMesh(_node: GraphNode): THREE.Mesh {
  const geo = new THREE.SphereGeometry(5, 16, 16);
  const mat = new THREE.MeshPhongMaterial({
    color: new THREE.Color(SKILL_COLOUR),
    emissive: new THREE.Color(SKILL_COLOUR),
    emissiveIntensity: 0.2,
    shininess: 60,
    transparent: true,
    opacity: 0.85,
  });
  const mesh = new THREE.Mesh(geo, mat);
  mesh.add(makeGlowSprite(SKILL_COLOUR, 22));   // ← ADD THIS
  return mesh;
}
```

B. **`nodeThreeObject` callback (lines 354–360):** Memory nodes currently return `new THREE.Object3D()`.
Replace with a glow sphere:
```ts
.nodeThreeObject((node: unknown) => {
  const n = node as GraphNode;
  if (isAgentNode(n)) return makeAgentMesh(n);
  if (isSkillNode(n)) return makeSkillMesh(n);
  // Memory nodes — small coloured sphere + glow
  const colour = n.color ?? "#6b7280";
  const radius = Math.max(3, Math.sqrt(n.val ?? 1) * 2);
  const geo = new THREE.SphereGeometry(radius, 12, 12);
  const mat = new THREE.MeshPhongMaterial({
    color: new THREE.Color(colour),
    emissive: new THREE.Color(colour),
    emissiveIntensity: 0.15,
    transparent: true,
    opacity: 0.8,
  });
  const mesh = new THREE.Mesh(geo, mat);
  mesh.add(makeGlowSprite(colour, radius * 4));  // ← glow sprite
  return mesh;
})
// Also update nodeThreeObjectExtend — memory nodes now return real meshes, NOT extend:
.nodeThreeObjectExtend((_node: unknown) => false)
```

**`makeGlowSprite` helper to add** (put after `makeSkillMesh`, before `LEGEND_ENTRIES`):
```ts
/** Create an additive-blended glow sprite (halo effect). size = sprite world-units diameter. */
function makeGlowSprite(hexColor: string, size: number): THREE.Sprite {
  const canvas = document.createElement("canvas");
  canvas.width = canvas.height = 128;
  const ctx = canvas.getContext("2d")!;
  const grad = ctx.createRadialGradient(64, 64, 0, 64, 64, 64);
  grad.addColorStop(0,   hexColor + "ff");
  grad.addColorStop(0.3, hexColor + "88");
  grad.addColorStop(1,   hexColor + "00");
  ctx.fillStyle = grad;
  ctx.fillRect(0, 0, 128, 128);
  const tex = new THREE.CanvasTexture(canvas);
  const mat = new THREE.SpriteMaterial({
    map: tex,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
  });
  const sprite = new THREE.Sprite(mat);
  sprite.scale.setScalar(size);
  return sprite;
}
```

**`nodeThreeObjectExtend` change:** Currently returns `true` for memory nodes (so force-graph adds its
default sphere AND the Object3D on top). After ② memory nodes return real meshes, so `extend` must
be `false` for ALL nodes: `.nodeThreeObjectExtend(false)` or `() => false`.

**TypeScript note:** `THREE.SpriteMaterial` and `THREE.Sprite` are standard Three.js — already imported.
`THREE.AdditiveBlending` is `THREE.AdditiveBlending` (number constant, always available).

#### Commit plan for Step 2.5

```
feat(web): Step 2.5 — radial constraints + additive glow sprites

① d3.forceRadial soft constraints: subagents r=80, skills r=160
② makeGlowSprite() helper; applied to skill meshes + memory nodes
③ isPrimaryAgent() helper; d3Force() added to ForceGraph3DInstance interface
④ nodeThreeObjectExtend → false for all (memory nodes now return real meshes)

tsc --noEmit clean ✓
```

Update `ROADMAP.md` Step 2.5 → `✅ COMPLETE (date)` in the same commit.
Update `opencode-dev-expert.md` Part 4 roadmap table: Step 2.5 → ✅, Step 3 → 🔲 **Next**.

---

### Step 3 — Team inbox watcher
- [ ] `/__team` Vite proxy reads `~/.config/opencode/team_inbox/*.jsonl`; returns `{ agent: string, count: number }[]`
- [ ] GalaxyView polls `/__team` every 5 s; on new messages → trigger edge particle burst on that agent's links
- [ ] Unread badge on agent node label

### Step 4 — Click-to-chat
- [ ] Click an agent node in the galaxy → open/focus that agent's most-recent session as the chat drawer
- [ ] If no session exists for that agent → `createSession()` with `agent` pre-filled
- [ ] Smooth camera fly-to on the clicked node before drawer opens

**Rationale:** Chat is ephemeral — you come and go from sessions. The galaxy is persistent and gives the "mission overview" at a glance. Session/chat is demoted to secondary workflow.

**Acceptance criteria:**
- App opens showing full-screen galaxy
- Clicking a session in the sidebar slides open the chat drawer
- Closing the drawer returns to full-screen galaxy with sidebar
- Busy sessions visually pulse in the galaxy
- Mission Control badge reflects real-time state

---

## Phase 4 — Tauri Desktop App 🖥️
> Goal: Native macOS `.app` — menu bar, wake word, native mic, no browser needed.  
> Effort: 1 week

- [ ] `npm create tauri-app` — wraps existing React frontend (zero React code changes)
- [ ] Menu bar integration — live session cost in the menu bar icon
- [ ] `Cmd+Space`-style global hotkey to summon/dismiss window
- [ ] Tauri sidecar: starts/stops `opencode serve --port 4096` automatically on app launch/quit
- [ ] Native mic via Tauri's `tauri-plugin-microphone` — upgrade from Web Speech API
- [ ] Whisper STT via Tauri command (replaces Web Speech API for higher quality)
- [ ] Wake word detection (always-on mic when app is backgrounded)
- [ ] Direct SQLite reads via Tauri's `tauri-plugin-sql` — bypass HTTP for analytics
- [ ] macOS `.app` bundle + DMG for distribution
- [ ] Auto-update via Tauri updater (points to GitHub Releases)

**Acceptance criteria:**
- App launches from Dock or menu bar, no terminal required
- OpenCode server starts/stops with the app
- Voice works without a browser permission dialog
- Ships as a `.app` installable on any BMW Mac

---

## Phase 5 — Local SQLite Project Tracker 🗄️
> Goal: Give the galaxy a persistent "mission layer" — projects, tasks, and agent activity live alongside the ephemeral session/memory data.  
> Effort: 1 week

### Database schema (`~/.config/opencode/web/data/opencode-tracker.db`)

```sql
CREATE TABLE projects (
  id           TEXT PRIMARY KEY,
  name         TEXT NOT NULL,
  description  TEXT,
  status       TEXT DEFAULT 'active',   -- active | paused | done | archived
  created_at   INTEGER NOT NULL,
  agent_assignments TEXT DEFAULT '[]'   -- JSON array of agent names
);

CREATE TABLE tasks (
  id             TEXT PRIMARY KEY,
  project_id     TEXT REFERENCES projects(id),
  title          TEXT NOT NULL,
  description    TEXT,
  status         TEXT DEFAULT 'pending', -- pending | in_progress | done | blocked
  assigned_agent TEXT,
  created_at     INTEGER NOT NULL,
  completed_at   INTEGER
);

CREATE TABLE agent_activity (
  id          TEXT PRIMARY KEY,
  agent_name  TEXT NOT NULL,
  session_id  TEXT,
  action_type TEXT NOT NULL,            -- session_start | tool_call | session_end | error
  metadata    TEXT DEFAULT '{}',        -- JSON blob
  timestamp   INTEGER NOT NULL
);

CREATE TABLE knowledge_links (
  id              TEXT PRIMARY KEY,
  entity_name     TEXT NOT NULL,
  entity_type     TEXT NOT NULL,
  project_id      TEXT REFERENCES projects(id),
  relevance_score REAL DEFAULT 1.0
);
```

### New galaxy node types
- **Project node** — gold sphere (`#f59e0b`), size scaled by task count
- **Task node** — small cube, colour by status:
  - `pending` → grey `#6b7280`
  - `in_progress` → BMW blue `#1c69d4`
  - `done` → green `#22c55e`
  - `blocked` → red `#ef4444`
- Tasks link to their assigned agent node and their parent project node
- `knowledge_links` rows create edges between memory entities and project nodes

### `/__db` Vite proxy (dev) / Tauri command (prod)

Reads SQLite via `better-sqlite3` (dev) or Tauri `tauri-plugin-sql` (Tauri build).

```
GET  /__db/projects              → list all projects
POST /__db/projects              → create project
PUT  /__db/projects/:id          → update project
DEL  /__db/projects/:id          → delete project

GET  /__db/tasks?projectId=...   → list tasks (optionally filtered by project)
POST /__db/tasks                 → create task
PUT  /__db/tasks/:id             → update task status / assignment
DEL  /__db/tasks/:id             → delete task

GET  /__db/activity?agent=...    → recent activity log
POST /__db/activity              → log agent action

GET  /__db/links?projectId=...   → knowledge links for a project
POST /__db/links                 → create knowledge link
```

### CRUD UI
- Click a project/task node in the galaxy → slide-in panel with edit form
- Inline status toggle on task nodes (click cube → cycles pending → in_progress → done)
- "New Task" fab inside project panel
- Agent assignment dropdown (populated from `GET /agent`)

### Integration with existing galaxy
- `lib/db-reader.ts` — fetches `/__db/projects` + `/__db/tasks`, maps to `ForceGraphData`
- `mergeGraphs()` updated to accept db layer as 4th source
- Layer toggle added: **Projects** (toggle project + task nodes on/off)
- Activity log feeds into galaxy edge particle density (more activity → more particles)

### Dev server setup
```
web/
  server/
    db-proxy.ts   ← express middleware for /__db routes (dev only)
  data/
    opencode-tracker.db   ← gitignored, created on first launch
```

**Acceptance criteria:**
- Create a project and two tasks via the galaxy click-to-edit panel
- Assign a task to an agent — a new edge appears in the galaxy
- Mark a task done — cube turns green in real-time
- Activity log shows agent tool calls within 5 s of SSE event

---

## Files Modified / Created (tracking)

| File | Phase | Status |
|---|---|---|
| `web/ROADMAP.md` | Setup | ✅ Created |
| `web/package.json` | 1 | ⬜ |
| `web/vite.config.ts` | 1 | ⬜ |
| `web/src/App.tsx` | 1 | ⬜ |
| `web/src/lib/opencode-client.ts` | 1 | ⬜ |
| `web/src/hooks/useSSE.ts` | 1 | ⬜ |
| `web/src/hooks/useSession.ts` | 1 | ⬜ |
| `web/src/hooks/useMessages.ts` | 1 | ⬜ |
| `web/src/components/SessionSidebar.tsx` | 1 | ⬜ |
| `web/src/components/ChatThread.tsx` | 1 | ⬜ |
| `web/src/components/PromptInput.tsx` | 1 | ⬜ |
| `web/src/components/StreamingText.tsx` | 1 | ⬜ |
| `web/src/components/CostBadge.tsx` | 1 | ⬜ |
| `bin/opencode-serve` | 1 | ⬜ |
| `web/src/components/AgentPicker.tsx` | 2 | ⬜ |
| `web/src/components/ModelPicker.tsx` | 2 | ⬜ |
| `web/src/components/ToolCallCard.tsx` | 2 | ⬜ |
| `web/src/components/PermissionDialog.tsx` | 2 | ⬜ |
| `web/src/components/SlashCommandPalette.tsx` | 2 | ⬜ |
| `web/src/components/DiffViewer.tsx` | 2 | ⬜ |
| `web/src/components/TodoPanel.tsx` | 2 | ⬜ |
| `web/src/components/CostTracker.tsx` | 2 | ⬜ |
| `web/src/lib/memory-reader.ts` | 3 | ⬜ |
| `web/src/components/GalaxyView.tsx` | 3 | ⬜ |
| `web/src/hooks/useVoice.ts` | 3 | ⬜ |
| `web/src/components/VoiceButton.tsx` | 3 | ⬜ |
| `web/src/App.tsx` (Phase 3.5 layout) | 3.5 | ✅ Galaxy-first layout |
| `web/ROADMAP.md` (Phase 3.5 + Phase 5) | 3.5 | ✅ Planning added |
| `README.md` | All | ⬜ updated at end |

---

## Key Decisions Made

1. **No proxy needed** — CORS is open by default on the OpenCode server
2. **`prompt_async` not `prompt`** — async endpoint returns 204 immediately; response via SSE
3. **SSE strategy: delta events** — use `message.part.delta` for streaming, `session.idle` to finalise
4. **Memory graph: file read** — read `memory.jsonl` directly, no MCP API call needed
5. **Voice Phase 1: Web Speech API** — 5 lines, works in Edge, upgrade to Whisper in Phase 4
6. **Tauri not Electron** — 5MB bundle vs 150MB, native WebView, Rust sidecar for OpenCode server
7. **BMW CI via Tailwind** — custom theme config with Density colour tokens
8. **No d3Force post-init** — calling `.d3Force()` after `.graphData()` crashes simulation tick; forces must be set BEFORE `.graphData()`
9. **`filteredData` must be `useMemo`** — inline object = new reference every render = infinite effect loop
10. **`dimensions` must be a `ref`** — React state causes re-render → new filteredData reference → effect re-fires
11. **StrictMode cleanup pattern** — unmount effect with `[]` must call `_destructor()` + clear DOM children + null `graphRef`
12. **`initTick` pattern** — single-purpose counter; incremented once by ResizeObserver on first real (non-zero) size; kicks init effect exactly once
13. **Agent self-update protocol** — `opencode-dev-expert` must update its own Part 4 and commit it in the same commit as every web feature
14. **Galaxy is always-on background** — not a toggleable panel; chat is a drawer overlay
15. **`/__agents` is fully dynamic** — reads filesystem at request time; no hardcoding
16. **sessionID → agentName bridge** — `useMissionControl` maps session IDs to agent names via `session.updated` SSE events; `sessionAgentMapRef` (useRef) avoids stale-closure issues
17. **Pulse hook point** — rotation `setInterval` in `GalaxyView.tsx` is the correct hook for emissive intensity oscillation
18. **`agentName` in mesh `userData`** — stored during `makeAgentMesh` so the rotation interval can match meshes to `busyAgentNames`
19. **Hybrid orbital feel** — soft `d3.forceRadial` constraints (not full orbital rewrite); orchestrator centres naturally via high connectivity; subagents r=80, skills r=160
20. **Additive glow sprites** — `SpriteMaterial + AdditiveBlending` child sprite; mirrors `memory-galaxy.html` `makeGlow()` pattern; applied to skill meshes + memory node meshes
21. **Full orbital rewrite rejected** — force graph gives real topology for free; orbital metaphor requires hardcoding tier assumptions that break as agent list grows
22. **`nodeThreeObjectExtend` → false after ②** — memory nodes currently use `extend=true` with empty Object3D (so force-graph renders its default sphere); once ② gives memory nodes real meshes, `extend` must be `false` for all nodes

---

## GalaxyView.tsx Confirmed Line Map (as of commit dc54612)

> File is ~670 lines. Tool output truncates at 2000 lines but the file exceeds single-read.
> Use `offset=N limit=M` in Read tool for targeted access.

| Section | Lines |
|---|---|
| Imports | 1–51 |
| `ForceGraph3DInstance` interface | 53–140 |
| `agentMeshRegistry` declaration | 142–144 |
| `makeAgentMesh()` | 148–185 |
| `makeSkillMesh()` | 187–199 |
| `LEGEND_ENTRIES` | 201–212 |
| `GalaxyViewProps` interface | 214–218 |
| Component body / state / refs | 219–321 |
| Init effect start | 328 |
| `Graph(el).backgroundColor(...)` chain start | 340 |
| `.d3AlphaDecay` / `.d3VelocityDecay` | 347–348 |
| **← insert d3.forceRadial HERE (before `.nodeLabel`)** | **349** |
| `.nodeLabel` / `.nodeVal` / `.nodeColor` | 351–353 |
| `.nodeThreeObject` callback | 354–360 |
| `.nodeThreeObjectExtend` callback | 361–367 |
| `.graphData(filteredData)` | 417 |
| Bloom post-processing | 419–437 |
| `graphRef.current = Graph` | 439 |
| Rotation interval + busy-pulse | 455–512 |
| Unmount cleanup effect | 520–533 |
| Return JSX | 535–669 |

**`makeGlowSprite` insert point:** After `makeSkillMesh()` (line 199), before `LEGEND_ENTRIES` (line 201).

---

## How to Resume This Session

```bash
# Check where we are
git -C ~/.config/opencode branch          # should be feat/web-frontend
git -C ~/.config/opencode log --oneline -5  # last commit: dc54612

# Start the OpenCode server for testing
opencode serve --port 4096 --hostname 127.0.0.1 &

# Run the web app
cd ~/.config/opencode/web && npm run dev  # http://localhost:3000
```

### Next task to execute (Step 2.5)

1. Read `GalaxyView.tsx` lines 340–420 to confirm init effect insertion point.
2. Apply **① soft radial constraints** — see "Step 2.5 → ①" section above for exact code.
3. Apply **② additive glow sprites** — see "Step 2.5 → ②" section above for exact code.
4. Run `tsc --noEmit` — must be clean before committing.
5. Commit with message from "Commit plan" block above.
6. Update this ROADMAP: Step 2.5 → `✅ COMPLETE (date)`.
7. Update `opencode-dev-expert.md` Part 4 roadmap table: Step 2.5 → ✅, Step 3 → 🔲 **Next**.

### Critical facts for the next agent

- **Dev server**: `http://localhost:3000/` (Vite v5.4.21)
- **Branch**: `feat/web-frontend` in `~/.config/opencode`
- **Last commit**: `dc54612` — "feat(web): Step 2 live agent status pulse"
- **`/__agents`**: returns 5 agents, 58 skills, 84 links, `orchestratorId: "agent:request-orchestrator"`
- **`/__memory` hardcoded path**: `/Users/QTE2362/.npm/_npx/15b07286cbcc3329/node_modules/@modelcontextprotocol/server-memory/dist/memory.jsonl`
- **`d3-force` is already in `node_modules`** (transitive dep of `3d-force-graph`) — no `npm install` needed
- **`THREE.SpriteMaterial`, `THREE.Sprite`, `THREE.AdditiveBlending`** — all available from existing `three` import
- **`nodeThreeObjectExtend` must change** — currently `true` for memory nodes (empty Object3D hack); after ② memory nodes return real meshes so set to `false` for all
- **`ForceGraph3DInstance` interface** — add `d3Force(name: string, force: unknown): ForceGraph3DInstance` method
- **`isPrimaryAgent` helper** — `n.entityType === "PrimaryAgent"` (same field checked in `makeAgentMesh`)
- **All Python** must run from `~/.opencode/plugins/clipjoint/.venv/bin/python3` — not relevant for this React task but noted for context
- **Web Frontend Feature Protocol** — after every web feature commit: update `opencode-dev-expert.md` Part 4 roadmap table AND `ROADMAP.md` in the same commit
