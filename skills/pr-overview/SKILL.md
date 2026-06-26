---
name: pr-overview
description: Get a comprehensive overview of pull request status including CI checks, review status, dependencies, reviewer assignments, and update timestamps. Perfect for daily PR triage and dependency chain tracking.
license: Proprietary
compatibility: Requires gh CLI (authenticated), git, uv (for running Python scripts), and GitHub API access
metadata:
  author: Matthias Bilger <matthias.bilger@bmw.de>
  version: "1.0.0"
  tags:
    - github
    - pr
    - pull-request
    - status
    - ci
    - review
    - dependency
    - triage
    - workflow
---

# pr-overview

## Goal

Provide a comprehensive overview of pull request status in a repository, including CI status, review state, dependencies (via `Depends-On:` tags), reviewer assignments, and time since last update. Helps teams quickly assess PR readiness and dependency chains.

## When to use

- User asks for "PR status", "pull request overview", or "check my PRs"
- Daily PR triage sessions
- Checking if dependent PRs are ready to merge
- Understanding review bottlenecks
- Monitoring CI health across open PRs

## Inputs

- Repository path (defaults to current directory)
- GitHub user filter (defaults to authenticated user)
- Optional PR number filter (check specific PR)
- Optional state filter: `open`, `closed`, `all` (defaults to `open`)

## Outputs

- Formatted table showing for each PR:

  - PR number and title
  - CI status (✅ passing, ❌ failing, ⏳ pending, ⚪ no checks)
  - Review status (✅ approved, 📝 changes requested, 💬 comments, ⏳ pending)
  - Days since last update
  - Reviewer assignments (✅ assigned, ⚠️ none)
  - Resolved/unresolved review threads
  - Dependency status (if `Depends-On:` found in description)

- Dependency chain summary:
  - List of dependent PRs with their merge readiness
  - Hint if all dependencies are ready to merge
  - Warning if any blocking PRs exist

## Agent instructions

**When the user requests PR overview information, run the appropriate command directly using the terminal.** Do not just explain what command to run—execute it and present the results.

Choose the appropriate command based on the user's request:

- For "all open PRs" or "complete picture": use `--all` flag
- For "my PRs" or unspecified: use default (current user)
- For specific user: use `--user <username>`
- For specific PR: use `--pr <number>`
- For closed PRs: use `--state all`

Always run from the repository root directory.

## Steps

### CLI invocation (preferred — runs in terminal, output rendered with rich)

```bash
# My open PRs
~/.opencode/plugins/clipjoint/.venv/bin/python3 \
  ~/.opencode/skills/pr-overview/scripts/pr_overview.py

# All open PRs in repo
~/.opencode/plugins/clipjoint/.venv/bin/python3 \
  ~/.opencode/skills/pr-overview/scripts/pr_overview.py --all

# Specific user
~/.opencode/plugins/clipjoint/.venv/bin/python3 \
  ~/.opencode/skills/pr-overview/scripts/pr_overview.py --user <username>

# Specific PR
~/.opencode/plugins/clipjoint/.venv/bin/python3 \
  ~/.opencode/skills/pr-overview/scripts/pr_overview.py --pr <number>

# Include closed PRs
~/.opencode/plugins/clipjoint/.venv/bin/python3 \
  ~/.opencode/skills/pr-overview/scripts/pr_overview.py --state all
```

### Programmatic usage (when you need PR data as structured objects)

```python
import sys, pathlib
sys.path.insert(0, str(pathlib.Path.home() / ".opencode/skills/pr-overview/scripts"))
from pr_overview import PROverview

overview = PROverview(repo_path=".")
prs = overview.get_prs()          # returns list of PRInfo dataclasses
overview.display_overview(prs)    # renders the rich table to terminal
```

## Example output

```plain
Pull Request Overview for DX/ttt-skills

Your open PRs (2):
┌────┬─────────────────────────┬───────────┬──────────────┬─────────────┬──────────────┬──────────┐
│ PR │ Title                   │ CI Status │ Review       │ Updated     │ Reviewers    │ Threads  │
├────┼─────────────────────────┼───────────┼──────────────┼─────────────┼──────────────┼──────────┤
│ 42 │ Add density skill       │ ✅ Pass   │ ✅ Approved  │ 2 days ago  │ ✅ alice     │ 3/3 ✅   │
│ 43 │ Fix git reorganization  │ ⏳ Pending│ 📝 Changes   │ 1 day ago   │ ✅ bob       │ 1/2 ✅   │
└────┴─────────────────────────┴───────────┴──────────────┴─────────────┴──────────────┴──────────┘

Dependencies:
  PR #43 → Depends on: #42 (✅ ready to merge)

Summary:
  • 1 PR ready to merge
  • 1 PR needs changes
  • All dependencies resolved ✅
```

## Implementation details

The Python script:

1. Uses `gh` CLI to fetch PR data with GraphQL queries
2. Parses PR descriptions for `Depends-On: #<number>` patterns
3. Fetches detailed status for each PR:
   - CI check runs and conclusions
   - Review decisions (approved, changes_requested, commented)
   - Reviewer assignments
   - Review thread counts (resolved/total)
   - Last update timestamp
4. Recursively checks dependency status
5. Formats output with clear status indicators
6. Provides actionable summary

## Error handling

- Missing `gh` CLI → Displays an error and exits
- Not in a git repository → Prompts for repository path
- No PRs found → Displays friendly message

## Tips

- Run daily as part of standup routine
- Use `--all` to identify stale PRs across the team
- Check dependency chains before merging to avoid breaking changes
- Filter by `--state all` to review recently closed PRs

## Related skills

- <skill>resolve-pr-comments</skill>: Address review feedback automatically
- <skill>pr-creation</skill>: Create well-structured PRs with proper metadata
