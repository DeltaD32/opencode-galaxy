# OpenCode Global Agent Instructions

> **Quick-ramp for agents working on this config repo** — read this section first,
> then the enforcing Rules below.

## Working in this Repo

**What this repo is:** `~/.config/opencode` — the entire OpenCode configuration for BMW.
Changes here affect every OpenCode session immediately. The repo is at
`https://atc-github.azure.cloud.bmw/qte2362/opencode-config.git`.

### Layout — what lives where

| Path | What it is |
|---|---|
| `opencode.json` | Main config: models, providers, MCPs, default agent. **Never edit MCPs manually — use `ttt-mcp-add`.** |
| `AGENTS.md` | This file — enforcing rules + quick-ramp. Loaded as system instructions every session. |
| `agents/` | Custom agent `.md` files. Must use `llm-api/*` models, `subagent` mode (only `request-orchestrator` uses `mode: primary`). |
| `agent-template.md` | Start here when creating a new agent. |
| `~/.opencode/skills/` | TTT-installed skills (canonical location). |
| `~/.config/opencode/skills/` | Mirror of `~/.opencode/skills/` — kept in sync by `ttt-skills-install`. |
| `~/.opencode/prompts/` | Installed slash commands. |
| `plugins/config-backup.ts` | Auto-backup plugin — fires on file change, rsync to `~/opencode-config-backup`. |
| `plugins/sidebar-panels.ts` | TUI sidebar — spend + active agent panels. |
| `bin/opencode-bmw-wsl2` | WSL2 wrapper (reads `.env` instead of Keychain). |
| `load-secrets.sh` | macOS only — loads Keychain secrets into env vars. Sourced by `.zshrc`. |

### Commands you must use (not the obvious alternatives)

```bash
# Install a skill — use the wrapper, NOT bare `ttt skills install`
ttt-skills-install dx/<skill-name>
# The wrapper: runs the TTT install → lints SKILL.md → syncs to skills/ → commits + pushes

# Add an MCP — use this, NOT manual opencode.json edits
ttt-mcp-add dx/<mcp-name>

# Refresh BMW OAuth2 bearer token (macOS only, ~2h TTL)
bmw-refresh

# Run skill-lint after any SKILL.md change
~/.opencode/plugins/clipjoint/.venv/bin/python3 ~/.opencode/skills/skill-lint.py [skill-name]

# All Python in skills and modules must run from the clipjoint venv, not system python
~/.opencode/plugins/clipjoint/.venv/bin/python3 <script>
```

### Git workflow

- **Minor fix** (single file, no new agent/MCP/prompt): commit directly to `main`.
- **Major enhancement** (3+ files, new agent/MCP/prompt, multi-step work): branch first.
  ```bash
  git checkout main && git pull origin main
  git checkout -b feat/<description>
  # ... work ...
  /create-pr   # slash command: commit cleanup → push → gh pr create
  ```
- Ask the user once before branching — never branch autonomously (Rule 12).
- Always sync `README.md` in the same commit as the enhancement (Rule 10).

### Gotchas agents regularly miss

- **`mode: primary` is for `request-orchestrator` only.** All other agents use `mode: subagent`.
- **Skill Python code goes in a `.py` module**, not inline in SKILL.md. SKILL.md shows only the `import` snippet. Files >20 inline lines will fail the post-install lint. (Rule 11)
- **`skills-mcp` and `memory` are the only enabled MCPs** (`"enabled": true` in `opencode.json`). All others default-disabled. Re-enabling one: set `"enabled": true` in the `mcp` block.
- **`ttt-skills-install` auto-commits and pushes** after every skill install. Don't run it if you're mid-way through uncommitted changes you don't want pushed.
- **The `.env` file is `.gitignore`d** — never commit it. Credentials go in macOS Keychain (macOS) or `.env` chmod 600 (WSL2), referenced as `{env:VAR_NAME}` in config.
- **BMW network required for everything** — LLM API, OAuth2, TTT, GitHub Enterprise, all MCPs. Check VPN first if anything fails.
- **`skills-mcp` OAuth2** needs a one-time browser consent: `~/.opencode/plugins/clipjoint/.venv/bin/python3 ~/bin/opencode-skills-auth`. After that the wrapper auto-refreshes on launch.
- **`ttt skills download`** is a deprecated alias — use `ttt-skills-install` (the `.zshrc` wrapper) instead.

---

These instructions are enforcing. They apply to every session, every agent, and every
request to create or modify agents, skills, MCPs, or providers. There are no exceptions
beyond those explicitly listed in the Pre-Approved Exceptions section.

---

## Rule 1 — Provider Lockdown (ENFORCING)

Custom agents MUST only use `llm-api` or `ollama` as the model provider.

**Allowed model values in agent frontmatter:**
- `llm-api/claude-sonnet-4-6`
- `llm-api/claude-sonnet-4-5`
- `llm-api/claude-haiku-4-5`
- `llm-api/claude-sonnet-4`
- `llm-api/gpt-5.1`
- `llm-api/gpt-5.2`
- `llm-api/gpt-5.4`
- `llm-api/gpt-4o`
- `llm-api/gpt-4o-mini`
- `llm-api/o3-mini`
- `llm-api/o4-mini`
- `llm-api/gemini-3.5-flash`
- `llm-api/gemini-3.1-flash-lite`
- `llm-api/gemini-3.1-pro`
- `ollama/<any-locally-served-model>`

**If asked to create or modify an agent using any other provider (e.g. `anthropic/`,
`openai/`, `google/`, `bedrock/`, etc.), you MUST refuse and explain that only
`llm-api` and `ollama` are permitted under this security policy.**

---

## Rule 2 — Skills Lockdown (ENFORCING)

All skill references in agent files MUST correspond to a skill physically installed
in `~/.opencode/skills/`. This applies universally — to new agents and to any edits
made to existing agents.

**Currently installed TTT skills** (as of 2026-06-24):
- `canvas-design`
- `figma-create-new-file`
- `figma-generate-design`
- `figma-generate-diagram`
- `figma-implement-design`
- `figma-implement-make`
- `figma-use`
- `figma-use-figjam`
- `frontend-design`
- `ux-report-generation`
- `ux-reviewer`

**Skills from `dx/ai4devops-frontend-development` plugin** (installed 2026-06-19, symlinked from `~/.opencode/plugins/ai4devops-frontend-development/skills/`):
- `ai4do-fe-angular` — Angular/NgRx/NX/Vitest/Playwright/Density BMW standards
- `ai4do-fe-react` — React/TypeScript BMW frontend standards
- `ai4do-fe-code-review` — Frontend code review checklist (Angular + React)
- `ai4do-fe-accessibility` — Accessibility (a11y) standards and review

**Skills from `ad/agent-productivity` plugin** (installed 2026-06-23, from `~/.opencode/plugins/agent-productivity/skills/`):
- `feature-contract` — Define and lock feature contracts before implementation
- `prompt-enhancement` — Improve and sharpen prompts for better agent results
- `session-analysis` — Analyse and reflect on an agent session's effectiveness
- `skill-execution-footprint` — Measure and minimise skill context/token usage
- `strategic-thinking` — Apply structured strategic reasoning to complex problems

**Manually created skills** (installed 2026-06-19):
- `gh-cli` — GitHub Enterprise CLI (`gh`) operations via `atc-github.azure.cloud.bmw`; use instead of the github MCP

**All other installed skills** (58 total as of 2026-06-24):

For the complete current list, run:
```bash
ls ~/.opencode/skills/
```

Key skills from TTT catalog include:
- **Git/GitHub**: `pr-overview`, `pr-creation`, `jira-adhoc-story`, `git-commit-reorganization`, `bmw-oss-dual-repo-workflow`, `gh-cli`
- **Code Quality**: `python-data-quality`, `embedded-review`, `ai4do-fe-code-review`
- **Presentations**: `bmw-pptx`, `bmw-slides`, `bmw-ppt-creator`, `bmw-github-pages`, `ppt-style-registry`
- **Figma/Design**: `figma-use`, `figma-generate-design`, `figma-generate-diagram`, `figma-implement-design`, `figma-create-new-file`, `canvas-design`, `frontend-design`
- **UX**: `ux-reviewer`, `ux-report-generation`
- **Angular**: `ace-angular-developer`, `ace-angular-core-components`, `ace-angular-core-components-form`, `ace-angular-core-theme`, `ace-angular-translations`, `ace-angular-major-version-migration-preparation`, `ace-angular-major-version-migration-execution`
- **Video**: `clipjoint`, `manim-renderer`, `storyboard-planner`, `tts`, `audio-generation`, `transcription`, `text-generation`, `image-generator`, `video-merger`
- **RAG**: `rag` — embed + cosine search + rerank + generate, numpy only, no external DB
- **PDF**: `pdf-chat` — base64 PDF upload to Claude via BMW LLM API, max 10 MB, supports Q&A + structured extraction
- **GAIA**: `gaia-tools` — call BMW GAIA Tools/Chatbots via Apigee; session→interaction→poll pattern; M2M auth; discover public tools via resource registry
- **Web Research**: `web-research`, `deep-web-research`
- **Office 365**: `morning-briefing`, `office365-graph-secure`
- **Agentic**: `bmw-tool-agent` — ReAct loop + **advisor-enhanced mode** (`bmw_advisor.py`); 7 named profiles (`speed`/`economy`/`balanced`/`claude`/`gpt`/`quality`/`deep`); 16-model catalogue with tier ratings; `recommend()` heuristic; `pick_profile()` interactive CLI; `RunStats` cost tracking. Basic mode for simple workflows; advisor mode for complex/high-stakes tasks.
- **Routing Cache**: `routing-cache` — self-learning semantic routing cache at Priority 0.5; `text-embedding-3-small` + numpy cosine ≥ 0.82; syncs from `opencode.db`; records every live routing decision.
- **Utilities**: `ttt`, `mcp-setup`, `dor-jira-updater`, `bmw-wisdom`, `file-handoff`

Before referencing any skill in an agent, verify it is in this list or confirm it
exists in `~/.opencode/skills/` by checking the filesystem.

**If a required skill is NOT installed, you MUST refuse to create the agent and
instead instruct the user to install it first:**

```bash
ttt skills install <namespace/name> --agent-type opencode --global
```

Then verify it appears in `~/.opencode/skills/` before proceeding.

**Do NOT reference skills from `~/.agents/skills/`, `~/.claude/skills/`,
`~/.github/skills/`, or any other path. Only `~/.opencode/skills/` is trusted.**

---

## Rule 3 — MCP Lockdown (ENFORCING)

MCP server entries MUST NOT be added to `opencode.json` manually.

All MCPs must come from the TTT catalog and be installed via the existing
shell function:

```bash
ttt-mcp-add <namespace/name>
# Example: ttt-mcp-add dx/grafana-mcp
```

**If asked to add an MCP any other way — including pasting a config block directly
into `opencode.json` — you MUST refuse and redirect to `ttt-mcp-add`.**

The only exception is the pre-approved `memory` MCP documented below.

---

## Rule 4 — Agent Creation Rules (ENFORCING)

When creating a new custom agent, ALL of the following constraints apply:

1. **Model** — must use `llm-api/...` or `ollama/...` only (see Rule 1)
2. **Skills** — must only reference skills installed in `~/.opencode/skills/` (see Rule 2)
3. **Credentials** — no raw secrets or tokens in agent files; use `{env:VAR_NAME}` references
4. **Location** — agent files go in `~/.config/opencode/agents/`
5. **Template** — use `~/.config/opencode/agent-template.md` as the starting point
6. **Mode** — set `mode: primary` for user-facing agents, `mode: subagent` for internal helpers

If any of the above constraints cannot be satisfied, refuse to create the agent and
explain which constraint is blocking it.

---

## Rule 5 — Pre-Approved Exceptions

The following items are explicitly approved and must NOT be flagged, disabled, or removed:

### `memory` MCP — `@modelcontextprotocol/server-memory`

- **Type:** Local only (`type: local`) — no network access, no remote connections
- **Credentials:** None required
- **Purpose:** Persistent knowledge graph storage across sessions via the memory tools
- **Risk:** Minimal — open-source, no exfiltration surface
- **Status:** Enabled — do not disable or modify this entry
- **Justification:** No TTT equivalent exists in the MCP catalog as of 2026-06-19

### TTT-sourced MCPs (added 2026-06-19)

The following MCPs are sourced from the TTT catalog (`dx/` namespace) and are
pre-approved. They were added manually because `ttt mcp install --agent-type opencode`
writes to the wrong path (`~/.opencode/mcp.json` instead of `~/.config/opencode/opencode.json`).

| Key in `opencode.json` | TTT source | Type | Credentials | Status |
|---|---|---|---|---|
| `fetch` | `dx/fetch-mcp` | `local` (npx, BMW registry) | None | Disabled |
| `github` | `dx/github-mcp` | `local` (docker, BMW nexus) | `{env:GITHUB_PAT}`, `{env:GITHUB_HOST}` | Disabled |
| `grafana` | `dx/grafana-mcp` | `local` (uvx) | `{env:GRAFANA_URL}`, `{env:GRAFANA_SERVICE_ACCOUNT_TOKEN}` | Disabled |
| `wiz` | `dx/wiz-mcp` | `remote` (https://mcp.app.wiz.io/) | OAuth auto-detect (run `opencode mcp auth wiz`) | Disabled |
| `skills-mcp` | `dx/skills-mcp` | `remote` (https://skills.bmwgroup.net/mcp) | `{env:TTT_PAT}` — see auth note below | **Enabled (Phase 3)** |
| `playwright` | `dx/playwright-mcp` | `local` (npx, BMW Nexus `@playwright/mcp@latest`) | None | Disabled |

**Skills MCP — auth architecture (important):**

The `skills-mcp` server at `skills.bmwgroup.net` returns a `WWW-Authenticate` header on
unauthenticated requests. OpenCode ≥ 1.17 detects this and automatically initiates an OAuth2
PKCE browser-redirect flow — **even when static `headers` are configured in `opencode.json`**.
This makes the normal `"Authorization": "Bearer {env:TTT_PAT}"` header approach unreliable.

**Working solution (2026-06-24, updated):** The `skills-mcp` server uses a real OAuth2 PKCE
flow — the TTT PAT alone cannot be injected as an access token (server returns HTTP 400).
The correct approach is a **one-time browser consent** that issues a proper `access_token`
(1h TTL) + `refresh_token` (persistent). The wrapper then auto-refreshes using the
`refresh_token` on every launch — no browser interaction needed after the first setup.

**One-time browser setup:**
```bash
~/.opencode/plugins/clipjoint/.venv/bin/python3 ~/bin/opencode-skills-auth
# Opens browser → click Allow → tokens written to mcp-auth.json automatically
```

**Self-healing:** `~/bin/opencode-bmw` now includes a `skills_mcp_heal()` function that
runs on every launch:
1. If `access_token` is fresh (>5 min remaining) → skip
2. If expired but `refresh_token` exists → silently refreshes using token endpoint
3. If entry is corrupted (stale OAuth state, no tokens) → clears it and prints a warning

**Manual recovery** (if skills-mcp stops working):
```bash
# Re-run the one-time auth (browser required once)
~/.opencode/plugins/clipjoint/.venv/bin/python3 ~/bin/opencode-skills-auth

# Then relaunch OpenCode normally — wrapper handles refresh from then on
opencode
```

All credentials are stored as blank placeholders in `~/.config/opencode/.env`.
Fill in real values there before using these MCPs.

No other MCPs may be added without updating this exceptions list and
creating a backup of `opencode.json` first.

---

## Rule 6 — Credential Hygiene (ENFORCING)

Credentials, tokens, API keys, and PATs MUST:

- Be stored in `~/.config/opencode/.env` (permissions: 600)
- Be referenced in config files as `{env:VAR_NAME}` — never as raw strings
- Never appear in agent files, skill files, or `AGENTS.md`

If asked to add a credential directly to any config file, refuse and redirect to
the `.env` + `{env:VAR}` pattern.

---

## Rule 6.1 — BMW LLM API Authentication (AUTO-REFRESH SYSTEM)

### OAuth2 Token Refresh Workflow

The BMW LLM API (`api.gcp.cloud.bmw/llmapi/v1`) uses OAuth2 bearer tokens with **~2-hour TTL**.
To prevent authentication failures and session hangs, an automatic token refresh system is deployed.

### Architecture

**Components:**
1. **Wrapper script** (`~/bin/opencode-bmw`) — refreshes tokens before every OpenCode launch
2. **Cron job** (optional) — refreshes tokens every 90 minutes in background (keeps Keychain current)
3. **Keychain storage** (`com.bmw.opencode` service) — secure token storage
4. **`bmw-refresh` function** (`.zshrc`) — fetches new tokens from `auth.bmwgroup.net`
5. **Shell alias** (`opencode` → `~/bin/opencode-bmw`) — transparent wrapper invocation

**Flow:**
```
User runs 'opencode' → alias → wrapper script → bmw_refresh_inline → Keychain update
                                                                    ↓
                                                            exports fresh env vars
                                                                    ↓
                                                            launches /opt/homebrew/bin/opencode
                                                                    ↓
                                                            reads opencode.json
                                                                    ↓
                                                            substitutes {env:LLM_API_BEARER_TOKEN}
                                                                    ↓
                                                            API request with fresh token (<2s old)
```

### Configuration Files

**`opencode.json`** — uses `{env:...}` substitution (NOT hardcoded tokens):
```json
{
  "provider": {
    "llm-api": {
      "options": {
        "headers": {
          "Authorization": "Bearer {env:LLM_API_BEARER_TOKEN}",
          "x-apikey": "{env:LLM_API_KEY}"
        }
      }
    }
  }
}
```

**`.env`** — non-secret config only (secrets come from Keychain):
```bash
# LLM API credentials — loaded from macOS Keychain via load-secrets.sh
# DO NOT store secrets here. Use Keychain (service: com.bmw.opencode)
# Secrets are exported by load-secrets.sh which is sourced in .zshrc
```

**`/opt/homebrew/bin/opencode`** — symlink replaced with wrapper (no alias needed):
```bash
# /opt/homebrew/bin/opencode -> /Users/QTE2362/bin/opencode-bmw
# Replaced the Homebrew symlink directly so the wrapper runs regardless of shell type.
# No alias in .zshrc required. Works from Terminal, Dock, scripts, and non-interactive shells.
ls -la /opt/homebrew/bin/opencode
# lrwxr-xr-x  opencode -> /Users/QTE2362/bin/opencode-bmw
```

### Network Requirements

**CRITICAL:** BMW LLM API and OAuth2 endpoint require:
- **On-site:** Corporate network access (direct)
- **Off-site:** Active VPN connection to BMW network

**If authentication fails:**
1. Check VPN status: `scutil --nc list` (should show "Connected")
2. Test OAuth2 endpoint manually: `bmw-refresh` (from `.zshrc`)
3. Check firewall rules: `curl -I https://auth.bmwgroup.net`
4. Review wrapper logs: `~/bin/opencode-bmw --version 2>&1`

### Maintenance

**Token refresh logs (if cron enabled):**
```bash
# View last 20 refresh attempts
tail -20 ~/Library/Logs/opencode/token-refresh.log

# Watch live refresh activity
tail -f ~/Library/Logs/opencode/token-refresh.log
```

**Manual token refresh:**
```bash
# Force immediate refresh (bypasses wrapper)
bmw-refresh

# Verify token in Keychain
security find-generic-password -s com.bmw.opencode -a llm_api_bearer_token -w
```

**Check wrapper is in use:**
```bash
type opencode
# Expected: opencode is an alias for /Users/QTE2362/bin/opencode-bmw

which opencode
# Expected: opencode: aliased to /Users/QTE2362/bin/opencode-bmw
```

### Troubleshooting

| Symptom | Cause | Solution |
|---------|-------|----------|
| OpenCode hangs on startup | Stale token, VPN disconnected | Check VPN, run `bmw-refresh` |
| "ProviderModelNotFoundError" | Model name format | Use `llm-api/model-name` not `model-name` |
| "Could not load LLM_API_BEARER_TOKEN" | Keychain locked or empty | Run `bmw-refresh` to initialize |
| Wrapper shows "Token refresh failed" | OAuth2 endpoint unreachable | Check VPN, corporate network, firewall |
| Cron not running | macOS permissions | Add Terminal to Full Disk Access in System Settings |

**Common fixes:**
```bash
# Reset token completely
bmw-refresh

# Test wrapper directly
~/bin/opencode-bmw --version

# Verify config uses {env:...} pattern
grep -A3 'headers' ~/.config/opencode/opencode.json
# Should show: "Authorization": "Bearer {env:LLM_API_BEARER_TOKEN}"

# Check if hardcoded tokens remain (BAD)
grep -E '[0-9a-zA-Z]{27}' ~/.config/opencode/opencode.json
# Should return nothing (no raw tokens)
```

### Optional: Cron Background Refresh

To keep Keychain tokens fresh between OpenCode sessions, add a cron job:

**Manual setup (requires Terminal Full Disk Access):**
```bash
# 1. Create log directory
mkdir -p ~/Library/Logs/opencode

# 2. Test command manually
/bin/zsh -c 'source ~/.zshrc && bmw-refresh' >> ~/Library/Logs/opencode/token-refresh.log 2>&1

# 3. Edit crontab
crontab -e

# 4. Add this line (runs every 90 minutes):
*/90 * * * * /bin/zsh -c 'source ~/.zshrc && bmw-refresh' >> ~/Library/Logs/opencode/token-refresh.log 2>&1

# 5. Verify crontab
crontab -l
```

**Note:** Cron is optional. The wrapper script refreshes tokens on every OpenCode launch, so cron only helps if you need fresh tokens for other tools reading from Keychain.

### Rollback Instructions

If auto-refresh system causes issues, revert to hardcoded tokens temporarily:

**Quick rollback (1 minute):**
```bash
# 1. Restore backup config
cp ~/.config/opencode/opencode.json.hardcoded-backup-* ~/.config/opencode/opencode.json

# 2. Restore the original Homebrew symlink
rm /opt/homebrew/bin/opencode
ln -s ../Cellar/opencode/1.17.5/bin/opencode /opt/homebrew/bin/opencode

# 3. Manually refresh token before each session
bmw-refresh && /opt/homebrew/bin/opencode
```

**Permanent rollback:**
```bash
# 1. Restore the original Homebrew symlink
rm /opt/homebrew/bin/opencode
ln -s ../Cellar/opencode/1.17.5/bin/opencode /opt/homebrew/bin/opencode

# 2. Remove wrapper script
rm ~/bin/opencode-bmw

# 3. Remove cron job (if configured)
crontab -e
# Delete the bmw-refresh line, save

# 4. Restore hardcoded config permanently
cp ~/.config/opencode/opencode.json.hardcoded-backup-* ~/.config/opencode/opencode.json
```

**After rollback, you must:**
- Manually run `bmw-refresh` every ~90 minutes
- Update hardcoded bearer token in `opencode.json` when it expires
- Remember: hardcoded tokens violate Rule 6 (Credential Hygiene)

---

## Rule 7 — Installed Custom Agents

### OpenCode agents (`~/.config/opencode/agents/`) — all follow Rules 1–6

| Agent file | Purpose | Key trigger phrases |
|---|---|---|
| `jirri-data-analyst.md` | JIRRI RPA cost-savings calculation auditor; Python/stdlib script expert | JIRRI, cost savings, MB1B, LT01, jirri_cost_savings.py |
| `uipath-rpa-expert.md` | UiPath Dispatcher/Worker documentation generator; XAML analyzer | uipath, rpa, dispatcher, worker, xaml, bot |
| `oracle-apex-expert.md` | Oracle APEX development + maintenance; Oracle SQL/PL/SQL expert; fetches live docs from docs.oracle.com | apex, oracle apex, plsql, oracle sql, ora- error, apex page, apex plugin |
| `opencode-dev-expert.md` | OpenCode version upgrades, wrapper maintenance, skill/plugin lifecycle, MCP setup, auth changes, config repo work | opencode upgrade, new opencode version, brew upgrade opencode, wrapper script, opencode broken, skill install, plugin update, mcp setup, opencode config, opencode development |

### Copilot agents (`~/.copilot/agents/`) — mirror of OpenCode custom agents for GitHub Copilot

| Agent file | Mirrors | Handoffs declared |
|---|---|---|
| `oracle-apex-expert/oracle-apex-expert.agent.md` | `oracle-apex-expert.md` | All 8 TTT agents |
| `uipath-rpa-expert/uipath-rpa-expert.agent.md` | `uipath-rpa-expert.md` | All 8 TTT agents |
| `jirri-data-analyst/jirri-data-analyst.agent.md` | `jirri-data-analyst.md` | All 7 TTT agents (excl. self-referential) |

**Keep OpenCode and Copilot versions in sync** when updating agent knowledge or handoff triggers.

### UX / Design skill routing (OpenCode only)

The following installed skills are available for UI/UX work. Custom agents invoke them directly — no separate agent handoff required.

| Skill | When to invoke |
|---|---|
| `ux-reviewer` | UX/usability review of any UI (APEX page, web app, bot UI) |
| `ux-report-generation` | Formal evaluation report wrapping UX review findings |
| `frontend-design` | Polished HTML/CSS/React prototype or dashboard |
| `canvas-design` | Poster, infographic, or static visual design artifact |
| `figma-generate-design` | Full page or screen built in Figma from code or description |
| `figma-generate-diagram` | Architecture, ER, or flow diagram in FigJam |
| `figma-implement-design` | Production code generated from a Figma design file |
| `figma-use` | Any write operation on a Figma canvas (MANDATORY prerequisite) |
| `figma-create-new-file` | Create a new blank Figma or FigJam file |
| `figma-use-figjam` | FigJam-specific canvas operations |
| `figma-implement-make` | Production code from Figma Make prototype |

### Cross-agent communication rules

- Agents MUST explicitly declare a handoff: name the target agent, what to pass, and why.
- When handing off involving Oracle/APEX context, always pass: APEX version, DB version, relevant table/view/page IDs.

#### Full routing matrix (TTT agents are Copilot-only; custom agents are OpenCode)

| From | To | Trigger |
|---|---|---|
| `oracle-apex-expert` | `jirri-data-analyst` | SQL result sets needing statistical analysis or cost calculations |
| `oracle-apex-expert` | `uipath-rpa-expert` | APEX page/workflow needs UiPath automation or bot documentation |
| `oracle-apex-expert` | `presentation-builder` | APEX/DB findings or architecture docs → slide deck |
| `oracle-apex-expert` | `aaa-security-fixer` | APEX security review, SQL injection, exposed ORDS endpoints, Oracle CVEs |
| `oracle-apex-expert` | `agile-master-pi-planning` | APEX features need PI backlog, capacity planning, sprint health |
| `oracle-apex-expert` | `agile-master-catalyst-coaching` | Team needs coaching on APEX adoption or tech debt conversations |
| `oracle-apex-expert` | `dor-agent` | APEX user stories need DoR compliance or Jira field population |
| `oracle-apex-expert` | `token-tom` | Request outside Oracle/APEX/SQL domain |
| `uipath-rpa-expert` | `oracle-apex-expert` | Bot touches Oracle APEX UI or needs Oracle SQL/PL/SQL |
| `uipath-rpa-expert` | `jirri-data-analyst` | Bot output data needs statistical analysis or Python post-processing |
| `uipath-rpa-expert` | `presentation-builder` | Bot architecture, flow diagrams, or run metrics → slide deck |
| `uipath-rpa-expert` | `aaa-security-fixer` | XAML or config contains hardcoded credentials or secrets |
| `uipath-rpa-expert` | `agile-master-pi-planning` | RPA development needs PI-level tracking or sprint health |
| `uipath-rpa-expert` | `agile-master-catalyst-coaching` | RPA team needs coaching on bot adoption or process change |
| `uipath-rpa-expert` | `dor-agent` | RPA user stories need DoR compliance check |
| `jirri-data-analyst` | `oracle-apex-expert` | Analysis requires Oracle SQL queries or APEX page data as source |
| `jirri-data-analyst` | `uipath-rpa-expert` | Cost savings data needs to be sourced from or delivered into a UiPath bot |
| `jirri-data-analyst` | `presentation-builder` | Cost savings results, ROI summary, or charts → slide deck |
| `jirri-data-analyst` | `agile-master-pi-planning` | JIRRI analysis results inform PI planning decisions |
| `jirri-data-analyst` | `agile-master-catalyst-coaching` | Findings reveal process inefficiencies needing team coaching |
| `jirri-data-analyst` | `dor-agent` | Analysis results become Jira stories needing DoR compliance |
| Any custom agent | `token-tom` | Request is outside the custom agent's domain; needs routing |
| Any TTT/custom agent | `oracle-apex-expert` | Oracle DB queries, PL/SQL blocks, or APEX page config needed |
| Any agent | `opencode-dev-expert` | OpenCode upgrade, version bump, wrapper fix, skill lifecycle, MCP setup, config repo changes |
| `opencode-dev-expert` | `aaa-security-fixer` | Upgrade introduces a security finding or CVE |
| `opencode-dev-expert` | `agile-master-pi-planning` | Upgrade needs PI-level planning or sprint capacity |

---

## Rule 8 — Oracle APEX Agent Deployment (Dual-Platform)

The `oracle-apex-expert` agent is deployed in **two runtimes**:

### OpenCode
- File: `~/.config/opencode/agents/oracle-apex-expert.md`
- Uses the `fetch` MCP (pre-approved, `dx/fetch-mcp`) to pull Oracle documentation
- Model: `llm-api/claude-sonnet-4-6`
- Credential: none required for public docs.oracle.com fetches

### GitHub Copilot (VSCode / GitHub CLI)
- File: `~/.copilot/agents/oracle-apex-expert/oracle-apex-expert.agent.md`
- Uses `web/fetch` tool (Copilot built-in)
- Models: Claude Sonnet 4.6 (copilot), Claude Sonnet 4.5 (copilot), GPT-4o (copilot)
- Handoffs declared to all 8 TTT agents

**Keep both files in sync** when updating Oracle APEX knowledge or documentation URL patterns. The Copilot version uses `web/fetch` and `model: [list]` syntax; the OpenCode version uses the `fetch` MCP and `model: llm-api/...` frontmatter.

### All three custom agents are now dual-platform

| Agent | OpenCode file | Copilot file |
|---|---|---|
| `oracle-apex-expert` | `~/.config/opencode/agents/oracle-apex-expert.md` | `~/.copilot/agents/oracle-apex-expert/oracle-apex-expert.agent.md` |
| `uipath-rpa-expert` | `~/.config/opencode/agents/uipath-rpa-expert.md` | `~/.copilot/agents/uipath-rpa-expert/uipath-rpa-expert.agent.md` |
| `jirri-data-analyst` | `~/.config/opencode/agents/jirri-data-analyst.md` | `~/.copilot/agents/jirri-data-analyst/jirri-data-analyst.agent.md` |

All Copilot versions carry `handoffs:` blocks covering all relevant TTT agents. OpenCode versions carry equivalent `## Cross-Agent Communication` and `## UX / Design Skill Handoffs` sections.

---

## Rule 9 — Installed Prompts (Slash Commands)

Slash commands are defined as markdown files in `~/.config/opencode/commands/`. OpenCode loads them from this directory automatically — the filename (without `.md`) becomes the command name.

> **Note:** `~/.opencode/prompts/*.prompt.md` files are a TTT convention and are **not loaded by opencode**. The working location is `~/.config/opencode/commands/*.md`.

| Command file | Slash command | Purpose | Required skills |
|---|---|---|---|
| `create-pr.md` | `/create-pr` | Stage → atomic commits → push → open PR via `gh` | `git-commit-reorganization`, `pr-creation` |
| `apply-pr-suggestions.md` | `/apply-pr-suggestions` | Read PR review comments and apply accepted ones | `gh-cli` |
| `nice-git-commits.md` | `/nice-git-commits` | Reorganise uncommitted changes into logical atomic commits | `git-commit-reorganization` |
| `security-fix.md` | `/security-fix` | AAA agent — fix GHAS/Wiz Code findings (`target=ghas` or `target=wiz`) | `aaa-ghas-remediation`, `aaa-wiz-remediation` |
| `security-explain.md` | `/security-explain` | Read-only — explain GHAS/Wiz findings, attack paths, remediation options | `aaa-ghas-remediation`, `aaa-wiz-remediation` |
| `bmw-wisdom.md` | `/bmw-wisdom` | Append one BMW-style saying to the end of a completion message | `bmw-wisdom` |
| `beast-mode.md` | `/beast-mode` | Autonomous execution — 3 RALPH loops, zero interruptions, self-correction | none |
| `direct.md` | `/direct` | Bypass routing — answer directly without skill loading or delegation | none |

> **Note:** `security-fix` and `security-explain` require the `aaa-security-remediation` bundle:
> `ttt skills install aaa/aaa-ghas-remediation --agent-type opencode --global`

---

## Rule 10 — README Sync (ENFORCING)

**Every system enhancement must update `README.md` before the final `git push`.**

The README at `~/.config/opencode/README.md` is the onboarding document for new BMW team members. It must accurately reflect the current state of the system at all times.

### When this rule applies

This rule is triggered by any of the following:
- Installing a new skill (`ttt skills install ...`)
- Adding a new slash command / prompt
- Creating or modifying a custom agent
- Enabling, disabling, or adding an MCP server
- Adding a new available model
- Adding a new configuration file
- Making an auth or startup change
- Achieving a measurable performance improvement

### What to check and update

| What changed | README section to update |
|---|---|
| New skill | `## Skills Library` — add row with name, purpose, install command |
| New slash command | `## Slash Commands (Prompts)` — add row |
| New custom agent | `## Custom Agents` — add row |
| MCP enabled/added/disabled | `## MCP Servers` — update table |
| New model | `## Models Available` — add row |
| Auth / startup change | `## Troubleshooting` and `## Architecture` |
| New config file | `## Configuration Files` — add row |
| Performance improvement | `## Performance Metrics` — update numbers |

### How to verify

```bash
# See what you changed
git diff --stat HEAD

# Check the relevant README sections manually
# Edit README.md to add missing entries

# Always stage README.md with the enhancement commit
git add README.md
```

### Commit convention

Include README changes in the same commit as the feature:
```
feat: add <capability>

- <what the feature does>
- README: updated <section name>
```

**If you are an agent completing an enhancement task: do not mark the task complete until `README.md` has been updated and staged.**

---

## Rule 11 — Skill Module-Import Paradigm (ENFORCING)

**SKILL.md files must be API references, not implementations.**

When writing or updating a skill, all executable Python logic MUST be extracted to a
`.py` module co-located in the skill directory. SKILL.md references the module via a
short import snippet. This keeps skill context lean and eliminates hallucination surface.

### The pattern

**Wrong (never do this):**
```markdown
## How to use
```python
import os, json
from pydantic import BaseModel
class MyModel(BaseModel):
    ...   # 50 lines of implementation
def my_function(...):
    ...
```
```

**Correct (always do this):**
1. Implementation goes in `~/.opencode/skills/<name>/my_module.py` (full docstring, type hints, etc.)
2. SKILL.md shows only the import snippet:

```markdown
## How to use
```python
import sys, pathlib
sys.path.insert(0, str(pathlib.Path.home() / ".opencode/skills/<name>"))
from my_module import my_function
result = my_function(...)
```
```

### Module location rules

| Module type | Location |
|---|---|
| Skill-specific logic | `~/.opencode/skills/<name>/<module>.py` |
| Pipeline-shared utilities (audio, TTS, image) | `~/.opencode/plugins/clipjoint/scripts/<module>.py` |
| **Never** | `~/.agents/skills/`, `~/.claude/skills/`, or any other path |

### Runtime

All modules must import cleanly from the clipjoint venv:
```bash
~/.opencode/plugins/clipjoint/.venv/bin/python3 -c "import <module>"
```

### Escape hatch

If a code block is **intentional documentation** (illustrative examples of patterns to
follow/avoid, not executable module code), suppress the linter with:
```markdown
<!-- skill-lint: ignore -->
```python
# example code...
```
```

### Enforcement

`~/.opencode/skills/skill-lint.py` checks every SKILL.md for violations:
```bash
# Lint all skills:
python3 ~/.opencode/skills/skill-lint.py

# Lint one skill after install:
python3 ~/.opencode/skills/skill-lint.py <skill-name>
```

The `ttt-skills-install` wrapper in `~/.zshrc` runs this automatically after every
`ttt skills install` call. `ttt-skills-download` is a deprecated alias that forwards
to `ttt-skills-install` for backwards compatibility. Warnings are non-fatal but must
be resolved before the skill is considered complete.

---

## Rule 12 — Feature Branch Workflow for Major Enhancements (ENFORCING)

**Major enhancements to the OpenCode configuration MUST be developed on a feature branch, not directly on `main`.**

### What counts as a "major enhancement"?

Use a feature branch if **any one** of the following is true:

| Signal | Examples |
|---|---|
| Touches **3 or more files** | New skill + AGENTS.md update + README |
| Introduces a **new agent, MCP, or prompt** | High blast-radius changes that affect all sessions |
| Involves **multi-step / phased work** | Anything warranting a CHANGE-SCOPE.md plan |
| Requires **coordination across subsystems** | Auth changes, provider updates, orchestrator rewrites |

Minor changes may go directly to `main` (e.g. fixing a typo, bumping a model version in a single file, adding one bullet to a doc).

### Branching convention

```
feat/<short-description>    — new capability
fix/<short-description>     — bug fix
chore/<short-description>   — housekeeping, deps, config tweaks
docs/<short-description>    — documentation-only changes
```

### The workflow

```bash
# 1. Branch off main
git checkout main && git pull origin main
git checkout -b feat/<description>

# 2. Work on the branch with atomic commits
#    (use /nice-git-commits to clean up if needed)

# 3. When ready: open a PR via /create-pr
#    The /create-pr prompt handles: commit cleanup → push → gh pr create

# 4. Merge to main after review
```

### Agent behaviour — Advisory mode (Option B)

When an agent detects the start of a **major enhancement** (as defined above), it MUST:

1. **Ask once** before touching any files:
   > "This looks like a major enhancement (touching N files / introducing a new agent/MCP/prompt). Would you like me to branch off `main` before we start? I'll create `feat/<suggested-name>`."
2. **If the user confirms** → run `git checkout -b feat/<name>` and proceed.
3. **If the user declines** → proceed on the current branch without asking again.
4. **Never ask more than once per session** — if the user has already answered, respect that.

The agent MUST NOT autonomously create a branch without asking first.

### End-of-enhancement reminder

When wrapping up a major enhancement (after README sync, Rule 10), the agent should remind:
> "Ready to open a PR? Type `/create-pr` to push this branch and open a pull request."

---

## Restore Instructions

If this configuration needs to be restored:

```bash
# Restore from backup (replace date as needed)
cp -r ~/opencode-backup-20260619 ~/.config/opencode
source ~/.config/opencode/.env
```

To add the `memory` MCP back if accidentally disabled:
```json
"memory": {
  "type": "local",
  "command": ["npx", "-y", "@modelcontextprotocol/server-memory"]
}
```
