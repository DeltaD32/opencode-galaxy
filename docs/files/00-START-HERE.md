# 00 — START HERE (project index & read order)

This is a **fresh, greenfield build** of JARVIS — a clean codebase that does **not** use opencode. A few docs in this folder are from the **old (v1) opencode system**; this index tells you exactly which files belong to the new build, which are reference, which are dead, and the order to use them.

> **If you read only one file:** `JARVIS-BUILD-MANUAL.md`. It's the step-by-step build. Everything else is either the code it builds, or reference it points to.

---

## The 1-minute orientation

- **NEW (the fresh build):** the `JARVIS-BUILD-*` docs + the `jarvis-starter/` code. This is what you build.
- **REFERENCE (read on demand):** the orchestration model, the galaxy visual language, and the voice/memory change orders — the manual links to these for depth.
- **OLD (v1 / opencode):** the master roadmap and the gap analysis. **Ignore these for the fresh build** — they're about improving the *existing* opencode repo. Keep them only if you also maintain v1.
- **DEAD (superseded):** `CHANGE-ORDER-003` and any loose single `.py` previews. Don't use them.

---

## A. BUILD THESE — the fresh build, in order

| # | File / folder | What it is | Status |
|---|---|---|---|
| 1 | **`JARVIS-BUILD-MANUAL.md`** | The step-by-step DIY manual (Do → Code → Run → Verify). **Your spine.** | mixed (see below) |
| 2 | **`jarvis-starter/`** | The verified, runnable code you start from. Run its 4 test suites first. | ✅ **BUILT** |
| 3 | **`JARVIS-BUILD-GUIDE.md`** | The architecture & "why" behind the manual. Read once up front. | reference |

**The manual's parts, and their real status:**

| Part / Module | What | Status |
|---|---|---|
| Part I (Steps 0–8) — foundation | LLM client, state DB, sandboxed tools, agent loop, **control-plane scheduler** (DAG/leases/governance/retry), decomposer, orchestrator | ✅ **BUILT & TESTED** (in `jarvis-starter/`) |
| Module A — Memory | `remember`/`recall`, project binding, dedup, vectors, the **learning loop** | ✅ **BUILT & TESTED** |
| Module B — Voice | streaming TTS, STT, wake word, barge-in | 📋 **SPEC** → see CO-002 |
| Module C — Galaxy + JARVIS shell | gateway API + React/Three.js live, scrubbable view | 📋 **SPEC** → see Galaxy Visual Language + CO-001 |
| Module D — Self-enhancement | routing cache, reflection loop, eval harness | 📋 **SPEC** (build-guide §4) |
| Module F — Self-extension | autonomous agent/skill creation; `config/autonomy.toml` is ✅ provided | 📋 **SPEC** (config built) |
| Module E — Security hardening | egress allowlist, sandbox, secrets, audit | 📋 **SPEC** |
| Transition & cutover | side-by-side v1↔v2 with parity gates | 📋 **SPEC** |

**So today:** the foundation + memory are **running code**; voice, galaxy, self-enhancement, self-extension, and security are **blueprints** with acceptance gates, ready to build next.

---

## B. REFERENCE — read when a module needs depth

The manual links to these. They're **runtime-agnostic** (they describe decisions/contracts, not opencode), so they apply to the fresh build.

| File | Use it for | Status |
|---|---|---|
| **`JARVIS-ORCHESTRATION-MODEL.md`** | The governance loop (decompose→propose→review→gate→execute), roles, conflict/approval rules | reference |
| **`GALAXY-VISUAL-LANGUAGE.md`** | The galaxy's visual grammar — the reference for **Module C** | reference |
| **`CHANGE-ORDER-002-VOICE.md`** | Full voice-loop spec — the reference for **Module B** | reference (spec) |
| **`CHANGE-ORDER-004-MEMORY.md`** | Memory deep-dive — the **remaining** memory work (gardener, `jsonl→sqlite` importer, libSQL sync) beyond the built core | reference (spec) |

**Deeper reference (concepts transfer, but written against v1 — use the ideas, ignore the opencode-specific bits):**

| File | Use it for | Caveat |
|---|---|---|
| `CHANGE-ORDER-005-EXECUTION.md` | The reasoning behind the DAG/lease/conflict model | The control-plane **core is already built** in the starter. The A/B/C "wrap opencode" path is **v1-only** — skip it for greenfield. |
| `CHANGE-ORDER-001.md` | Blackboard→graph data shapes for the galaxy | The specific code diffs target the **v1 React app**. For the fresh build, follow Galaxy Visual Language + Module C instead. |

---

## C. OLD (v1 / opencode) — NOT for the fresh build

Only relevant if you also keep improving the **existing opencode repo**. Quarantined so they're not confused with the new build.

| File | What | Use? |
|---|---|---|
| `MASTER-ROADMAP.md` | Sequences the change orders against the **v1 opencode repo** | v1 only — for greenfield, the manual's Milestones are your roadmap |
| `BUILD-GAP-ANALYSIS.md` | Current-vs-vision audit of the **existing opencode codebase** | v1 only |

---

## D. DEAD — ignore / delete

| Item | Why |
|---|---|
| `CHANGE-ORDER-003` (per-project memory) | **Superseded** — folded entirely into `CHANGE-ORDER-004` |
| Loose single `.py` files shown individually | Just previews of files now inside `jarvis-starter/` — reference the folder, not the loose copies |

---

## E. The exact path to follow (fresh build)

1. **Read** `JARVIS-BUILD-GUIDE.md` once (architecture).
2. **Open** `jarvis-starter/`, run all four test suites (no creds needed). Confirm green.
3. **Work** `JARVIS-BUILD-MANUAL.md` top to bottom:
   - Part I + Module A are already code in the starter — read them to understand, run the tests, then add your real credentials (Step 1) and live agent prompts.
   - Build **Module B (voice)** → reference `CHANGE-ORDER-002-VOICE.md`.
   - Build **Module C (galaxy)** → reference `GALAXY-VISUAL-LANGUAGE.md`.
   - Build **Modules D, F, E** → build-guide §4 + the autonomy config.
4. **Each module has an acceptance test** — don't advance until it passes.
5. **Migrate v1 knowledge** (optional) with the `jsonl→sqlite` importer (CO-004 M4).
6. **Cut over** from v1 using the Transition gates (manual) when parity passes.

---

## F. Optional: a clean naming scheme

If you want the folder self-ordering, rename with number prefixes (read-order encoded in the name):

```
00-START-HERE.md                  (this file)
10-build-manual.md                ← JARVIS-BUILD-MANUAL.md
11-build-guide.md                 ← JARVIS-BUILD-GUIDE.md
20-orchestration-model.md         ← JARVIS-ORCHESTRATION-MODEL.md
21-galaxy-visual-language.md      ← GALAXY-VISUAL-LANGUAGE.md
31-voice.md                       ← CHANGE-ORDER-002-VOICE.md
32-memory.md                      ← CHANGE-ORDER-004-MEMORY.md
33-execution-reference.md         ← CHANGE-ORDER-005-EXECUTION.md   (concepts only)
34-galaxy-data-reference.md       ← CHANGE-ORDER-001.md             (concepts only)
90-v1-master-roadmap.md           ← MASTER-ROADMAP.md               (v1 only)
91-v1-gap-analysis.md             ← BUILD-GAP-ANALYSIS.md           (v1 only)
starter/                          ← jarvis-starter/
# delete: CHANGE-ORDER-003, loose .py previews
```
The `00/10/20…` prefixes give read order at a glance; `90/91` quarantines the v1 docs; deleting the dead two removes the confusion. This index stays accurate whether or not you rename — the descriptions are what matter.

---

### TL;DR
**Build:** the manual + the starter (foundation & memory already coded). **Reference:** orchestration model, galaxy visual language, voice & memory change orders. **Ignore for greenfield:** master roadmap, gap analysis (v1), change-order-003 (dead), loose .py previews (in starter).
