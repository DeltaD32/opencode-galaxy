# Galaxy Visual Language

**Status:** Canonical design decisions — captured 2026-06-26
**Scope:** How the orchestration model (`JARVIS-ORCHESTRATION-MODEL.md`) is rendered in the galaxy panel.
**Companion docs:** `JARVIS-ORCHESTRATION-MODEL.md`, `BUILD-GAP-ANALYSIS.md`.

The galaxy is not a static knowledge-graph viewer. It is a **live + scrubbable mission-control view of the blackboard**, pulled up on demand. This document defines its visual grammar so the rendering matches how the system is actually used.

---

## 1. The scene's metaphor

| System element | Galaxy representation |
|---|---|
| JARVIS / orchestrator | The **sun** at the centre |
| Project manager | A structurally **central planet** — every ticket routes through it; sits closest to the sun (or acts as a gate the work passes through) |
| Subagents | **Planets** orbiting the sun |
| Skills / capabilities | Tier-2 nodes co-rotating with their owning agent |
| MCP memory entities | Ambient **knowledge cloud** (low brightness backdrop) |
| Blackboard tickets | Small **bodies** that travel between the PM and assignee planets |
| Decisions / conflicts | Markers and **flares between planets** |

### Colour by role
- **Orchestrator (sun):** warm gold.
- **Primary agent:** BMW blue `#1c69d4`.
- **Subagents:** purple `#a855f7`.
- These come from `agent-reader.ts` per-node `color` — the scene must **read that**, not hardcode a single colour. The blue-vs-purple distinction *is* the visual language that lets you tell the orchestrator from its subagents at a glance.

---

## 2. The two-tier brightness rule (most important)

At all times the scene has two visual tiers:

- **Active set** — agents, skills, tickets, and memory engaged in the current session (or at the scrubbed timestamp). **Full brightness, saturated colour, lit tethers.**
- **Dormant set** — everything that exists but isn't engaged right now. **Dimmed way down** — present so you can see the whole team's shape, but clearly "not in play."

This solves the "wall of nodes" problem: with 10 agents, dozens of skills, and a growing memory graph, equal brightness is noise. Dimming the dormant set makes the active work *pop* without hiding context.

**It recomputes as you scrub.** At 2:00 only the dev-expert may be bright; scrub to 2:30 and three planets light while the dev-expert dims. The galaxy becomes a living map of *attention over time*.

**Data requirement:** every element needs a clear "am I active right now?" signal.
- Agents → the precise signal is **`specialist_queue.status = 'active'`** (the one specialist currently being delegated to). This is better than deriving from `sections`, which only tells you who has *contributed* to an open board, not who is executing now. Fall back to the `sections`-derived `deriveAgentStatuses` only if the queue isn't being read yet. **Blackboard is the authority either way — not SSE.**
- Tickets/boards → `blackboards.status` (`deliberating` / `awaiting-approval` / `executing` / `done` / `blocked`).
- Memory entities → harder to know per-session usage; default to a low ambient "knowledge backdrop" brightness, and let only agents/tickets do the bright/dim dance unless an agent explicitly reads/writes a node.

---

## 3. Working state: the lit tether

When an agent is working, **the tether line from the sun to that subagent-planet lights up and stays lit for the full duration of the work**, then fades back to dim when the task completes.

This was chosen over animated probes because:
- **Duration is legible** — a steady lit line shows *sustained* effort; a probe is a momentary blip.
- **Concurrency reads instantly** — three lit lines = three agents working in parallel, no counting.
- **It binds directly to state** — lit while the agent is active per the board; dim otherwise. No animation timing to manage.
- **It scrubs perfectly** — at any paused moment, the set of lit lines = exactly who was working at that timestamp.

### Tether/planet states (richer than on/off)
Because of the submit-for-review cycle, "busy" is not binary. Suggested mapping:

| Board state | Visual |
|---|---|
| idle / no task | Tether **dim**, planet dormant |
| proposing (`deliberating`) | Tether **building / gentle pulse** — thinking, not yet acting |
| awaiting review (`awaiting-approval`) | **Amber** — pending your/PM approval (see §4) |
| approved, executing (`executing`) | Tether **solid bright** |
| blocked (`blocked`) | **Amber/red** — needs attention |
| done (`done`) | Tether **fades out**, planet returns to dormant |

Optional later polish: gentle pulse on lit tethers (reads as "alive," not just "on"); intensity reflecting how long it's been working; colour shift on a problem.

---

## 4. Amber = pending your decision

When the blackboard has a decision **waiting on your approval**, the relevant node (or the conflict point between two agents) **glows amber**. Amber is reserved for "JARVIS needs your call."

This reinforces the voice loop: you *hear* "the dev expert and PM disagree, which way?" **and** *see* the amber marker pulsing at the same time. Audio and visual point at the same thing.

### Conflicts between agents
A conflict between two subagents' tickets shows as a **flare/line between the two planets** (not just planet-to-sun). When agent A's ticket conflicts with agent B's, a line flares amber *between them*. This makes the cross-checking step of the coordination loop visible.

---

## 5. Timeline: live + scrubbable

The galaxy is **both** a real-time view and a playback you can scrub.

- A **timeline scrubber** (bottom or side) spans the session duration.
- You can **pause real-time and rewind** to any moment.
- Each frame is **timestamped** so you can cross-reference to chat logs — click a moment in the galaxy and see the messages that were flying around then.
- Board state (tickets, decisions, conflicts) is **keyed to time** so you see the exact moment a decision was made.

### Playback stays put
When you've rewound to 2:00, you **stay at 2:00** even as new events arrive live. You're never yanked to "now."
- A **`● LIVE` indicator** lights when you're at the live edge.
- When you scrub back, it goes **dim/clickable** — click it to jump back to live.

---

## 6. Panel behaviour

- The galaxy is a **pull-up panel** (current slide-in drawer model is correct), **not always open.** JARVIS (orb + voice + chat) is the primary surface; the galaxy is the "show me the board" gesture.
- **But the timeline must exist even while the panel is closed** — see `JARVIS-ORCHESTRATION-MODEL.md` §7. The **renderer mounts lazily** when the panel opens; the **recorder runs always**. When the panel opens, the renderer reads the recorder's history so the full scrubbable timeline is there immediately.

---

## 7. Galaxy + Kanban: two views of one dataset

The galaxy and a literal Kanban board are **two renderings of the same blackboard data**:
- **Galaxy (Panel #1):** spatial — who's working on what, where the conflicts are, attention over time.
- **Kanban board (future Panel #2):** flat columns and tickets — To Do / In Progress / Review / Done.

Both read the same `/__db` data. Worth keeping the panel system able to host both.

---

## 8. Spotlight on query

When you ask JARVIS about a specific agent (§4.3 of the orchestration model), the galaxy can **spotlight that agent's planet** — focus/highlight it — so the pull query has a visual answer, not just a spoken one.

---

## 9. Quick reference — the visual grammar

- **Sun (gold):** orchestrator / JARVIS
- **Central planet:** project manager (work routes through it)
- **Planet (BMW blue):** primary agent
- **Planet (purple):** subagent
- **Bright element:** active in current session / scrubbed moment
- **Dim element:** exists but not engaged
- **Lit tether:** that agent is working now
- **Pulsing tether:** proposing / thinking
- **Amber node or flare:** pending *your* decision, or a conflict
- **Flare between two planets:** inter-agent conflict
- **Ambient cloud:** MCP memory (knowledge backdrop)
- **`● LIVE`:** at the live edge; dim when scrubbed back
