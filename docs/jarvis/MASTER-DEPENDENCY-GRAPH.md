# JARVIS Master Dependency Graph

This is the canonical dependency map for the JARVIS docs set.

## Core chain

```text
CHANGE-ORDER-001.md
├── BUILD-GAP-ANALYSIS.md
├── JARVIS-ORCHESTRATION-MODEL.md
└── GALAXY-VISUAL-LANGUAGE.md
```

## Voice branch

```text
CHANGE-ORDER-002-VOICE.md
├── JARVIS-ORCHESTRATION-MODEL.md
├── GALAXY-VISUAL-LANGUAGE.md
└── BUILD-GAP-ANALYSIS.md
```

## Memory branch

```text
CHANGE-ORDER-004-MEMORY.md
├── CHANGE-ORDER-001.md
├── JARVIS-ORCHESTRATION-MODEL.md
└── BUILD-GAP-ANALYSIS.md
```

## Supporting docs

```text
JARVIS-ROADMAP-REVIEW 2.md
└── critique / validation layer

README.md
└── navigation + builder guidance
```

## Build order

1. `CHANGE-ORDER-001.md`
2. `BUILD-GAP-ANALYSIS.md`
3. `JARVIS-ORCHESTRATION-MODEL.md`
4. `GALAXY-VISUAL-LANGUAGE.md`
5. `CHANGE-ORDER-002-VOICE.md`
6. `CHANGE-ORDER-004-MEMORY.md`
7. `JARVIS-ROADMAP-REVIEW 2.md`

## Notes for implementing agents

- Treat the change-order docs as execution contracts.
- Treat the orchestration model as the authority for behavior.
- Treat the roadmap review as a critique layer, not a source of truth.
- Always verify runtime claims against the repo before coding.
