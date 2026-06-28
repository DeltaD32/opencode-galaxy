# JARVIS Galaxy — frontend (Module C)

Vite + React 18 + TypeScript + Three.js. A deterministic orbital galaxy: the
orchestrator is the amber sun, subagents are planets on inclined golden-angle
orbits, and the task currently `active` lights its tether. Colour comes from data.

Every body is emissive + carries an additive glow sprite over a deep-space clear
colour, and a `ResizeObserver` drives canvas sizing — so the first paint is never
the "blank galaxy", even at 0×0 mount.

## Run

Requires **Node ≥ 18** (not installed in the build environment that scaffolded
this, so the production `npm run build` here was not executed — the sources are
type-consistent under `tsconfig.json`'s `strict`).

```bash
npm install
npm run dev      # http://localhost:5273
npm run build    # tsc (typecheck) + vite build  ← the e2e gate
```

Data source: the gateway daemon (`daemons/gateway`) at `http://localhost:8132`.
If the gateway is unreachable the galaxy renders from a small mock set so it
works standalone.
