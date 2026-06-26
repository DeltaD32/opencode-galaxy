---
description: "Commit changes atomically, push to a feature branch, and open a pull request — all in one step."
---

Take all current (uncommitted or loosely committed) changes in the repository and turn them into a clean, reviewed pull request. Work through the following steps in order:

**Step 1 — Inspect state**
Run `git status`, `git diff --stat`, `git log --oneline -5`, and `gh auth status`. Identify changed files, current branch, and confirm `gh` is authenticated.

**Step 2 — Ensure we are on a feature branch**
If on `main` or `master`, derive a short kebab-cased branch name from the nature of the changes and run `git checkout -b <branch-name>`. If already on a feature branch, continue on it.

**Step 3 — Commit atomically**
Load the `git-commit-reorganization` skill. Analyse all uncommitted changes, group them into logical units, propose a commit plan with Conventional Commits messages (`feat:`, `fix:`, `chore:`, `docs:`), confirm with the user, then execute.

**Step 4 — Validate pre-commit hooks**
Run `pre-commit run --from-ref HEAD~<n> --to-ref HEAD` (where n = number of commits just created). If not installed, skip and note it. If a hook fails, apply auto-fixes and amend/fixup the affected commit, then re-run until clean.

**Step 5 — Push**
Run `git push --set-upstream origin <branch-name>`. If rejected due to diverged history, report the error and stop.

**Step 6 — Open the PR**
Load the `pr-creation` skill. Construct `gh pr create --title "<type>: <summary>" --body "<description>" --base main`. The body must include: what changed and why (2–4 sentences), a bullet list of commits, any testing steps, and a ticket reference if inferable from the branch name or commits. Fill `.github/pull_request_template.md` if it exists.

**Step 7 — Report**
Print:
```
✅ PR created successfully
Branch : <branch-name>
PR URL : <url>
Title  : <title>
Commits: <n> commit(s) pushed
```
