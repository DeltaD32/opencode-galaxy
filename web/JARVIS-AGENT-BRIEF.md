# JARVIS — Agent Brief
**For:** Any agent working on the OpenCode JARVIS frontend  
**Version:** 1.1 — updated with current branch state  
**Last updated:** 2026-06-26

**Read this first.** This is the single source of truth for what JARVIS is, what
already exists, what needs to change, and what we are building toward. All
implementation decisions derive from the two detailed specs listed at the bottom.

---

## What Is JARVIS?

JARVIS is a **holographic, voice-first GUI shell** that becomes the new front door
to OpenCode. Think Tony Stark's assistant — a gyroscope orb with a living particle
field, push-to-talk voice, British TTS, floating draggable panels — but **relaxed and
laid-back**, not aggressive. Minority Report aesthetic, smooth animations, tech vibe.

It is **not** a redesign of the TUI. The TUI keeps running. JARVIS is a **second
surface** — the thing you see when you open the desktop app.

---

## Current State of the Codebase

### Branch: `feat/web-frontend`

This branch is **active and has significant work already done**. Here is exactly
what exists today, by status:

#### ✅ Complete and Working

| Feature | Files | Notes |
|---|---|---|
| React 18 + TypeScript + Vite 5 scaffold | `web/package.json`, `web/vite.config.ts`, `web/index.html` | Fully wired, Tailwind configured |
| OpenCode SSE client | `src/hooks/useSSE.ts` | Connects to `localhost:4096/api/event`, handles all event types |
| Session management | `src/hooks/useSession.ts`, `src/hooks/useMessages.ts` | List, create, load sessions |
| Chat interface | `src/components/ChatThread.tsx`, `src/components/PromptInput.tsx` | Streaming tokens via `message.part.delta` |
| Agent + model pickers | `src/components/AgentPicker.tsx`, `src/components/ModelPicker.tsx` | Pull from live `/api/agent` endpoint |
| Cost tracking | `src/components/CostTracker.tsx`, `src/components/CostBadge.tsx` | Live per-turn cost from `step-finish` events |
| Tool call display | `src/components/ToolCallCard.tsx` | Shows tool name, input, output, status |
| Galaxy 3D view | `src/components/GalaxyView.tsx` (~967 lines) | Full Three.js force-graph with agents, skills, memory entities, bloom post-processing |
| Live agent pulse | `GalaxyView.tsx` + `useMissionControl()` in `App.tsx` | Busy agents pulse their mesh via `emissiveIntensity` sine wave |
| Projects layer | `src/lib/db-reader.ts` (~456 lines) | Reads `opencode.db` via `/__db` Vite bypass — projects, blackboards, decisions cluster in galaxy |
| Memory graph | `src/lib/memory-reader.ts` | Reads `memory.jsonl`, feeds galaxy |
| Agent graph | `src/lib/agent-reader.ts` | Reads agent `.md` files, builds skill nodes |
| Voice button (basic) | `src/components/VoiceButton.tsx`, `src/hooks/useVoice.ts` | Web Speech API STT → appends transcript to composer. **Functional but not JARVIS-quality.** |
| Session sidebar | `src/components/SessionSidebar.tsx` | Collapsible, session list with cost |
| Slash command palette | `src/components/SlashCommandPalette.tsx` | `/` trigger, lists available commands |
| Right panel overlays | `src/components/TodoPanel.tsx`, `src/components/DiffViewer.tsx` | Float over galaxy |
| Permissions dialog | `src/components/PermissionDialog.tsx` | Tool approval prompts |
| E2E test suite | `web/e2e/01-*.spec.ts` → `13-*.spec.ts` | 13 Playwright specs covering all major flows |
| opencode-serve script | `bin/opencode-serve` | Starts OpenCode server headlessly for web use |

#### 🔲 Step 2.5 — Visual Polish (Next planned item on `feat/web-frontend`)

From `web/ROADMAP.md`:
```
### Step 2.5 — Visual polish (cherry-picked from memory-galaxy.html) 🔲 Next
```
This step would bring the existing Galaxy closer to the `memory-galaxy.html` reference
(additive glow sprites, radial orbit constraints, etc.). **This work is SUPERSEDED by
JARVIS** — do not implement Step 2.5 in isolation. The Galaxy polish happens as part of
JARVIS Phase 3 when Galaxy becomes a panel.

#### 📋 Planned but Not Started

| Item | From existing roadmap | JARVIS status |
|---|---|---|
| Phase 4 — Tauri desktop app | `web/ROADMAP.md` Phase 4 | **Aligned** — same goal, JARVIS Phase 4 |
| Phase 5 — SQLite project tracker | `web/ROADMAP.md` Phase 5 | **Absorbed** — already done in `db-reader.ts`; JARVIS surfaces it as the Projects panel |

---

### Current App Architecture (What Exists)

```
src/main.tsx
  └── App.tsx  (573 lines — everything in one component)
       ├── Galaxy (GalaxyView.tsx) — FULL SCREEN background, always rendered
       ├── SessionSidebar — collapsible left rail, 240px / 48px icon
       ├── Chat drawer — slides in from right when session is active
       ├── Right panel overlays (todos, diff, cost) — position:fixed
       ├── Mission Control badge (top-left)
       └── VoiceButton — basic mic toggle in the composer
```

**Key architectural fact:** The current design has Galaxy as the **always-on
background** and chat as a **sliding drawer overlay**. This is the
"Galaxy-first" layout from Phase 3.5, completed 2026-06-25.

---

## What Changes for JARVIS

This section describes the **delta** — what specifically has to be added, moved,
or restructured to go from the current state to JARVIS. Nothing is thrown away.

### 1. `App.tsx` — Split and Promote

**Current:** One 573-line God component rendering everything.

**JARVIS target:** `App.tsx` becomes a thin root that renders `<JarvisShell />`.
All existing logic migrates into focused components:

| Current location in `App.tsx` | Moves to |
|---|---|
| `useMissionControl()` hook | `src/jarvis/session/SessionContext.tsx` |
| SSE wiring (`useSSE`) | `src/jarvis/session/sseClient.ts` |
| Session state | `src/jarvis/session/SessionContext.tsx` |
| Right-panel overlay logic | `src/jarvis/panels/panelStore.ts` |
| Galaxy layer toggle state | `src/jarvis/panels/panelStore.ts` |
| Cost badge display | `src/jarvis/session/SessionContext.tsx` (exposed as context) |
| `GalaxyView` render | Stays in `src/components/GalaxyView.tsx` — wrapped in `PanelFrame` |

### 2. Galaxy — From Background to Panel

**Current:** `GalaxyView` renders as a full-screen `<canvas>` that fills the entire
viewport. Chat overlays it.

**JARVIS target:** Galaxy becomes **Panel #1** in the panel system. It is not
the default view — the **JARVIS orb** is the default view. The user (or JARVIS)
can summon the Galaxy panel at any time via voice ("show me the galaxy"), the
panel registry, or a keyboard shortcut.

**Migration:** `GalaxyView.tsx` does not need to be rewritten. It needs:
1. A thin `GalaxyApp.tsx` wrapper that mounts it as a standalone Vite entry
   (for `localhost:3001` iframe hosting in dev)
2. Removal of its dependency on `App.tsx` props — it should pull its own data
   via the existing `/__memory`, `/__agents`, `/__db` hooks
3. The panel chrome (title bar, drag handle, close button) is provided by
   `PanelFrame.tsx`, not by `GalaxyView` itself

### 3. Chat — From Drawer to JARVIS Response Area

**Current:** Chat is a ~480px sliding drawer from the right edge of the screen.

**JARVIS target:** There is no "chat drawer". JARVIS responses stream directly
into the response text area below the orb. The existing `ChatThread.tsx` and
`PromptInput.tsx` components are **reused** — they live inside the JARVIS
response column, not in a separate drawer. `SessionSidebar.tsx` is retained as
an optional panel (Panel #6 in the registry).

### 4. VoiceButton — Promoted to PTT System

**Current:** `VoiceButton.tsx` + `useVoice.ts` provide basic Web Speech API
integration — a mic toggle button in the chat composer that appends transcript
text. Works, but has no visual presence, no keyboard shortcut, no state
communication with the orb.

**JARVIS target:** The voice system becomes a full pipeline:

| Current | JARVIS replacement |
|---|---|
| `useVoice.ts` (Web Speech API) | **Keep as-is** → becomes `SttBridge.ts` |
| `VoiceButton.tsx` (small toggle in composer) | **Replace** → `PttManager.ts` + `InputBar.tsx` (full PTT with keyboard shortcuts and orb state integration) |
| No TTS | **New** → `TtsPipeline.ts` + `TtsLocal.ts` + `TtsBmw.ts` |
| No audio visualisation | **New** → `audioAnalyser.ts` + `ThreeOrb.tsx` (vox corona) |

The core `useVoice.ts` STT logic is **good and reusable** — don't rewrite it.
Wrap it.

### 5. Right Panel Overlays — Promoted to Panel System

**Current:** `TodoPanel.tsx`, `DiffViewer.tsx`, `CostTracker.tsx` render as
`position: fixed` overlays wired to specific state flags in `App.tsx`.

**JARVIS target:** These become registered panels in `panelRegistry.ts`. They
gain drag/resize via `PanelFrame.tsx`. The same component code is largely reused
— they just get a new mount point and lifecycle managed by `panelStore.ts`.

### 6. New Components (No Existing Equivalent)

These are entirely new — nothing to migrate from:

| Component | Why it's new |
|---|---|
| `JarvisShell.tsx` | New root shell with the 3-layout-state system |
| `Canvas2DOrb.tsx` | SVG gyroscope rings + Canvas 2D particle field — no existing equivalent |
| `ThreeOrb.tsx` | Three.js InstancedMesh vox corona — no existing equivalent |
| `ActivityModal.tsx` | Step-by-step thinking display — currently the tool call cards in `ToolCallCard.tsx` are the closest thing, but the modal is a different UX entirely |
| `PanelHost.tsx` / `PanelFrame.tsx` | Panel management system — no existing equivalent |
| `TtsPipeline.ts` / `TtsLocal.ts` / `TtsBmw.ts` | TTS is entirely new |
| `PttManager.ts` | Keyboard shortcut management is entirely new |
| `SettingsDrawer.tsx` | No settings UI currently exists |
| Theme CSS token system | Tailwind + custom vars exist; JARVIS-specific behavioral tokens are new |

---

## Validated API Facts (do not re-research)

These are confirmed working from the existing `web/ROADMAP.md`:

- OpenCode server: `opencode serve --port 4096 --hostname 127.0.0.1`
- **CORS is open by default** — no `--cors` flag needed
- `POST /session/{id}/prompt_async` → 204 immediately; response arrives via SSE
- `GET /event` → SSE stream, `Content-Type: text/event-stream`
- Agent shape: `{ name, description, mode, color, hidden, model }` — key is `name` not `id`
- `step-finish` part carries `{ tokens: { total, input, output, cache }, cost }` — live cost

### SSE Event Lifecycle (one prompt)
```
session.status              { type: "busy" }
message.part.updated        type: "step-start"
message.part.updated        type: "tool"        ← feeds ActivityModal steps
message.part.delta          delta: "<token>"    ← streaming text
message.part.updated        type: "step-finish" { tokens, cost }
session.status              { type: "idle" }
session.idle                                    ← TTS trigger point
```

### Tool part shape
```json
{
  "type": "tool",
  "tool": "bash",
  "callID": "toolu_...",
  "state": { "status": "completed", "input": {}, "output": "", "title": "" }
}
```

### Known Gotchas (from existing development)
- `filteredData` must be `useMemo` — inline object = new reference = infinite effect loop
- `dimensions` must be a `ref`, not state — state causes re-render → effect re-fires
- `d3Force()` must be called **before** `.graphData()` — calling after crashes the sim
- Galaxy unmount: must call `_destructor()` + clear DOM children + null `graphRef`
- `initTick` pattern — increment once on first real ResizeObserver size, kicks init exactly once
- StrictMode double-invoke: null-check `graphRef.current` before init

---

## The JARVIS Orb

The central visual identity. **A three-ring gyroscope** — three nested, independently
rotating elliptical rings around a soft radial glow core. Not a sphere.

### States & Engines

| State | Trigger | Engine | Particles | Behaviour |
|---|---|---|---|---|
| `IDLE` | App open, waiting | Canvas 2D + SVG | 48 | Slow Lissajous drift, 80–120px orbit, breathing glow |
| `LISTENING` | PTT pressed | Canvas 2D + SVG | 80 | Accelerate, tighten to 55–90px, waveform bar appears below |
| `THINKING` | PTT released, processing | Canvas 2D + SVG | 80 | Slow inward spiral, Activity Modal appears |
| `SPEAKING` | TTS audio starts | **Three.js InstancedMesh** | 120 | Radial vox corona — FFT bands expand particles outward in circular EQ pattern |

**SVG ↔ Three.js handoff:** Same `<canvas>` element. Departing renderer calls
`dispose()`. Crossfade: `opacity` CSS transition, 400ms. State machine in
`src/jarvis/orb/particleState.ts`.

**Note on Three.js:** `GalaxyView.tsx` already uses Three.js v0.185. `ThreeOrb.tsx`
shares the same import — no version conflict. However the orb and galaxy render in
**separate canvas elements** — do not share a renderer or scene.

---

## Layout — Three States

### Idle (default — replaces the current Galaxy background)
```
╔══════════════════════════════════════════════════════╗
║                                                      ║
║              ◎  JARVIS ORB  ◎                       ║
║         [particle field, breathing]                  ║
║                                                      ║
║               "How can I help?"                      ║
║                    [● MIC]                           ║
╚══════════════════════════════════════════════════════╝
[theme]                                    [settings ⚙]
```

### Listening
Same layout. Orb scale → `1.23×`. Mic waveform bar fades in below orb.
Status label `"listening"` appears above PTT button.

### Responding + Panel open
```
╔═══════════════════════╦══════════════════════════════╗
║   ◎  ORB  ◎           ║  ╔═══════════════════════╗  ║
║   [vox corona]        ║  ║ Panel Title        [×] ║  ║
║                       ║  ║                        ║  ║
║  JARVIS response      ║  ║  [panel content]       ║  ║
║  text streams here    ║  ║                        ║  ║
║                       ║  ╚═══════════════════════╝  ║
╚═══════════════════════╩══════════════════════════════╝
   ← 2/3 viewport →     (panel is position:fixed, not grid)
```
Orb column: `translateX(-16%)`, `500ms` spring. Panel: `position:fixed`, slides in
from right. Multiple panels stack `+20px x/y`. Draggable + resizable via interact.js.

---

## Voice Pipeline

```
PTT (CMD+SHIFT+SPACE / hold-SPACE / mic button)
  │
  ▼
useVoice.ts (Web Speech API) ─── already exists, reuse ───► Transcript
  │  (mlx-whisper FastAPI bridge localhost:5001 — opt-in, Phase 2+)
  ▼
POST /session/{id}/prompt_async  →  OpenCode backend
  │
  ▼
SSE message.part (tool) events  →  ActivityModal steps
  │
  ▼
session.idle event  →  TTS decision:
  ├── ≤120 chars  →  macOS `say -v Daniel`  (instant, offline, British)
  └──  >120 chars  →  BMW Audio TTS API     (quality, streaming MP3)
  │
  ▼
Audio element  →  Web Audio AnalyserNode  →  ThreeOrb vox corona FFT
```

### PTT Shortcuts
| Method | Phase | How |
|---|---|---|
| `CMD+SHIFT+SPACE` | P1 (browser keydown) / P4 (Tauri OS-level) | Primary |
| Hold `SPACE` | P1 | When no text input focused |
| On-screen mic button | P1 | Always visible bottom-centre |
| "Hey JARVIS" wake word | P5 only | Porcupine WASM, off by default |

---

## Activity Modal

Replaces/supplements the existing `ToolCallCard.tsx` display for the JARVIS context.

- `position: fixed`, `bottom: 72px`, `right: 24px`, `width: 320px`
- Glassmorphic: `backdrop-filter: blur(16px)`, border glow
- Steps fed from `message.part` tool events (same data as `ToolCallCard.tsx`)
- **Auto-dismiss**: 15s after `session.idle`. Depleting 1px countdown line on top edge.
- Hover pauses countdown. `[×]` for instant close.
- Entrance: `translateY(12px) scale(0.96) opacity:0` → normal, `280ms --ease-spring`

---

## Notifications (Toasts)

Async, non-blocking. Never interrupts active agent work.

- Stack: `top: 72px`, `right: 24px`. Max 4. 6s auto-dismiss. Hover pauses.
- On async `task.complete`: orb glow pulses once (500ms soft bloom) before toast appears.
- `[→]` action opens the relevant panel.

---

## Theme System

### What currently exists
The current codebase uses **Tailwind** with a custom config (`tailwind.config.ts`)
that has BMW CI colour tokens. The existing `src/styles/index.css` sets a small
number of CSS custom properties. There is **no theme-switching system** yet.

### What JARVIS adds
- `data-jarvis-theme` attribute on `<html>` — instant swap, no flash
- One CSS file per theme in `src/jarvis/theme/themes/`
- **Blink transition**: full-screen overlay 150ms in → variables swap → 300ms out
- Persisted: `localStorage` key `jarvis-theme`
- 5 existing Galaxy themes **ported** to CSS variable tokens
- 2 new JARVIS-exclusive themes: **Black Ice** (cold monochrome) + **Chrome** (gunmetal)

### Themes
| Name | Vibe | Key Colors |
|---|---|---|
| `observatory` | Deep space, default | Blue `#4d8df6`, gold `#ffb627` |
| `cel-shade` | Cartoon, daytime | Toon, bright sky |
| `blueprint` | Wireframe, technical | Cyan `#36d6e7`, dashed rings |
| `synthwave` | 80s neon grid | Magenta `#c44af0`, pink `#f564c4` |
| `forge` | Ember/fire | Orange `#ff6420`, ember particles |
| `black-ice` *(new)* | Cold monochrome | Steel `#8ab0d0` |
| `chrome` *(new)* | Gunmetal silver | Silver `#8090a8` |

### New JARVIS CSS Token Groups (behavioral — beyond existing Galaxy signal tokens)
```
--jarvis-bg, --jarvis-surface, --jarvis-surface-alt
--jarvis-border, --jarvis-border-glow
--jarvis-idle-particle, --jarvis-listen-particle, --jarvis-speak-particle
--jarvis-orb-glow, --jarvis-orb-ring
--jarvis-text-primary, --jarvis-text-secondary, --jarvis-text-code, --jarvis-text-accent
--jarvis-notify-bg, --jarvis-notify-border, --jarvis-notify-success/warning/error
--jarvis-activity-bg, --jarvis-activity-step-done/active/pending
--jarvis-ptt-idle, --jarvis-ptt-idle-rgb, --jarvis-ptt-active, --jarvis-ptt-active-rgb
```

### Shared Animation Easings
```css
--ease-spring:    cubic-bezier(0.34, 1.56, 0.64, 1);  /* orb scale, panel slide-in */
--ease-out-expo:  cubic-bezier(0.16, 1, 0.3, 1);       /* panel + toast entrance */
--ease-out-cubic: cubic-bezier(0.33, 1, 0.68, 1);      /* modal steps, general decel */
--ease-in-cubic:  cubic-bezier(0.32, 0, 0.67, 0);      /* exit animations */
```

---

## Panel Registry

### Built-in Panels (v1)
| Panel ID | Title | Current component | Notes |
|---|---|---|---|
| `galaxy` | Memory Galaxy | `GalaxyView.tsx` | Served at `localhost:3001` in dev |
| `blackboard` | Blackboard | New (no current equivalent) | `/__blackboard` |
| `briefing` | Morning Briefing | New | `/__briefing` |
| `tokens` | Token Tracker | `CostTracker.tsx` (adapted) | `/__tokens` |
| `projects` | Project Status | Uses `db-reader.ts` data (adapted) | `/__projects` |
| `sessions` | Sessions | `SessionSidebar.tsx` (adapted) | Optional |
| `todos` | Todo Panel | `TodoPanel.tsx` (adapted) | `/__todos` |
| `diff` | Diff Viewer | `DiffViewer.tsx` (adapted) | `/__diff` |

```typescript
interface PanelDef {
  id: string;
  title: string;
  url: string;
  defaultSize: { w: number; h: number };
  defaultPosition: { x: number; y: number };
  sandbox: string;
}
```

---

## SSE Events → JARVIS Actions

| SSE event | Current handling | JARVIS handling |
|---|---|---|
| `session.updated` | Updates `sessionAgentMapRef` in `useMissionControl` | Same, moves to `SessionContext` |
| `session.status` (busy/idle) | Updates `busyAgentNames`, galaxy pulse | Same + drives orb `THINKING`/`IDLE` state |
| `session.idle` | Stops streaming indicator | **New**: triggers TTS pipeline |
| `message.part.delta` | Streams into `ChatThread` | Streams into JARVIS response area |
| `message.part` (tool) | Renders `ToolCallCard` | **New**: feeds `ActivityModal` steps |
| `message.part` (step-finish) | Updates cost badge | Same, via `SessionContext` |

---

## New Dependencies (by Phase)

| Package | Phase | Purpose | Already in package.json? |
|---|---|---|---|
| `zustand ^4.5` | P1 | State (panels, toasts, activity, theme) | ❌ No |
| `interact.js ^1.10` | P3 | Panel drag + resize | ❌ No |
| `@picovoice/porcupine-web ^3.0` | P5 | Wake word WASM in Web Worker | ❌ No |
| `@tauri-apps/api ^2.x` | P4 | Tauri JS bridge | ❌ No |
| `@tauri-apps/plugin-global-shortcut` | P4 | OS-level CMD+SHIFT+SPACE | ❌ No |
| `@tauri-apps/plugin-shell` | P4 | macOS `say` command | ❌ No |
| `tauri-plugin-sql` | P4 | opencode.db in desktop | ❌ No |

Everything else (React, TypeScript, Vite, Three.js, Tailwind, Web Speech API,
Web Audio API, SSE) is already present or browser-native.

---

## Implementation Phases

### Phase 1 — JARVIS Shell MVP  ← START HERE
**Goal:** JARVIS orb replaces the Galaxy as the app entry point. Idle state
looks and feels right. Text interaction works end-to-end.

**Prerequisite:** All Phase 1 work happens on `feat/web-frontend`. No new branch needed
(it is already a feature branch off `main`).

**What to add:**
```
src/jarvis/
  JarvisShell.tsx               ← new root (replaces App.tsx role)
  JarvisShell.css
  orb/
    OrbContainer.tsx
    Canvas2DOrb.tsx              ← SVG rings + Canvas 2D particle field
    particleState.ts
  activity/
    ActivityModal.tsx
    activityStore.ts
    ActivityModal.css
  input/
    InputBar.tsx                 ← text input + PTT button
    InputBar.css
  session/
    sseClient.ts                 ← extract from App.tsx useSSE wiring
    SessionContext.tsx           ← extract from App.tsx useMissionControl
  theme/
    jarvisThemeTokens.css
    themeStore.ts
    themes/{observatory,cel-shade,blueprint,synthwave,forge}.css
```

**What to modify:**
```
src/main.tsx          → boot <JarvisShell /> instead of <App />
src/App.tsx           → keep as-is for now, referenced by JarvisShell during migration
web/package.json      → add zustand
web/vite.config.ts    → add /galaxy proxy for iframe (localhost:3001)
```

**What NOT to touch yet:**
- `GalaxyView.tsx` — leave entirely alone in Phase 1
- `ChatThread.tsx`, `PromptInput.tsx` — reused as-is inside JarvisShell
- `useVoice.ts` — leave alone, used in Phase 2

New deps: `zustand`  
Estimate: **3–4 weeks**

---

### Phase 2 — Voice
**Goal:** CMD+SHIFT+SPACE PTT works. JARVIS speaks back via TTS.

**What to add:**
```
src/jarvis/voice/
  VoiceController.tsx
  SttBridge.ts              ← thin wrapper around existing useVoice.ts
  TtsPipeline.ts
  TtsLocal.ts               ← macOS `say` via Vite middleware
  TtsBmw.ts                 ← BMW Audio TTS API
  PttManager.ts             ← keyboard + button state machine
  audioAnalyser.ts          ← Web Audio AnalyserNode wrapper
src/jarvis/notifications/
  ToastLayer.tsx
  toastStore.ts
  ToastLayer.css
scripts/
  tts-server.mjs            ← Vite dev middleware: POST /api/tts-local → `say`
```

Estimate: **2–3 weeks**

---

### Phase 3 — Vox Corona + Panel System
**Goal:** JARVIS speaks visually. Galaxy and other panels open on command.

**What to add:**
```
src/jarvis/orb/
  ThreeOrb.tsx              ← Three.js InstancedMesh vox corona
  orb.vert.glsl / orb.frag.glsl
src/jarvis/panels/
  PanelHost.tsx
  PanelFrame.tsx            ← draggable/resizable via interact.js
  panelRegistry.ts
  panelStore.ts
  panels.css
src/galaxy/
  GalaxyApp.tsx             ← standalone Galaxy entry for iframe hosting
src/jarvis/settings/
  SettingsDrawer.tsx
  SettingsDrawer.css
src/jarvis/theme/themes/
  black-ice.css
  chrome.css
```

New deps: `interact.js`  
Estimate: **4–5 weeks**

---

### Phase 4 — Tauri Desktop App
**Goal:** Native macOS `.app`. OS-level global shortcut. `say` via Tauri shell.

**Aligned with existing `web/ROADMAP.md` Phase 4** — same goals, JARVIS is the UI.

**What to add:**
```
src-tauri/                  ← Tauri scaffold
src/jarvis/platform/
  tauriShim.ts              ← isTauri capability shim
src/jarvis/voice/
  SttMlxBridge.ts           ← mlx-whisper HTTP bridge (opt-in sidecar)
scripts/
  stt-bridge.py             ← mlx-whisper FastAPI server
```

New deps: `@tauri-apps` suite  
Estimate: **3–4 weeks**

---

### Phase 5 — Always-On + Wake Word
**Goal:** "Hey JARVIS" activates without keyboard.

**What to add:**
```
public/jarvis/
  wake-word-model.ppn
src/jarvis/voice/
  WakeWordWorker.worker.ts
src/jarvis/settings/
  WakeWordSettings.tsx
```

New deps: `@picovoice/porcupine-web`  
Estimate: **1–2 weeks**

---

## Key Constraints (Non-Negotiable)

| Constraint | Detail |
|---|---|
| **Local only** | JARVIS shell is offline-capable. Panels connect to OpenCode backend as before. |
| **Single user** | No auth, no multi-user. |
| **BMW network** | BMW Audio TTS + LLM API require BMW network / VPN. |
| **M3 Pro Apple Silicon** | mlx-whisper, `say`, Tauri all target ARM64 macOS. |
| **No Galaxy code deleted** | Galaxy becomes Panel #1. All `GalaxyView.tsx` code preserved. |
| **Browser-first** | Validate everything in Vite dev before touching Tauri. |
| **No implementation yet** | This is a planning document. Do not start implementing until explicitly asked. |

---

## Reference Documents

| Document | Path | What's in it |
|---|---|---|
| **This brief** | `web/JARVIS-AGENT-BRIEF.md` | Current state, what changes, full context |
| Full design spec | `web/JARVIS-ROADMAP.md` | Complete UX/visual spec — particle physics, animation curves, component designs, theme tokens |
| Full architecture spec | `web/JARVIS-ARCHITECTURE-SPEC.md` | 2080-line technical spec — voice pipeline code, panel IPC, Tauri migration, full data flow |
| Design ref images | `web/jarvis-design-refs/*.png` | 4 AI-generated visual references |
| Galaxy reference | `/Users/QTE2362/ECC-APPS/memory-galaxy.html` | Original Galaxy HTML — 5 theme defs, orbital metaphor, CSS tokens |
| Existing web roadmap | `web/ROADMAP.md` (on `feat/web-frontend`) | Prior phase decisions, validated API facts, known gotchas |

---

## How To Use This Brief

**Starting any JARVIS session:**
> "I'm working on the OpenCode JARVIS frontend. Read
> `~/.config/opencode/web/JARVIS-AGENT-BRIEF.md` for full context, then [task]."

**When implementing a specific phase:**
> "Implement JARVIS Phase 1. Read the brief at
> `~/.config/opencode/web/JARVIS-AGENT-BRIEF.md` first, then begin."

**When in doubt about a design decision:**
→ `JARVIS-ROADMAP.md` for design intent  
→ `JARVIS-ARCHITECTURE-SPEC.md` for technical approach  
→ `web/ROADMAP.md` on `feat/web-frontend` for validated API/SSE facts and gotchas  
This brief is the summary; those documents are the authority.

---

*JARVIS Agent Brief v1.1 — BMW Internal — 2026-06-26*
