# OpenCode JARVIS — Frontend Roadmap
**Version 1.0 | BMW Internal | 2026-06-26**
**Branch:** `feat/web-frontend` → extend existing Galaxy frontend

---

## Executive Summary

JARVIS is a holographic, voice-first GUI shell for the OpenCode AI coding assistant. It replaces the current browser entry point with a Minority Report–inspired ambient assistant: a gyroscope orb with a living particle field, push-to-talk voice interaction, British TTS voice, floating draggable panels, and full integration with the existing Memory Galaxy, Blackboard, and Projects systems.

JARVIS is built browser-first (Vite dev server, extending `feat/web-frontend`) and migrates to a Tauri desktop app in Phase 4.

---

## Design Reference Images

Generated reference images are at `/Users/QTE2362/ECC-APPS/jarvis-design-refs/`:

| File | What it shows |
|---|---|
| `jarvis-idle-observatory.png` | Idle state — Observatory theme. Gyroscope orb, calm particle field, minimal chrome, bottom-center mic button. |
| `jarvis-speaking-vox.png` | Speaking state — particle vox corona active. Radial frequency bands wrapped around the orb. Activity modal visible bottom-right. |
| `jarvis-panel-galaxy.png` | Panel-open state. JARVIS shifts left 2/3, Galaxy panel opens as floating draggable overlay on the right. |
| `jarvis-listening-synthwave.png` | Listening state — Synthwave theme. Neon grid, tight particle orbit, waveform bar below orb. |

---

## Design Vision

### Feel
- **Minority Report aesthetic but relaxed** — holographic HUD, floating panels, smooth animations; no aggression, no urgency
- **Laid-back tech** — spring curves instead of linear easing, unhurried transitions (200–600ms), whispered alerts, lowercase status text
- **Starts minimal, scales up** — idle state is near-empty; JARVIS adds chrome only when it has something to say

### The JARVIS Orb
A **multi-ring gyroscope** — three nested, independently rotating rings around a soft glow core. Not a sphere. The rings are the identity.

- **Idle**: Rings rotate slowly (48s / 28s / 14s cycles), glow core breathes at 4s, ~48 particles drift lazily in orbit
- **Listening**: Rings speed up 1.8×, particles accelerate and tighten inward, waveform bar fades in below
- **Speaking**: SVG hands off to Three.js `InstancedMesh`. 120 particles form a **radial vox corona** driven by Web Audio API FFT — particles expand outward in frequency bands, wrapping the orb like a circular equalizer
- **Thinking**: Slow inward spiral, activity modal appears

### Layout States

```
STATE A: Idle (default)
╔══════════════════════════════════════════════════════╗
║                                                      ║
║              ◎  JARVIS ORB  ◎                       ║
║         [particle field, breathing]                  ║
║                                                      ║
║               "How can I help?"                      ║
║                                                      ║
║                    [● MIC]                           ║
║                                                      ║
╚══════════════════════════════════════════════════════╝
[theme]                                    [settings]

STATE B: Listening
— Same as A but orb is 1.23× scale, waveform bar fades in below —

STATE C: Responding + Panel
╔═══════════════════════╦══════════════════════════════╗
║                       ║  ╔═════════════════════════╗ ║
║   ◎  ORB  ◎           ║  ║  [PANEL TITLE]      [×] ║ ║
║   [vox corona]        ║  ║                         ║ ║
║                       ║  ║  [panel content]        ║ ║
║  ┌───────────────┐    ║  ║                         ║ ║
║  │ JARVIS text   │    ║  ║  [draggable floating    ║ ║
║  │ streams here  │    ║  ║   overlay modal]        ║ ║
║  └───────────────┘    ║  ╚═════════════════════════╝ ║
║                       ║                              ║
╚═══════════════════════╩══════════════════════════════╝
   ← 2/3 viewport →           (panel is position:fixed)
```

### Themes
JARVIS extends the 5 existing Galaxy themes (Observatory, Cel Shade, Blueprint, Synthwave, Forge) with new behavioral CSS tokens, plus 2 JARVIS-exclusive themes:

| Theme | Vibe | Particle Color | Orb Glow |
|---|---|---|---|
| Observatory | Deep space, default | `#4d8df6` blue | `#ffb627` gold |
| Cel Shade | Cartoon, daytime | `#5be08a` green | `#ffd23f` yellow |
| Blueprint | Wireframe, technical | `#36d6e7` cyan | `#7fe8ff` ice blue |
| Synthwave | 80s neon grid | `#9a7bff` purple | `#c44af0` magenta |
| Forge | Ember/fire | `#ff6420` orange | `#ff8c20` amber |
| **Black Ice** *(new)* | Pure monochrome, cold | `rgba(200,220,240,0.6)` | `#8ab0d0` steel |
| **Chrome** *(new)* | Gunmetal silver | `#8090a8` | `#6080a0` |

Theme switching uses a `data-jarvis-theme` attribute on `<html>` — instant, no flash. A brief screen "blink" transition (150ms overlay) mimics a system restart for dramatic effect.

---

## Technical Architecture

### Stack (extending `feat/web-frontend`)
- **React 18 + TypeScript + Vite 5** — existing
- **Three.js v0.185** — existing (speaking vox corona)
- **Zustand** — lightweight state (panels, toasts, activity, theme)
- **interact.js** — panel drag + resize
- **Porcupine WASM** — wake word detection in Web Worker
- **Web Audio API** — AnalyserNode for vox visualization
- **Web Speech API** — primary STT (privacy-safe, no external call)
- **mlx-whisper** (Phase 2) — local Python STT bridge via FastAPI `localhost:5001`

### Architectural Principle: JARVIS = Shell, Galaxy = Panel

```
OLD: Vite entry → Galaxy (full screen)
NEW: Vite entry → JarvisShell → [Galaxy as iframe panel, on demand]
```

Galaxy moves into `src/galaxy/GalaxyApp.tsx` as a self-contained micro-frontend loaded in a `PanelFrame` iframe. Zero Galaxy code deleted — it becomes Panel #1.

### Voice Pipeline

```
PTT trigger (CMD+SHIFT+SPACE, hold-SPACE, mic button)
    │
    ▼
[Browser] MediaRecorder → Web Speech API (real-time transcript)
    │                    OR
    │              mlx-whisper bridge (POST /transcribe → localhost:5001)
    │
    ▼
Transcript → OpenCode backend (POST /api/session/{id}/message)
    │
    ▼
SSE event stream (/api/event) → activity steps → ActivityModal
    │
    ▼
Response text → TTS pipeline decision:
    ├── short (<120 chars) → macOS `say` command (instant, local)
    └── long (≥120 chars) → BMW Audio TTS API (quality, streaming)
    │
    ▼
Audio element → Web Audio AnalyserNode → particle vox corona
```

**PTT shortcuts:**
- `CMD+SHIFT+SPACE` — browser global (note: Tauri Phase 4 adds OS-level global shortcut)
- `SPACE` hold — when no text input is focused
- On-screen mic button — always visible

**Wake word (Phase 5 / always-on mode):**
- Porcupine WASM running in Web Worker
- Default: "Hey JARVIS" (configurable in settings)
- Wake word model: `wake-word-model.ppn` in `/public/jarvis/`
- Always-on is off by default; opt-in in settings

### Panel System

**Panel registry** (`panelRegistry.ts`):
```typescript
interface PanelDef {
  id: string;
  title: string;
  url: string;                    // iframe src
  defaultSize: { w: number; h: number };
  defaultPosition: { x: number; y: number };
  sandbox: string;                // iframe sandbox attr
}
```

**Built-in panels (v1):**
| Panel | URL | Notes |
|---|---|---|
| Memory Galaxy | `/galaxy/` (port 3001 in dev) | 3D Three.js orbital view |
| Blackboard | `/__blackboard` | Current agent task detail |
| Morning Briefing | `/__briefing` | Calendar + email |
| Token Tracker | `/__tokens` | Spend tracking |
| Project Status | `/__projects` | projects.db view |

Panels are `position: fixed`, draggable via interact.js, resizable. Multiple panels stack with +20px offset. Positions/sizes saved to `localStorage`.

### OpenCode Integration

**SSE event stream → JARVIS:**

| Event type | JARVIS action |
|---|---|
| `session.start` | Update active session display |
| `message.part` (tool_use) | Add activity modal step |
| `message.part` (text) | Stream JARVIS response text |
| `agent.complete` | Start TTS, update activity modal |
| `session.cost` | Update token tracker |
| `task.complete` (async) | Fire notification toast + orb pulse |

**Activity modal steps** fed from `message.part` tool_use events:
```typescript
interface ActivityStep {
  id: string;
  label: string;           // "Querying blackboard…"
  status: 'done' | 'active' | 'pending';
  durationMs?: number;     // shown for done steps
}
```

### CSS Token System

New JARVIS behavioral tokens (beyond existing Galaxy signal tokens):

```css
/* Core surfaces */
--jarvis-bg, --jarvis-surface, --jarvis-surface-alt
--jarvis-border, --jarvis-border-glow

/* Interaction states */
--jarvis-idle-particle, --jarvis-listen-particle, --jarvis-speak-particle
--jarvis-orb-glow, --jarvis-orb-ring

/* Text */
--jarvis-text-primary, --jarvis-text-secondary, --jarvis-text-code, --jarvis-text-accent

/* Notifications */
--jarvis-notify-bg, --jarvis-notify-border
--jarvis-notify-success, --jarvis-notify-warning, --jarvis-notify-error

/* Activity modal */
--jarvis-activity-bg
--jarvis-activity-step-done, --jarvis-activity-step-active, --jarvis-activity-step-pending

/* PTT button */
--jarvis-ptt-idle, --jarvis-ptt-idle-rgb
--jarvis-ptt-active, --jarvis-ptt-active-rgb, --jarvis-ptt-glow
```

**Shared animation easings:**
```css
--ease-spring:    cubic-bezier(0.34, 1.56, 0.64, 1);   /* slight overshoot */
--ease-out-expo:  cubic-bezier(0.16, 1, 0.3, 1);
--ease-out-cubic: cubic-bezier(0.33, 1, 0.68, 1);
--ease-in-cubic:  cubic-bezier(0.32, 0, 0.67, 0);
```

---

## Component Inventory

| Component | File | State | Priority |
|---|---|---|---|
| `JarvisShell` | `jarvis/JarvisShell.tsx` | Theme provider, layout root | P0 |
| `OrbContainer` | `jarvis/orb/OrbContainer.tsx` | Mounts Canvas2D or ThreeOrb | P0 |
| `Canvas2DOrb` | `jarvis/orb/Canvas2DOrb.tsx` | IDLE/LISTENING particle engine | P1 |
| `ThreeOrb` | `jarvis/orb/ThreeOrb.tsx` | SPEAKING vox corona | P3 |
| `ActivityModal` | `jarvis/activity/ActivityModal.tsx` | Step display, 15s dismiss | P1 |
| `ToastLayer` | `jarvis/notifications/ToastLayer.tsx` | Async notification stack | P2 |
| `PanelHost` | `jarvis/panels/PanelHost.tsx` | Renders all open panels | P2 |
| `PanelFrame` | `jarvis/panels/PanelFrame.tsx` | Draggable iframe wrapper | P2 |
| `InputBar` | `jarvis/input/InputBar.tsx` | Text input + PTT button | P1 |
| `VoiceController` | `jarvis/voice/VoiceController.tsx` | STT/TTS context | P2 |
| `PttManager` | `jarvis/voice/PttManager.ts` | Keyboard/button PTT state | P1 |
| `TtsPipeline` | `jarvis/voice/TtsPipeline.ts` | fast/quality path decision | P2 |
| `SettingsDrawer` | `jarvis/settings/SettingsDrawer.tsx` | Voice, theme, panels config | P3 |
| `WakeWordWorker` | `jarvis/voice/WakeWordWorker.worker.ts` | Porcupine WASM Web Worker | P5 |

---

## Implementation Phased Roadmap

### Phase 1 — Browser Shell MVP
**Goal:** JARVIS is the app entry point. Idle state looks right. PTT works. Text chat works.

**New files:**
```
src/jarvis/JarvisShell.tsx
src/jarvis/JarvisShell.css
src/jarvis/theme/jarvisThemeTokens.css
src/jarvis/theme/themes/{observatory,cel-shade,blueprint,synthwave,forge}.css
src/jarvis/theme/themeStore.ts
src/jarvis/orb/OrbContainer.tsx
src/jarvis/orb/Canvas2DOrb.tsx        ← SVG gyroscope rings + Canvas 2D particles
src/jarvis/orb/particleState.ts
src/jarvis/input/InputBar.tsx
src/jarvis/input/InputBar.css
src/jarvis/activity/ActivityModal.tsx
src/jarvis/activity/activityStore.ts
src/jarvis/activity/ActivityModal.css
src/jarvis/session/sseClient.ts
src/jarvis/session/SessionContext.tsx
```

**Modified files:**
```
src/main.tsx          → boot JarvisShell instead of Galaxy directly
src/galaxy/           → move existing GalaxyView into GalaxyApp.tsx (standalone)
vite.config.ts        → add /galaxy proxy for iframe panel
```

**New deps:**
```
zustand              # lightweight state
```

**Scope:**
- [x] Idle layout (orb centered, minimal chrome, theme switcher, settings icon)
- [x] Canvas2D orb: SVG gyroscope rings + idle particle field (48 particles, slow drift)
- [x] PTT button (on-screen only, Phase 1)
- [x] Listening state: orb scale + particle acceleration + waveform bar
- [x] Activity modal: appears when SSE tool_use events fire, 15s auto-dismiss
- [x] Text input (fallback to typed interaction)
- [x] SSE event stream connected
- [x] 5 themes fully tokenized

**Complexity:** L | **Estimated:** 3–4 weeks

---

### Phase 2 — Voice Integration
**Goal:** CMD+SHIFT+SPACE PTT works. JARVIS speaks back in British accent.

**New files:**
```
src/jarvis/voice/VoiceController.tsx
src/jarvis/voice/SttBridge.ts         ← Web Speech API adapter
src/jarvis/voice/TtsPipeline.ts       ← fast/quality handoff
src/jarvis/voice/TtsLocal.ts          ← macOS `say` via Vite middleware
src/jarvis/voice/TtsBmw.ts            ← BMW Audio TTS API
src/jarvis/voice/PttManager.ts        ← keyboard PTT state machine
src/jarvis/orb/audioAnalyser.ts       ← Web Audio AnalyserNode wrapper
scripts/tts-server.mjs                ← Vite middleware: POST /api/tts-local → `say`
```

**New deps:**
```
(none — Web Speech API and Web Audio are browser native)
```

**New Vite middleware:**
`/api/tts-local` → spawns `say -v "Daniel" -r 180 "..."` (macOS), returns MP3 via `ffmpeg -f avfoundation` capture or WAV passthrough

**TTS handoff rule:**
- Response ≤ 120 chars → `TtsLocal.ts` → macOS `say` (instant, offline)
- Response > 120 chars → `TtsBmw.ts` → BMW Audio TTS API (quality, streaming chunks)

**Scope:**
- [x] `CMD+SHIFT+SPACE` PTT (browser keydown listener + focus management)
- [x] `SPACE` hold PTT (when no input focused)
- [x] Web Speech API → transcript → OpenCode message
- [x] TTS pipeline: `say` for short, BMW TTS for long
- [x] Web Audio `AnalyserNode` wired to TTS audio output
- [x] Listening waveform bar (user mic input)
- [x] Notification toasts (SSE task.complete events)

**Complexity:** L | **Estimated:** 2–3 weeks

---

### Phase 3 — Vox Corona + Panel System
**Goal:** JARVIS speaks visually (particle vox). Galaxy and other panels open on command.

**New files:**
```
src/jarvis/orb/ThreeOrb.tsx           ← Three.js InstancedMesh speaking engine
src/jarvis/orb/shaders/orb.vert.glsl
src/jarvis/orb/shaders/orb.frag.glsl
src/jarvis/panels/PanelHost.tsx
src/jarvis/panels/PanelFrame.tsx
src/jarvis/panels/panelRegistry.ts
src/jarvis/panels/panelStore.ts
src/jarvis/panels/panels.css
src/jarvis/notifications/ToastLayer.tsx
src/jarvis/notifications/toastStore.ts
src/jarvis/notifications/ToastLayer.css
src/jarvis/settings/SettingsDrawer.tsx
src/jarvis/settings/SettingsDrawer.css
```

**New deps:**
```
interact.js          # panel drag + resize (12KB, no React dependency)
```

**Scope:**
- [x] ThreeOrb: `InstancedMesh` 120 particles, FFT-driven radial vox corona
- [x] SVG ↔ Three.js crossfade (400ms) on state transition
- [x] Layout shift: orb translateX(-16%) when panel opens
- [x] Panel Host: floating, draggable, resizable iframes
- [x] Panel registry: Galaxy, Blackboard, Morning Briefing, Token Tracker, Project Status
- [x] Panel persistence: positions/sizes in `localStorage`
- [x] JARVIS intent → panel open (parse response for panel intents)
- [x] Toast system: SSE async events → non-blocking notification stack
- [x] Settings Drawer: voice settings, wake word config, TTS voice selector, particle intensity slider
- [x] Black Ice + Chrome themes

**Complexity:** XL | **Estimated:** 4–5 weeks

---

### Phase 4 — Tauri Desktop App
**Goal:** JARVIS ships as a native macOS desktop app. OS-level global shortcut. Always on top.

**New files:**
```
src-tauri/                            ← Tauri scaffold
src-tauri/src/main.rs
src-tauri/tauri.conf.json
src-tauri/capabilities/
src/jarvis/platform/tauriShim.ts      ← `isTauri` capability shim
src/jarvis/voice/SttMlxBridge.ts      ← mlx-whisper HTTP bridge adapter
scripts/stt-bridge.py                 ← FastAPI STT server (dev) / Tauri sidecar (prod)
```

**New deps:**
```
@tauri-apps/api             # Tauri JS API
@tauri-apps/plugin-global-shortcut  # OS-level CMD+SHIFT+SPACE
@tauri-apps/plugin-shell    # invoke macOS `say` command
tauri-plugin-sql            # replaces better-sqlite3 for opencode.db access
```

**Key migrations:**
| Browser pattern | Tauri pattern |
|---|---|
| Vite `/api/tts-local` middleware | `tauri::command` shell invoke |
| `/__db` Vite bypass | `invoke("query_db", ...)` via tauri-plugin-sql |
| `/__memory` Vite bypass | `invoke("read_memory", ...)` |
| `CMD+SHIFT+SPACE` keydown listener | `globalShortcut.register("CmdOrCtrl+Shift+Space")` |

**mlx-whisper sidecar (optional, opt-in):**
- `scripts/stt-bridge.py` → PyInstaller → ARM64 binary → Tauri sidecar
- Registered in `tauri.conf.json` `externalBin`
- Frontend swaps `SttBridge.ts` → `SttMlxBridge.ts` when sidecar is running
- Falls back to Web Speech API if sidecar not available

**Window modes:**
```
Standard:    Normal window, 1440×900 default, resizable
Always-on:   `tauri::window::Window::set_always_on_top(true)`, transparent chrome
Overlay:     Transparent background, click-through regions for non-JARVIS areas
```

**Complexity:** XL | **Estimated:** 3–4 weeks

---

### Phase 5 — Always-On & Wake Word
**Goal:** JARVIS listens in the background. Say "Hey JARVIS" → it activates.

**New files:**
```
public/jarvis/wake-word-model.ppn     ← Porcupine keyword model
src/jarvis/voice/WakeWordWorker.ts
src/jarvis/voice/WakeWordWorker.worker.ts
src/jarvis/settings/WakeWordSettings.tsx
```

**New deps:**
```
@picovoice/porcupine-web              # WASM wake word engine (~3MB)
```

**Scope:**
- [x] Porcupine WASM in Web Worker (doesn't block main thread)
- [x] Wake word configurable: "Hey JARVIS" default, text field in settings
- [x] Always-on toggle (off by default) in settings
- [x] When activated by wake word: orb pulses once, PTT auto-starts
- [x] When Tauri: mic permission persists, always-on survives app minimize
- [x] Privacy indicator: subtle green dot when mic is live

**Complexity:** M | **Estimated:** 1–2 weeks

---

## Dependency Summary

| Package | Version | Phase | Purpose |
|---|---|---|---|
| `zustand` | `^4.5` | P1 | State management |
| `interact.js` | `^1.10` | P3 | Panel drag/resize |
| `@picovoice/porcupine-web` | `^3.0` | P5 | Wake word WASM |
| `@tauri-apps/api` | `^2.x` | P4 | Tauri JS bridge |
| `@tauri-apps/plugin-global-shortcut` | `^2.x` | P4 | OS shortcut |
| `@tauri-apps/plugin-shell` | `^2.x` | P4 | `say` command |
| `tauri-plugin-sql` | `^2.x` | P4 | DB access |

**All other capabilities (Three.js, React, Vite, Web Audio, Web Speech API, SSE) are already present or browser-native.**

---

## Implementation Priority Order (Within Phases)

| Priority | Component | Why first |
|---|---|---|
| P0 | CSS token system + theme switching | Foundation — everything depends on it |
| P0 | Static JARVIS layout (3 layout states) | Shell without interaction |
| P1 | SVG Orb (idle animation) | Identity, first impression |
| P1 | PTT Button + keyboard shortcuts | Core interaction |
| P1 | Activity Modal | Shows JARVIS is working |
| P2 | Particle canvas engine (idle + listen) | Visual richness |
| P2 | Panel Container (draggable overlay) | Panel hosting |
| P2 | Notification Toast system | Async delivery |
| P3 | Three.js speaking vox corona | Premium feel |
| P3 | Web Audio API integration | Required for vox corona |
| P3 | Always-on wake word detection | Optional feature |
| P4 | Settings Drawer (full) | Configuration |
| P4 | Black Ice / Chrome themes | Extensions |
| P5 | Sound design micro-interactions | Polish |
| P5 | Reduced-motion full audit | Accessibility |

---

## Key Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| JARVIS vs Galaxy architecture | JARVIS = shell, Galaxy = panel | Zero existing code deleted; Galaxy becomes Panel #1 |
| Component library | Raw React + CSS custom properties | Precise control over particles, glassmorphism, glow |
| State management | Zustand | Lightweight, no boilerplate, works outside React tree |
| Panel drag/resize | interact.js | React DnD doesn't handle resize; Floating UI is position-only |
| STT primary | Web Speech API | Zero deps, private (no network), instant setup |
| STT quality | mlx-whisper bridge | Apple Silicon M3 Pro native, PyInstaller sidecar in Tauri |
| TTS fast path | macOS `say` command | Instant, offline, British "Daniel" voice available natively |
| TTS quality path | BMW Audio TTS API | Existing auth, higher quality for long responses |
| TTS handoff rule | 120-character threshold | Empirically: short answers feel snappier from `say`; long responses need quality |
| Wake word | Porcupine WASM | ~3MB bundle, Web Worker (non-blocking), free tier covers "Jarvis" |
| Theme system | `data-jarvis-theme` on `<html>` | Instant, no flash, cascades to all panels |
| Theme transition | Screen "blink" overlay 150ms | Minority Report system-restart aesthetic; no partial state |
| Particle idle/listen | Canvas 2D | Lightweight, no Three.js overhead in idle state |
| Particle speaking | Three.js InstancedMesh | Single draw call, M3 Pro handles 120 instances trivially |
| Panel IPC | `postMessage` to iframe | Standard, sandboxed, works browser and Tauri |
| Desktop Tauri migration | Phase 4 | Browser-first validates UX before shipping a full native app |

---

## Full Data Flow: Single PTT Interaction

```
1. User presses CMD+SHIFT+SPACE
   → PttManager.ts: state IDLE → LISTENING
   → Canvas2DOrb: particle energy tween 0.2 → 0.85, 600ms ease-out-cubic
   → Orb: scale 1.0 → 1.23, 400ms spring
   → Waveform bar: fade in, 200ms
   → MediaRecorder: start (Web Speech API real-time transcript OR mlx-whisper)

2. User speaks. Waveform bar animates with mic input.

3. User releases CMD+SHIFT+SPACE
   → MediaRecorder: stop
   → PttManager: state LISTENING → THINKING
   → Waveform bar: fade out
   → Transcript ready

4. Transcript → fetch POST /api/session/{id}/message
   → Activity modal appears (step: "Sending to OpenCode…")

5. OpenCode processes. SSE events stream back.
   → Each `message.part` tool_use → new ActivityModal step
   → Steps animate in: translateY(4px)→0, opacity 0→1, 150ms

6. Response ready. TTS pipeline:
   → len(response) < 120 → TtsLocal: fetch /api/tts-local → `say -v Daniel`
   → len(response) ≥ 120 → TtsBmw: BMW Audio TTS API → streaming MP3

7. Audio starts playing.
   → Web Audio AnalyserNode attaches to audio element
   → PttManager: THINKING → SPEAKING
   → Canvas2D fades out, Three.js ThreeOrb fades in (400ms crossfade)
   → InstancedMesh: 120 particles, FFT-driven radial vox corona begins
   → Response text streams into JARVIS response area

8. Audio ends.
   → ActivityModal: last step → "Complete ✓"
   → 15s dismiss countdown bar begins
   → Vox corona: particles decelerate (energy 1.0 → 0.15 over 1500ms)
   → ThreeOrb → Canvas2DOrb crossfade (after 600ms cooldown)
   → PttManager: SPEAKING → IDLE
   → Orb: scale returns to 1.0, 800ms ease-out-cubic

9. [Auto 15s or user clicks ×]
   → ActivityModal dismisses (exit anim 220ms)
   → Layout returns to full-width idle
```

---

## File Structure (Additions to `feat/web-frontend`)

```
~/.config/opencode/web/
├── src/
│   ├── main.tsx                          # MODIFIED: boots JarvisShell
│   │
│   ├── jarvis/                           # NEW
│   │   ├── JarvisShell.tsx
│   │   ├── JarvisShell.css
│   │   │
│   │   ├── orb/
│   │   │   ├── OrbContainer.tsx
│   │   │   ├── Canvas2DOrb.tsx
│   │   │   ├── ThreeOrb.tsx
│   │   │   ├── particleState.ts
│   │   │   └── audioAnalyser.ts
│   │   │
│   │   ├── voice/
│   │   │   ├── VoiceController.tsx
│   │   │   ├── SttBridge.ts
│   │   │   ├── SttMlxBridge.ts
│   │   │   ├── WakeWordWorker.worker.ts
│   │   │   ├── TtsPipeline.ts
│   │   │   ├── TtsLocal.ts
│   │   │   ├── TtsBmw.ts
│   │   │   └── PttManager.ts
│   │   │
│   │   ├── panels/
│   │   │   ├── PanelHost.tsx
│   │   │   ├── PanelFrame.tsx
│   │   │   ├── panelRegistry.ts
│   │   │   ├── panelStore.ts
│   │   │   └── panels.css
│   │   │
│   │   ├── activity/
│   │   │   ├── ActivityModal.tsx
│   │   │   ├── activityStore.ts
│   │   │   └── ActivityModal.css
│   │   │
│   │   ├── notifications/
│   │   │   ├── ToastLayer.tsx
│   │   │   ├── toastStore.ts
│   │   │   └── ToastLayer.css
│   │   │
│   │   ├── session/
│   │   │   ├── SessionContext.tsx
│   │   │   └── sseClient.ts
│   │   │
│   │   ├── input/
│   │   │   ├── InputBar.tsx
│   │   │   └── InputBar.css
│   │   │
│   │   ├── settings/
│   │   │   ├── SettingsDrawer.tsx
│   │   │   └── SettingsDrawer.css
│   │   │
│   │   └── theme/
│   │       ├── jarvisThemeTokens.css
│   │       ├── themeStore.ts
│   │       └── themes/
│   │           ├── observatory.css
│   │           ├── cel-shade.css
│   │           ├── blueprint.css
│   │           ├── synthwave.css
│   │           ├── forge.css
│   │           ├── black-ice.css         # new
│   │           └── chrome.css            # new
│   │
│   ├── galaxy/                           # MODIFIED: moved from root
│   │   ├── GalaxyApp.tsx                 # standalone app when loaded as iframe
│   │   └── ... (existing code)
│   │
│   └── shared/
│       ├── useOpenCodeSSE.ts
│       └── types.ts
│
├── scripts/
│   ├── tts-server.mjs                    # Vite middleware for macOS `say`
│   └── stt-bridge.py                     # mlx-whisper FastAPI bridge
│
└── public/
    └── jarvis/
        └── wake-word-model.ppn           # Porcupine model (Phase 5)
```

---

## Milestones & Timeline Estimate

| Phase | Milestone | Est. Duration | Status |
|---|---|---|---|
| P1 | Browser Shell MVP — idle, PTT, activity modal, themes | 3–4 weeks | 🔵 Planned |
| P2 | Voice integration — STT, TTS, `say` bridge, toasts | 2–3 weeks | 🔵 Planned |
| P3 | Vox corona + panel system + settings | 4–5 weeks | 🔵 Planned |
| P4 | Tauri desktop app + mlx-whisper + global shortcut | 3–4 weeks | 🔵 Planned |
| P5 | Always-on + wake word + polish | 1–2 weeks | 🔵 Planned |

**Total estimated:** 13–18 weeks (working alongside other projects)

---

## Appendix: Reference Files

| File | Purpose |
|---|---|
| `/Users/QTE2362/ECC-APPS/memory-galaxy.html` | Source Galaxy HTML — 5 theme definitions, orbital metaphor, CSS tokens |
| `/Users/QTE2362/.config/opencode/web/JARVIS-ARCHITECTURE-SPEC.md` | Full technical architecture spec (programming-expert output) |
| `/Users/QTE2362/ECC-APPS/jarvis-design-refs/jarvis-idle-observatory.png` | Design ref: idle state, Observatory theme |
| `/Users/QTE2362/ECC-APPS/jarvis-design-refs/jarvis-speaking-vox.png` | Design ref: speaking with vox corona active |
| `/Users/QTE2362/ECC-APPS/jarvis-design-refs/jarvis-panel-galaxy.png` | Design ref: panel-open state, Galaxy panel |
| `/Users/QTE2362/ECC-APPS/jarvis-design-refs/jarvis-listening-synthwave.png` | Design ref: listening state, Synthwave theme |

---

*JARVIS Frontend Roadmap v1.0 — BMW Internal — 2026-06-26*
*Spec produced by: design-expert (UX/visual) + programming-expert (architecture)*
*Ready for Phase 1 implementation on `feat/web-frontend` branch*
