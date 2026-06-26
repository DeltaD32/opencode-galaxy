# JARVIS GUI Frontend — Technical Architecture Specification

**Target branch:** `feat/web-frontend`  
**Base:** `~/.config/opencode/web/` (React 18 + TypeScript + Vite 5 + Three.js v0.185 + 3d-force-graph)  
**Date:** 2026-06-26  
**Status:** Pre-implementation design document

---

## Table of Contents

1. [Project Structure](#1-project-structure)
2. [Voice Pipeline Architecture](#2-voice-pipeline-architecture)
3. [Particle System Architecture](#3-particle-system-architecture)
4. [Panel System Architecture](#4-panel-system-architecture)
5. [OpenCode Integration](#5-opencode-integration)
6. [Theme System Implementation](#6-theme-system-implementation)
7. [Tauri Desktop Integration (Phase 2)](#7-tauri-desktop-integration)
8. [Data Flow Diagram](#8-data-flow-diagram)
9. [Build & Dev Setup](#9-build--dev-setup)
10. [Phase Roadmap](#10-phase-roadmap)

---

## 1. Project Structure

### 1.1 Architectural Decision: JARVIS as the App Shell

JARVIS is the **top-level shell** — it is not a new route inside Galaxy. Galaxy (the 3D
memory graph) becomes one of several panels that JARVIS can host. The single Vite entry
point (`src/main.tsx`) boots JARVIS. Galaxy is loaded on demand inside a panel iframe.

```
┌─────────────────────────────────────────────────────────────────┐
│                         JARVIS Shell                            │
│  ┌──────────────┐  ┌───────────────────────────────────────┐   │
│  │  Orb / Vox   │  │           Panel Host Layer             │   │
│  │  (canvas +   │  │  ┌─────────┐ ┌──────────┐ ┌────────┐  │   │
│  │   Three.js)  │  │  │ Galaxy  │ │Blackboard│ │Morning │  │   │
│  └──────────────┘  │  │ iframe  │ │  iframe  │ │Briefing│  │   │
│  ┌──────────────┐  │  └─────────┘ └──────────┘ └────────┘  │   │
│  │ Input / PTT  │  └───────────────────────────────────────┘   │
│  └──────────────┘                                               │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │           Activity Modal + Toast layer                    │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 File/Folder Layout

```
~/.config/opencode/web/
├── index.html                        # unchanged — mounts #root
├── vite.config.ts                    # add JARVIS panel dev-server proxy
├── tailwind.config.ts                # extend with JARVIS tokens
├── package.json
│
├── public/
│   ├── bmw-icon.svg
│   └── jarvis/
│       └── wake-word-model.ppn       # Porcupine keyword model (Phase 5)
│
└── src/
    ├── main.tsx                      # entry — renders <JarvisShell />
    ├── index.css                     # import jarvis tokens AFTER existing base
    │
    ├── jarvis/                       # ★ new — all JARVIS-specific code
    │   ├── JarvisShell.tsx           # root component; theme provider; panel host
    │   ├── JarvisShell.css           # CSS variable overrides per theme
    │   │
    │   ├── orb/
    │   │   ├── OrbContainer.tsx      # mounts either Canvas2D or Three.js orb
    │   │   ├── Canvas2DOrb.tsx       # IDLE / LISTENING states
    │   │   ├── ThreeOrb.tsx          # SPEAKING state — InstancedMesh
    │   │   ├── particleState.ts      # state machine + shared types
    │   │   ├── audioAnalyser.ts      # Web Audio AnalyserNode wrapper
    │   │   └── shaders/
    │   │       ├── orb.vert.glsl
    │   │       └── orb.frag.glsl
    │   │
    │   ├── voice/
    │   │   ├── VoiceController.tsx   # React context — exposes startSTT / stopSTT
    │   │   ├── SttBridge.ts          # browser Web Speech API adapter
    │   │   ├── SttMlxBridge.ts       # mlx-whisper HTTP bridge adapter
    │   │   ├── WakeWordWorker.ts     # Web Worker — porcupine WASM loop
    │   │   ├── WakeWordWorker.worker.ts
    │   │   ├── TtsPipeline.ts        # decides fast/quality path; schedules chunks
    │   │   ├── TtsLocal.ts           # macOS `say` via fetch /api/tts-local
    │   │   ├── TtsBmw.ts             # BMW Audio TTS API caller
    │   │   └── PttManager.ts         # keyboard/button PTT state machine
    │   │
    │   ├── panels/
    │   │   ├── PanelHost.tsx         # renders all open panels
    │   │   ├── PanelFrame.tsx        # single draggable/resizable iframe
    │   │   ├── panelRegistry.ts      # built-in + dynamic panel definitions
    │   │   ├── panelStore.ts         # zustand store — open panels, positions
    │   │   └── panels.css
    │   │
    │   ├── activity/
    │   │   ├── ActivityModal.tsx     # step-by-step thinking display
    │   │   ├── activityStore.ts      # zustand store — current steps
    │   │   └── ActivityModal.css
    │   │
    │   ├── notifications/
    │   │   ├── ToastLayer.tsx        # non-blocking toast container
    │   │   ├── toastStore.ts         # zustand store — toast queue
    │   │   └── ToastLayer.css
    │   │
    │   ├── session/
    │   │   ├── SessionContext.tsx    # active session / agent / cost
    │   │   └── sseClient.ts         # SSE connection to localhost:4096/api/event
    │   │
    │   ├── input/
    │   │   ├── InputBar.tsx          # text input + PTT button
    │   │   └── InputBar.css
    │   │
    │   └── theme/
    │       ├── jarvisThemeTokens.css # JARVIS-specific CSS custom properties
    │       ├── themeStore.ts         # zustand + localStorage persistence
    │       └── themes/
    │           ├── observatory.css
    │           ├── cel-shade.css
    │           ├── blueprint.css
    │           ├── synthwave.css
    │           └── forge.css
    │
    ├── galaxy/                       # ★ moved — Galaxy is now a panel app
    │   ├── GalaxyApp.tsx             # standalone entry when loaded in iframe
    │   ├── GalaxyApp.css
    │   └── ... (existing Galaxy Three.js code)
    │
    └── shared/
        ├── useOpenCodeSSE.ts         # shared SSE hook
        └── types.ts                  # shared TypeScript interfaces
```

### 1.3 Component Library Decision

**Raw React + CSS custom properties.** No heavy UI library.

Rationale:
- JARVIS aesthetic requires precise control over particle rendering, glassmorphism,
  glow effects — component libraries fight this.
- Existing Galaxy codebase already uses raw Tailwind + custom CSS. Consistency matters.
- Tailwind stays for layout utilities; JARVIS-specific visual tokens go in CSS custom
  properties defined in `jarvisThemeTokens.css`.
- Exception: `interact.js` for panel drag/resize (see §4.4).

### 1.4 Galaxy as a Panel

Galaxy's existing `src/` becomes `src/galaxy/`. It is served by a second Vite dev server
(port 3001) and embedded as `http://localhost:3001` in a JARVIS panel iframe. In the Tauri
build, Galaxy is bundled as a separate HTML entry point via Vite's multi-page build.

```ts
// vite.config.ts — multi-page build
export default defineConfig({
  build: {
    rollupOptions: {
      input: {
        jarvis: 'index.html',       // JARVIS shell (port 5173 in dev)
        galaxy: 'galaxy.html',      // Galaxy panel (port 3001 in dev)
      }
    }
  }
})
```

---

## 2. Voice Pipeline Architecture

### 2.1 STT Architecture

#### Option A: Browser Web Speech API (primary, recommended)

```
Microphone → MediaStream → SpeechRecognition (browser built-in)
                                    ↓
                          continuous: true, interimResults: true
                                    ↓
                          onresult → transcript string
                                    ↓
                          VoiceController.onTranscript(text)
```

**Pros:** Zero setup, works immediately in Chrome/Safari, no Python dependency, private
(runs in browser engine, not sent to cloud — Chromium on macOS uses Apple STT locally).  
**Cons:** Less accurate than Whisper for code/technical terms; requires page focus in
browser (not solvable in Vite dev mode, only solved in Tauri Phase 2).

#### Option B: mlx-whisper bridge (optional upgrade, macOS only)

mlx-whisper runs as a local Python process. It cannot run in a browser context. The
integration pattern is a **local HTTP bridge server**:

```
┌─────────────────────────────────────────────────────────────────┐
│  Browser                                                        │
│  MediaRecorder → chunks (float32 PCM) → POST /api/stt/whisper  │
│                                              ↓                  │
│                              Vite dev server /api proxy         │
│                                              ↓                  │
│                        Python bridge (localhost:5001)           │
│                        ┌─────────────────────────────────────┐  │
│                        │  mlx_whisper.transcribe(audio_data)  │  │
│                        │  model: "mlx-community/whisper-base" │  │
│                        └──────────────┬──────────────────────┘  │
│                                       ↓                         │
│                        {"text": "...", "language": "en"}        │
└─────────────────────────────────────────────────────────────────┘
```

**Python bridge** (`~/.config/opencode/web/scripts/stt-bridge.py`):
```python
from fastapi import FastAPI, UploadFile
import mlx_whisper, tempfile, io, numpy as np, soundfile as sf

app = FastAPI()

@app.post("/transcribe")
async def transcribe(audio: UploadFile):
    data, sr = sf.read(io.BytesIO(await audio.read()))
    result = mlx_whisper.transcribe(data, path_or_hf_repo="mlx-community/whisper-base-mlx")
    return {"text": result["text"]}
```

**Recommendation:** Start with **Web Speech API** (Option A). It ships in Phase 2 with
zero infrastructure. Add Option B as a user-configurable backend in Phase 3 via a setting
toggle. The SttBridge interface abstracts both:

```ts
// src/jarvis/voice/SttBridge.ts
export interface SttBackend {
  start(opts: SttOptions): void
  stop(): Promise<string>  // returns final transcript
  onInterim: (cb: (text: string) => void) => void
}
```

### 2.2 PTT Implementation

#### Browser Vite dev mode

`CMD+SHIFT+SPACE` is registerable via `keydown` event on `document`:

```ts
// src/jarvis/voice/PttManager.ts
export class PttManager {
  private active = false

  constructor(private onStart: () => void, private onStop: () => void) {
    document.addEventListener('keydown', this.handleKey)
    document.addEventListener('keyup',   this.handleKey)
  }

  private handleKey = (e: KeyboardEvent) => {
    const isPtt = e.code === 'Space' && e.metaKey && e.shiftKey
    if (!isPtt) return
    e.preventDefault()
    if (e.type === 'keydown' && !this.active) {
      this.active = true
      this.onStart()
    } else if (e.type === 'keyup' && this.active) {
      this.active = false
      this.onStop()
    }
  }

  destroy() {
    document.removeEventListener('keydown', this.handleKey)
    document.removeEventListener('keyup',   this.handleKey)
  }
}
```

**Browser limitation:** `CMD+SHIFT+SPACE` is not globally capturable when the browser
window lacks focus. This is a hard browser security boundary. In Vite dev mode, the
window must be focused. Resolution in Tauri Phase 2 (see §7.1).

#### PTT activation modes

| Mode | Trigger | Phase |
|------|---------|-------|
| Hold-Space | Hold CMD+SHIFT+SPACE | Phase 1 (browser) |
| On-screen button | PTT button in InputBar | Phase 1 (browser) |
| Global shortcut | Tauri globalShortcut plugin | Phase 2 (Tauri) |

### 2.3 Wake Word Detection

**Recommendation: `@picovoice/porcupine-web`**

Comparison:
| Option | WASM? | Offline? | Custom KW? | Bundle size | Quality |
|--------|-------|----------|------------|-------------|---------|
| Porcupine WASM | ✓ | ✓ | ✓ (.ppn) | ~3 MB | Best |
| vosk-wasm | ✓ | ✓ | grammar-based | ~50 MB | Good |
| ONNX Runtime + custom | ✓ | ✓ | needs training | ~6 MB | Variable |
| Silero VAD | ✓ | ✓ | VAD only, no KW | ~2 MB | N/A |

Porcupine wins: small model, proven library, free tier includes "Hey Siri"/"Jarvis"
keyword, configurable wake word via `.ppn` file, runs entirely in a Web Worker.

```ts
// src/jarvis/voice/WakeWordWorker.worker.ts
import { PorcupineWorker } from '@picovoice/porcupine-web'

let worker: PorcupineWorker | null = null

self.onmessage = async (e) => {
  if (e.data.type === 'init') {
    worker = await PorcupineWorker.create(
      e.data.accessKey,
      [{ label: 'hey-jarvis', publicPath: '/jarvis/hey-jarvis_en_wasm_v3_0_0.ppn' }],
      ({ label }) => {
        if (label === 'hey-jarvis') self.postMessage({ type: 'wake' })
      },
      { publicPath: '/jarvis/porcupine_params.pv' }
    )
    await worker.start()
  }
  if (e.data.type === 'stop') worker?.stop()
}
```

**Worker bridge in React:**
```ts
// src/jarvis/voice/WakeWordWorker.ts
export function createWakeWordWorker(onWake: () => void) {
  const worker = new Worker(
    new URL('./WakeWordWorker.worker.ts', import.meta.url),
    { type: 'module' }
  )
  worker.onmessage = (e) => {
    if (e.data.type === 'wake') onWake()
  }
  return {
    start: (accessKey: string) => worker.postMessage({ type: 'init', accessKey }),
    stop: () => worker.postMessage({ type: 'stop' }),
    destroy: () => worker.terminate(),
  }
}
```

Note: Porcupine free tier requires an access key from Picovoice console (no cloud
calls — key just unlocks local WASM). Store in `.env.local` as `VITE_PICOVOICE_KEY`.

### 2.4 TTS Pipeline

```
JARVIS response text
        │
        ▼
 TtsPipeline.speak(text, opts)
        │
   char count > 120  ─── YES ──▶  BMW Audio TTS API (streaming)
   OR opts.quality?                        │
        │                          chunked MP3 → AudioContext
        NO                                 │
        │                         AnalyserNode → particle engine
        ▼
 macOS `say` command (fast)
 (via fetch /api/tts-say in dev;
  Tauri invoke in Phase 2)
        │
        ▼
 system audio out → AnalyserNode
```

#### Local fast path (`TtsLocal.ts`)

In browser dev mode, Vite's custom middleware serves a `/api/tts-say` endpoint:

```ts
// vite.config.ts — custom middleware
import { exec } from 'node:child_process'

server: {
  middlewares: [
    (req, res, next) => {
      if (req.url !== '/api/tts-say') return next()
      let body = ''
      req.on('data', c => body += c)
      req.on('end', () => {
        const { text, voice = 'Samantha' } = JSON.parse(body)
        // sanitize: strip shell metacharacters
        const safe = text.replace(/[`$"\\]/g, '')
        exec(`say -v "${voice}" "${safe}"`)
        res.end('ok')
      })
    }
  ]
}
```

**Voices available on M3 Pro macOS:** Samantha (en-US), Alex (en-US), Daniel (en-GB),
Siri (system). Default: `Samantha` (Neural, sounds good).

#### BMW Audio TTS path (`TtsBmw.ts`)

```ts
export async function* streamBmwTts(
  text: string,
  voice = 'nova'
): AsyncGenerator<ArrayBuffer> {
  const res = await fetch('https://api.gcp.cloud.bmw/audio/v1/speech', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${import.meta.env.VITE_LLM_API_BEARER_TOKEN}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ model: 'tts-1', input: text, voice, response_format: 'mp3' })
  })
  const reader = res.body!.getReader()
  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    yield value.buffer
  }
}
```

#### Handoff decision logic

```ts
// src/jarvis/voice/TtsPipeline.ts
const FAST_PATH_THRESHOLD = 120  // characters

export async function speak(text: string, opts?: { forceQuality?: boolean }) {
  const useQuality = opts?.forceQuality || text.length > FAST_PATH_THRESHOLD
  
  if (!useQuality) {
    await fetch('/api/tts-say', {
      method: 'POST',
      body: JSON.stringify({ text })
    })
    return
  }
  
  // Quality path: stream to Web Audio
  const ctx = getAudioContext()
  const analyser = getAnalyserNode()
  const source = ctx.createBufferSource()
  
  const chunks: ArrayBuffer[] = []
  for await (const chunk of streamBmwTts(text)) {
    chunks.push(chunk)
  }
  
  const combined = concatBuffers(chunks)
  const decoded = await ctx.decodeAudioData(combined)
  source.buffer = decoded
  source.connect(analyser)
  analyser.connect(ctx.destination)
  source.start()
  source.onended = () => particleStateStore.transition('SPEAKING', 'IDLE')
}
```

### 2.5 Web Audio API Integration

```ts
// src/jarvis/orb/audioAnalyser.ts
let _ctx: AudioContext | null = null
let _analyser: AnalyserNode | null = null

export function getAudioContext(): AudioContext {
  if (!_ctx) _ctx = new AudioContext()
  return _ctx
}

export function getAnalyserNode(): AnalyserNode {
  if (!_analyser) {
    _analyser = getAudioContext().createAnalyser()
    _analyser.fftSize = 256        // 128 frequency bins — enough for visual
    _analyser.smoothingTimeConstant = 0.8
  }
  return _analyser
}

// Called every animation frame by the particle engine
export function getEnergyBands(): { low: number; mid: number; high: number } {
  const analyser = getAnalyserNode()
  const data = new Uint8Array(analyser.frequencyBinCount)  // 128 bins
  analyser.getByteFrequencyData(data)
  
  const binSize = data.length / 3
  const avg = (arr: Uint8Array, start: number, end: number) =>
    Array.from(arr.slice(start, end)).reduce((a, b) => a + b, 0) / (end - start) / 255

  return {
    low:  avg(data, 0, binSize),
    mid:  avg(data, binSize, binSize * 2),
    high: avg(data, binSize * 2, data.length),
  }
}
```

Also connect microphone input (during LISTENING) so the orb reacts to the user's voice:

```ts
export async function connectMicToAnalyser(): Promise<() => void> {
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
  const source = getAudioContext().createMediaStreamSource(stream)
  source.connect(getAnalyserNode())
  return () => { source.disconnect(); stream.getTracks().forEach(t => t.stop()) }
}
```

---

## 3. Particle System Architecture

### 3.1 State Machine

```
       ┌──────────────┐
       │     IDLE     │◀──────────────────────────────┐
       │  Canvas 2D   │                               │
       └──────┬───────┘                               │
              │ PTT press / wake word                  │
              ▼                                        │ response done
       ┌──────────────┐                               │ (15s timeout)
       │  LISTENING   │                               │
       │  Canvas 2D   │                               │
       │  + mic input │                               │
       └──────┬───────┘                               │
              │ STT result / PTT release              │
              ▼                                        │
       ┌──────────────┐                               │
       │   THINKING   │                               │
       │  Canvas 2D   │                               │
       │  (spinner)   │───────────────────────────────┤
       └──────┬───────┘   OpenCode error/cancel       │
              │ TTS starts                            │
              ▼                                        │
       ┌──────────────┐                               │
       │   SPEAKING   │───────────────────────────────┘
       │  Three.js    │
       │  InstancedMesh│
       └──────────────┘
```

**TypeScript state machine:**

```ts
// src/jarvis/orb/particleState.ts
export type OrbState = 'IDLE' | 'LISTENING' | 'THINKING' | 'SPEAKING'

type Transition = {
  from: OrbState | OrbState[]
  to: OrbState
  trigger: string
}

const TRANSITIONS: Transition[] = [
  { from: 'IDLE',      to: 'LISTENING', trigger: 'ptt_start | wake_word' },
  { from: 'LISTENING', to: 'THINKING',  trigger: 'ptt_stop | stt_result'  },
  { from: 'THINKING',  to: 'SPEAKING',  trigger: 'tts_start'              },
  { from: 'THINKING',  to: 'IDLE',      trigger: 'error | cancel'         },
  { from: 'SPEAKING',  to: 'IDLE',      trigger: 'tts_end'                },
]

import { create } from 'zustand'

interface OrbStore {
  state: OrbState
  transition: (trigger: string) => void
}

export const useOrbStore = create<OrbStore>((set, get) => ({
  state: 'IDLE',
  transition: (trigger) => {
    const current = get().state
    const t = TRANSITIONS.find(t => {
      const froms = Array.isArray(t.from) ? t.from : [t.from]
      return froms.includes(current) && t.trigger.includes(trigger)
    })
    if (t) set({ state: t.to })
  }
}))
```

### 3.2 Canvas 2D Orb (IDLE / LISTENING / THINKING)

Data structures:

```ts
// src/jarvis/orb/Canvas2DOrb.tsx
interface Particle {
  x: number; y: number
  vx: number; vy: number
  life: number         // 0..1 — normalized age
  maxLife: number      // seconds
  size: number
  opacity: number
  color: string        // from theme token --jarvis-orb-particle-color
}

interface Canvas2DOrbState {
  particles: Particle[]
  canvas: HTMLCanvasElement
  ctx: CanvasRenderingContext2D
  raf: number
  lastTime: number
  orbState: OrbState
}
```

Update loop (60fps target, M3 Pro handles 120fps — cap at screen refresh):

```ts
function update(state: Canvas2DOrbState, dt: number) {
  const { low, mid, high } = getEnergyBands()
  const energy = orbState === 'LISTENING' ? mid * 2 : 0.2  // base idle energy

  // Spawn new particles based on energy
  const spawnCount = Math.floor(energy * 8)
  for (let i = 0; i < spawnCount && state.particles.length < MAX_PARTICLES; i++) {
    spawnParticle(state, energy)
  }

  // Update existing
  state.particles = state.particles.filter(p => {
    p.life += dt
    const t = p.life / p.maxLife
    p.x += p.vx * dt
    p.y += p.vy * dt
    // Gravity toward orb center with slight spiral
    const dx = CENTER_X - p.x, dy = CENTER_Y - p.y
    const dist = Math.hypot(dx, dy)
    p.vx += (dx / dist) * 30 * dt
    p.vy += (dy / dist) * 30 * dt
    p.opacity = Math.sin(t * Math.PI)  // fade in/out
    return t < 1.0
  })
}

function draw(state: Canvas2DOrbState) {
  const { ctx, canvas } = state
  // Clear with trail effect (not full clear — ghosting)
  ctx.fillStyle = 'rgba(0,0,0,0.08)'
  ctx.fillRect(0, 0, canvas.width, canvas.height)

  // Draw orb core glow
  const gradient = ctx.createRadialGradient(CENTER_X, CENTER_Y, 0, CENTER_X, CENTER_Y, ORB_RADIUS)
  gradient.addColorStop(0, getCssVar('--jarvis-orb-core'))
  gradient.addColorStop(1, 'transparent')
  ctx.fillStyle = gradient
  ctx.beginPath(); ctx.arc(CENTER_X, CENTER_Y, ORB_RADIUS, 0, Math.PI * 2)
  ctx.fill()

  // Draw particles
  state.particles.forEach(p => {
    ctx.globalAlpha = p.opacity
    ctx.fillStyle = p.color
    ctx.beginPath(); ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2)
    ctx.fill()
  })
  ctx.globalAlpha = 1
}
```

**Performance budget for Canvas 2D:**
- `MAX_PARTICLES = 400` (IDLE), `800` (LISTENING), `600` (THINKING)
- Canvas resolution: `devicePixelRatio * 300px` (i.e., 600px on M3 Retina = 2×)
- Target: ≥60fps. Profile with Chrome Perf: Canvas 2D draws at ~0.3ms at 400 particles.

### 3.3 Three.js InstancedMesh Orb (SPEAKING)

The Three.js orb shares the **same `<canvas>` element** as the Canvas 2D renderer. The
handoff works by:

1. Canvas 2D calls `ctx.clearRect()` on transition to SPEAKING
2. Three.js renderer is initialized with `canvas: existingCanvasElement` in its
   `WebGLRenderer` constructor
3. On transition back to IDLE, Three.js renderer's `dispose()` is called; Canvas 2D
   resumes with a fresh `raf` loop

```tsx
// src/jarvis/orb/ThreeOrb.tsx
import * as THREE from 'three'

const PARTICLE_COUNT = 3000

export function ThreeOrb({ canvas }: { canvas: HTMLCanvasElement }) {
  useEffect(() => {
    const renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true })
    renderer.setPixelRatio(window.devicePixelRatio)
    renderer.setSize(canvas.clientWidth, canvas.clientHeight, false)

    const scene = new THREE.Scene()
    const camera = new THREE.PerspectiveCamera(60, 1, 0.1, 100)
    camera.position.z = 3

    // InstancedMesh — one draw call for all particles
    const geo = new THREE.SphereGeometry(0.015, 4, 4)
    const mat = new THREE.MeshBasicMaterial({ color: 0x4488ff })
    const mesh = new THREE.InstancedMesh(geo, mat, PARTICLE_COUNT)
    scene.add(mesh)

    const positions = new Float32Array(PARTICLE_COUNT * 3)
    const velocities = new Float32Array(PARTICLE_COUNT * 3)
    // Initialize on sphere surface
    for (let i = 0; i < PARTICLE_COUNT; i++) {
      const phi = Math.acos(2 * Math.random() - 1)
      const theta = Math.random() * Math.PI * 2
      positions[i*3]   = Math.sin(phi) * Math.cos(theta)
      positions[i*3+1] = Math.sin(phi) * Math.sin(theta)
      positions[i*3+2] = Math.cos(phi)
    }

    const dummy = new THREE.Object3D()
    let rafId: number

    function animate() {
      rafId = requestAnimationFrame(animate)
      const { low, mid, high } = getEnergyBands()

      for (let i = 0; i < PARTICLE_COUNT; i++) {
        const x = positions[i*3] + (Math.random() - 0.5) * 0.01 * (1 + mid * 3)
        const y = positions[i*3+1] + (Math.random() - 0.5) * 0.01 * (1 + mid * 3)
        const z = positions[i*3+2] + (Math.random() - 0.5) * 0.01

        // Keep on sphere surface + audio energy pulsing
        const len = Math.hypot(x, y, z)
        const r = 1.0 + mid * 0.4 + high * 0.2
        positions[i*3]   = (x / len) * r
        positions[i*3+1] = (y / len) * r
        positions[i*3+2] = (z / len) * r

        dummy.position.set(positions[i*3], positions[i*3+1], positions[i*3+2])
        dummy.updateMatrix()
        mesh.setMatrixAt(i, dummy.matrix)
      }
      mesh.instanceMatrix.needsUpdate = true

      // Color pulse on beat (high energy)
      const hue = (Date.now() / 5000) % 1
      mat.color.setHSL(hue, 0.8, 0.5 + high * 0.3)

      renderer.render(scene, camera)
    }
    animate()

    return () => {
      cancelAnimationFrame(rafId)
      renderer.dispose()
      scene.clear()
    }
  }, [canvas])

  return null
}
```

**Performance budget for Three.js:**
- `PARTICLE_COUNT = 3000` (M3 Pro handles 10k+ easily, but keep headroom)
- FPS floor: 60fps. Three.js `InstancedMesh` at 3000 particles: ~0.8ms GPU time.
- Canvas resolution: same `devicePixelRatio` aware sizing as Canvas 2D pass.
- Memory: ~250KB for 3000 instance matrices.

### 3.4 React Container Component

```tsx
// src/jarvis/orb/OrbContainer.tsx
export function OrbContainer() {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const orbState = useOrbStore(s => s.state)
  
  return (
    <div className="orb-container" style={{ width: 300, height: 300, position: 'relative' }}>
      <canvas
        ref={canvasRef}
        width={300 * devicePixelRatio}
        height={300 * devicePixelRatio}
        style={{ width: 300, height: 300 }}
      />
      {/* Render engines are conditionally mounted but share the canvas ref */}
      {orbState !== 'SPEAKING'
        ? <Canvas2DOrb canvas={canvasRef.current} state={orbState} />
        : <ThreeOrb canvas={canvasRef.current!} />
      }
    </div>
  )
}
```

---

## 4. Panel System Architecture

### 4.1 Panel Registry

```ts
// src/jarvis/panels/panelRegistry.ts

export interface PanelDefinition {
  id: string
  label: string
  icon: string                // emoji or SVG path
  url: string | (() => string) // static or computed URL
  defaultSize: { width: number; height: number }
  defaultPosition: { x: number; y: number }
  singleton: boolean          // only one instance allowed
  sandbox: string             // iframe sandbox attribute value
  minSize?: { width: number; height: number }
}

export const BUILT_IN_PANELS: PanelDefinition[] = [
  {
    id: 'galaxy',
    label: 'Memory Galaxy',
    icon: '🌌',
    url: () => `http://localhost:${import.meta.env.VITE_GALAXY_PORT ?? 3001}`,
    defaultSize: { width: 900, height: 700 },
    defaultPosition: { x: 60, y: 60 },
    singleton: true,
    sandbox: 'allow-scripts allow-same-origin allow-forms',
  },
  {
    id: 'blackboard',
    label: 'Blackboard',
    icon: '📋',
    url: '/__panels/blackboard',
    defaultSize: { width: 700, height: 500 },
    defaultPosition: { x: 120, y: 120 },
    singleton: true,
    sandbox: 'allow-scripts allow-same-origin',
  },
  {
    id: 'morning-briefing',
    label: 'Morning Briefing',
    icon: '☀️',
    url: '/__panels/morning-briefing',
    defaultSize: { width: 600, height: 400 },
    defaultPosition: { x: 180, y: 180 },
    singleton: true,
    sandbox: 'allow-scripts allow-same-origin allow-popups',
  },
  {
    id: 'token-tracker',
    label: 'Token Tracker',
    icon: '💰',
    url: '/__panels/token-tracker',
    defaultSize: { width: 400, height: 300 },
    defaultPosition: { x: 240, y: 240 },
    singleton: true,
    sandbox: 'allow-scripts allow-same-origin',
  },
]
```

Dynamic discovery: JARVIS queries `GET /api/panels` from OpenCode backend. OpenCode
can advertise panels from installed plugins. Schema:

```ts
// OpenCode API response
interface RemotePanelDescriptor {
  id: string
  label: string
  url: string    // absolute URL or path relative to OpenCode server
}
```

### 4.2 IPC Protocol

JARVIS communicates with panels via `window.postMessage`. The protocol uses a typed
message envelope:

```ts
// src/shared/types.ts

// JARVIS → Panel
type JarvisMessage =
  | { type: 'jarvis:open' }
  | { type: 'jarvis:close' }
  | { type: 'jarvis:focus' }
  | { type: 'jarvis:theme-change'; theme: string }
  | { type: 'jarvis:session-context'; sessionId: string; agentName: string }

// Panel → JARVIS
type PanelMessage =
  | { type: 'panel:ready'; panelId: string }
  | { type: 'panel:title-change'; title: string }
  | { type: 'panel:request-close' }
  | { type: 'panel:badge'; count: number }
```

```ts
// src/jarvis/panels/PanelFrame.tsx — sending to iframe
function sendToPanel(iframe: HTMLIFrameElement, msg: JarvisMessage) {
  iframe.contentWindow?.postMessage(msg, '*')
}

// Receiving from panels
useEffect(() => {
  const handler = (e: MessageEvent<PanelMessage>) => {
    if (e.data?.type?.startsWith('panel:')) {
      handlePanelMessage(panelId, e.data)
    }
  }
  window.addEventListener('message', handler)
  return () => window.removeEventListener('message', handler)
}, [panelId])
```

### 4.3 Iframe Sandboxing

All panels use the `sandbox` attribute. Required permissions per panel type:

| Permission | Built-in panels | External panels |
|-----------|-----------------|-----------------|
| `allow-scripts` | ✓ | ✓ |
| `allow-same-origin` | ✓ (for localStorage) | ✓ |
| `allow-forms` | Galaxy only | ✗ |
| `allow-popups` | Morning Briefing | ✗ |
| `allow-downloads` | ✗ | ✗ |
| `allow-top-navigation` | ✗ | ✗ |

**`allow-same-origin` + `allow-scripts` warning:** This combination allows the iframe to
escape its sandbox via `parent.window`. For internal/trusted panels (Galaxy, Blackboard)
this is acceptable. For external dynamic panels, use only `allow-scripts` and rely on
postMessage for communication.

### 4.4 Draggable / Resizable Implementation

**Recommendation: `interact.js`**

Comparison:
| Library | Bundle | Multi-touch | Resize grips | React integration |
|---------|--------|-------------|--------------|-------------------|
| interact.js | 26KB gz | ✓ | ✓ | Manual (ref-based) |
| React DnD | 34KB gz | ✗ | ✗ (drag only) | Native |
| Floating UI | 10KB gz | ✗ | ✗ (position only) | Native |
| Custom pointer | 0KB | Possible | Custom | Native |

interact.js wins: only library that handles both drag AND resize in one, touch support,
snap-to-grid support (useful later), proven with floating panels.

```ts
// src/jarvis/panels/PanelFrame.tsx
import interact from 'interactjs'

const panelRef = useRef<HTMLDivElement>(null)

useEffect(() => {
  if (!panelRef.current) return
  const interactable = interact(panelRef.current)
    .draggable({
      listeners: { move: (e) => {
        const x = (parseFloat(e.target.style.left) || 0) + e.dx
        const y = (parseFloat(e.target.style.top)  || 0) + e.dy
        e.target.style.left = `${x}px`
        e.target.style.top  = `${y}px`
        panelStore.updatePosition(panelId, { x, y })
      }},
      modifiers: [interact.modifiers.restrictRect({ restriction: 'window', endOnly: true })]
    })
    .resizable({
      edges: { right: true, bottom: true, bottomRight: true },
      listeners: { move: (e) => {
        e.target.style.width  = `${e.rect.width}px`
        e.target.style.height = `${e.rect.height}px`
        panelStore.updateSize(panelId, { width: e.rect.width, height: e.rect.height })
      }},
      modifiers: [interact.modifiers.restrictSize({ min: definition.minSize ?? { width: 300, height: 200 } })]
    })
  return () => interactable.unset()
}, [panelId])
```

### 4.5 Panel State Persistence

Panel positions and sizes persist in **`localStorage`** with key `jarvis:panels:state`:

```ts
// src/jarvis/panels/panelStore.ts
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface PanelInstance {
  id: string
  definitionId: string
  position: { x: number; y: number }
  size: { width: number; height: number }
  zIndex: number
  minimized: boolean
}

export const usePanelStore = create<PanelStore>()(
  persist(
    (set, get) => ({
      panels: [] as PanelInstance[],
      openPanel: (defId: string) => { /* ... */ },
      closePanel: (id: string) => { /* ... */ },
      bringToFront: (id: string) => { /* ... */ },
      updatePosition: (id: string, pos: { x: number; y: number }) => { /* ... */ },
      updateSize: (id: string, size: { width: number; height: number }) => { /* ... */ },
    }),
    {
      name: 'jarvis:panels:state',
      partialize: (s) => ({ panels: s.panels })  // only persist layout, not runtime
    }
  )
)
```

Phase 4 (Tauri): migrate to `tauri-plugin-store` for encrypted, cross-process persistent
storage. The `persist` middleware's `storage` adapter will be swapped.

---

## 5. OpenCode Integration

### 5.1 SSE Event Stream

OpenCode server at `localhost:4096` exposes events at `/api/event` (proxied through Vite
as `/api/event` → `http://localhost:4096/api/event`).

```ts
// src/jarvis/session/sseClient.ts

export type OpenCodeEvent =
  | { type: 'session.created';    properties: { sessionID: string } }
  | { type: 'session.updated';    properties: { session: Session } }
  | { type: 'session.status';     properties: { sessionID: string; status: SessionStatus } }
  | { type: 'message.created';    properties: { message: Message } }
  | { type: 'message.part.delta'; properties: { messageID: string; partID: string; delta: string; field: string } }
  | { type: 'message.part.updated'; properties: { part: Part } }
  | { type: 'message.completed';  properties: { messageID: string } }
  | { type: 'tool.call.started';  properties: { toolName: string; callId: string; args: unknown } }
  | { type: 'tool.call.completed';properties: { callId: string; result: unknown; durationMs: number } }
  | { type: 'agent.started';      properties: { agentName: string; sessionID: string } }
  | { type: 'agent.completed';    properties: { agentName: string; sessionID: string; cost: number } }

export function createSseClient(onEvent: (e: OpenCodeEvent) => void) {
  let es: EventSource
  let reconnectTimer: number

  function connect() {
    es = new EventSource('/api/event')
    es.onmessage = (e) => {
      try {
        const event: OpenCodeEvent = JSON.parse(e.data)
        onEvent(event)
      } catch { /* ignore malformed */ }
    }
    es.onerror = () => {
      es.close()
      reconnectTimer = window.setTimeout(connect, 2000)
    }
  }

  connect()
  return () => { es.close(); clearTimeout(reconnectTimer) }
}
```

### 5.2 Activity Modal Feed

Agent stream events → steps in the Activity Modal. Schema:

```ts
// src/jarvis/activity/activityStore.ts

export interface ActivityStep {
  id: string
  type: 'tool_call' | 'message' | 'thinking' | 'agent_start' | 'agent_done'
  label: string         // human-readable: "Calling read_file", "Thinking..."
  detail?: string       // optional detail: file path, tool args summary
  status: 'running' | 'done' | 'error'
  startedAt: number     // Date.now()
  durationMs?: number
}

export interface ActivitySession {
  sessionId: string
  agentName: string
  steps: ActivityStep[]
  startedAt: number
  completedAt?: number
  totalCost?: number
}
```

Event → step mapping:

```ts
function openCodeEventToStep(e: OpenCodeEvent): Partial<ActivityStep> | null {
  switch (e.type) {
    case 'agent.started':
      return { type: 'agent_start', label: `${e.properties.agentName} started`, status: 'running' }
    case 'tool.call.started':
      return { type: 'tool_call', label: `Calling ${e.properties.toolName}`,
               detail: JSON.stringify(e.properties.args).slice(0, 80), status: 'running' }
    case 'tool.call.completed':
      return { type: 'tool_call', status: 'done', durationMs: e.properties.durationMs }
    case 'agent.completed':
      return { type: 'agent_done', label: 'Done', status: 'done' }
    default:
      return null
  }
}
```

Auto-dismiss: 15 seconds after `agent.completed` event. The modal can be pinned by
clicking a pin icon (sets `pinned: true` in the store — auto-dismiss is skipped).

### 5.3 Notification System

Priority/filtering rules:

```ts
// src/jarvis/notifications/toastStore.ts

export type ToastPriority = 'info' | 'success' | 'warning' | 'error'

export interface Toast {
  id: string
  message: string
  priority: ToastPriority
  dismissAfter: number   // ms, 0 = manual dismiss only
  source: string         // e.g. 'agent.completed', 'session.error'
}

// Filtering: never show toasts for events that already have activity modal open
// (reduces noise during active agent work)
function shouldToast(e: OpenCodeEvent, hasActiveModal: boolean): boolean {
  if (e.type === 'tool.call.started' || e.type === 'message.part.delta') return false
  if (hasActiveModal && e.type === 'agent.completed') return false  // modal covers it
  return true
}
```

Toasts are positioned top-right, stack vertically, never block the input bar or orb.
Max 5 toasts visible simultaneously; extras queue and appear as previous ones dismiss.

### 5.4 Session Awareness

```ts
// src/jarvis/session/SessionContext.tsx

export interface JarvisSessionState {
  sessionId: string | null
  agentName: string | null
  isWorking: boolean
  currentCost: number             // USD, from agent.completed events
  sessionStartedAt: number | null
  lastMessageAt: number | null
}
```

Data sources:
- `sessionId`, `agentName`, `isWorking`: derived from SSE `agent.started` / `agent.completed`
- `currentCost`: cumulative from `agent.completed` `cost` property
- Session list for session-picker: `GET /api/session` REST endpoint

```ts
// Fetch session list on mount + after each session.created event
async function fetchSessions(): Promise<Session[]> {
  const res = await fetch('/api/session')
  return res.json()
}
```

---

## 6. Theme System Implementation

### 6.1 CSS Variable Architecture

The existing Galaxy uses Tailwind tokens (e.g. `text-bmw-blue-light`) and basic CSS
variables. JARVIS extends with a dedicated layer in `jarvisThemeTokens.css`:

```css
/* src/jarvis/theme/jarvisThemeTokens.css */
/* 
 * All --jarvis-* variables must be defined here and overridden per-theme.
 * This file defines the defaults (Observatory dark theme).
 */

:root {
  /* ── Orb ── */
  --jarvis-orb-core:              #4488ff;          /* inner glow color */
  --jarvis-orb-ring:              rgba(68,136,255,0.3); /* ring halo */
  --jarvis-orb-particle-color:    #88bbff;          /* Canvas 2D particles */
  --jarvis-orb-idle-energy:       0.15;             /* base particle spawn rate */
  --jarvis-orb-bg:                radial-gradient(circle, rgba(10,20,50,0.6) 0%, transparent 70%);

  /* ── Shell chrome ── */
  --jarvis-bg:                    rgba(5, 10, 20, 0.85);   /* backdrop */
  --jarvis-surface:               rgba(15, 25, 50, 0.9);   /* card/panel backgrounds */
  --jarvis-surface-hover:         rgba(20, 35, 70, 0.95);
  --jarvis-border:                rgba(68, 136, 255, 0.2);
  --jarvis-border-active:         rgba(68, 136, 255, 0.7);
  --jarvis-text-primary:          #e8f0ff;
  --jarvis-text-secondary:        #8899cc;
  --jarvis-text-muted:            #445577;
  --jarvis-accent:                #4488ff;
  --jarvis-accent-glow:           rgba(68, 136, 255, 0.4);

  /* ── Activity modal ── */
  --jarvis-modal-bg:              rgba(5, 10, 30, 0.95);
  --jarvis-modal-border:          rgba(68, 136, 255, 0.3);
  --jarvis-step-running-color:    #4488ff;
  --jarvis-step-done-color:       #44ff88;
  --jarvis-step-error-color:      #ff4455;

  /* ── Notifications ── */
  --jarvis-toast-bg:              rgba(15, 25, 50, 0.95);
  --jarvis-toast-border:          rgba(68, 136, 255, 0.3);
  --jarvis-toast-success:         #44ff88;
  --jarvis-toast-warning:         #ffaa44;
  --jarvis-toast-error:           #ff4455;

  /* ── Input bar ── */
  --jarvis-input-bg:              rgba(10, 20, 45, 0.9);
  --jarvis-input-border:          rgba(68, 136, 255, 0.3);
  --jarvis-input-focus-ring:      rgba(68, 136, 255, 0.6);
  --jarvis-ptt-active:            #ff4455;  /* red when recording */

  /* ── Panel chrome ── */
  --jarvis-panel-titlebar-bg:     rgba(10, 20, 45, 0.95);
  --jarvis-panel-titlebar-text:   #8899cc;
  --jarvis-panel-resize-handle:   rgba(68, 136, 255, 0.4);

  /* ── Transitions ── */
  --jarvis-transition-fast:       150ms ease;
  --jarvis-transition-med:        300ms ease;
  --jarvis-transition-slow:       600ms cubic-bezier(0.16, 1, 0.3, 1);
}
```

### 6.2 Per-Theme Overrides

Each of the 5 existing themes gets a JARVIS override file:

```css
/* src/jarvis/theme/themes/synthwave.css */
/* Activated when <html data-jarvis-theme="synthwave"> */

[data-jarvis-theme="synthwave"] {
  --jarvis-orb-core:              #36f9f6;   /* teal from synthwave84 primary */
  --jarvis-orb-ring:              rgba(54, 249, 246, 0.3);
  --jarvis-orb-particle-color:    #b084eb;   /* purple accent */
  --jarvis-bg:                    rgba(38, 35, 53, 0.9);   /* synthwave neutral */
  --jarvis-surface:               rgba(45, 42, 65, 0.92);
  --jarvis-border:                rgba(54, 249, 246, 0.2);
  --jarvis-border-active:         rgba(54, 249, 246, 0.7);
  --jarvis-text-primary:          #ffffff;
  --jarvis-text-secondary:        #848bbd;
  --jarvis-accent:                #36f9f6;
  --jarvis-accent-glow:           rgba(54, 249, 246, 0.4);
  --jarvis-step-done-color:       #72f1b8;   /* synthwave success */
  --jarvis-toast-success:         #72f1b8;
}
```

Theme color source: pull `palette.primary`, `palette.accent`, `palette.neutral`,
`palette.success` from each theme's `.json` file in
`~/.config/opencode/web/src/galaxy/themes/`.

**Map (existing theme ID → JARVIS css file):**

| OpenCode theme id | JARVIS theme file | Orb core color |
|-------------------|-------------------|----------------|
| `observatory`     | `observatory.css` | `#4488ff` (blue) |
| `cel-shade`       | `cel-shade.css`   | `#ff6633` (orange) |
| `blueprint`       | `blueprint.css`   | `#00bfff` (sky) |
| `synthwave84`     | `synthwave.css`   | `#36f9f6` (teal) |
| `forge`           | `forge.css`       | `#ff8800` (amber) |

### 6.3 Live Theme Switching

```ts
// src/jarvis/theme/themeStore.ts
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

type JarvisThemeId = 'observatory' | 'cel-shade' | 'blueprint' | 'synthwave' | 'forge'

interface ThemeStore {
  theme: JarvisThemeId
  setTheme: (t: JarvisThemeId) => void
}

export const useThemeStore = create<ThemeStore>()(
  persist(
    (set) => ({
      theme: 'observatory',
      setTheme: (theme) => {
        // CSS class swap on <html> — single DOM write, no JS style updates
        document.documentElement.setAttribute('data-jarvis-theme', theme)
        set({ theme })
        // Notify open panels via postMessage
        document.querySelectorAll<HTMLIFrameElement>('.panel-frame iframe')
          .forEach(iframe => iframe.contentWindow?.postMessage(
            { type: 'jarvis:theme-change', theme }, '*'
          ))
      }
    }),
    {
      name: 'jarvis:theme',       // localStorage key
      onRehydrateStorage: () => (state) => {
        if (state?.theme) {
          document.documentElement.setAttribute('data-jarvis-theme', state.theme)
        }
      }
    }
  )
)
```

**CSS loading:** All 5 theme override files are `@import`-ed statically in `index.css`.
They are inactive until the `[data-jarvis-theme="X"]` attribute is set. No dynamic CSS
injection, no flash — the single attribute swap is instant.

```css
/* src/index.css */
@import './jarvis/theme/jarvisThemeTokens.css';
@import './jarvis/theme/themes/observatory.css';
@import './jarvis/theme/themes/synthwave.css';
@import './jarvis/theme/themes/blueprint.css';
@import './jarvis/theme/themes/cel-shade.css';
@import './jarvis/theme/themes/forge.css';
```

### 6.4 Theme Extension Points

Adding a new JARVIS-exclusive theme:
1. Create `src/jarvis/theme/themes/<name>.css` with `[data-jarvis-theme="<name>"]` block
2. Add `@import` to `index.css`
3. Add to `JarvisThemeId` union in `themeStore.ts`
4. Add to the theme picker in `JarvisShell.tsx`

No build changes required. Zero-config discovery is intentional.

---

## 7. Tauri Desktop Integration

### 7.1 Global Keyboard Shortcut

```rust
// src-tauri/src/main.rs
use tauri_plugin_global_shortcut::{GlobalShortcutExt, Shortcut, ShortcutState};

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_global_shortcut::Builder::new().build())
        .setup(|app| {
            let handle = app.handle().clone();
            app.global_shortcut().on_shortcut("CmdOrCtrl+Shift+Space", move |_, shortcut, event| {
                match event.state() {
                    ShortcutState::Pressed  => { handle.emit("ptt-start", ()).ok(); }
                    ShortcutState::Released => { handle.emit("ptt-stop",  ()).ok(); }
                }
            })?;
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
```

Frontend receives:
```ts
import { listen } from '@tauri-apps/api/event'

// in PttManager.ts — Phase 2 branch
const unlistenStart = await listen('ptt-start', () => voiceController.startListening())
const unlistenStop  = await listen('ptt-stop',  () => voiceController.stopListening())
```

### 7.2 Always-On Window

```rust
// src-tauri/tauri.conf.json
{
  "windows": [{
    "label": "main",
    "title": "JARVIS",
    "alwaysOnTop": true,
    "decorations": false,        // frameless
    "transparent": true,          // macOS vibrancy
    "width": 380,
    "height": 600,
    "x": 40,
    "y": 40,
    "resizable": true,
    "vibrancy": "under-window"    // macOS blur behind window
  }]
}
```

For the full JARVIS panel-extended layout, a second window is created on demand:
```rust
tauri::WebviewWindowBuilder::new(app, "panels", WebviewUrl::App("index.html".into()))
    .title("JARVIS Panels")
    .inner_size(1440.0, 900.0)
    .transparent(true)
    .decorations(false)
    .build()?;
```

### 7.3 Local TTS via `say`

```rust
// src-tauri/src/commands.rs
#[tauri::command]
async fn say(text: String, voice: Option<String>) -> Result<(), String> {
    let voice = voice.unwrap_or_else(|| "Samantha".into());
    // Sanitize: only allow word characters, spaces, basic punctuation
    let safe: String = text.chars()
        .filter(|c| c.is_alphanumeric() || " .,!?'-".contains(*c))
        .collect();
    std::process::Command::new("say")
        .args(["-v", &voice, &safe])
        .spawn()
        .map_err(|e| e.to_string())?;
    Ok(())
}
```

Frontend:
```ts
// src/jarvis/voice/TtsLocal.ts — Phase 2 branch
import { invoke } from '@tauri-apps/api/core'

export async function sayLocal(text: string, voice = 'Samantha') {
  await invoke('say', { text, voice })
}
```

### 7.4 mlx-whisper as Tauri Sidecar

```
src-tauri/
├── src/
│   └── main.rs        # registers sidecar
├── binaries/
│   └── stt-bridge-aarch64-apple-darwin  # compiled Python → binary via PyInstaller
└── tauri.conf.json    # "externalBin": ["binaries/stt-bridge"]
```

```rust
// src-tauri/src/commands.rs
use tauri_plugin_shell::ShellExt;

#[tauri::command]
async fn start_stt_sidecar(app: tauri::AppHandle) -> Result<(), String> {
    let sidecar = app.shell().sidecar("stt-bridge")
        .map_err(|e| e.to_string())?;
    let (_rx, child) = sidecar
        .args(["--port", "5001"])
        .spawn()
        .map_err(|e| e.to_string())?;
    // Store child handle in Tauri managed state for later kill
    app.manage(SttSidecarState { child: Mutex::new(Some(child)) });
    Ok(())
}
```

The sidecar (`stt-bridge.py`) is compiled with PyInstaller into a self-contained binary:
```bash
pyinstaller --onefile --target-arch arm64 \
  --hidden-import mlx_whisper \
  scripts/stt-bridge.py \
  -n stt-bridge-aarch64-apple-darwin
```

Communication: the sidecar listens on `localhost:5001`. The Tauri frontend calls it via
`fetch('http://localhost:5001/transcribe', ...)` — identical to the Vite dev mode path.
No Tauri IPC needed for the audio data (binary blobs work better over HTTP).

### 7.5 Migration from Vite Bypass to Tauri IPC

Current Galaxy uses Vite `server.proxy` for `/__memory`, `/__agents`:

```ts
// vite.config.ts (current)
proxy: {
  '/__memory': { target: 'http://localhost:4096', ... },
  '/__agents':  { target: 'http://localhost:4096', ... },
  '/api':       { target: 'http://localhost:4096', ... },
}
```

Phase 4 migration: Replace with Tauri invoke commands backed by `tauri-plugin-sql`:

```ts
// src/jarvis/session/SessionContext.tsx — Phase 4 branch
import { invoke } from '@tauri-apps/api/core'

// Before (Vite proxy):
const sessions = await fetch('/__memory').then(r => r.json())

// After (Tauri IPC):
const sessions = await invoke<Session[]>('get_memory_nodes')
```

```rust
#[tauri::command]
async fn get_memory_nodes(db: tauri::State<'_, DbPool>) -> Result<Vec<MemoryNode>, String> {
    let pool = db.0.lock().await;
    pool.select::<MemoryNode>("SELECT * FROM entities ORDER BY created_at DESC LIMIT 200")
        .await
        .map_err(|e| e.to_string())
}
```

**Migration strategy:** Keep the HTTP proxy paths working in dev. Add a Tauri capability
detection at startup:

```ts
const isTauri = '__TAURI_INTERNALS__' in window

const api = isTauri
  ? createTauriApi()     // invoke-based
  : createHttpApi()      // fetch/proxy-based
```

This gives a clean compatibility shim so Galaxy/JARVIS code doesn't need to care.

---

## 8. Data Flow Diagram

### PTT Interaction — Complete Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│  USER                                                               │
│    CMD+SHIFT+SPACE pressed                                         │
└────────────┬────────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  BROWSER: PttManager.handleKey()                                    │
│  - Sets active = true                                               │
│  - Calls VoiceController.startListening()                           │
└────────────┬────────────────────────────────────────────────────────┘
             │
       ┌─────┴──────────────────────────────────────┐
       ▼                                            ▼
┌─────────────┐                          ┌──────────────────────────┐
│ OrbStore    │                          │ SttBridge                │
│ transition  │                          │ .start({continuous:true})│
│ IDLE →      │                          │                          │
│ LISTENING   │                          │ navigator.mediaDevices   │
└─────────────┘                          │ .getUserMedia({audio:true})
       │                                 └──────────┬───────────────┘
       ▼                                            │
┌─────────────────────────────────────────┐         │ mic stream
│ Canvas2DOrb re-renders with             │         ▼
│ LISTENING state:                        │ ┌─────────────────────┐
│ - higher particle spawn rate            │ │ audioAnalyser.ts    │
│ - orb pulses with mic input             │ │ connectMicToAnalyser│
│ - getEnergyBands() from mic stream      │ │ → AnalyserNode live │
└─────────────────────────────────────────┘ └─────────────────────┘
             │                                       │
             │ interim transcript shown in InputBar  │ energy → orb
             │ (onInterim callback)                  │
             │
┌────────────┴────────────────────────────────────────────────────────┐
│  USER releases CMD+SHIFT+SPACE                                      │
└────────────┬────────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  PttManager: active = false → VoiceController.stopListening()       │
│  SttBridge.stop() → returns final transcript string                │
│  OrbStore.transition('ptt_stop') → LISTENING → THINKING            │
└────────────┬────────────────────────────────────────────────────────┘
             │
             │  transcript: "What is the status of my current PR?"
             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  VoiceController submits to OpenCode                                │
│  POST /api/session/{sessionId}/message                              │
│  body: { text: transcript, role: "user" }                          │
└────────────┬────────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  OpenCode backend processes (async, SSE events flow back)           │
│                                                                     │
│  SSE: agent.started       → ActivityModal: "Agent started"         │
│  SSE: tool.call.started   → ActivityModal: "Calling get_pr_status" │
│  SSE: tool.call.completed → ActivityModal: step marked done        │
│  SSE: message.part.delta  → text accumulates in SessionContext     │
│  SSE: agent.completed     → SessionContext cost updated            │
│  SSE: message.completed   → final response text ready             │
└────────────┬────────────────────────────────────────────────────────┘
             │
             │  response text: "Your PR #42 has 2 review comments and CI is green."
             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  TtsPipeline.speak(responseText)                                    │
│                                                                     │
│  text.length = 65 chars  → below 120 threshold → fast path        │
│  fetch POST /api/tts-say { text, voice: "Samantha" }               │
│  Vite middleware: exec(`say -v Samantha "..."`)                    │
│                                                                     │
│  macOS system audio plays: "Your PR forty-two has two..."          │
└────────────┬────────────────────────────────────────────────────────┘
             │
             │ (simultaneously)
             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  OrbStore.transition('tts_start') → THINKING → SPEAKING            │
│                                                                     │
│  (for 'say' fast path, we estimate duration from char count:       │
│   ~150 chars/min at normal speech → 65 chars ≈ 2.6s)               │
│  setTimeout(() => transition('tts_end'), estimatedMs)              │
│                                                                     │
│  OR for BMW TTS streaming path:                                     │
│  AudioContext sourceNode.onended → transition('tts_end')           │
└────────────┬────────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  ThreeOrb renders InstancedMesh (3000 particles)                    │
│  Audio AnalyserNode drives particle pulsing                         │
│  (for 'say' path: no AnalyserNode connection — orb uses simulated  │
│   energy curve; BMW TTS path: AnalyserNode connected to AudioContext│
│   source → real waveform-driven animation)                         │
└────────────┬────────────────────────────────────────────────────────┘
             │
             │ tts_end
             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  OrbStore.transition('tts_end') → SPEAKING → IDLE                  │
│  ThreeOrb disposed; Canvas2DOrb resumes                             │
│  ActivityModal auto-dismiss timer starts (15s)                      │
└─────────────────────────────────────────────────────────────────────┘
```

**Data formats at each boundary:**

| Boundary | Format |
|----------|--------|
| PttManager → VoiceController | `void` event dispatch |
| SttBridge → VoiceController | `string` (transcript) |
| VoiceController → OpenCode | `application/json` over HTTP POST |
| OpenCode → JARVIS | `text/event-stream` (SSE), JSON per event |
| ActivityModal ← SSE | `ActivityStep` objects |
| TtsPipeline ← response | `string` |
| TtsPipeline → local say | `application/json` HTTP POST |
| AnalyserNode → particle engine | `Uint8Array` (128 frequency bins) per frame |

---

## 9. Build & Dev Setup

### 9.1 Adding JARVIS to feat/web-frontend

No branch change needed. JARVIS extends the existing branch:

```bash
# From ~/.config/opencode/web/
git checkout feat/web-frontend
git pull

# Restructure Galaxy into its own subdirectory
mkdir -p src/galaxy
git mv src/App.tsx src/App.css src/galaxy/GalaxyApp.tsx   # adjust as needed
# (actual Galaxy source files — to be determined from full source inspection)

# Install new dependencies
npm install zustand interactjs @picovoice/porcupine-web
npm install -D @types/interactjs

# Optional Phase 2 deps (install later)
# npm install @tauri-apps/api
# npm install @tauri-apps/cli --save-dev
```

### 9.2 Updated vite.config.ts

```ts
// vite.config.ts
import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import { exec } from 'node:child_process'
import { promisify } from 'node:util'

const execAsync = promisify(exec)

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd())
  const port = parseInt(env.VITE_OPENCODE_PORT ?? '4096')

  return {
    plugins: [
      react(),
      // Custom middleware for macOS TTS (dev only)
      {
        name: 'tts-say-middleware',
        configureServer(server) {
          server.middlewares.use('/api/tts-say', async (req, res) => {
            if (req.method !== 'POST') { res.statusCode = 405; res.end(); return }
            let body = ''
            req.on('data', c => body += c)
            req.on('end', async () => {
              const { text, voice = 'Samantha' } = JSON.parse(body)
              const safe = text.replace(/[`$"\\<>|&;()]/g, '').slice(0, 500)
              try {
                exec(`say -v "${voice}" "${safe}"`)
                res.end(JSON.stringify({ ok: true }))
              } catch (e) {
                res.statusCode = 500
                res.end(JSON.stringify({ error: String(e) }))
              }
            })
          })
        }
      }
    ],

    server: {
      port: 5173,
      proxy: {
        '/api/event': {
          target: `http://localhost:${port}`,
          changeOrigin: true,
          // SSE: disable buffering
          configure: (proxy) => {
            proxy.on('proxyReq', (proxyReq) => {
              proxyReq.setHeader('Accept', 'text/event-stream')
              proxyReq.setHeader('Cache-Control', 'no-cache')
            })
          }
        },
        '/api': {
          target: `http://localhost:${port}`,
          changeOrigin: true,
        },
        '/__memory': {
          target: `http://localhost:${port}`,
          changeOrigin: true,
        },
        '/__agents': {
          target: `http://localhost:${port}`,
          changeOrigin: true,
        },
        '/__panels': {
          // Future panel micro-frontends served from OpenCode
          target: `http://localhost:${port}`,
          changeOrigin: true,
        }
      }
    },

    build: {
      rollupOptions: {
        input: {
          jarvis: 'index.html',
          galaxy: 'galaxy.html',   // Phase 3 — Galaxy as standalone panel entry
        }
      }
    }
  }
})
```

### 9.3 New npm Scripts

```json
// package.json additions
{
  "scripts": {
    "dev":           "vite",                             // JARVIS shell on :5173
    "dev:galaxy":    "vite --config vite.galaxy.config.ts --port 3001",
    "dev:all":       "concurrently \"npm:dev\" \"npm:dev:galaxy\"",
    "build":         "tsc && vite build",
    "build:tauri":   "tauri build",                     // Phase 4
    "dev:tauri":     "tauri dev",                       // Phase 4
    "stt:bridge":    "python3 scripts/stt-bridge.py",   // Phase 3 — mlx-whisper bridge
    "test":          "vitest run",
    "test:e2e":      "playwright test"
  }
}
```

```bash
npm install --save-dev concurrently
```

### 9.4 Environment Variables

```bash
# .env.local (gitignored — add to your local copy)

# OpenCode server
VITE_OPENCODE_PORT=4096
VITE_OPENCODE_HOST=127.0.0.1

# Galaxy panel dev port
VITE_GALAXY_PORT=3001

# Porcupine wake word (get free key from console.picovoice.ai)
VITE_PICOVOICE_KEY=your_access_key_here

# TTS: 'local' | 'bmw' | 'auto'
VITE_TTS_MODE=auto

# BMW Audio TTS (reuses existing LLM API token)
# Loaded from Keychain via load-secrets.sh — do NOT hardcode
VITE_LLM_API_BEARER_TOKEN=    # set by wrapper script at launch
VITE_LLM_API_KEY=             # set by wrapper script at launch

# Feature flags
VITE_WAKE_WORD_ENABLED=false  # Phase 5 only
VITE_STT_BACKEND=webspeech    # 'webspeech' | 'mlx'
```

### 9.5 Dev Workflow

```bash
# Option A: JARVIS shell only (Galaxy panel loads at 3001 externally)
npm run dev            # starts :5173
# → open http://localhost:5173 → JARVIS shell with Galaxy panel embedded

# Option B: Full stack — JARVIS + Galaxy panel dev server
npm run dev:all        # starts :5173 + :3001 concurrently
# → Panel iframe at http://localhost:3001 is live-reloaded independently

# Ensure OpenCode backend is running first:
opencode server        # or just: opencode
```

---

## 10. Phase Roadmap

### Phase 1 — Browser MVP (JARVIS Shell)

**Goal:** JARVIS orb renders in the browser, text input works, panels can open/close,
theme system live-switches. No voice yet.

**In scope:**
- JARVIS shell layout (`JarvisShell.tsx`)
- Canvas 2D orb (IDLE + THINKING states only — no mic/TTS)
- Particle state machine (IDLE / THINKING)
- SSE client + session awareness
- Activity modal (tool call steps)
- Toast notification layer
- Panel host + PanelFrame with interact.js
- Galaxy moved to panel (embedded at `localhost:3001`)
- 5-theme CSS variable system
- Live theme switching

**New files:**
```
src/jarvis/JarvisShell.tsx
src/jarvis/orb/OrbContainer.tsx
src/jarvis/orb/Canvas2DOrb.tsx
src/jarvis/orb/particleState.ts
src/jarvis/panels/PanelHost.tsx
src/jarvis/panels/PanelFrame.tsx
src/jarvis/panels/panelRegistry.ts
src/jarvis/panels/panelStore.ts
src/jarvis/activity/ActivityModal.tsx
src/jarvis/activity/activityStore.ts
src/jarvis/notifications/ToastLayer.tsx
src/jarvis/notifications/toastStore.ts
src/jarvis/session/sseClient.ts
src/jarvis/session/SessionContext.tsx
src/jarvis/input/InputBar.tsx
src/jarvis/theme/jarvisThemeTokens.css
src/jarvis/theme/themeStore.ts
src/jarvis/theme/themes/*.css  (5 files)
```

**New dependencies:** `zustand`, `interactjs`, `@types/interactjs`  
**Complexity: L** (mostly frontend, no native APIs)

---

### Phase 2 — Voice (STT + TTS)

**Goal:** PTT works, JARVIS speaks responses.

**Added:**
- Web Speech API STT (`SttBridge.ts`)
- PTT keyboard/button (`PttManager.ts`)
- `VoiceController.tsx` React context
- TTS pipeline: `TtsPipeline.ts`, `TtsLocal.ts`, `TtsBmw.ts`
- Vite middleware: `/api/tts-say` → macOS `say`
- Web Audio AnalyserNode + mic connection
- LISTENING / SPEAKING orb states
- `ThreeOrb.tsx` (InstancedMesh for SPEAKING)
- `audioAnalyser.ts`

**New files:**
```
src/jarvis/voice/VoiceController.tsx
src/jarvis/voice/SttBridge.ts
src/jarvis/voice/PttManager.ts
src/jarvis/voice/TtsPipeline.ts
src/jarvis/voice/TtsLocal.ts
src/jarvis/voice/TtsBmw.ts
src/jarvis/orb/ThreeOrb.tsx
src/jarvis/orb/audioAnalyser.ts
```

**New dependencies:** None (Web Speech API and Web Audio API are browser built-ins; Three.js already installed)  
**Complexity: M**

---

### Phase 3 — Panels + mlx-whisper Bridge

**Goal:** Panel system fully functional; mlx-whisper available as STT backend.

**Added:**
- Panel discovery from OpenCode `/api/panels`
- `SttMlxBridge.ts` — HTTP bridge to `scripts/stt-bridge.py`
- `scripts/stt-bridge.py` — FastAPI + mlx-whisper server
- STT backend selector in settings
- Additional built-in panels: Blackboard, Token Tracker, Morning Briefing
- Panel IPC protocol fully implemented
- Wake word infrastructure (worker file, no model yet)
- `galaxy.html` — Galaxy standalone entry for multi-page build

**New files:**
```
src/jarvis/voice/SttMlxBridge.ts
src/jarvis/voice/WakeWordWorker.ts
src/jarvis/voice/WakeWordWorker.worker.ts (stub — no model)
scripts/stt-bridge.py
galaxy.html
vite.galaxy.config.ts
```

**New dependencies:** `@picovoice/porcupine-web` (stub install), Python: `fastapi uvicorn mlx-whisper soundfile`  
**Complexity: M**

---

### Phase 4 — Tauri Desktop

**Goal:** JARVIS runs as a native macOS app. Global shortcut works system-wide.
Always-on-top transparent overlay.

**Added:**
- `src-tauri/` scaffolded via `tauri init`
- `src-tauri/src/commands.rs`: `say`, `get_memory_nodes`, `get_sessions`, `start_stt_sidecar`
- Global shortcut via `tauri-plugin-global-shortcut`
- `tauri-plugin-shell` for `say` command
- `tauri-plugin-sql` replacing better-sqlite3
- Capability detection shim (`isTauri` flag)
- Transparent/frameless window + macOS vibrancy
- PyInstaller build of `stt-bridge` into Tauri sidecar binary
- `npm run build:tauri` pipeline

**New files:**
```
src-tauri/
├── Cargo.toml
├── tauri.conf.json
├── src/
│   ├── main.rs
│   └── commands.rs
└── binaries/
    └── stt-bridge-aarch64-apple-darwin
src/shared/tauriCompat.ts    # isTauri detection + shim
```

**New dependencies:** `@tauri-apps/api`, `@tauri-apps/cli` (dev); Rust crates: `tauri`, `tauri-plugin-global-shortcut`, `tauri-plugin-shell`, `tauri-plugin-sql`  
**Complexity: XL**

---

### Phase 5 — Always-On Wake Word

**Goal:** "Hey JARVIS" works system-wide even when JARVIS is backgrounded/minimized.

**Added:**
- `WakeWordWorker.worker.ts` fully implemented with Porcupine WASM
- `public/jarvis/hey-jarvis_en_wasm_v3_0_0.ppn` — keyword model
- `public/jarvis/porcupine_params.pv` — acoustic model
- Always-on mode setting toggle
- Tauri window: always-on-top behavior + system tray icon
- System tray: "JARVIS listening" / "JARVIS idle" states
- Background microphone permission handling (macOS privacy)
- Configurable wake word setting (custom `.ppn` upload)

**New files:**
```
src/jarvis/voice/WakeWordWorker.worker.ts   (complete implementation)
public/jarvis/hey-jarvis_en_wasm_v3_0_0.ppn
public/jarvis/porcupine_params.pv
src-tauri/src/tray.rs
```

**New dependencies:** `@picovoice/porcupine-web` fully configured; Porcupine free API key  
**Complexity: M** (Porcupine SDK does the heavy lifting)

---

## Appendix A: Key TypeScript Interfaces

```ts
// src/shared/types.ts — complete interface registry

export interface Session {
  id: string
  title: string
  createdAt: number
  updatedAt: number
  agentName?: string
  parentID?: string
}

export interface SessionStatus {
  sessionID: string
  status: 'idle' | 'running' | 'error'
  cost?: number
}

export interface Message {
  id: string
  sessionID: string
  role: 'user' | 'assistant'
  createdAt: number
}

export interface Part {
  id: string
  messageID: string
  type: 'text' | 'tool_call' | 'tool_result'
  text?: string
  toolName?: string
  toolArgs?: unknown
  toolResult?: unknown
}

export interface PanelDefinition { /* see §4.1 */ }
export interface ActivityStep { /* see §5.2 */ }
export interface Toast { /* see §5.3 */ }
export type OrbState = 'IDLE' | 'LISTENING' | 'THINKING' | 'SPEAKING'
export type JarvisThemeId = 'observatory' | 'cel-shade' | 'blueprint' | 'synthwave' | 'forge'
```

---

## Appendix B: Dependency Summary

| Package | Version | Phase | Purpose |
|---------|---------|-------|---------|
| `zustand` | `^4.5` | 1 | State management (orb, panels, toasts, theme) |
| `interactjs` | `^1.10` | 1 | Panel drag + resize |
| `@types/interactjs` | `^1.10` | 1 | TypeScript types |
| `concurrently` | `^9.0` | 1 | `npm run dev:all` |
| `@picovoice/porcupine-web` | `^3.0` | 5 | Wake word WASM |
| `@tauri-apps/api` | `^2.0` | 4 | Tauri JS bindings |
| `@tauri-apps/cli` | `^2.0` | 4 | Tauri build CLI (dev) |

All existing dependencies remain unchanged:
`react@18`, `three@^0.185`, `3d-force-graph`, `better-sqlite3`, `vite@5`, `typescript@5`,
`tailwindcss@3`, `@vitejs/plugin-react`, `vitest`

---

## Appendix C: File Count Impact per Phase

| Phase | New files | Modified files | Deleted files |
|-------|-----------|----------------|---------------|
| 1 | ~22 | 3 (`main.tsx`, `index.css`, `vite.config.ts`) | 0 |
| 2 | ~8 | 2 (`vite.config.ts`, `VoiceController.tsx`) | 0 |
| 3 | ~6 | 2 | 0 |
| 4 | ~12 (incl. Rust) | 4 | 0 |
| 5 | ~4 | 2 | 0 |
| **Total** | **~52** | **~13** | **0** |

No existing Galaxy files are deleted. Galaxy is wrapped, not replaced.
