---
description: "Apply PR review comments — acknowledgement flow (👍 or self-authored) and correction rerun flow."
---

Apply review comments from a GitHub PR. Pass the PR number or full URL as the argument.

Usage: `/apply-pr-suggestions $ARGUMENTS`

Where `$ARGUMENTS` is a PR number (e.g. `42`) or full URL (e.g. `https://atc-github.azure.cloud.bmw/owner/repo/pull/42`).

Load the `gh-cli` skill, then work through these phases:

**Phase 1 — Determine repository context**
Parse `$ARGUMENTS`. If a full URL, extract hostname/owner/repo/PR number directly. If a number only, derive hostname/owner/repo from `git remote get-url origin`.

**Phase 2 — Verify auth and fetch PR metadata**
Run `gh auth status` and `gh repo view owner/repo --json name`. Stop and report if either fails.

**Phase 3 — Fetch and categorise review threads**
Use `gh api` to fetch all review threads for the PR. Categorise each thread:
- **Acknowledgement flow:** thread is self-authored by the PR author OR has a 👍 reaction from the PR author → apply the change
- **Correction rerun flow:** a previously-applied thread was manually unresolved with a correcting reply → re-read the conversation, infer the desired outcome, fix or resolve accordingly
- **Skip:** all other threads (unreviewed, declined)

**Phase 4 — Apply changes**
For each applicable thread: check out the PR branch if not already on it, apply the suggested change, stage the file.

**Phase 5 — Commit and report**
Commit all applied changes with message `fix: apply PR #<n> review suggestions`. Report a summary of what was applied, skipped, and any threads that need manual attention.
