# Change Order 005 — Execution control plane (orchestration ≠ runtime)

**Audience:** an implementing coding agent or a human dev — but read the decision section first; this is an architecture change, not a patch.
**Repo:** `opencode-galaxy`. Touches a new `skills/control-plane/`, `skills/projects/projects.py` (schema), the agent `.md` configs (decomposition output), and `vite.config.ts` (`/__db` exposure).
**Branch:** `feat/control-plane`.
**Companions:** `CHANGE-ORDER-001` (blackboard/galaxy), `CHANGE-ORDER-004` (memory), `JARVIS-ORCHESTRATION-MODEL.md`, `MASTER-ROADMAP.md`.
**Grounded in:** `agents/request-orchestrator.md` ("Sequential fan-out only — the `task` tool cannot spawn custom agents in parallel"), `agents/worker.md` (failure handling: no retry, blackboard left active), `agents/secretary.md` (manual resume), `skills/projects/projects.py` (`specialist_queue` DDL).

---

## The decision (read this first)

**Finding:** the system's ceiling isn't a missing feature — it's that **opencode is a single-user terminal coding agent being used as a multi-agent orchestration server**, which it was not built to be. The evidence is in your own codebase: the blackboard, secretary, worker, specialist queue, handoff protocol, and approval gates are all things you *built on top of* opencode because opencode doesn't orchestrate. The sequential `task` tool isn't a bug to patch — it's a property of the runtime. You have already built an orchestrator outside opencode; it's just entangled with it.

**Direction:** separate the two layers.

- **Control plane (new, deterministic code):** owns the task DAG, scheduling, parallelism, task lifecycle (lease → heartbeat → timeout → retry → resume), conflict/file-lock management, and **enforces governance in code** (no execution before approval — a scheduler invariant, not an LLM's choice).
- **Execution runtime (pluggable):** runs exactly one agent task and returns. opencode becomes **one runtime option**, not the foundation. The control plane dispatches "run this task, here's its context" and doesn't care whether the runtime is an opencode session, a Claude Agent SDK loop, or a direct API agent loop.

**Everything valuable is preserved** — the blackboard, memory (CO-004), the handoff protocol, agent domain expertise, routing — all runtime-agnostic. That's the real IP. opencode just stops being load-bearing.

### Three paths (commit incrementally — do NOT rip-and-replace)

| Path | What | Risk | When |
|---|---|---|---|
| **A — Wrap** | Control plane dispatches to **multiple parallel opencode sessions**. opencode unchanged. Unlocks most parallelism + all resilience. | low | **Start here.** Proves the control plane with zero backend migration. |
| **B — Pluggable runtime** | Add Agent-SDK / direct-API runtimes; choose runtime *per task*. opencode kept where its skills earn it. | medium | After A is stable. Gradual, reversible. |
| **C — Replace** | Retire opencode where it's the bottleneck. | higher | Only if A+B prove it. Evidence-gated. |

This change order specifies **A in full** (executable now), then **B and C as contracts** (build when the time comes).

---

## Hard invariants

1. **Blackboard stays the source of truth.** The control plane reads/writes task state in `opencode.db`; a scheduler restart re-derives all state from it (resumability is free).
2. **Governance is enforced in code.** A task may not enter execution unless its blackboard is `executing` (approved). The worker gate becomes a scheduler precondition, not a prompt the LLM may ignore.
3. **No two concurrent tasks touch the same file.** Parallelism requires disjoint `file_scope`, enforced by `file_leases`. This is the one genuinely new hard problem — treat it as first-class.
4. **Conflicts and approvals still escalate to the user** (per `JARVIS-ORCHESTRATION-MODEL.md` §3). Concurrency does not auto-resolve disagreements.
5. **Local-first.** The control plane is a local daemon (sibling to the memory and voice daemons). No cloud dependency to schedule work.
6. **Backwards-safe.** Sequential execution remains valid as `concurrency=1`; the control plane must run correctly with a single lane before parallelism is enabled.

---

## Schema: turn the linear queue into a leased task DAG

Current `specialist_queue` (from `projects.py`): `id, blackboard_id, agent, status, queued_at, started_at, completed_at` — strictly linear, statuses `pending|active|done|skipped`.

Extend it into a dependency-aware, leased, retryable task table (idempotent `ALTER`s — see CO-004 migration note for the column-exists guard):

```sql
ALTER TABLE specialist_queue ADD COLUMN handoff_id        TEXT;     -- correlation key (CO-001 B-DB1)
ALTER TABLE specialist_queue ADD COLUMN depends_on        TEXT;     -- JSON array of task ids (DAG edges)
ALTER TABLE specialist_queue ADD COLUMN file_scope        TEXT;     -- JSON array of paths this task may touch
ALTER TABLE specialist_queue ADD COLUMN runtime           TEXT;     -- opencode | agent-sdk | api  (Phase B)
ALTER TABLE specialist_queue ADD COLUMN lease_owner       TEXT;     -- scheduler/worker id holding the task
ALTER TABLE specialist_queue ADD COLUMN lease_expires_at  TEXT;     -- heartbeat deadline → stale-reap
ALTER TABLE specialist_queue ADD COLUMN attempts          INTEGER NOT NULL DEFAULT 0;
ALTER TABLE specialist_queue ADD COLUMN max_attempts      INTEGER NOT NULL DEFAULT 3;
ALTER TABLE specialist_queue ADD COLUMN last_error        TEXT;
-- status vocabulary grows: pending | ready | active | done | skipped | failed | blocked | retrying

-- File-lease table — the concurrency safety mechanism (invariant 3)
CREATE TABLE IF NOT EXISTS file_leases (
  path          TEXT PRIMARY KEY,            -- absolute path
  task_id       TEXT NOT NULL,
  blackboard_id TEXT NOT NULL,
  acquired_at   TEXT NOT NULL,
  expires_at    TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_file_leases_task ON file_leases(task_id);
```

The DAG + `file_scope` are produced by the decomposition step (below). Everything else is the scheduler's.

---

## PHASE A — Control plane wrapping opencode (executable now)

### Task A1 — Decomposition emits a DAG, not a list
- **Goal:** the scheduler needs task dependencies and file scope to know what's parallelizable and safe.
- **Files:** `agents/request-orchestrator.md` + `agents/project-manager.md` (the decomposition/queue-build step), `skills/projects/projects.py` (`enqueue_specialists` → accept `depends_on` + `file_scope`).
- **Change:** when the PM/orchestrator decomposes a request, each specialist task records: `depends_on` (which task ids must finish first) and `file_scope` (which paths it will touch — from the HANDOFF v1 `scope.files_to_change`, which already exists). Independent tasks get empty `depends_on` and disjoint `file_scope` → parallelizable.
- **Acceptance:** a request that decomposes into two independent specialists yields two `specialist_queue` rows with no mutual dependency and disjoint `file_scope`; a dependent pair records the edge.
- **Commit:** `feat(orchestration): decomposition emits task DAG with file_scope`

### Task A2 — The scheduler daemon (ready-set + concurrency)
- **Files:** new `skills/control-plane/scheduler.py`.
- **Change:** a loop that:
  1. **Ready set:** tasks where `status='pending'` AND every `depends_on` task is `done`.
  2. **Lease check:** for each ready task, if any path in its `file_scope` is held in `file_leases` by another active task, leave it pending (defer). Else acquire leases (`expires_at = now + lease_ttl`), set `status='active'`, `lease_owner`, `lease_expires_at`.
  3. **Dispatch** up to a concurrency limit (`CONCURRENCY`, default 3) to the runtime (Phase A: `OpencodeRuntime`). Honors invariant 2: a task whose blackboard isn't `executing` cannot dispatch to the execute step.
  4. On completion → `done`, release leases, advance the DAG (newly-ready tasks dispatch next tick).
- **Acceptance:** two independent tasks run **concurrently** (wall-clock ≈ max, not sum); a dependent task waits for its predecessor; `CONCURRENCY=1` reproduces today's sequential behavior exactly.
- **Commit:** `feat(control-plane): DAG scheduler with concurrency + file-lease gating`

### Task A3 — Leases, heartbeats, stale-task reaper (resilience)
- **Files:** `skills/control-plane/scheduler.py`, `OpencodeRuntime`.
- **Change:** running tasks renew `lease_expires_at` on a heartbeat. A reaper pass finds `status='active'` tasks with an expired lease (crash/abandonment) and resets them to `pending` (releasing `file_leases`) or `failed` if `attempts >= max_attempts`. This is what fixes today's "an abandoned `active` row stays active forever."
- **Acceptance:** kill a running task mid-flight → within one lease TTL it is reaped, its file leases released, and it is retried or failed; no row stays `active` indefinitely.
- **Commit:** `feat(control-plane): leases + heartbeats + stale-task reaper`

### Task A4 — Retry with backoff + failure escalation
- **Files:** `skills/control-plane/scheduler.py`.
- **Change:** on task failure, increment `attempts`, record `last_error`; if `attempts < max_attempts` → `retrying` with exponential backoff, else `failed` → escalate (amber; surface to the user per the orchestration model). Distinguish transient (retry) from deterministic BLOCK (worker's "plan not executable" → straight to escalation, no retry).
- **Acceptance:** a transient failure retries and can succeed; a hard BLOCK escalates immediately without burning retries; exhausted retries escalate as `failed`.
- **Commit:** `feat(control-plane): retry-with-backoff and failure escalation`

### Task A5 — File-lease conflict model (the hard part, done right)
- **Files:** `skills/control-plane/scheduler.py`, ties into the existing `conflicts` table.
- **Change:** parallel tasks must hold disjoint `file_scope`. If decomposition can't guarantee disjoint scope (two tasks legitimately need the same file), the scheduler **serializes** those two (treat overlap as an implicit dependency) rather than risking a collision. If two completed proposals conflict semantically, record a `conflicts` row and escalate (existing model). Leases expire with the task lease so a crashed holder doesn't deadlock.
- **Acceptance:** two tasks with overlapping `file_scope` never run simultaneously (they serialize); a crash never leaves a permanent lock; a semantic conflict escalates rather than silently last-write-wins.
- **Commit:** `feat(control-plane): file-lease conflict model with safe serialization`

### Task A6 — `OpencodeRuntime` (dispatch to parallel sessions)
- **Files:** `skills/control-plane/runtimes/opencode_runtime.py`.
- **Change:** implement `run_task(task) -> result` by opening an **opencode session** (SDK/client), delivering the HANDOFF v1 envelope to the one assigned specialist, awaiting completion, and collecting the RESPONSE v1 / sections / result. Concurrency comes from **N sessions running at once** — sidestepping the `task`-tool single-agent limit entirely (opencode unchanged).
- **Acceptance:** the scheduler runs 3 specialists across 3 concurrent opencode sessions; each writes its sections to the blackboard; results are collected and the DAG advances.
- **Commit:** `feat(control-plane): OpencodeRuntime — parallel sessions as the executor`

### Task A7 — Expose control-plane state to the galaxy
- **Files:** `vite.config.ts` (`/__db`), `web/src/lib/db-reader.ts`.
- **Change:** surface the new `specialist_queue` columns (`depends_on`, `lease_*`, `attempts`, `status`) and `file_leases` so the galaxy can render the **DAG, parallel lanes, retries, and conflicts** (CO-001's lit-tethers become multiple concurrent lit tethers — finally accurate to real parallel execution).
- **Acceptance:** the galaxy shows concurrent tasks as concurrent lit tethers, dependency edges, and amber on `failed`/`blocked`.
- **Commit:** `feat(db): expose control-plane task DAG to the galaxy`

**Phase A Definition of Done:** independent specialists run concurrently; crashed/abandoned tasks self-heal; transient failures retry; file collisions are impossible; opencode is unchanged; `CONCURRENCY=1` is byte-for-byte today's behavior.

---

## PHASE B — Pluggable runtime (contract)

**`AgentRuntime` interface:**
```python
class AgentRuntime(Protocol):
    def run_task(self, task: TaskSpec) -> TaskResult: ...
# TaskSpec: agent, handoff(envelope), blackboard_id, file_scope, context_pack(from memory recall)
# TaskResult: status, sections[], result, memory_to_persist, error?
```
- Implement `AgentSdkRuntime` (Claude Agent SDK loop) and `ApiRuntime` (direct Anthropic API agent loop with tools) alongside `OpencodeRuntime`.
- Select per task via the `runtime` column / a policy (e.g. "pure LLM+tools → api; needs opencode skill X → opencode").
- **Acceptance:** the same task runs identically through any runtime; switching a task's runtime is a column/policy change, no orchestration change.
- **Commits:** `feat(control-plane): AgentRuntime interface` · `feat(control-plane): agent-sdk + api runtimes`

---

## PHASE C — Selective opencode retirement (evidence-gated)

Only after A+B run in production with metrics. Move task classes off opencode where it's the measured bottleneck; keep it where its skills/tooling ecosystem earns its place. The control plane makes this mechanical — change the runtime policy, not the orchestration. **Do not start C without data from A+B.**

---

## What this fixes (recap, all verified gaps today)

- **Parallelism:** latency becomes the critical path, not the sum. Today's `task` tool serializes even independent work; dependency tracking barely exists (`depends_on` only at blackboard level; `check_dependencies` referenced but not implemented in `projects.py`).
- **Resilience:** no stale-task detection, no retry, manual resume, no partial-failure handling today → the scheduler's leases/heartbeats/retries/blackboard-state provide all four.
- **Enforced governance:** gates/sequencing stop being prompt-honored and become scheduler invariants.
- **Backend freedom:** opencode becomes swappable per task instead of foundational.

## Suggested PR breakdown

| PR | Contains | Risk |
|---|---|---|
| PR1 | A1 (DAG decomposition) + schema | low — additive |
| PR2 | A2 + A6 (scheduler + OpencodeRuntime, `CONCURRENCY=1`) | medium — prove parity first |
| PR3 | A3 + A4 (leases/reaper + retry) | medium — resilience |
| PR4 | A5 (file-lease conflict model) then raise `CONCURRENCY` | medium — turn on parallelism |
| PR5 | A7 (galaxy exposure) | low |
| PR6 | B (pluggable runtimes) | higher — optional |

Land PR1–PR5 and you have a parallel, self-healing executor with opencode unchanged and the galaxy showing it live. B/C are the backend-freedom headroom, taken on evidence.
