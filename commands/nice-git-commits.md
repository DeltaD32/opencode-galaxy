---
description: "Reorganise all uncommitted changes into clean, atomic, conventionally-messaged git commits."
---

Load the `git-commit-reorganization` skill and use it to:

1. Analyse all uncommitted changes (staged and unstaged) in the current repository.
2. Group related changes into logical, atomic units.
3. Propose a commit plan with Conventional Commits messages (`feat:`, `fix:`, `chore:`, `docs:`, etc.).
4. Present the plan to the user for quick confirmation.
5. Execute the commits after confirmation.

Each commit must be self-contained. Do not push — just commit.
