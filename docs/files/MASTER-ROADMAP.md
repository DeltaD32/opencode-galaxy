# JARVIS — Master Roadmap (prioritized path to the target agentic setup)

**Purpose:** sequence every change order into one ordered plan, so the build order is unambiguous. This is the "what to do next, and why now" doc.
**Last updated:** 2026-06-26.
**Source docs:** `CHANGE-ORDER-001` (galaxy), `-002` (voice), `-004` (memory), `-005` (execution control plane), `JARVIS-ORCHESTRATION-MODEL`, `GALAXY-VISUAL-LANGUAGE`, `BUILD-GAP-ANALYSIS`.

---

## The one-sentence strategy

Make **execution** correct, parallel, and backend-agnostic (the foundation), make **state** durable and self-binding (memory + blackboard), and make the **interfaces** — galaxy and voice — fast and faithful windows onto that system. Execution is the headline because it's the largest gap between what this is (a single-agent runtime) and what you want (an asynchronous multi-agent platform).

## How the pieces relate

```
                 ┌───────────────────────────────────────────────┐
   INTERFACES    │  Galaxy (CO-001)        Voice loop (CO-002)    │  ← windows onto the system
                 └───────────────▲───────────────────▲───────────┘
                                 │ reads                │ speaks/hears
                 ┌───────────────┴───────────────────────────────┐
   STATE         │  Blackboard (opencode.db)   Memory (CO-004)    │  ← source of truth + knowledge
                 └───────────────▲───────────────────────────────┘
                                 │ owns task state
                 ┌───────────────┴───────────────────────────────┐
   EXECUTION     │  Control plane (CO-005)  →  pluggable runtime  │  ← the foundation; opencode swappable
                 └───────────────────────────────────────────────┘
```

The control plane **produces** the rich task state; the galaxy **visualizes** it; memory **feeds** task context; voice is the **conversational** surface. That's why a little galaxy + blackboard wiring should land early (so you can *see* the control plane working), and why execution is the spine.

---

## Priority tiers

### TIER 0 — Unblock + foundation hygiene *(days; do immediately)*
Cheap, low-risk, and everything else benefits.

| Item | Source | Why now |
|---|---|---|
| `npm install`, archive dead `App.tsx` | CO-001 Ph0 | Nothing builds otherwise. |
| **Fix `sections.compressed` query** | CO-001 Task 2.0 | One line; the live view is silently empty without it. |
| Persist `handoff_id` + `status_events` + `summary/blockers` | CO-001 B-DB1/2/3 | The control plane (Tier 1) and the durable timeline both lean on these. Cheapest moment to add. |
| Galaxy render fixes (ResizeObserver, colour-from-data, layer reactivity) | CO-001 Ph1 | Makes the window legible before live data flows. |

**Exit:** the app builds, the galaxy renders correctly, and the DB carries the correlation/audit columns the rest of the plan needs.

### TIER 1 — Execution control plane, Phase A *(the headline)*
The biggest efficiency **and** effectiveness win. Wrap opencode; don't replace it yet.

| Item | Source | Effect |
|---|---|---|
| DAG decomposition (`depends_on` + `file_scope`) | CO-005 A1 | Makes work parallelizable + collision-safe. |
| Scheduler (ready-set, concurrency) | CO-005 A2 | Latency = critical path, not sum. |
| Leases + heartbeats + reaper | CO-005 A3 | Crashed/abandoned tasks self-heal. |
| Retry + escalation | CO-005 A4 | Transient failures recover; hard blocks escalate. |
| File-lease conflict model | CO-005 A5 | Safe parallelism (the one hard new problem). |
| `OpencodeRuntime` (parallel sessions) | CO-005 A6 | Concurrency without changing opencode. |
| Expose DAG to galaxy | CO-005 A7 | You can *see* parallel lanes/retries/conflicts. |

**Run sequence:** prove `CONCURRENCY=1` parity first (PR2), add resilience (PR3), then raise concurrency behind the lease model (PR4).
**Exit:** independent specialists run concurrently, the system self-heals, opencode is unchanged, and the galaxy shows it live.

### TIER 1 (parallel track) — Galaxy live wiring
Independent of execution internals; do alongside Tier 1 so the control plane is observable.

| Item | Source |
|---|---|
| Pass live props; read `specialist_queue` (`status='active'`) | CO-001 Ph2 |
| Lit tethers + two-tier brightness | CO-001 Ph2 |
| Render blackboard graph; amber states; conflict flares | CO-001 Ph3 |

**Exit:** the galaxy is a faithful live view of real (now parallel) execution.

### TIER 2 — State durability + felt UX *(parallelizable tracks)*

**Memory (CO-004)** — foundational quality; bigger migration.
| Item | Source |
|---|---|
| SQLite + sqlite-vec store; local embeddings | CO-004 M0/M1 |
| `jsonl → sqlite` import with dedup-merge | CO-004 M4.1 |
| `remember()` / `recall()` (project-bound, enforcing) | CO-004 M2 |
| Cutover; retire hnswlib | CO-004 M4.2/4.3 |

**Voice (CO-002)** — the felt latency win; fully independent.
| Item | Source |
|---|---|
| Streaming sentence-chunked TTS | CO-002 V1.1 |
| Warm mic/socket; smaller model | CO-002 V1.2/1.3 |
| One-shot PTT + sidecar fix (correctness) | CO-002 V2 |

**Exit:** knowledge is durable, private, drift-free, and self-binding; JARVIS responds fast and reliably.

### TIER 3 — Depth + headroom *(when the foundation is solid)*

| Item | Source |
|---|---|
| Timeline scrubber + recorder (on `status_events`) | CO-001 Ph4 |
| Conversational intents (mute, status query, scope amend, barge-in) | CO-001 Ph5 / CO-002 |
| Memory tiering + gardener + consolidation | CO-004 M3 |
| Cloud fallback (libSQL + `local_only`) | CO-004 M5 |
| PCM capture + Silero VAD; wake word + AEC | CO-002 V3/V4 |
| Pluggable runtimes (agent-sdk / api) | CO-005 Ph B |
| Voice/memory/control-plane daemons consolidated | CO-002 V5 / CO-004 / CO-005 |

### TIER 4 — Evidence-gated
| Item | Source | Gate |
|---|---|---|
| Selective opencode retirement | CO-005 Ph C | Only with metrics from Tier 1+3 showing opencode is the bottleneck. |

---

## Why this order (the dependencies that matter)

- **Tier 0 before Tier 1:** the control plane writes richer task state; `handoff_id`/`status_events` should exist *before* it starts producing them, and the galaxy should render before it has live data to show.
- **Execution before timeline:** the scrubbable timeline (Tier 3) is only meaningful once there's real, durable, parallel execution state to scrub — and it rides on `status_events` from Tier 0.
- **Memory parallel, not blocking:** CO-004 improves task-context quality but doesn't gate execution; run it as its own track.
- **Voice fully parallel:** CO-002 is the UX surface and shares nothing with execution; sequence it by your appetite for the felt win.
- **Backend swap last:** B/C in CO-005 are taken on evidence, after A proves the control plane.

## The "perfect agentic setup," stated plainly

When this roadmap is done you have: an **asynchronous multi-agent platform** where a control plane decomposes a request into a DAG, runs independent work **concurrently**, **self-heals** crashes and retries transient failures, **enforces** the propose→review→approve→execute governance in code, draws task context from a **durable, self-binding, local-first memory**, lets you **steer by voice** with low-latency responses, shows you **everything live and scrubbable** in the galaxy — and treats opencode (or any runtime) as a **swappable engine**, not a foundation.

---

## At-a-glance order

1. **Tier 0** — build hygiene + `sections.compressed` fix + DB correlation columns + galaxy render fixes.
2. **Tier 1** — control plane Phase A (parallel + self-healing, opencode wrapped) **+** galaxy live wiring.
3. **Tier 2** — memory v2 migration **‖** voice streaming-TTS + STT correctness.
4. **Tier 3** — timeline, intents, memory tiering/cloud, voice-first, pluggable runtimes.
5. **Tier 4** — retire opencode where the data says to.
