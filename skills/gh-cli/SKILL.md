# gh CLI Skill

Use this skill when the user asks about GitHub repositories, pull requests, issues, branches, workflows, or any other GitHub operation against the BMW GitHub Enterprise instance.

## Environment

- **Primary host:** `atc-github.azure.cloud.bmw` (GHE 3.19.4) — authenticated as `qte2362`
- **Secondary host:** `bmw.ghe.com` — authenticated as `Bruce-Jensen`
- **CLI:** `/opt/homebrew/bin/gh` v2.90.0
- **Auth:** stored in keyring (no PAT needed in commands)

## Targeting the GHE Host

Two patterns — use the right one per command:

### 1. `GH_HOST` env var (works for ALL subcommands)
```bash
GH_HOST=atc-github.azure.cloud.bmw gh <any-command>
```

### 2. `--hostname` flag (only works with `gh api` and `gh auth`)
```bash
gh api /user --hostname atc-github.azure.cloud.bmw
gh auth status --hostname atc-github.azure.cloud.bmw
```

**Always use `GH_HOST=...` as the default pattern** — it works universally.

## Common Patterns

### Repository operations
```bash
GH_HOST=atc-github.azure.cloud.bmw gh repo view <owner>/<repo>
GH_HOST=atc-github.azure.cloud.bmw gh repo clone <owner>/<repo>
GH_HOST=atc-github.azure.cloud.bmw gh repo list <org> --limit 50
```

### Pull requests
```bash
GH_HOST=atc-github.azure.cloud.bmw gh pr list --repo <owner>/<repo>
GH_HOST=atc-github.azure.cloud.bmw gh pr view <number> --repo <owner>/<repo>
GH_HOST=atc-github.azure.cloud.bmw gh pr create --repo <owner>/<repo> \
  --title "..." --body "..." --base main --head <branch>
GH_HOST=atc-github.azure.cloud.bmw gh pr checks <number> --repo <owner>/<repo>
```

### Issues
```bash
GH_HOST=atc-github.azure.cloud.bmw gh issue list --repo <owner>/<repo>
GH_HOST=atc-github.azure.cloud.bmw gh issue create --repo <owner>/<repo> \
  --title "..." --body "..."
```

### Raw API calls
```bash
# GET (path relative to /api/v3 on GHE)
gh api /user --hostname atc-github.azure.cloud.bmw
gh api /repos/<owner>/<repo>/pulls --hostname atc-github.azure.cloud.bmw

# POST with form fields
gh api --method POST /repos/<owner>/<repo>/issues \
  --hostname atc-github.azure.cloud.bmw \
  -f title="Bug: ..." -f body="..."

# GraphQL
gh api graphql --hostname atc-github.azure.cloud.bmw \
  -f query='{ viewer { login } }'
```

### Workflows / Actions
```bash
GH_HOST=atc-github.azure.cloud.bmw gh workflow list --repo <owner>/<repo>
GH_HOST=atc-github.azure.cloud.bmw gh workflow run <workflow-id> --repo <owner>/<repo>
GH_HOST=atc-github.azure.cloud.bmw gh run view <run-id> --repo <owner>/<repo> --log
```

### Search
```bash
GH_HOST=atc-github.azure.cloud.bmw gh search repos <query>
GH_HOST=atc-github.azure.cloud.bmw gh search code <query>
```

## Output Formatting

Use `--json` with `--jq` for machine-readable output:

```bash
GH_HOST=atc-github.azure.cloud.bmw gh pr list --repo <owner>/<repo> \
  --json number,title,state,url \
  --jq '.[] | "\(.number) \(.state) \(.title)"'
```

## Error Handling

| Error | Cause | Fix |
|---|---|---|
| `gh` uses github.com instead of GHE | Forgot `GH_HOST` env var | Prefix with `GH_HOST=atc-github.azure.cloud.bmw` |
| `unknown flag: --hostname` | Using `--hostname` on a non-api subcommand | Switch to `GH_HOST=...` prefix |
| `HTTP 401` | Token expired | Run `gh auth login --hostname atc-github.azure.cloud.bmw` |
| `HTTP 404` | Wrong repo path or private repo without access | Verify `<owner>/<repo>` |
| `HTTP 422` | Invalid request body | Check `-f` field names against the API docs |

## When to Use `gh api` vs Dedicated Commands

- Prefer dedicated commands (`gh pr`, `gh issue`, `gh repo`) — they handle pagination and formatting automatically.
- Use `gh api` for endpoints not covered by dedicated commands (e.g. branch protection rules, webhooks, team membership, deploy keys).
