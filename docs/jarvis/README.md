# JARVIS Docs Index

These docs are the working guide for building the JARVIS / Galaxy experience.

## Reading order

If you are an implementing agent, read in this order:

1. `CHANGE-ORDER-001.md`
2. `BUILD-GAP-ANALYSIS.md`
3. `JARVIS-ORCHESTRATION-MODEL.md`
4. `GALAXY-VISUAL-LANGUAGE.md`
5. `CHANGE-ORDER-002-VOICE.md`
6. `CHANGE-ORDER-004-MEMORY.md`
7. `JARVIS-ROADMAP-REVIEW 2.md`

## Why this order

- **Change order first:** gives the concrete implementation plan.
- **Gap analysis second:** explains what is already built vs. still missing.
- **Orchestration model third:** locks the behavioral rules and source of truth.
- **Visual language fourth:** preserves the intended Galaxy UI semantics.
- **Roadmap review last:** useful critique and validation, but not the primary build spec.

## Dependency map

### `CHANGE-ORDER-001.md`
Depends on:
- `BUILD-GAP-ANALYSIS.md` for rationale and confirmed gaps
- `JARVIS-ORCHESTRATION-MODEL.md` for coordination rules
- `GALAXY-VISUAL-LANGUAGE.md` for visual behavior

Use it for:
- implementation sequencing
- exact file targets
- acceptance criteria

### `BUILD-GAP-ANALYSIS.md`
Depends on:
- repo state
- `JARVIS-ORCHESTRATION-MODEL.md`
- `GALAXY-VISUAL-LANGUAGE.md`

Use it for:
- prioritization
- blocker detection
- deciding what is already done

### `JARVIS-ORCHESTRATION-MODEL.md`
Depends on:
- project intent
- blackboard / coordinator semantics

Use it for:
- agent behavior
- source-of-truth rules
- approval and escalation logic

### `GALAXY-VISUAL-LANGUAGE.md`
Depends on:
- orchestration model
- live blackboard state

Use it for:
- visual semantics
- active vs dormant rules
- timeline and conflict rendering

### `JARVIS-ROADMAP-REVIEW 2.md`
Depends on:
- roadmap/spec files
- design references

Use it for:
- critique
- corrections
- implementation guidance

### `CHANGE-ORDER-002-VOICE.md`
Depends on:
- `JARVIS-ORCHESTRATION-MODEL.md` for conversational intents and authority rules
- `GALAXY-VISUAL-LANGUAGE.md` for query/highlight behavior
- `BUILD-GAP-ANALYSIS.md` for the current gap map and sequencing

Use it for:
- voice-specific implementation steps
- intent handling
- narration/mute/interrupt behavior

### `CHANGE-ORDER-004-MEMORY.md`
Depends on:
- `CHANGE-ORDER-001.md` for blackboard / opencode.db context
- `JARVIS-ORCHESTRATION-MODEL.md` for coordination and memory usage rules
- `BUILD-GAP-ANALYSIS.md` for the current system gaps and order of work

Use it for:
- memory architecture
- persistence and retrieval changes
- schema / daemon / index work

## Builder guidance

If you are building the system later:

1. Treat `CHANGE-ORDER-001.md` as the execution contract.
2. Validate each claim in `BUILD-GAP-ANALYSIS.md` against the repo before editing.
3. Do not violate the orchestration rules in `JARVIS-ORCHESTRATION-MODEL.md`.
4. Preserve the active/dormant visual grammar from `GALAXY-VISUAL-LANGUAGE.md`.
5. Use `CHANGE-ORDER-002-VOICE.md` for voice work, but keep it subordinate to the orchestration model.
6. Use `CHANGE-ORDER-004-MEMORY.md` for memory work, but keep it aligned with blackboard and orchestration rules.
7. Use `JARVIS-ROADMAP-REVIEW 2.md` as a quality check, not as the primary spec.

## Notes

- The five all-caps docs were moved into this folder for easier navigation.
- Keep future JARVIS docs here so the implementation trail stays together.
