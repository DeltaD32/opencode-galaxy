# JARVIS — DIY Build Manual (step-by-step, with code)

**Who this is for:** you, or an AI agent (default model `anthropic/claude-sonnet-4-6`), building the platform from an empty directory.
**How to use it:** do the steps **in order**. Each step is **Do → Code → Run → Verify**. Do not advance past a step whose **Verify** fails. Part I is fully runnable code (verified in a sandbox). Part II builds the bigger subsystems with the same rhythm, citing the change orders for exhaustive detail.
**Companion docs:** `JARVIS-BUILD-GUIDE.md` (architecture/why), `CHANGE-ORDER-001/002/004/005`, `JARVIS-ORCHESTRATION-MODEL.md`, `GALAXY-VISUAL-LANGUAGE.md`.
**Starter code:** the Part I files are provided as a working starter (`jarvis-build/`) — you can build from scratch by following the steps, or start from the starter and read along.

> **For an AI agent building this:** after every step, run the step's Verify command and paste the output. If it fails, fix before continuing. Never skip the acceptance test at the end of a Part. Use `claude-sonnet-4-6` for your own reasoning; the platform's per-task model is configured separately (Step 2).

---

# PART I — Foundation (runnable; ends at a governed, concurrent multi-agent core)

When Part I is done you have: an LLM-API agent loop, sandboxed tools, a SQLite blackboard + task DAG, and a control-plane scheduler that runs independent agents **concurrently**, enforces a **governance gate**, **self-heals** crashed tasks, and **never lets two agents edit the same file at once** — with no opencode. This is the proof the architecture works.

## Step 0 — Environment

**Do:** create the project and a virtualenv; install deps.
```bash
mkdir jarvis && cd jarvis
python3 -m venv .venv && source .venv/bin/activate
pip install openai fastembed sqlite-vec fastapi "uvicorn[standard]" pydantic python-dotenv httpx
# (sqlite-vec → in-DB vectors for memory; fastembed → local embeddings. On a managed
#  Python you may need: pip install --break-system-packages sqlite-vec)
mkdir -p jarvis schema agents tests
```
**Verify:**
```bash
python -c "import openai, sqlite3; print('deps ok')"
```
Expect `deps ok`.

## Step 1 — Secrets & config

**Do:** create `.env` (never commit it) with your BMW LLM API credentials. These names are verified against the stored docs.
```bash
cat > .env <<'EOF'
LLM_API_BASE_URL=https://api.gcp.cloud.bmw/llmapi/v1
LLM_API_BEARER_TOKEN=        # OAuth2 token (your gateway login provides this)
LLM_API_KEY=                 # BMW gateway key
JARVIS_MODEL=anthropic/claude-sonnet-4-6
JARVIS_DB_PATH=./.jarvis/state.db
EOF
echo ".env" >> .gitignore
```
**Verify:** `cat .env` shows the keys. Load it in your shell with `set -a; . ./.env; set +a` before running anything that calls the LLM.

> **Egress security:** in production, allow outbound network **only** to `api.gcp.cloud.bmw` (and any approved connectors). Default-deny everything else. The platform needs no other egress.

## Step 2 — The LLM client (`jarvis/llm.py`)

**Do:** create the provider-agnostic client. It's OpenAI-compatible (`chat/completions`), uses `provider/model` strings, and defaults to Sonnet 4-6.

```python
# jarvis/llm.py
from __future__ import annotations
import os, time

DEFAULT_MODEL = os.environ.get("JARVIS_MODEL", "anthropic/claude-sonnet-4-6")
BASE_URL = os.environ.get("LLM_API_BASE_URL", "https://api.gcp.cloud.bmw/llmapi/v1")

def _client():
    from openai import OpenAI
    headers = {}
    tok = os.environ.get("LLM_API_BEARER_TOKEN")
    if tok:
        headers["Authorization"] = f"Bearer {tok}"
    return OpenAI(base_url=BASE_URL, api_key=os.environ.get("LLM_API_KEY", "unused"),
                  default_headers=headers or None)

def complete(messages, tools=None, model=None, max_retries=4):
    """One chat/completions call → assistant message (.content, .tool_calls).
    Retries with backoff. NOTE: no streaming inside the tool loop (gateway rule)."""
    model = model or DEFAULT_MODEL
    client = _client()
    delay = 1.0
    for attempt in range(max_retries):
        try:
            resp = client.chat.completions.create(model=model, messages=messages, tools=tools or None)
            return resp.choices[0].message
        except Exception:
            if attempt == max_retries - 1:
                raise
            time.sleep(delay); delay *= 2
```
**Verify (only if you have live credentials):**
```bash
python -c "from jarvis.llm import complete; print(complete([{'role':'user','content':'reply with OK'}]).content)"
```
Expect `OK`. (No creds yet? Skip — Part I's tests use a mock LLM.)

**Model policy (verified available; Opus is RESTRICTED — don't use it):**
`anthropic/claude-sonnet-4-6` workhorse (has prompt caching — your main cost lever); `anthropic/claude-haiku-4-5` fast/cheap; `openai/gpt-5.4` (922K) or `google/gemini-3.1-pro` (2M) only when context > 200K. Prefer Claude for any agent with a stable system prompt + repeated context.

## Step 3 — State schema (`schema/state.sql`) + DB (`jarvis/db.py`)

**Do:** create `schema/state.sql` (provided in the starter — `projects, blackboards, tasks (the DAG), sections, decisions, conflicts, status_events, file_leases`) and `jarvis/db.py` (provided: `connect`, `init_db`, `now`, `new_id`, `log_status`). Both are in the starter verbatim.

**Verify:**
```bash
python -c "from jarvis import db; c=db.connect(':memory:'); db.init_db(c); \
print([r[0] for r in c.execute(\"SELECT name FROM sqlite_master WHERE type='table' ORDER BY name\")])"
```
Expect: `['blackboards', 'conflicts', 'decisions', 'file_leases', 'projects', 'sections', 'status_events', 'tasks']`.

## Step 4 — Tool framework (`jarvis/tools.py`)

**Do:** create the registry + sandboxed tools (provided in the starter). Key properties to preserve:
- Tools are OpenAI function-calling shaped (`{"type":"function","function":{...}}`).
- `ToolContext` carries `repo_root` + `file_scope`; `read_file`/`write_file` call `ctx._check(path)` which **rejects any path outside `file_scope`**.
- `bash` runs in `repo_root` (wrap in a real container/sandbox with no network for production).
- Tool errors are **returned to the model**, never raised — the agent can recover.

**Verify:** covered by the Part I acceptance test (Step 7), specifically the `file_scope` sandbox test.

## Step 5 — Agent runtime loop (`jarvis/runtime.py`)

**Do:** create `TaskSpec`, `TaskResult`, and `run_task` (provided). This is the opencode replacement — the OpenAI function-calling loop:
1. messages = `[system, user]` (**one** system prompt — gateway rejects multiple for Claude).
2. call `complete(messages, tools)`; append the assistant message.
3. if no `tool_calls` → done, return final text.
4. else execute **all** tool calls this step (parallel calls allowed), append each `{"role":"tool", tool_call_id, content}`, loop.
5. stop at `max_steps` (default 10).

**Verify:** Step 7 acceptance test (`test_agent_loop`).

## Step 6 — Control-plane scheduler (`jarvis/scheduler.py`)

**Do:** create the scheduler (provided). One `tick()`:
1. **reap** stale `active` tasks whose lease expired (crash self-heal).
2. build the **ready set**: `pending/retrying` tasks whose `depends_on` are all `done`.
3. drop any task whose blackboard isn't `executing` (**governance gate**).
4. drop any task whose `file_scope` overlaps a held lease **or** a scope already claimed earlier in this tick (**serialize same-file edits**).
5. acquire leases, mark `active`, **dispatch up to `concurrency` tasks in parallel**.
6. on done → `done` + release leases; on fail → `retrying` (backoff) or `failed`.
`run_until_idle()` ticks until no live tasks remain.

> The bug worth knowing (already fixed in the starter): leases are written at dispatch, so within one tick you must also track paths *claimed this tick* — otherwise two same-file tasks both pass the check and run together. The starter tracks an in-tick `claimed` set.

## Step 7 — ✅ ACCEPTANCE: run the foundation test

**Do:** use the provided `tests/test_smoke.py` (mock LLM — no network needed).
**Run:**
```bash
python tests/test_smoke.py
```
**Verify — expect exactly:**
```
schema applies cleanly:
  ✓ tables: ['blackboards', 'conflicts', 'decisions', 'file_leases', 'projects', 'sections', 'status_events', 'tasks']
  ✓ agent loop runs tool-use cycle and writes within file_scope
  ✓ file_scope sandbox blocks out-of-scope writes
  ✓ independent tasks dispatch together; dependent task waits for both
  ✓ governance gate: task will not run until blackboard is 'executing'
  ✓ overlapping file_scope serializes (no concurrent edit to same file)

ALL FOUNDATION TESTS PASSED ✅
```
**This is Milestone M2.** You now have a governed, concurrent, self-healing multi-agent core with no opencode. Everything in Part II builds on it.

## Step 8 — Decomposer + orchestrator: request → DAG → concurrent run (Milestone M1→M2 complete)

**Do:** create `jarvis/decomposer.py`, `jarvis/agents.py`, `jarvis/orchestrator.py`, and `run.py` (all provided in the starter, all tested). This is the link from "a request" to "a running DAG":
- **`decomposer.decompose(request, repo_root, llm, agents)`** — the planner LLM call returns JSON; `parse_plan` **validates hard** (unique ids, valid `depends_on`, **acyclic**, `file_scope` resolves under `repo_root`) and **rejects broken plans** rather than seeding them. `seed_plan` writes the project/blackboard/tasks.
- **`agents.py`** — the registry (agents are *data*; Module F later makes the Architect create them). Ships with built-in defaults so the foundation runs before you author prompts.
- **`orchestrator.handle_request(request, repo_root, llm, auto_approve=…)`** — decompose → seed → (if approved) `run_until_idle` → summary. The single hand-over entrypoint.

**Run (no creds — the tests use a mock planner):**
```bash
python tests/test_decompose.py
```
**Verify — expect:**
```
  ✓ valid plan parses and file_scope normalises under repo_root
  ✓ dependency cycle is rejected
  ✓ bad dependency ref and file_scope escape are rejected
  ✓ end-to-end: request -> DAG -> approve -> concurrent run -> all tasks done
  ✓ without auto_approve, the gate holds (awaiting-approval) — nothing executes

DECOMPOSER + ORCHESTRATION TESTS PASSED ✅
```

**Run (with live creds) — the one-command hand-over:**
```bash
set -a; . ./.env; set +a
python run.py "build a hello-world FastAPI app"          # plan only — prints the DAG, gate holds
python run.py --go "build a hello-world FastAPI app"     # plan + execute concurrently
```
**Verify:** plan-only prints the tasks with their `depends_on` + `file_scope`; `--go` runs them (independent tasks concurrently, dependent tasks after their predecessors) and reports each task `done`. Inspect `status_events` for the full lifecycle.

**You are now end-to-end:** talk to it → it decomposes → governed, concurrent execution → results. No opencode anywhere.

---

# PART II — Subsystems

Same rhythm. Each subsystem cites the change order with full diffs/contracts; here you get the build order, the key code/contracts, and the acceptance gate.

## Module A — Memory (self-learning) · ✅ BUILT & TESTED (provided in starter) · full spec: `CHANGE-ORDER-004`

The memory system is **implemented and verified** in the starter (`jarvis/memory/`, `schema/memory.sql`, wired into `orchestrator.py`). What's there:

- **Store** (`schema/memory.sql` + `jarvis/memory/store.py`): `entities, entity_aliases, observations, relations` + a `sqlite-vec` `entity_vectors` table created at runtime with the engine's dim. SQLite + vectors in one DB → no index drift. Singleton + dedup are enforced by **unique indexes**, not prompts.
- **Pluggable embeddings** (`jarvis/memory/embeddings.py`): `HashEngine` (deterministic, offline — used by tests and as a no-dependency fallback), `LocalEngine` (`fastembed` `bge-small`, 384-d — **production default**, `pip install fastembed`), `BmwEngine` (gateway, fallback). Dim is recorded in `meta` and a mismatch is refused (no silent corruption).
- **`remember(project=…, observations=…, relations=…)`**: resolves the canonical entity from `project` via the alias table (deterministic placement — agents never choose where things go), dedups observations, replaces singletons (`Status:`), ensures ≥1 relation, embeds name+observations.
- **`learn(agent, tag, domain, note)`**: per-agent WORKED/AVOID/PATTERN learnings (PATTERN decays 2× slower).
- **`recall(project=…, query=…, agent=…)`** + **`recall_text(…)`**: returns a project context pack + the agent's decay-ranked learnings + semantic KNN, formatted as an injectable prompt block.

**The learning loop is wired into the orchestrator:** before a task runs, `_build_spec` injects `memory.recall_text(...)` into the agent prompt; after the run, `handle_request` records a `WORKED` learning per completed task + a project status. Pass a store to turn it on:
```python
from jarvis.memory import MemoryStore
mem = MemoryStore.open()                      # ~/.jarvis/memory.db, local embeddings
orchestrator.handle_request(req, repo, complete, auto_approve=True, memory=mem)
```

**✅ Acceptance (run it):**
```bash
python tests/test_memory.py              # project binding, dedup, singleton, KNN, decay, dim-guard
python tests/test_memory_integration.py  # run 1 records a learning → run 2 RECALLS it into the prompt
```
Both pass offline (HashEngine). For real semantics in production set `JARVIS_EMBED_ENGINE=local` (installs/uses `fastembed`).

**Still to add from CO-004 (not yet coded):** the gardener (decay→tier migration + cold consolidation, M3), the `memory.jsonl → memory.db` importer (M4, for porting v1 knowledge), and libSQL cloud sync (M5). The store and learning loop — the core — are done.

> **Two real bugs the tests caught while building this** (so you trust the rest): vectors must be embedded from *name + observations* (not just the name) or semantic recall misses the content; and `sqlite-vec` virtual tables need delete-then-insert (no `INSERT OR REPLACE`). Both fixed in the shipped code. A threading fix also moved spec-building (memory reads) onto the main thread — DB reads aren't thread-safe across the scheduler's workers.

## Module B — Voice (JARVIS I/O) · full spec: `CHANGE-ORDER-002`

**Build order (latency first):**
1. **Voice daemon** (`daemons/voice/`): FastAPI + WebSocket. STT via `faster-whisper` (portable) or `mlx-whisper` (mac); TTS via **Piper** (local, streaming). One `/health` reporting active engines.
2. **TTS pipeline**: sentence-queue. **Important gateway nuance:** the LLM loop does **not** stream tokens (CO-002 §ammendment / build-guide §2.1), so JARVIS narrates **completed** responses — chunk a finished response into sentences and synthesize/play sentence N+1 while N plays (audio-side pipelining).
3. **STT correctness**: one-shot blob per push-to-talk (no mid-stream WebM clearing); end on release. Then PCM + Silero VAD for hands-free.
4. **Voice-first**: openWakeWord ("Hey JARVIS"), barge-in (`tts.stop()` on detected speech) with `echoCancellation:true`.
5. **Pluggable engines**: `STT_ENGINE`/`TTS_ENGINE`/`TTS_VOICE` env, all local-first.

**✅ Acceptance:** you speak a request, it transcribes fully (no cutoff), JARVIS begins speaking sentence 1 of a multi-sentence reply before the last sentence's audio is synthesized, and talking over it stops playback.

## Module C — JARVIS shell + Memory Galaxy · full spec: `CHANGE-ORDER-001` + `GALAXY-VISUAL-LANGUAGE`

**Build order:**
1. **Gateway** (`daemons/gateway/`): one local API the frontend talks to — exposes blackboard/task/memory snapshots (read from `state.db`/`memory.db`) and an SSE/event stream the control plane feeds. The browser stays a thin client.
2. **Frontend scaffold**: React 18 + TS + Vite + Three.js + Zustand. The JARVIS shell (orb state machine + voice controls) and the galaxy panel (pull-up drawer).
3. **Galaxy (orbital)**: sun = orchestrator; planets = agents (BMW-blue primary / purple sub, **colour from data**); lit tether = the task currently `active` (read the task DAG); two-tier active/dormant brightness; amber = `awaiting-approval`/`blocked`; conflict flares between agents.
4. **Live + scrubbable**: an always-on recorder over the gateway's events + `status_events`; a timeline scrubber that stays put when rewound (`● LIVE` indicator).
5. **Conversational intents**: mute narration, "what's agent X doing?", "are we on track?", scope-amend, barge-in→abort.

**✅ Acceptance:** start a project by voice, watch concurrent agents as concurrent lit tethers, see amber when something needs you, scrub back to any moment and cross-reference chat.

## Module D — Self-enhancement (the differentiator) · build-guide §4 / Phase 7

**Build order:**
1. **Routing cache**: embed each routing decision; reuse high-similarity routes. Routing gets faster/better with use.
2. **Reflection loop**: on project completion, a reviewer agent analyzes the run (failures, retries, AVOID patterns, critical-path time) → consolidated learnings + **improvement proposals** (prompt tweaks, decomposition changes, routing thresholds, "no skill for this recurring task").
3. **Gated self-modification**: proposals are written as **amber items for your approval** — the system never silently rewrites its own prompts/skills. Approved changes are versioned.
4. **Eval harness** (`evals/`): representative requests with expected routing/outcomes. **Any prompt/routing change must pass evals before acceptance.** This is what makes self-improvement safe, not drift.
5. **Skill-gap detection**: recurring task shapes with no skill surface as candidate skills.

**✅ Acceptance:** completing projects measurably improves routing/recall; the system proposes its own improvements that you approve and that pass evals before taking effect.

## Module E — Security hardening · build-guide Phase 8

**Checklist (each is an acceptance test):**
- **Egress allowlist** default-deny (only the LLM gateway + approved connectors). *Test:* a tool's attempt to reach any other host fails.
- **Sandboxed executor**: file/bash tools constrained to leased `file_scope`, no ambient FS/network. *Test:* the Part I `file_scope` test + a no-network bash test.
- **Governance gates**: no execute without approval. *Test:* the Part I governance test.
- **Secrets** in keychain/`.env` only — never in DB/memory/logs/galaxy. *Test:* grep the DBs and logs for token substrings → none.
- **Prompt-injection**: tool/web/connector outputs are untrusted; agents can't escalate their tool allowlist. *Test:* a poisoned tool result instructing "ignore your scope" does not change behavior.
- **Audit**: every transition in `status_events`. *Test:* reconstruct a full run from the table alone.

## Module F — Self-extension: dynamic agent & skill creation · build-guide Phase 7 (extends Module D)

**Why this is easy here:** in this build, **agents and skills are data**, not hardcoded runtime features.
- An **agent** = a row + one consolidated system prompt + a tool allowlist + a model + a file-scope policy + routing keywords.
- A **skill** = a folder (`skills/<name>/`) with a handler, an OpenAI function-calling schema, a `SKILL.md`, and tests, registered in the tool registry.

Because they're data, a privileged **Architect** agent can create them on request — you ask in natural language, the system scaffolds, and a gate keeps it safe.

## Module F — Autonomous self-extension: self-model + verified agent/skill creation · extends Module D

**Goal:** the system understands its own architecture and creates/changes agents and skills **autonomously**, cleanly on the first try — without you approving every change. The trick to making "autonomous" and "clean" the same thing: **replace the human gate with an automated verification gate.** Autonomy is high; safety comes from the system checking its own work, not from you watching.

**Why it's feasible here:** agents and skills are **data** (a row + prompt + tool allowlist + model; or a folder with handler + schema + tests). So the system can read and write its own composition.

### F.1 — Self-model (so it "understands its own architecture")
A change is only clean if the system can *see itself accurately*. Build an always-current, machine-readable self-model and introspection tools.
- **`manifest.json`** auto-generated from the live registries: agents (from the `agents` table), skills (`skills` table + tool registry), tool schemas, DB schemas (DDL), the planes, and the **invariants** (the hard rules). Never hand-maintained — regenerated on every change so it can't go stale.
- **Introspection tools** the Architect can call: `describe_architecture()`, `describe_agent(name)`, `describe_skill(name)`, `list_invariants()`.
- **Templates**: `agent.template.md` and `skills/_template/` (handler + schema + tests stub). Creation is *fill-in-the-blanks against a template + the self-model*, not freeform — this is what drives first-try success up.

### F.2 — The autonomous change pipeline (generate → verify → repair → apply)
The Architect runs this loop **by itself**; you don't sit in it:
1. **Generate** the agent/skill from the template + self-model (matches existing naming, tool conventions, invariants).
2. **Verify automatically** — the gate that replaces a human:
   - schema/syntax valid; typecheck/lint clean;
   - **skill unit tests pass** (run in the sandbox);
   - **eval harness passes** (Module D) — no regression to routing/behavior;
   - invariant check (`list_invariants()` assertions all hold);
   - sandbox **dry-run** of the new capability.
3. **Auto-repair:** any red feeds the exact failure back to the Architect, which regenerates — up to N attempts. *This loop is why it's "clean on first try" from your seat: the iterations happen autonomously in seconds, and you only ever see a converged result.*
4. **Apply** only if all green: register, **version**, regenerate the manifest. If it can't converge in N tries → it stops and surfaces the failure to you (failures escalate; successes don't).
5. **Instant rollback** by version if anything misbehaves later — a bad change is never destructive.

### F.3 — Autonomy dial (per risk class, configurable)
Not all changes carry the same risk, so autonomy is a policy, not a switch:

| Change class | Default mode | Behavior |
|---|---|---|
| New agent from template; new skill w/ passing tests+evals | **`auto`** | verify → apply, no human, you're notified after |
| Editing an existing agent's prompt/tools; routing changes | **`auto` or `notify`** | apply if evals pass; log a notice |
| Anything touching the **control plane, governance gate, sandbox, egress, or eval gate itself** | **`gate`** (locked) | proposal requires *you* — cannot be set to `auto` |

So day-to-day capability growth is fully autonomous; only changes to the system's own safety machinery require you.

### F.4 — The immutable floor (what makes autonomy safe & recoverable)
A self-modifying system that can disable its own safety is one bad generation from unrecoverable. So a small **constitution** is enforced in code and **cannot be changed by the system**, only by you editing it directly:
- It may **not** widen its own **egress allowlist**.
- It may **not** remove or weaken the **sandbox / file-scope enforcement**.
- It may **not** disable the **verification/eval gate** or the **auto-rollback**.
- It may **not** grant an agent broader **file-scope** than policy allows.
- The `gate`-locked classes in F.3 cannot be promoted to `auto` by the system.

Inside this floor, it extends itself freely. The floor is exactly what lets you *grant* high autonomy without it being able to autonomously erode its own guarantees — autonomy over **creating capabilities** is unrestricted; autonomy over **removing its own safety** is zero.

### F.5 — The dial as config (`config/autonomy.toml`)
The autonomy levels are a hot-reloadable config (provided in the starter). Defaults: `create_agent`/`create_skill`/`edit_agent_prompt`/`edit_routing` = **`auto`** (verify → apply, notify after); `edit_agent_tools`/`retire_*` = **`notify`**; `max_repair_attempts = 4`; verification requires tests + evals + invariants + sandbox dry-run with `eval_min_pass_rate = 1.0`.

**Loader rule (critical):** the `[modes.locked]` section is read **for display only**. The code enforces those classes as `denied`/`gate` regardless of the file's contents — so editing `autonomy.toml` to set, say, `weaken_sandbox = "auto"` has **no effect**. The floor lives in code; the TOML can only tune what's *above* it. To change the floor itself you edit the enforcing code directly (and that's `edit_autonomy_floor = "gate"` — it routes to you).

To make it more autonomous: raise `max_repair_attempts` and move `notify` classes to `auto`. To make it more cautious: drop classes to `gate`. The one thing the dial can't do is touch the floor.

**Tables:**
```sql
CREATE TABLE agents (
  id TEXT PRIMARY KEY, name TEXT UNIQUE, system_prompt_path TEXT, model TEXT,
  tool_allowlist TEXT, file_scope_policy TEXT, routing_keywords TEXT,
  version INTEGER NOT NULL DEFAULT 1,
  status TEXT NOT NULL DEFAULT 'active',     -- active | retired (auto mode skips 'proposed')
  created_at TEXT NOT NULL
);
CREATE TABLE skills (
  id TEXT PRIMARY KEY, name TEXT UNIQUE, path TEXT, schema_json TEXT,
  version INTEGER NOT NULL DEFAULT 1, tests_passing INTEGER NOT NULL DEFAULT 0,
  evals_passing INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'active',
  created_at TEXT NOT NULL
);
```

**✅ Acceptance:** you ask for a new specialist and a new skill; the system generates, verifies (tests + evals + invariants + dry-run), auto-repairs any failures, and **applies them without your approval** when green — then notifies you. A request that would touch the sandbox/egress/governance is refused autonomy and surfaces as a gated proposal. A skill whose tests can't be made to pass in N attempts is not applied — you get the failure, not a broken skill. Every change is versioned and one-command-revertible.

---

# Transition & cutover (side-by-side → clean, provably)

Run v1 (opencode) and v2 (this build) in parallel until v2 earns the switch. "Clean" is guaranteed by **isolation + a parity check + explicit gates + a reversible flip** — not by hoping.

1. **Isolation (no shared code).** v1 and v2 share **only data**, and only a **copy** of it. v2 reads a *copy* of `memory.jsonl` (imported once into `memory.db`); it never touches v1's files or processes. Neither can break the other.
2. **Parity harness.** Keep ~10–20 representative requests. Run each through **both** systems; compare outcomes (routing choice, files changed, decisions, pass/fail). This turns "is it ready?" into an objective number.
3. **Transition gates — all must be green before cutover:**
   - Memory migrated **and** `verify` passes (counts, no orphans, no dup names).
   - Every v1 agent is ported **or recreated via the Architect (Module F)**.
   - Every v1 skill is ported/recreated and its tests pass.
   - Parity harness ≥ your threshold (e.g. matches v1 on N/N core requests).
   - Rollback tested once.
4. **Reversible cutover.** v1 stays **frozen but runnable**. Cutover = point your entry (the JARVIS shell / voice) at the v2 gateway. If anything's wrong, point back at v1 — your migrated memory is a copy, so nothing is lost either way.
5. **Non-destructive by construction.** The importer only **reads** `memory.jsonl`; v2 writes only to `memory.db`/`state.db`. v1's data is never mutated.

**Result:** you migrate when the parity harness and gates say so, with a one-line rollback the whole time. The Architect (Module F) is what makes porting the v1 team fast — you can literally ask v2 to recreate each specialist rather than hand-copying configs.

---



| Milestone | Steps / Modules | You can… |
|---|---|---|
| **M1** | Part I Steps 0–5, 8 | run one sandboxed agent via the LLM API |
| **M2** | Part I Steps 6–7 | decompose → run concurrently → gate before execute (✅ test) |
| **M3** | Module A (+ Part I) | agents recall/record automatically; full governance loop |
| **M4** | Modules B + C | steer by voice; watch the live, scrubbable galaxy |
| **M5** | Module D | the system proposes its own eval-guarded, gated improvements |
| **M5+** | Module F | you ask for new agents/skills; system generates → self-verifies → applies autonomously; only its safety-floor changes need you |
| **M6** | Module E | secure, audited, observable |
| **Cutover** | Transition gates | parity passes → flip to v2, one-line rollback the whole time |

**Build to M2 first** — it's the proof. Everything after is additive, and each module has its own acceptance gate so you always know you're on solid ground.

---

# Appendix — foundation file map (provided starter)

```
jarvis/
  llm.py          # OpenAI-compatible BMW-gateway client (Step 2)
  db.py           # connect/init/log_status (Step 3)
  tools.py        # registry + sandboxed file/bash tools (Step 4)
  runtime.py      # TaskSpec/TaskResult + run_task loop (Step 5)
  scheduler.py    # DAG + leases + governance + retry (Step 6)
  decomposer.py   # request -> validated task DAG -> seed (Step 8)
  agents.py       # agent registry (agents are data; Module F) (Step 8)
  orchestrator.py # handle_request: the single entrypoint (+ memory loop) (Step 8/Module A)
  memory/
    store.py      # remember()/recall(), project binding, dedup, KNN (Module A) ✅
    embeddings.py # hash (offline) | local fastembed | bmw (Module A) ✅
schema/
  state.sql       # blackboard + task DAG + audit (Step 3)
  memory.sql      # entities/observations/relations (Module A) ✅
config/
  autonomy.toml   # Module F autonomy dial (defaults provided)
run.py            # CLI: `python run.py --go "build X"` (Step 8)
tests/
  test_smoke.py             # M2 foundation acceptance (Step 7) — green
  test_decompose.py         # request->DAG->run acceptance (Step 8) — green
  test_memory.py            # memory store acceptance (Module A) — green
  test_memory_integration.py# the learning loop (Module A) — green
```
Every file above runs as-is. All four test suites pass with no network (mock LLM + HashEngine). With live creds + `JARVIS_EMBED_ENGINE=local`, you get real semantic memory and the full request→DAG→run→learn loop. Start here, then build the remaining Part II modules against their acceptance gates.
