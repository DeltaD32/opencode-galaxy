# JARVIS Orchestration & Coordination Model

**Status:** Canonical design decisions — captured 2026-06-26
**Scope:** The backend coordination model and JARVIS's conversational behaviour.
**Companion docs:** `GALAXY-VISUAL-LANGUAGE.md` (how this is visualised), `BUILD-GAP-ANALYSIS.md` (current build vs. this spec).

This document is the source of truth for *how the multi-agent system coordinates* and *how you interact with it through JARVIS*. It is deliberately implementation-light — it records decisions and the reasoning behind them, not code.

---

## 1. What this system is

An **asynchronous, multi-agent software platform** with a voice-first conversational front end.

- **JARVIS** is the orchestrator you talk to. You drive it by voice or text.
- Beneath JARVIS sits a **project manager (PM)** agent and a team of **specialist subagents** (programming, opencode-dev, oracle-apex, uipath-rpa, data-analyst, design, etc.).
- The agents coordinate through a **shared blackboard** (SQLite) structured as a **Scrum / Kanban board**.
- A separate **MCP memory server** holds semantic knowledge (what the system *knows*), distinct from the blackboard (what the system is *doing*).
- The **galaxy** is a pull-up visual panel that shows the live state of all of this, and lets you scrub backward through time.

The platform can see and modify your codebase on your request, track project status through the blackboard, and report progress back to you conversationally.

---

## 2. The coordination loop (the core protocol)

> **Role note (reconciled with the actual build, 2026-06-26):** In conversation this was framed as "the project manager decomposes and gates." The implemented system splits that role across a **trio**, and the `project-manager` agent is actually a *domain specialist* (Agile/Jira), not the coordinator. The real mapping:
> - **request-orchestrator** (primary) — decomposes the request, creates the blackboard, delegates to specialists in sequence, reviews their proposals, writes the Execution Plan, and makes the gate decision.
> - **secretary** (subagent) — stateful project coordinator over `opencode.db`: registers blackboards, manages the specialist queue, records decisions/conflicts, answers "where are we?", and resolves conflicts (escalating to you when needed). Never executes work.
> - **worker** (subagent) — mechanical executor. Reads the approved Execution Plan and applies it. Enforces the governance gate: refuses to run unless status is `executing`.
> - **specialists** (programming-expert, design-expert, project-manager, oracle-apex, uipath-rpa, jirri, …) — domain experts that post `## Analysis` + `## Proposed Changes` to the blackboard.
>
> Read "PM" below as "the orchestrator+secretary coordination role," not the `project-manager` agent.

Every request flows through the same governed loop:

1. **You → JARVIS.** "Build X" / "fix Y" — voice or text.
2. **JARVIS → PM.** The orchestrator hands the request to the project manager.
3. **PM decomposes.** The PM breaks the request into **phases**, and each phase into **workable blocks of assignments** (tickets). This is sprint planning: an epic becomes tickets.
4. **PM assigns.** Each ticket is routed to the relevant specialist subagent and posted to the blackboard.
5. **Subagent proposes.** The assigned agent reads its ticket *from the board*, works out its **recommended changes** and **next steps**, and **submits the proposal back to the board** — *before taking any action*.
6. **Review + conflict check.** Proposals are checked against each other for conflicts (does agent A's change break agent B's assumptions? do two edits collide?). The PM gates this.
7. **Conflicts escalate to you.** If agents disagree, or a proposal is risky, JARVIS surfaces it and **asks for your approval before any decision is picked.** (See §3.)
8. **Approved tickets execute.** Only after review/approval does the agent act. The board moves the ticket across its columns.
9. **Finished product** is assembled from the completed board.
10. **JARVIS keeps you informed** at whatever altitude you've chosen (see §4).

### Key principle: submit-for-review before action

No agent acts unilaterally. Each agent must post its plan (recommended changes + next steps) to the board and pass review **before** it executes. This is the platform's **governance / safety mechanism** — it's how you prevent agents from making changes you never sanctioned. The blackboard + PM gate is where that governance lives, and the galaxy is how you *watch* it happen and catch a bad proposal at the amber stage.

---

## 3. Human-in-the-loop: conflicts & interruption

**Conflicts require your approval.** JARVIS does **not** auto-resolve. When two subagents disagree, or a proposal needs a judgment call, JARVIS presents the disagreement plainly ("the dev expert wants to rewrite the config; the PM wants to patch it — which way?") and waits for your decision. The orb enters a waiting state; the relevant board item glows amber.

**You can interrupt anything, mid-task.** Including JARVIS itself. Starting to speak, or issuing a stop/cancel, pauses what's happening. This is a hard requirement:
- The opencode backend must expose an **abort mechanism** (`abortSession()` already exists in the session layer).
- JARVIS must listen for your voice starting (or a cancel keyword) and fire the abort mid-stream.

---

## 4. JARVIS as chief of staff (not narrator)

JARVIS's job is to be a **conversational interface to the blackboard, at whatever altitude you want.** Narration is one mode, not the whole job.

### 4.1 Narration mode (optional, mutable)
- When on, JARVIS reads **response headlines** — a basic summary of what an agent reported ("the dev expert found a blank-render issue in the ResizeObserver setup"). Not verbose; details live in chat.
- Narration is driven by **agent responses**, not JARVIS's internal reasoning. You hear *conclusions*, not deliberation.
- **Narration can be muted** — by voice command or a settings toggle. Muted, JARVIS works silently and the galaxy carries the visual story.

### 4.2 Thousand-foot view (the primary role)
With narration muted (or alongside it), JARVIS holds the **strategic picture**: which phases are done, what's blocked, what's next, where the risks are. You ask "are we on track?" and it answers from the altitude of the whole board — the sprint summary, not the line items. JARVIS sees the forest while the subagents are in the trees.

### 4.3 Status queries (pull, on demand)
You can ask about any agent and JARVIS checks **live**: "what's the oracle-apex-expert doing?" → "it's in review, waiting on the PM to approve its schema change." This is a *pull* interaction that complements *push* narration — even with narration muted, you can always ask. Asking about an agent may also **spotlight its planet** in the galaxy.

### 4.4 Scope amendment (mid-project)
You can change the plan while it's running: "also handle the error case" / "don't forget to add tests." JARVIS routes the amendment to the PM, who **slots a new ticket into the right phase** (possibly reordering or adding a dependency). The plan is **living**, not frozen at kickoff — the PM accepts mid-sprint amendments, and the galaxy shows a new ticket appearing in its column.

### JARVIS's conversational intents (summary)
| Intent | Direction | Example |
|---|---|---|
| Narrate | push | "The dev expert found…" (mutable) |
| Summarize status | pull | "Are we on track?" → sprint-level answer |
| Query agent | pull | "What's agent X doing?" → live board check |
| Amend scope | command | "Also add Y" → new ticket to PM |
| Approve/resolve | command | "Go with the dev expert's approach" |
| Interrupt | command | "Stop" → abort mid-task |

---

## 5. Source of truth: the blackboard wins

**The blackboard (SQLite) is authoritative.** SSE is the nervous system, not the truth.

- **Blackboard = durable, queryable, time-keyed.** It says what the real state is: which tickets exist, who's assigned, what column each is in, what decisions and conflicts are open. Because it's queryable by timestamp, **scrubbing the timeline = querying board state at time T.** This is what makes the audit/playback feature natural.
- **SSE = the trigger, not the authority.** SSE events ("agent started", "message updated") tell the recorder *"something changed — re-poll the board."* You get real-time responsiveness without making ephemeral events the source of truth.
- **When they disagree, re-query the board and the board wins.**

### The blackboard is bidirectional
It is **both** the instruction channel and the report channel:
- Agents **receive** work from it (PM posts assignments; agents pull their tickets).
- Agents **report** work to it (agents post proposals, results, decisions, conflicts).

This is a true blackboard system (agents reading/writing a shared structure) wearing a Kanban board's clothes.

### Ticket lifecycle (columns)
A ticket moves through states that map to board columns. Current DB statuses already in use: `deliberating`, `awaiting-approval`, `executing`, `blocked`, `done`. Conceptually:

```
To Do (assigned) → Proposing (deliberating) → Review (awaiting-approval)
        → Executing (approved) → Done
                  ↘ Blocked (needs you / conflict) ↗
```

`awaiting-approval` / `blocked` are the states that pull *you* in (amber). `executing` is active work (bright). `done` fades to dormant.

---

## 6. Two kinds of memory (don't conflate them)

| | **Blackboard (SQLite)** | **MCP memory server (memory.jsonl)** |
|---|---|---|
| Holds | Working memory — what we're *doing* | Semantic memory — what we *know* |
| Content | Projects, tickets, decisions, conflicts | Entities, relations, observations |
| Role | Coordination protocol + source of truth | Knowledge backdrop |
| In the galaxy | The active, central drama | Ambient, low-brightness cloud |
| Volatility | Changes constantly during work | Grows slowly; reference layer |

The blackboard is the **center of gravity**. MCP memory is context the agents draw on, shown as a quieter backdrop.

---

## 7. Always-on recorder vs. lazy renderer (architectural consequence)

Two decisions collide and force a separation of concerns:
- The galaxy is a **pull-up panel** (not always open) → for performance, the **Three.js renderer should mount only when the panel opens.**
- The galaxy is a **scrubbable audit log**, and **playback stays put while live continues** → something must be **recording continuously, even when the panel is closed.**

**Resolution — split data capture from rendering:**
- **Recorder (always on, non-visual):** subscribes to SSE and polls `/__db` from app start, keeping a **timestamped time-series of board snapshots** in memory (and/or persisted). Cheap — just collecting state, no rendering. Runs whether or not the galaxy is open.
- **Renderer (lazy):** the Three.js scene mounts when the panel opens, reads the recorder's history so the **full timeline is immediately scrubbable**, plus the live edge.

This mirrors how the orb and top-bar already work (they react to SSE continuously); the galaxy simply hasn't joined that pattern yet. The recorder is essentially "what `SessionContext` already tracks, but kept as a time-series instead of only the current value."

---

## 8. Glossary

- **JARVIS** — the orchestrator/front end you converse with.
- **PM** — project-manager agent; the scrum master. Decomposes, assigns, gates execution.
- **Subagent** — specialist expert that proposes and (on approval) executes tickets.
- **Blackboard** — SQLite Kanban board; durable source of truth; bidirectional.
- **Ticket** — a workable block of assignment (a task on the board).
- **MCP memory** — semantic knowledge graph (memory.jsonl) via the MCP server.
- **Recorder** — always-on data layer capturing board snapshots over time.
- **Renderer** — the galaxy's Three.js scene; mounts lazily when the panel opens.
- **Live edge** — the present moment on the timeline; where playback sits until you scrub back.
