# Context Handoff Protocol (HANDOFF v1 / RESPONSE v1)

This repo runs a **multi-agent** OpenCode system. The most common failure mode is **lost or ambiguous context** (wrong working directory, wrong files, wrong branch), especially when:

- The orchestrator sends multiple short messages instead of one complete handoff.
- Agents assume the shell CWD instead of using an explicit **repo root**.
- Specialists return prose instead of a worker-executable plan.

This document defines a **standard, enforceable envelope** for every:

1) orchestrator → specialist message
2) specialist → worker (or specialist → orchestrator) response

---

## Design principles

1. **One message = one complete handoff.** No “thin” delegations.
2. **Absolute paths only.** Never rely on implicit CWD.
3. **Context echo.** Every specialist must repeat the source-of-truth `repo_root` + `branch`.
4. **Worker-executable output.** Specialists produce diffs or numbered steps (not vague advice).
5. **Addenda are explicit.** If more context is needed, send an `ADDENDUM` referencing the same `handoff_id`.

---

## HANDOFF v1 (orchestrator → specialist)

Send **exactly one** message that contains this block.

```text
[HANDOFF v1]
handoff_id: <REQUIRED unique id; suggested: <project>-<yyyymmdd>-<sequence> e.g. apex-fixer-20260626-001>
project: <project-name>
repo_root: <absolute path to repo root>
workdir: <absolute path; usually same as repo_root>
git:
  branch: <current branch>
  base: <optional: main/master>
  remote: <optional>
scope:
  files_to_inspect:
    - <absolute or repo-relative paths>
  files_to_change:
    - <absolute or repo-relative paths>
  out_of_scope:
    - <things you must not touch>
prior_decisions_in_force:
  - <bullet list>
task:
  description: |
    <exact task description>
  acceptance_criteria:
    - <measurable outcomes>
deliverable:
  response_format: RESPONSE v1
  expected_artifacts:
    - <e.g. “unified diff”, “worker steps”, “risk notes”>
constraints:
  - Use absolute paths; do not assume CWD.
  - If you propose bash commands, include explicit workdir.
  - If context is missing, request a re-handoff (do not guess).
```

**`handoff_id` is REQUIRED.** It is a unique identifier for end-to-end traceability across:
- orchestrator → specialist handoffs
- addenda (`ADDENDUM`) to an existing handoff
- specialist responses (`RESPONSE v1`)

Format is flexible, but it **must be unique per task delegation**. Recommended format:
`<project>-<yyyymmdd>-<sequence>` (example: `apex-fixer-20260626-001`).

### Example (apex-fixer)

```text
[HANDOFF v1]
handoff_id: apex-fixer-20260626-001
project: apex-fixer
repo_root: /Users/QTE2362/ECC-APPS/mn-apex
workdir: /Users/QTE2362/ECC-APPS/mn-apex
git:
  branch: feat/apex-fixer-ui
  base: main
scope:
  files_to_inspect:
    - web/index.html
    - web/app.js
    - web/setup.html
  files_to_change:
    - web/app.js
  out_of_scope:
    - backend/
prior_decisions_in_force:
  - Keep SPA tab architecture; no framework migration.
task:
  description: |
    Fix tab-state persistence bug where Settings resets after refresh.
  acceptance_criteria:
    - Refresh preserves last active tab
    - No regression in setup wizard
deliverable:
  response_format: RESPONSE v1
  expected_artifacts:
    - Minimal diff for worker to apply
    - Test / repro steps
constraints:
  - Use absolute paths; do not assume CWD.
  - If you propose bash commands, include explicit workdir.
  - If context is missing, request a re-handoff (do not guess).
```

---

## RESPONSE v1 (specialist → orchestrator / specialist → worker via blackboard)

Every specialist response **must** start with this block.

```text
[RESPONSE v1]
handoff_id: <REQUIRED; must exactly match HANDOFF v1>
agent: <your agent name>
context_echo:
  project: <project>
  repo_root: <absolute path>
  git.branch: <branch>
summary:
  - <1–5 bullets of what you found>
files:
  to_change:
    - <absolute or repo-relative paths>
  referenced:
    - <paths you inspected>
worker_plan:
  method: diff | steps
  diff: |
    <unified diff blocks, ready to apply>
  steps:
    1) <exact instruction with absolute paths>
    2) <...>
validation:
  - <exact commands + workdir>
risks:
  - <what might break>
blockers:
  - <questions / missing info>
memory_to_persist:
  worked:
    - <what worked>
  avoided:
    - <pitfalls>
  patterns:
    - <reusable pattern>
```

### Notes

- If you cannot identify `repo_root` and `branch` with high confidence, **stop and request a corrected HANDOFF v1**.
- `worker_plan.method: diff` is preferred.
