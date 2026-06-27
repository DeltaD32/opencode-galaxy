# JARVIS — Greenfield Build Guide

**A clean-room build for an efficient, secure, self-learning agentic platform.**
Backend: **direct LLM-API agent loops** (no opencode). State: local-first SQLite. Interfaces: JARVIS voice + memory galaxy.

This guide assumes you start from an empty directory. It is the **spine**; the detailed mechanics for individual subsystems live in the change orders (`CHANGE-ORDER-001/002/004/005`) and `JARVIS-ORCHESTRATION-MODEL` / `GALAXY-VISUAL-LANGUAGE`, which this guide references rather than duplicates.

---

## 0. What you're building, and what carries over

A **local-first, asynchronous multi-agent platform** you steer by voice or text. A control plane decomposes each request into a task DAG, runs independent work concurrently across LLM-API agent loops, enforces a propose→review→approve→execute governance gate in code, learns from every task, and shows you everything live in a 3-D "memory galaxy."

**Keep from v1 (it's runtime-agnostic — the real IP):**
- The governance model (decompose → assign → propose → review → gate → execute) — `JARVIS-ORCHESTRATION-MODEL.md`.
- The memory schema + conventions and the self-learning design — `CHANGE-ORDER-004`.
- The galaxy visual language — `GALAXY-VISUAL-LANGUAGE.md`.
- The agent domain prompts (programming, design, oracle-apex, etc.) and the HANDOFF/RESPONSE envelopes.

**Drop:** opencode as the runtime, `memory.jsonl` as storage, the `say`/vite-middleware hacks, the sequential `task` tool. These are replaced, not ported.

**The single biggest change vs v1:** agents are **direct LLM-API loops** (a system prompt + allowed tools + the messages API tool-use loop), dispatched by the control plane. Concurrency, governance, and resilience become properties of *your* code, not of a borrowed runtime.

---

## 1. Architecture — five planes

```
┌──────────────────────────────────────────────────────────────────┐
│ INTERFACE PLANE   JARVIS voice shell  +  Memory Galaxy (React/3D)  │
└───────────────▲───────────────────────────────▲──────────────────┘
                │ speak/listen                    │ live + scrubbable view
┌───────────────┴───────────────────────────────┴──────────────────┐
│ CONTROL PLANE     scheduler · task DAG · leases · retry · governance│
│                   gate (enforced in code) · conflict/file-lock      │
└───────────────▲───────────────────────────────▲──────────────────┘
        dispatch │                                 │ reads/writes
┌───────────────┴──────────┐         ┌────────────┴──────────────────┐
│ RUNTIME PLANE            │         │ STATE PLANE                    │
│ Agent = LLM-API loop +   │◄───────►│ Blackboard (working memory)    │
│ tools (sandboxed)        │ context │ Memory (semantic, SQLite+vec)  │
│ pluggable per task       │         │ Audit log (status_events)      │
└───────────────▲──────────┘         └────────────────────────────────┘
                │ calls
┌───────────────┴──────────────────────────────────────────────────┐
│ TOOL PLANE   file (scoped) · bash (sandboxed) · web · connectors   │
│              · skills · memory r/w · LLM-API client                 │
└────────────────────────────────────────────────────────────────────┘
```

**Why planes:** each is independently testable and replaceable. The runtime is pluggable (today an API loop; tomorrow anything) precisely because the control plane and state plane never assume what's underneath.

---

## 2. Tech stack (concrete, secure, local-first)

| Concern | Choice | Why |
|---|---|---|
| Daemons (control/memory/voice/runtime) | **Python 3.11+** | Best ecosystem for embeddings, whisper, piper, sqlite-vec. |
| Frontend | **React 18 + TypeScript + Vite + Three.js + Zustand** | The galaxy + JARVIS shell; matches v1 strengths. |
| LLM connection | **One provider-agnostic client** over the BMW LLM API — an **OpenAI-compatible `chat/completions` gateway** (`https://api.gcp.cloud.bmw/llmapi/v1`) reached with the `openai` SDK; tool use in **OpenAI function-calling** format | Verified against the stored docs (§2.1). The gateway fronts Claude/GPT/Gemini behind `provider/model` strings. Keep the client swappable for a direct Anthropic endpoint later. |
| Working + semantic state | **SQLite (WAL)** + **`sqlite-vec`** | ACID, one engine, vectors co-located (no index drift). |
| Cloud fallback (opt-in) | **libSQL / Turso** embedded replica | Durable + cross-machine; local replica authoritative. |
| Embeddings | **fastembed `bge-small`** (local, 384-d); BMW API fallback | Private by default, swappable. |
| STT / TTS | **faster-whisper** (portable) / **Piper** (local, streaming) | Portable, offline, low-latency; CO-002. |
| Wake word | **openWakeWord** (ONNX/WASM) | On-device "Hey JARVIS." |
| Sandbox | **Podman/Docker** (or OS sandbox) for the executor | Isolates agent file/bash actions. |
| IPC | Local HTTP + WebSocket per daemon; frontend is a thin client | Clear boundaries; nothing privileged in the browser. |

**Repo layout**
```
jarvis/
  daemons/
    control_plane/      # scheduler, DAG, leases, governance
    runtime/            # LLM-API agent loop + tool dispatch + sandbox
    memory/             # remember()/recall(), embeddings, gardener
    voice/              # STT/TTS streaming, wake word, barge-in
    gateway/            # single local API the frontend talks to
  agents/               # role prompts (md) + tool allowlists + model + policy
  tools/                # tool implementations (file, bash, web, connectors, memory)
  schema/               # SQL DDL (state.sql, memory.sql)
  web/                  # React + Three.js galaxy + JARVIS shell
  config/               # .env.example, policies, egress allowlist
  evals/                # regression harness for agent/prompt changes
```

---

## 2.1 Verified against the stored LLM API docs

Checked against `available-models-reference.json`, `GPT-MODEL-AUDIT.md`, and the `bmw-tool-agent` skill (`bmw_tool_agent.py` / SKILL.md). These are facts to build to, not assumptions:

**Connection & auth.** OpenAI-compatible: `OpenAI(base_url="https://api.gcp.cloud.bmw/llmapi/v1", …)` with header `Authorization: Bearer ${LLM_API_BEARER_TOKEN}` (OAuth2, auto-refreshed) plus `LLM_API_KEY`; optional `BMW_CA_BUNDLE`. Calls are `client.chat.completions.create(model, messages, tools)`. Models are namespaced `provider/model`.

**Tool use is OpenAI function-calling**, not Anthropic blocks: tools are `{"type":"function","function":{name,parameters}}`; the model returns `msg.tool_calls` (`tc.function.name`, `tc.function.arguments` as a JSON string); you reply with `{"role":"tool","tool_call_id":…,"content":…}`. The provider-agnostic client normalizes this.

**Three gateway constraints that shape the design:**
1. **No streaming inside the tool loop** — *"tool call IDs require complete responses."* So you cannot stream tokens while tools are in play. **Implication for voice:** JARVIS narrates *completed* agent responses, so the streaming-TTS win (CO-002 V1.1) is **audio-side pipelining** — sentence-chunk a finished response and synthesize/play sentence N+1 while N plays — not LLM-token streaming. Still a latency win; just not "speak before the model finishes." (Amends CO-002 V1.1 for the direct-gateway build.)
2. **Default max ~10 steps per agent loop**; the model may emit **parallel tool calls** in one step (execute all before the next call). Budget accordingly.
3. **Claude rejects multiple system prompts on this gateway** (`400: multiple system prompts`) — keep one consolidated system prompt per agent.

**Models (verified available) + policy.** Opus is **RESTRICTED** — do **not** design around it.

| Role | Model (`provider/model`) | Why |
|---|---|---|
| Workhorse specialists / executor | `anthropic/claude-sonnet-4-6` (200K ctx) | Strong + **prompt caching** (cache_read ~10× cheaper) — the cost lever |
| Cheap/fast tasks, worker | `anthropic/claude-haiku-4-5` | Fast, cheap, caches |
| Huge-context analysis | `openai/gpt-5.4` (922K) or `google/gemini-3.1-pro` (2M) | When context > 200K |
| Cheapest bulk | `google/gemini-3.5-flash` / `gemini-3.1-flash-lite` (1M) | Ultra-cheap, big context |
| Deep reasoning | `openai/o4-mini` / `o3-mini` | Reasoning-heavy steps |

**Cost-efficiency rule:** prefer **Claude models for any agent with a stable system prompt + repeated context** — prompt caching is the biggest lever and (per the GPT audit) GPT caching is not reliably available here. Reserve GPT/Gemini for genuine huge-context or specific-reasoning needs. The control plane picks the model per task (this is the `runtime`/model policy from CO-005).



Each phase: **goal · components · key decisions · done-when.** Phases are dependency-ordered; you have a usable system by Phase 6 and a self-improving one by Phase 7.

### Phase 0 — Foundations
**Goal:** the spine everything plugs into.
- **LLM client** (`tools/llm.py`): provider-agnostic wrapper over the **OpenAI-compatible** gateway exposing `complete(messages, tools, model)` returning text + tool calls. Uses the `openai` SDK against `LLM_API_BASE_URL` with `Authorization: Bearer ${LLM_API_BEARER_TOKEN}` + `LLM_API_KEY` (see §2.1). One place for base URL, auth, timeouts, retries (exponential backoff on 429/5xx). **Not streaming inside the tool loop** (gateway constraint §2.1); a separate non-tool call may stream the final narration text if needed.
- **Config + secrets:** `.env` / OS keychain only. Never store secrets in SQLite or the memory graph. An **egress allowlist** (LLM API host + approved connectors) — default-deny everything else.
- **SQLite bootstrap:** WAL mode; `schema/state.sql` + `schema/memory.sql` applied idempotently; a `meta` table records schema + embedding-engine versions.
**Done when:** `llm.complete()` returns a tool call against a trivial tool; DBs initialize; no secret is ever written to disk outside the keychain/.env.

### Phase 1 — Agent runtime (the opencode replacement)
**Goal:** run one agent task end-to-end via the LLM API.
- **Agent definition:** a role = system prompt (`agents/<name>.md`) + a **tool allowlist** + a model + a policy (max steps, token budget). Specialists are data, not code.
- **The agent loop** (`daemons/runtime/loop.py`): standard tool-use cycle in **OpenAI function-calling** form (§2.1) — send `messages + tools` → model returns `msg.tool_calls` → dispatch each tool → append `{"role":"tool", tool_call_id, content}` → repeat until the model returns a final text answer or hits the step/token budget (**default ~10 steps**). Handle **parallel tool calls** in one step (execute all, then continue). Emits structured events (step start/finish, tool call, result) for the audit log and galaxy.
- **Tool framework** (`tools/`): each tool is `name + JSON schema + handler`. Start with `read_file`, `write_file` (scoped), `bash` (sandboxed), `web_fetch`, `memory_read`. **Every tool validates its inputs and treats outputs as untrusted** (prompt-injection hygiene).
- **Sandbox:** file/bash tools run in the executor sandbox restricted to the task's declared `file_scope`. The runtime cannot touch paths it didn't lease.
**Done when:** a single agent (e.g. programming-expert) completes a real task through the loop, using sandboxed tools, producing a RESPONSE v1 envelope.

### Phase 2 — State plane (blackboard + audit)
**Goal:** durable source of truth.
- **Blackboard schema** (`schema/state.sql`): `projects, blackboards, tasks (the DAG — see Phase 3), sections, decisions, conflicts, status_events`. Carry `handoff_id` everywhere for end-to-end traceability; `status_events` is an append-only audit log (powers the timeline). (Schemas: `CHANGE-ORDER-001` + `-005`.)
- **Invariant:** blackboard is the source of truth; any daemon restart re-derives state from it.
**Done when:** an agent's run writes sections/decisions and every status transition appends a `status_events` row.

### Phase 3 — Control plane (the orchestrator you own)
**Goal:** concurrent, self-healing, governed execution. (Full spec: `CHANGE-ORDER-005`.)
- **Decomposition → DAG:** the project-manager/orchestrator role turns a request into `tasks` with `depends_on` (edges) and `file_scope` (paths). Independent tasks → parallelizable + collision-safe.
- **Scheduler:** ready-set (deps done) → acquire file leases (disjoint scope) → dispatch up to `CONCURRENCY` to the runtime → advance DAG on completion.
- **Resilience:** leases + heartbeats + a reaper (crashed tasks self-heal); retry-with-backoff; resumable because state lives in the blackboard.
- **Governance in code:** a task cannot enter the *execute* step unless its blackboard is `approved/executing`. Conflicts and approvals escalate to the user — never auto-resolved.
- **File-conflict model:** overlapping `file_scope` **serializes** (never races); semantic conflicts → `conflicts` row → escalate.
**Done when:** two independent specialists run concurrently (wall-clock ≈ max, not sum), a killed task self-heals, a transient failure retries, and nothing executes without approval. `CONCURRENCY=1` reproduces strictly sequential behavior.

### Phase 4 — Memory (self-learning core)
**Goal:** durable, private, self-binding knowledge. (Full spec: `CHANGE-ORDER-004`.)
- **Store:** SQLite + `sqlite-vec`; `entities, entity_aliases, observations, relations, entity_vectors`. Local embeddings by default.
- **Two verbs, deterministic placement:** `remember(handoff, …)` resolves the canonical entity from `handoff.project` (alias table) and writes transactionally with dedup + singleton enforcement; `recall(project, query, agent)` returns the project context pack + the agent's decayed learnings + a semantic search — **the agent never chooses where things go.**
- **Self-learning layers:** per-agent WORKED/AVOID/PATTERN with decay; project knowledge graph; recall at task start, `remember` at task end (enforced like the worker gate).
- **Gardener:** decay drives hot→warm→cold tiering; cold knowledge is LLM-consolidated so the searched surface stays bounded as history grows.
**Done when:** an agent recalls relevant prior learnings before acting and records new ones after, with zero manual placement; the warm working set stays bounded under load.

### Phase 5 — Orchestration glue
**Goal:** the full governance loop wired through control plane + state + memory.
- **Envelopes:** HANDOFF v1 (orchestrator→agent) and RESPONSE v1 (agent→blackboard) with mandatory `handoff_id`, absolute `repo_root`, `file_scope`, acceptance criteria. The control plane mints handoffs; agents must echo context.
- **Flow:** request → decompose (DAG) → schedule → each agent recalls memory, proposes (writes `## Proposed Changes`), submits → review + conflict check → **approval gate** (user for high-stakes) → executor applies approved plan in its sandbox → record result → `remember()`.
**Done when:** a multi-step request flows end-to-end with proposals gated before execution and learnings persisted.

### Phase 6 — Interfaces (JARVIS + galaxy)
**Goal:** voice-first control and a live window.
- **Voice daemon** (`CHANGE-ORDER-002`): streaming sentence-chunked TTS (start speaking mid-generation), warm-socket low-latency STT, PCM+VAD endpointing, wake word + barge-in with echo cancellation, pluggable local engines.
- **JARVIS shell + galaxy** (`CHANGE-ORDER-001` + `GALAXY-VISUAL-LANGUAGE`): the orb state machine; the orbital scene reading live state from the gateway — lit tethers for concurrently-executing agents, two-tier active/dormant brightness, amber for pending-your-approval, conflict flares, the timeline scrubber over `status_events` (live + scrubbable, playback stays put).
- **Conversational intents:** mute narration, "what's agent X doing?", "are we on track?", mid-project scope amendments, voice barge-in → abort.
**Done when:** you start a project by voice, hear headline responses, watch parallel agents work in the galaxy, scrub back through the run, and approve/redirect by voice.

### Phase 7 — Self-enhancement (the meta-loop) ⟵ the differentiator
**Goal:** the system improves *itself*, with you in the loop.
- **Routing cache:** every routing decision is embedded and cached; future requests reuse high-similarity routes — routing gets faster and more accurate over time (learns from itself).
- **Reflection loop:** on project completion, a reviewer agent analyzes the run (failures, retries, AVOID patterns, time-on-critical-path) and writes consolidated learnings + **improvement proposals**: prompt refinements, decomposition tweaks, routing-threshold changes, or "this recurring task has no skill — propose one."
- **Proposals are gated:** improvement proposals are written to the blackboard as amber items **for your approval** — the system never silently rewrites its own prompts/skills. Approved changes are versioned.
- **Eval harness** (`evals/`): a regression suite of representative requests with expected routing/outcomes. **Any agent-prompt or routing change must pass evals before it's accepted** — this is what makes self-modification safe rather than drift-prone.
- **Skill-gap detection:** recurring task shapes with no matching skill surface as "candidate skills" for you to approve and the system to scaffold.
**Done when:** completing projects measurably improves routing/recall, and the system proposes its own prompt/skill improvements that you approve and that pass evals before taking effect.

### Phase 8 — Security hardening
**Goal:** safe by construction. (Woven throughout; consolidated here.)
- **Local-first:** all state on-device; the LLM API is the only required egress; **egress allowlist** default-deny.
- **Sandboxed execution:** file/bash tools run in an isolated executor constrained to leased `file_scope`; no ambient FS/network access.
- **Governance gates:** no write/execute without approval; conflicts escalate; the gate is a scheduler invariant.
- **Secrets:** keychain/.env only; never in DB, memory, logs, or the galaxy. `local_only` memory entities never sync to cloud.
- **Prompt-injection defense:** tool outputs and web/connector content are untrusted; the control plane mediates what re-enters a model's context; agents can't escalate their own tool allowlist.
- **Audit:** append-only `status_events` + full handoff/response logging = a complete, scrubbable record of who did what, when, and why.
**Done when:** a hostile tool output can't exfiltrate secrets or touch unleased files; every action is gated and audited; pulling the network leaves the local system fully functional.

### Phase 9 — Observability & ops
- Structured logs per daemon; metrics (task latency, critical-path vs sum, retry rate, recall hit rate, token spend per project — a real cost tracker).
- Backups: SQLite snapshots; optional libSQL sync.
- The galaxy's stats view doubles as live observability (tier counts, active lanes, decay distribution).
**Done when:** you can see, at a glance, what the system is doing, what it costs, and how well it's learning.

---

## 4. Self-learning & self-enhancing — the full picture

Five loops, increasing in scope:

1. **Per-task recall/record** (Phase 4): agents recall before, record after. Tactical.
2. **Decay + gardener** (Phase 4): knowledge ages, consolidates, stays bounded. Hygiene.
3. **Routing cache** (Phase 7): routing learns from its own decisions. Faster dispatch.
4. **Reflection loop** (Phase 7): the system critiques completed work and proposes improvements. Strategic.
5. **Gated self-modification + evals** (Phase 7): approved improvements to prompts/skills/routing, regression-guarded. **Safe** self-enhancement.

The crucial design choice: **self-modification is proposal-based and human-gated, and every change must pass evals.** That's what separates a system that *improves* from one that *drifts*. The galaxy surfaces these proposals as amber items, so enhancing JARVIS feels like the same approve/redirect loop as any other task.

---

## 5. Migration from v1 (you don't lose anything)

- **Knowledge:** run the `memory.jsonl → SQLite` importer (`CHANGE-ORDER-004` M4) with the dedup-merge — your accumulated learnings carry over, cleaned.
- **Agents:** the role prompts port directly (they're runtime-agnostic); strip opencode-specific tool references and map to the new tool allowlists.
- **Governance + envelopes:** the HANDOFF/RESPONSE protocol and the propose→gate→execute loop transfer as-is.
- **Galaxy + voice specs:** already runtime-agnostic; build per their change orders against the new gateway.
- **Blackboard:** schema is largely reused; the control-plane columns (`depends_on`, `file_scope`, leases) are added from day one rather than retrofitted.

You can run v1 and the greenfield build side by side, pointing both at a copy of the migrated memory store, until you trust the new one.

---

## 6. Suggested milestones

| Milestone | Phases | You can… |
|---|---|---|
| **M1 — One agent, real tools** | 0–1 | run a single sandboxed agent via the LLM API |
| **M2 — Governed multi-agent** | 2–3 | decompose → run concurrently → gate before execute |
| **M3 — Self-learning** | 4–5 | agents recall/record automatically; full governance loop |
| **M4 — JARVIS** | 6 | steer by voice, watch the live galaxy, scrub history |
| **M5 — Self-enhancing** | 7 | the system proposes its own (eval-guarded, gated) improvements |
| **M6 — Hardened** | 8–9 | secure, audited, observable, cost-tracked |

Build to **M2** first — that's the proof the architecture works (concurrent, governed, no opencode). Everything after is additive.

---

## 7. The north star

When this is done: a **secure, local-first, asynchronous multi-agent platform** that you converse with as JARVIS; that decomposes work into a DAG and runs it concurrently across LLM-API agents; that enforces propose→review→approve→execute in code; that learns from every task and **proposes its own improvements** behind your approval and a regression suite; that keeps all knowledge in a durable, self-binding, private memory; and that shows you the whole living system — parallel agents, decisions, conflicts, history — in a galaxy you can fly through and rewind. opencode (or any runtime) is just an engine you could choose — never the foundation.
