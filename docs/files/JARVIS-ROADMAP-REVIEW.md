# JARVIS / Galaxy — Review, Repairs & Suggestions

**Branch:** `feat/jarvis-galaxy-fixes`
**Scope reviewed:** `web/JARVIS-ROADMAP.md`, `web/JARVIS-ARCHITECTURE-SPEC.md`, `web/JARVIS-AGENT-BRIEF.md`, `web/jarvis-design-refs/*`, and the opencode architecture at repo root (`opencode.json`, `AGENTS.md`, `agents/`, `routing-matrix.md`).

This document is analysis + corrections. It does **not** modify any live config (`opencode.json`, `agents/`, `AGENTS.md`), per the repo rule that MCPs/skills are managed only through the `ttt-*` wrappers. The only files added on this branch are this review and two runnable references under `web/reference/`.

---

## TL;DR

1. **The galaxy/JARVIS web app source is not in the repo.** `web/` contains only the roadmap, spec, brief, and design PNGs; the app at `~/.config/opencode/web/` is gitignored (`node_modules/`, `.opencode/`, etc.). So the "blank galaxy" bug can't be patched from here. Its **root cause is known and fixed** in the included reference — see §3.
2. **Two runnable references are included** under `web/reference/`. `memory-galaxy.html` is a complete, populated, themeable Galaxy panel (now with all **7** roadmap themes) that already renders the design in `jarvis-panel-galaxy.png`. It is iframe-ready and can serve as **Panel #1** while the React migration proceeds, and as a visual spec for the implementing agent.
3. **Three roadmap claims need correcting** before Phase 2 — most importantly the Web Speech "privacy-safe" claim (§4.1).

---

## 1. Alignment — the roadmap is sound

The core architecture ("JARVIS = shell, Galaxy = panel"; Galaxy as a sandboxed iframe; Zustand for state; interact.js for panels; Canvas2D idle orb → Three.js speaking corona; SSE → activity modal) is coherent and well sequenced. The phase ordering (shell → voice → vox/panels → Tauri → wake word) front-loads UX validation before the native build, which is the right call.

The design refs match the built reference closely: `jarvis-panel-galaxy.png` is exactly the orbital model in `web/reference/memory-galaxy.html` — amber sun (orchestrator) at center, planets (subagents) on inclined elliptical orbits, inside a glass floating panel.

## 2. Key structural finding — app source absent

`git ls-files web/` returns only docs + design refs. The runtime app referenced throughout the roadmap (`src/jarvis/...`, `src/galaxy/GalaxyApp.tsx`, `vite.config.ts`) is not tracked here.

**Recommendation:** commit the frontend (at least `src/`, `index.html`, `vite.config.ts`, `package.json`, `tsconfig.json`) to a `feat/web-frontend` branch so the roadmap's "Modified files" lists are actionable and reviewable. Without it, Phase-1 work can't be diffed or handed to an agent.

## 3. The "blank galaxy" bug — root cause + fix (mapped to Phase 1)

Observed in prior screenshots: galaxy renders nearly empty (a few faint dots) with the chrome (legend, layers, counts) intact. Four compounding causes, all fixed in `web/reference/memory-galaxy.html`:

1. **Non-emissive nodes on a light background.** Small standard-material nodes against a bright clear color disappear. *Fix:* true deep-space clear color + every body is emissive **and** carries an additive radial-glow sprite, so nodes stay visible at any zoom.
2. **Force-directed layout that never settles** (or settles off-screen). *Fix:* deterministic orbital layout — sun at origin, subagents on golden-angle inclined orbits, capabilities co-rotating with their owner. First paint is always populated.
3. **Canvas buffer not matched to display on first paint** (and never re-measured) — the classic cause of an off-center / empty render, especially on mobile where the address bar resizes after load. *Fix:* a `ResizeObserver` on the container plus `visualViewport`/orientation handlers and a guarded `resize()`.
4. **Camera not framed on content.** *Fix:* camera initialized looking at the sun at a sane distance.

**For the React app:** if the galaxy uses a force sim (looks likely from the prior "87 nodes · 98 links" + clustering sessions), the highest-leverage change is to (a) give nodes emissive material + a glow sprite/bloom, (b) drive sizing from a `ResizeObserver` on the canvas's parent, and (c) verify the renderer clear color is dark. Those three resolve the symptom regardless of the layout engine.

## 4. Corrections to the roadmap

### 4.1 Web Speech API is **not** private / on-device (high priority)
The roadmap lists `Web Speech API (privacy-safe, no external call)`. In Chromium, `webkitSpeechRecognition` **streams microphone audio to Google's servers** for transcription — it is neither offline nor private. For a BMW-internal assistant this is a meaningful data-egress issue.

**Recommendation:** keep Web Speech only as an optional convenience path with an explicit "audio leaves this machine" disclosure, and treat the **mlx-whisper local bridge (Phase 2/4)** as the privacy-safe default for any internal use. Consider promoting the bridge earlier if privacy is a hard requirement.

### 4.2 macOS `say` capture is overcomplicated (medium)
The roadmap captures `say` output via `ffmpeg -f avfoundation`. `say` can write a file directly — no system-audio capture (and no extra mic/screen-recording permission) needed:

```bash
say -v Daniel -r 180 -o /tmp/jarvis.aiff "your text"
# optional: ffmpeg -i /tmp/jarvis.aiff /tmp/jarvis.mp3   (only if you need MP3)
```

`avfoundation` capture records an output device and is fragile across machines; `say -o` is deterministic and offline.

### 4.3 `CMD+SHIFT+SPACE` browser global shortcut (low — already flagged)
In-browser it only fires while the tab is focused, and the OS/Spotlight may intercept it. The roadmap correctly defers OS-level global to Tauri (Phase 4). Suggest making the on-screen mic button + hold-`SPACE` the documented Phase-1/2 path and treating the chord as best-effort until Tauri.

### 4.4 Pin Three.js + name the import path (low)
`Three.js v0.185` should be pinned to a verified published version in `package.json`, and the app should standardize on ESM addon imports (`three/examples/jsm/...`) for `OrbitControls`/post-processing. The included reference deliberately uses r128 UMD + hand-rolled camera controls to stay dependency-free as a single file; the React app should not copy that constraint.

## 5. How the included references map to the roadmap

| Roadmap item | Reference coverage |
|---|---|
| Galaxy panel (Panel #1), `jarvis-panel-galaxy.png` | `web/reference/memory-galaxy.html` — populated orbital view, iframe-ready (auto-sizes to container) |
| 7 themes (5 + Black Ice + Chrome) | All 7 implemented in the reference's `THEMES` table + `data`-driven selector |
| Activity / "JARVIS is working" feedback | Galaxy work-loop: orchestrator dispatches a probe → planet transmits → reply probe; office build has the phone/paper equivalent |
| Orchestrator asking the user for a decision | "orchestrator ⟶ you" modal: plain-language checkboxes + free-text custom instruction + hand-off. This is the **text-mode analog** of the PTT/intent flow and slots directly under Phase-1 "text input" |
| Theme tokens / behavioral states | Reference themes already encode bg/fog/sky/glow/ring/particle treatments per theme |
| Panel embedding via iframe | Reference sizes via `ResizeObserver`, so it drops into `PanelFrame` with no internal changes |

`web/reference/agent-office.html` is a second "world" (same data model, office metaphor) — useful as a comparison render and not part of the JARVIS critical path.

## 6. opencode architecture notes (root)

- `opencode.json` is valid; `request-orchestrator` is the sole `mode: primary` agent routing to `jirri-data-analyst`, `opencode-dev-expert`, `oracle-apex-expert`, `uipath-rpa-expert`. This maps cleanly onto the galaxy: orchestrator = sun, the four specialists = planets, their skills/MCPs = capability nodes.
- The galaxy's mock data should be replaced with the live `client.agent.list()` + `client.session.list()` + the `mcp` block from `opencode.json`, and the SSE stream (`client.event.subscribe()`) used as the "something changed" tick to animate new agents/tools in (the reference's spawn API is shaped for exactly this).
- No config changes made here by design.

## 7. Prioritized punch list

1. **Commit the web app source** to `feat/web-frontend` so Phase 1 is reviewable. *(blocker)*
2. **Fix the blank render** via emissive+glow, dark clear color, and a `ResizeObserver`-driven canvas size. *(P0 — see §3)*
3. **Correct the Web Speech privacy claim**; decide whether mlx-whisper is the default for internal use. *(P0 — §4.1)*
4. Drop the Galaxy reference in as **Panel #1** (iframe `/galaxy/`) to unblock the panel system before the full React port. *(P1)*
5. Wire **live opencode data** (agents/sessions/mcp/SSE) into the galaxy in place of mock data. *(P1)*
6. Simplify TTS local path to `say -o`. *(P2 — §4.2)*
7. Pin Three.js; standardize addon imports. *(P2 — §4.4)*
8. Add **Black Ice + Chrome** to the React theme token set to match the reference. *(P2)*

---

*Generated as a local review on branch `feat/jarvis-galaxy-fixes`. No live config files were modified.*
