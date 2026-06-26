# Request Orchestrator — Final Deployment State

**Date:** 2026-06-23  
**Baseline commit:** `b84172f` (adjusting readme)  
**Backup location:** `~/opencode-backup-20260623/` (538M snapshot)  
**Status:** ✅ **COMPLETE** — Phases 0-6 deployed and tested

---

## What This Change Does

Adds a **default routing agent** (`request-orchestrator`) that automatically routes OpenCode requests to the best specialist agent, skill, or discovers new capabilities via `ttt` when no local match exists.

**User-facing behavior:**
- All new OpenCode sessions start with the router agent by default
- The router detects intent and delegates to specialist agents (Oracle, UiPath, JIRRI, presentation-builder, etc.)
- The router proactively suggests installed slash commands (prompts) when they match the request (e.g. "commit and open PR" → suggests `/create-pr`)
- For unknown tasks, the router searches the TTT skills catalog and offers to install + apply relevant skills
- Users can bypass routing with the `/direct` slash command for simple tasks

**Routing priority (6 levels):**
0. **Installed prompts** — suggests 8 slash commands when matching intent detected
1. **Trivial questions** — answers directly without delegation
2. **Specialist agents** — routes to 8 domain experts (3 custom + 5 TTT agents)
3. **Installed skills** — loads from 52 installed skills in `~/.opencode/skills/`
4. **TTT discovery** — searches catalog (313 skills, 21 prompts, 44 agents) via `skills-mcp` MCP or `ttt` CLI fallback
5. **Best-effort** — attempts task directly when no match found

---

## All Files Changed (Phases 0-6)

### Phase 0: Backup & Documentation
| File | Change |
|---|---|
| `~/opencode-backup-20260623/` | **CREATE** — 538M full backup snapshot |
| `~/.config/opencode/CHANGE-SCOPE.md` | **CREATE** — This file |
| `~/.config/opencode/RESTORE-CHECKLIST.md` | **CREATE** — Rollback instructions |

### Phase 1: Router Agent + `/direct` Prompt
| File | Change |
|---|---|
| `~/.config/opencode/agents/request-orchestrator.md` | **CREATE** — Default routing agent with 6-priority decision tree |
| `~/.opencode/prompts/direct.prompt.md` | **CREATE** — `/direct` bypass slash command (version fix applied) |
| `~/.config/opencode/opencode.json` | **EDIT** — add `default_agent: request-orchestrator`, add `skills-mcp` MCP (disabled), fix provider block |
| `~/.config/opencode/.env` | **EDIT** — add `TTT_PAT` placeholder |

### Phase 2: Remove `token-tom` References
| File | Change |
|---|---|
| `~/.config/opencode/agents/oracle-apex-expert.md` | **EDIT** — replace `token-tom` with `request-orchestrator` in fallback section |
| `~/.config/opencode/agents/uipath-rpa-expert.md` | **EDIT** — replace `token-tom` with `request-orchestrator` in fallback section |
| `~/.config/opencode/agents/jirri-data-analyst.md` | **EDIT** — replace `token-tom` with `request-orchestrator` in fallback section |
| `~/.config/opencode/routing-matrix.md` | **CREATE** — Complete routing documentation (domains, handoffs, discovery stack, prompts table) |

### Phase 3: Enable `skills-mcp` MCP
| File | Change |
|---|---|
| `~/.config/opencode/opencode.json` | **EDIT** — set `skills-mcp` `enabled: true` |
| `~/.config/opencode/agents/request-orchestrator.md` | **EDIT** — add MCP-aware discovery (Priority 4: `skills-mcp` tools primary, `ttt` CLI fallback) |

### Phase 4: Prompt Awareness
| File | Change |
|---|---|
| `~/.config/opencode/agents/request-orchestrator.md` | **EDIT** — add Priority 0 (installed prompts awareness) with 8 prompts table |

### Phase 6: Hardening
| File | Change |
|---|---|
| `~/.config/opencode/AGENTS.md` | **EDIT** — update Rule 2 skills list (52 skills, organized by category), add `skills-mcp` to Rule 5 pre-approved MCPs |
| `~/.config/opencode/CHANGE-SCOPE.md` | **EDIT** — update to reflect final deployment state |

**Git commits:** `2b2230f`, `5abf12a`, `51f3a16`, `c3fc6a0`, `62c25b8`, `d8152d1`

---

## What This Does NOT Touch

- ✅ Specialist agents (`oracle-apex-expert`, `uipath-rpa-expert`, `jirri-data-analyst`) — only updated handoff fallback in Phase 2
- ❌ No changes to installed skills in `~/.opencode/skills/` (52 skills unchanged)
- ✅ MCP state changes: `skills-mcp` enabled in Phase 3 (was disabled in Phase 1)
- ❌ No changes to runtime plugins (`config-backup.ts` untouched)
- ❌ No changes to TTT skills bundles in `~/.opencode/plugins/` (6 plugins: `agent-productivity`, `ai4devops-frontend-development`, `clipjoint`, `office365`, `presentations`, `web-research`)
- ❌ No changes to `~/.copilot/` Copilot agents (3 agents: `oracle-apex-expert`, `uipath-rpa-expert`, `jirri-data-analyst`)
- ❌ No changes to TTT agents in `~/.opencode/agents/` (5 agents: `aaa-security-fixer`, `agile-master-catalyst-coaching`, `agile-master-pi-planning`, `dor-agent`, `presentation-builder`)
- ❌ No credential changes except adding `TTT_PAT` placeholder to `.env` (Phase 1)

---

## Safety Constraints Enforced

1. **IT validation requirement:** All new skills/agents/prompts must come from `ttt` CLI or `skills-mcp` MCP — no arbitrary downloads
2. **Router discovery loop:** When searching TTT catalog, the router uses confidence scoring (option C):
   - **High confidence (≥0.8):** Auto-install and inform user
   - **Low confidence (<0.8):** Present candidates, ask user to confirm before installing
3. **MCP status (updated Phase 3):** `skills-mcp` is now `"enabled": true` after Phase 3 completion
   - **Auth requirement:** First use requires manual authentication — OpenCode will prompt for it
   - Uses `TTT_PAT` from `.env` for Bearer token auth

---

## Testing Results

### Phase 1 Smoke Test
1. ✅ OpenCode starts without errors
2. ✅ Router agent appears in TUI agent list (`@request-orchestrator`)
3. ✅ Simple request goes to router → answers directly (e.g. "What is 2+2?")
4. ✅ Oracle/APEX request goes to router → delegates to `oracle-apex-expert`
5. ✅ `/direct` slash command works and bypasses router
6. ✅ Git status shows only expected files changed

### Phase 3 MCP Test
- ✅ `skills-mcp` enabled successfully
- ✅ MCP auth completed (manual auth prompt on first use)
- ✅ Fallback to `ttt` CLI works when MCP unavailable
- ⚠️ MCP semantic search returns 0 results (server-side issue) — keyword mode works

### Phase 4 Prompt Awareness Test
- ✅ Router recognized "commit and open PR" → suggested `/create-pr`
- ✅ Prompt explanation accurate
- ✅ User instruction clear ("type /create-pr")

---

## Rollback Plan

See `RESTORE-CHECKLIST.md` for step-by-step rollback instructions.

Quick rollback:
```bash
# 1. Restore from backup (538M snapshot includes all config)
rsync -a --delete ~/opencode-backup-20260623/config/ ~/.config/opencode/

# 2. Remove new files
rm -f ~/.config/opencode/agents/request-orchestrator.md
rm -f ~/.opencode/prompts/direct.prompt.md
rm -f ~/.config/opencode/routing-matrix.md

# 3. Restore specialist agent fallbacks (revert token-tom removal)
git checkout b84172f -- ~/.config/opencode/agents/oracle-apex-expert.md
git checkout b84172f -- ~/.config/opencode/agents/uipath-rpa-expert.md
git checkout b84172f -- ~/.config/opencode/agents/jirri-data-analyst.md

# 4. Restart OpenCode
```

---

## Deployment Summary

**Total deployment time:** ~2 hours (2026-06-23)  
**Total commits:** 6 (`2b2230f`, `5abf12a`, `51f3a16`, `c3fc6a0`, `62c25b8`, `d8152d1`)  
**Backup size:** 538M  
**Files created:** 3 (router agent, `/direct` prompt, routing-matrix.md)  
**Files modified:** 7 (opencode.json, .env, AGENTS.md, CHANGE-SCOPE.md, 3 specialist agents)  
**Phases completed:** 6 (backup, router, token-tom removal, MCP enable, prompt awareness, hardening)  

**Key capabilities added:**
- ✅ Default routing layer with 6-priority decision tree
- ✅ Automatic discovery of TTT catalog (313 skills, 21 prompts, 44 agents)
- ✅ Prompt awareness (suggests 8 installed slash commands)
- ✅ Two-layer discovery stack (`skills-mcp` MCP primary, `ttt` CLI fallback)
- ✅ Confidence-based install workflow (HIGH ≥0.8 auto-install, LOW <0.8 ask user)
- ✅ `/direct` bypass for simple tasks

**Current state:**
- Router is default agent (`default_agent: request-orchestrator` in opencode.json)
- `skills-mcp` MCP enabled and authenticated
- 8 specialist agents remain functional (3 custom + 5 TTT)
- 52 skills installed and discoverable
- 8 prompts available via slash commands
- AGENTS.md updated with current inventory

**Next steps (optional):**
- Monitor router performance in production use
- Tune confidence thresholds based on user feedback
- Add more specialist agents as domains emerge
- Expand prompt library for common workflows

---

## README Sync Requirement (All Future Enhancements)

> **This step is MANDATORY before any `git push` for a system enhancement.**

Every enhancement phase must verify that `README.md` reflects the new state before committing. The README is the onboarding document for new BMW team members — it must stay current.

### README sync checklist (run before final commit)

For each new or changed capability, verify the README covers it:

| What changed | README section to check/update |
|---|---|
| New skill installed | `## Skills Library` — add row with skill name, purpose, install command |
| New slash command / prompt | `## Slash Commands (Prompts)` — add row |
| New custom agent | `## Custom Agents` — add row |
| New MCP enabled/added | `## MCP Servers` — update enabled/disabled status |
| New model available | `## Models Available` — add row |
| Auth / startup change | `## Troubleshooting` and `## Architecture` sections |
| New config file | `## Configuration Files` — add row |
| Performance improvement | `## Performance Metrics` — update numbers |

### How to do the check

```bash
# 1. Diff your changes to see what's new
git diff --stat HEAD

# 2. Open the README and scan the relevant sections
# (use the table above to know which sections to check)

# 3. Update any stale or missing entries
# Edit README.md directly

# 4. Stage README.md with your other changes
git add README.md

# 5. Include README changes in the same commit as the enhancement
# (keeps the git log coherent — one commit = one feature + its docs)
```

### Commit message convention

When README changes are part of an enhancement commit:
```
feat: add <capability> with README sync

- <what the feature does>
- README: updated Skills Library / Slash Commands / etc.
```

When README is updated standalone (catch-up):
```
docs: sync README with current system state
```
