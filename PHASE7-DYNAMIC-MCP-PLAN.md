# Phase 7 — Dynamic MCP Management

**Status:** 📋 PLANNED (not started)  
**Created:** 2026-06-23  
**Author:** request-orchestrator session  
**Depends on:** Phases 0-6 complete ✅  
**Estimated effort:** 2-4 hours  
**Priority:** Low — only valuable if more MCPs are enabled in future

---

## Problem Statement

Every enabled MCP injects its tool definitions into **every single request**, regardless of whether those tools are needed. As more MCPs are enabled, this overhead compounds silently.

### Current Token Overhead (per request)

| MCP | Tools | Est. Tokens | Status |
|---|---|---|---|
| `memory` | 9 | ~400 | Always enabled |
| `skills-mcp` | 3 | ~150 | Always enabled |
| `fetch` | 1 | ~50 | Disabled |
| `github` | ~30 | ~1,500 | Disabled |
| `grafana` | ~15 | ~750 | Disabled |
| `wiz` | ~10 | ~500 | Disabled |

**Today:** ~550 tokens overhead per request (2 MCPs enabled).  
**If all enabled:** ~3,350 tokens overhead per request — a **6× increase**.

At BMW LLM API rates, enabling all MCPs for every session wastes tokens on requests that never use them (e.g. a GitHub MCP in context for a "what is 2+2?" question).

### Real-World Impact

With a team of 10 developers each running ~50 requests/day:
- **All MCPs enabled:** ~1.675M tokens/day in MCP overhead alone
- **Dynamic management:** ~275K tokens/day
- **Saving:** ~1.4M tokens/day (~83% reduction)

---

## Goal

Enable the `request-orchestrator` to activate only the MCPs required for each request, and return to the minimal default state after the task completes.

**In-scope:**
- Dynamic enable/disable of `fetch`, `github`, `grafana`, `wiz` MCPs
- Intent detection to predict required MCPs
- Automatic state restoration after each task

**Out-of-scope:**
- `memory` MCP — always enabled (knowledge graph, no task dependency)
- `skills-mcp` MCP — always enabled (router needs it for discovery in Priority 4)
- New MCP installations (still via `ttt-mcp-add`)

---

## Design Options

Three approaches were evaluated. **Option B is recommended.**

---

### Option A: Session-Scoped File Mutation

The router edits `opencode.json` at the start of each session based on detected intent.

**Flow:**
```
Request → Router detects intent → Edit opencode.json (enable MCPs) → Route to agent → Edit opencode.json (disable MCPs)
```

**Pros:**
- Simple to implement
- Persistent across agent handoffs within a session

**Cons:**
- File I/O on every request
- Race conditions if two sessions run concurrently
- Requires OpenCode restart to pick up MCP changes (config is read at startup)
- **Verdict: Not viable** — config changes don't hot-reload in OpenCode v1.17.5

---

### Option B: Intent-Based MCP Mapping in Router (Recommended)

The router maintains a declarative intent → MCP mapping table. When it detects intent matching an MCP's domain, it tells the user to invoke OpenCode with those MCPs enabled (or provides a wrapper command).

**Flow:**
```
Request → Router detects MCP-requiring intent → Router informs user which MCP is needed
        → If MCP already enabled: proceed
        → If MCP disabled: router instructs user to enable it, or runs the task without it
```

**Pros:**
- No file mutation
- Centralised mapping table (easy to maintain)
- Transparent to user
- No race conditions

**Cons:**
- Doesn't auto-enable (requires user action or wrapper script)
- Partial solution: reduces wasted tokens but doesn't fully automate

**Verdict: Best fit for OpenCode's current architecture**

---

### Option C: Agent Frontmatter MCP Declarations

Each specialist agent declares its required MCPs:

```yaml
---
name: oracle-apex-expert
mcps:
  required: [fetch]
  optional: []
---
```

The router reads these declarations before handoff and enables MCPs accordingly.

**Pros:**
- Declarative — intent lives with the agent that needs it
- Self-documenting
- Clean separation of concerns

**Cons:**
- Requires editing all agent files
- OpenCode doesn't natively support `mcps:` frontmatter (custom parsing needed)
- Still depends on hot-reload working (same issue as Option A)

**Verdict: Best long-term design, but requires OpenCode platform support**

---

### Option D: Wrapper Script Per-Session (Recommended Interim)

Extend the existing `~/bin/opencode-bmw` wrapper script to accept an `--mcps` flag that enables specific MCPs for the current session by writing a temporary config overlay.

```bash
opencode --mcps github,fetch   # enables github + fetch for this session
opencode                       # default: only memory + skills-mcp
```

**Pros:**
- Doesn't mutate the permanent `opencode.json`
- Works with OpenCode's startup config read
- User retains control
- Composable with existing auto-refresh logic

**Cons:**
- Manual — user must know which MCPs they need
- No auto-detection

**Verdict: Good interim solution while awaiting Option B/C**

---

## Recommended Implementation Plan

### Phase 7a — Wrapper Script MCP Flag (Quick Win, ~30 min)

Extend `~/bin/opencode-bmw` to accept an optional `--mcps` argument that generates a temporary config overlay enabling the requested MCPs for that session only.

**Changes:**
1. Edit `~/bin/opencode-bmw` — add `--mcps` flag parsing
2. Generate a temp `opencode.override.json` merging base config + requested MCPs enabled
3. Launch OpenCode with the override config
4. Clean up temp file on exit

**Usage:**
```bash
# Default session (memory + skills-mcp only)
opencode

# GitHub PR review session
opencode --mcps github

# Security review session (Wiz + GitHub)
opencode --mcps github,wiz

# Full fetch + grafana session
opencode --mcps fetch,grafana
```

**Effort:** ~30 minutes  
**Token savings:** Immediate — users can opt into only the MCPs they need

---

### Phase 7b — Router MCP Awareness (Medium effort, ~1-2 hours)

Add an MCP requirements lookup table to the router. When the router detects intent that requires a currently-disabled MCP, it warns the user proactively.

**Changes to `request-orchestrator.md`:**

Add a new section to the decision tree (between Priority 2 and 3):

```
Priority 2.5: MCP Requirement Check
- After matching a specialist agent, check if that agent needs a disabled MCP
- If required MCP is disabled: inform user, suggest restart with --mcps flag
- If required MCP is enabled: proceed normally
```

**Intent → MCP mapping table to add to router:**

| Intent Keywords | Required MCP | Disabled By Default |
|---|---|---|
| github, pull request, PR, repository, ghas, codeql | `github` | ✅ |
| fetch, url, web page, documentation, docs.oracle.com | `fetch` | ✅ |
| grafana, dashboard, metrics, prometheus, alert, panel | `grafana` | ✅ |
| wiz, security findings, cve, vulnerability, sca, container scan | `wiz` | ✅ |

**Router behavior when required MCP is disabled:**

```
I detected this request needs the `github` MCP, which is currently disabled.

To enable it for this session, restart OpenCode with:
  opencode --mcps github

Or enable it permanently in opencode.json (not recommended for token efficiency).

I'll attempt to proceed without it, but some capabilities will be limited.
```

**Effort:** ~1-2 hours  
**Token savings:** Avoids user confusion, guides correct MCP selection

---

### Phase 7c — Long-Term: Platform-Native MCP Scoping (Future, ~4+ hours)

Track the OpenCode roadmap for native MCP scoping support. If OpenCode adds:
- Per-agent MCP declarations in frontmatter
- Hot-reload of MCP config changes
- Session-scoped MCP activation API

...then revisit Option A or Option C which offer full automation.

**Watch:** OpenCode release notes / changelog for MCP lifecycle management features.

---

## Implementation Details: Phase 7a

### Wrapper Script Changes (`~/bin/opencode-bmw`)

Current wrapper structure:
```bash
#!/bin/zsh
# 1. Refresh bearer token from Keychain
# 2. Export LLM_API_BEARER_TOKEN env var
# 3. exec /opt/homebrew/bin/opencode "$@"
```

Target wrapper structure:
```bash
#!/bin/zsh
# 1. Parse --mcps flag from args
# 2. Refresh bearer token from Keychain
# 3. Export LLM_API_BEARER_TOKEN env var
# 4. If --mcps flag present:
#    a. Read base opencode.json
#    b. Merge MCP overrides (enable requested MCPs)
#    c. Write to /tmp/opencode-session-$$.json
#    d. Launch opencode with --config /tmp/opencode-session-$$.json
#    e. Trap EXIT to clean up temp file
# 5. Else: exec /opt/homebrew/bin/opencode (no override)
```

### MCP Enable/Disable JSON Structure

Each MCP in `opencode.json` has an `enabled` field:

```json
"github": {
  "enabled": false,
  "type": "local",
  "command": ["docker", "run", "..."],
  "environment": {
    "GITHUB_PAT": "{env:GITHUB_PAT}",
    "GITHUB_HOST": "{env:GITHUB_HOST}"
  }
}
```

The wrapper script would use `jq` to enable specified MCPs:

```bash
# Enable github MCP
jq '.mcp.github.enabled = true' ~/.config/opencode/opencode.json > /tmp/opencode-override.json
```

### Supported MCP Names

| Flag value | `opencode.json` key | Description |
|---|---|---|
| `github` | `github` | GitHub MCP (PRs, issues, code search) |
| `fetch` | `fetch` | Web fetch MCP (URL retrieval) |
| `grafana` | `grafana` | Grafana MCP (dashboards, alerts) |
| `wiz` | `wiz` | Wiz MCP (security findings) |

Always-on (cannot be disabled via flag):
- `memory` — persistent knowledge graph
- `skills-mcp` — router catalog discovery

---

## Implementation Details: Phase 7b

### Router MCP Mapping Table

Add to `request-orchestrator.md` as a new section after the Specialist Agent Handoff Table:

```markdown
## MCP Requirement Check (Priority 2.5)

Before delegating to a specialist, check if required MCPs are enabled.

| Domain | Required MCP | Status Check |
|---|---|---|
| GitHub, PRs, repositories, GHAS, CodeQL | `github` | Check if enabled in opencode.json |
| Web fetch, URL, external docs | `fetch` | Check if enabled in opencode.json |
| Grafana, metrics, dashboards | `grafana` | Check if enabled in opencode.json |
| Wiz, security findings, CVE | `wiz` | Check if enabled in opencode.json |

If required MCP is disabled, respond with:
> ⚠️ This request needs the `{mcp-name}` MCP which is currently disabled.
> Restart with: `opencode --mcps {mcp-name}`
> I'll proceed with limited capability in the meantime.
```

### How Router Checks MCP Status

```bash
# Check if github MCP is enabled
jq '.mcp.github.enabled // false' ~/.config/opencode/opencode.json
# Returns: false (disabled) or true (enabled)
```

---

## Files to Create/Modify

| File | Action | Phase |
|---|---|---|
| `~/bin/opencode-bmw` | **EDIT** — add `--mcps` flag parsing and temp config overlay | 7a |
| `~/.config/opencode/agents/request-orchestrator.md` | **EDIT** — add Priority 2.5 MCP awareness section | 7b |
| `~/.config/opencode/AGENTS.md` | **EDIT** — document `--mcps` flag in Rule 6.1 (BMW LLM API section) | 7a |
| `~/.config/opencode/CHANGE-SCOPE.md` | **EDIT** — append Phase 7 entry | 7a+7b |
| `~/.config/opencode/README.md` | **EDIT** — update `## MCP Servers` table with `--mcps` flag info | 7a+7b |

**No changes to:**
- `opencode.json` — MCPs remain disabled by default (that's the point)
- Specialist agent files — no MCP declarations needed for 7a/7b
- `.env` — credentials already present

> **Rule 10 reminder:** README.md must be staged and committed alongside Phase 7 changes.
> Specifically: update `## MCP Servers` to document the `--mcps` flag and the wrapper script's
> new capability, and update `## Architecture` if the startup flow changes.

---

## Prerequisites

Before starting Phase 7a:

1. **Verify `jq` is installed:**
   ```bash
   which jq && jq --version
   ```
   If missing: `brew install jq`

2. **Verify current wrapper script location:**
   ```bash
   cat ~/bin/opencode-bmw | head -5
   ```

3. **Verify MCP keys in opencode.json match expected names:**
   ```bash
   jq '.mcp | keys' ~/.config/opencode/opencode.json
   # Expected: ["fetch", "github", "grafana", "memory", "skills-mcp", "wiz"]
   ```

4. **Verify OpenCode supports `--config` flag:**
   ```bash
   /opt/homebrew/bin/opencode --help | grep config
   ```
   If not supported, Phase 7a needs a different approach (env var or symlink swap).

5. **Create a baseline commit** before starting:
   ```bash
   git -C ~/.config/opencode add -A && git commit -m "chore: baseline before Phase 7 dynamic MCP management"
   ```

---

## Testing Plan

### Phase 7a Tests

1. **Default session (no flag):**
   ```bash
   opencode
   # Verify: only memory + skills-mcp in context
   # Ask router: "what MCPs are enabled?" → should list only memory, skills-mcp
   ```

2. **Single MCP flag:**
   ```bash
   opencode --mcps github
   # Verify: github MCP tools appear in tool list
   # Verify: temp config file created in /tmp/
   # Verify: temp config file cleaned up on exit
   ```

3. **Multiple MCPs flag:**
   ```bash
   opencode --mcps github,fetch
   # Verify: both github and fetch MCPs active
   ```

4. **Invalid MCP name:**
   ```bash
   opencode --mcps nonexistent
   # Verify: wrapper prints error and falls back to default
   ```

5. **Concurrent sessions (race condition check):**
   ```bash
   opencode --mcps github &
   opencode --mcps grafana &
   # Verify: each session uses its own temp config (no conflict)
   ```

### Phase 7b Tests

1. **GitHub intent with MCP disabled:**
   - Ask: "Show me open PRs in this repo"
   - Expected: Router warns about disabled `github` MCP, suggests `opencode --mcps github`

2. **GitHub intent with MCP enabled (session started with `--mcps github`):**
   - Ask: "Show me open PRs in this repo"
   - Expected: Router proceeds normally, delegates to specialist

3. **No MCP-requiring intent:**
   - Ask: "What is the capital of France?"
   - Expected: Router answers directly, no MCP warning

---

## Success Criteria

- [ ] Default session uses ≤2 MCPs (memory + skills-mcp)
- [ ] `opencode --mcps github` correctly enables only `github` + defaults
- [ ] No temp config files left behind after session ends
- [ ] Concurrent sessions don't interfere with each other
- [ ] Router warns user when required MCP is disabled (Phase 7b)
- [ ] Token overhead reduction measurable (compare context sizes)
- [ ] Wrapper script `--help` documents the `--mcps` flag
- [ ] AGENTS.md Rule 6.1 documents the new flag

---

## Rollback Plan

If Phase 7a causes issues:

```bash
# 1. Restore wrapper script from backup
cp ~/opencode-backup-20260623/bin/opencode-bmw ~/bin/opencode-bmw
chmod +x ~/bin/opencode-bmw

# 2. Remove any stale temp config files
rm -f /tmp/opencode-session-*.json

# 3. Verify default behavior restored
opencode --version
```

If Phase 7b causes issues:

```bash
# Restore router agent from git
git -C ~/.config/opencode checkout HEAD~1 -- agents/request-orchestrator.md
```

---

## Open Questions

1. **Does OpenCode v1.17.5 support `--config` flag for alternate config file?**
   - If not, alternative: symlink swap (`opencode.json` ↔ `opencode.override.json`)
   - Or: env var override if OpenCode supports `OPENCODE_CONFIG` env var

2. **Does `jq` reliably handle `{env:VAR_NAME}` strings in opencode.json without expanding them?**
   - Test: `jq '.mcp.github.enabled = true' ~/.config/opencode/opencode.json | head -20`
   - These are raw strings — jq should pass them through unchanged

3. **Should `skills-mcp` be disableable via `--no-skills-mcp` flag?**
   - Use case: users who never use TTT discovery want zero MCP overhead for the router
   - Trade-off: kills Priority 4 discovery capability

4. **Should the wrapper script log MCP session choices somewhere?**
   - Similar to token refresh log at `~/Library/Logs/opencode/token-refresh.log`
   - Helps audit which MCPs are being used most → informs which to enable by default

---

## Future Enhancements (Post Phase 7)

- **Auto-detection:** Router reads prior session logs to predict which MCPs are usually needed and pre-warms them
- **MCP profiles:** Named profiles like `opencode --profile security` that enable `github + wiz`
- **Usage analytics:** Track MCP activation frequency to identify candidates for always-on
- **Platform native:** If OpenCode adds per-agent MCP scoping in a future version, migrate to Option C (agent frontmatter declarations)

---

## Context for the Implementing Agent

When you pick this up, here is the full context:

**What exists today:**
- `~/bin/opencode-bmw` — wrapper script that refreshes OAuth2 token before each OpenCode launch
- `~/.config/opencode/opencode.json` — has 6 MCPs: `memory` (enabled), `skills-mcp` (enabled), `fetch`/`github`/`grafana`/`wiz` (all disabled)
- `~/.config/opencode/agents/request-orchestrator.md` — default routing agent with 6-priority decision tree
- Phases 0-6 are complete and committed to `atc-github.azure.cloud.bmw/qte2362/opencode-config`
- Backup at `~/opencode-backup-20260623/` (538M)

**Key architectural constraint:**
OpenCode reads `opencode.json` at **startup only** — changing it during a session has no effect. This is why Phase 7a uses a temp config overlay at launch time (via `--config` flag), not runtime mutation.

**Recommended starting point:**
1. Run the prerequisites checklist above
2. Check if OpenCode supports `--config` flag (this is the critical unknown)
3. If yes: implement Phase 7a wrapper script changes
4. If no: evaluate symlink swap or env var approach, update this doc before proceeding
5. Then implement Phase 7b router awareness
