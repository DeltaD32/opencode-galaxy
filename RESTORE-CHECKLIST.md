# Restore Checklist — Request Orchestrator Rollback

**Backup location:** `~/opencode-backup-20260623/`  
**Baseline commit:** `b84172f`

---

## Quick Rollback (1 minute)

If Phase 1 causes immediate issues, run these commands:

```bash
# 1. Restore opencode.json
cp ~/opencode-backup-20260623/config/opencode.json ~/.config/opencode/opencode.json

# 2. Remove new agent and prompt
rm ~/.config/opencode/agents/request-orchestrator.md
rm ~/.opencode/prompts/direct.prompt.md

# 3. Restore .env if TTT_PAT was added
cp ~/opencode-backup-20260623/config/.env ~/.config/opencode/.env

# 4. Verify git status
cd ~/.config/opencode && git status

# 5. Restart OpenCode
# (exit current session and launch new one)
```

**After rollback:** OpenCode will use the global `model` setting with no default agent — standard pre-orchestrator behavior.

---

## Full Restore (complete rollback)

If the entire orchestration project needs to be unwound:

### Step 1: Restore from backup

```bash
# Back up current state first (in case you need to compare)
mv ~/.config/opencode ~/.config/opencode-ROLLBACK-$(date +%Y%m%d-%H%M%S)

# Restore from Phase 0 backup
rsync -av ~/opencode-backup-20260623/config/ ~/.config/opencode/

# Restore .opencode if prompts were changed
rsync -av ~/opencode-backup-20260623/opencode/ ~/.opencode/
```

### Step 2: Verify git state

```bash
cd ~/.config/opencode
git status
# Should show: nothing to commit, working tree clean

git log --oneline -1
# Should show: b84172f adjusting readme
```

### Step 3: Clean up documentation

```bash
# Remove orchestrator docs created during this project
rm ~/.config/opencode/CHANGE-SCOPE.md
rm ~/.config/opencode/RESTORE-CHECKLIST.md
rm ~/.config/opencode/routing-matrix.md 2>/dev/null || true
```

### Step 4: Restart OpenCode

Exit current OpenCode session and launch fresh.

---

## Verification After Restore

✅ OpenCode starts without errors  
✅ No `request-orchestrator` agent in TUI  
✅ `/direct` command does not exist  
✅ `git status` in `~/.config/opencode` is clean  
✅ Specialist agents (`oracle-apex-expert`, `uipath-rpa-expert`, `jirri-data-analyst`) still work

---

## Partial Rollback Scenarios

### Keep router agent, disable as default

```bash
# Edit opencode.json, remove the "default_agent" field
# Router remains available as @request-orchestrator but won't auto-activate
```

### Keep MCP config but disable it

```bash
# Edit opencode.json, set skills-mcp "enabled": false
# (This is the Phase 1 default state anyway)
```

### Re-enable token-tom references (Phase 2 rollback)

If Phase 2 removed `token-tom` handoffs from specialist agents:

```bash
# Restore specialist agents from backup
cp ~/opencode-backup-20260623/config/agents/*.md ~/.config/opencode/agents/
```

---

## Support

If rollback fails or produces unexpected behavior:

1. Check `~/.local/share/opencode/logs/` for error logs
2. Verify file permissions: `ls -la ~/.config/opencode/`
3. Compare current state vs backup: `diff -r ~/.config/opencode ~/opencode-backup-20260623/config/`
4. Nuclear option: delete `~/.config/opencode` and re-run OpenCode first-launch setup

---

## Backup Retention

The Phase 0 backup (`~/opencode-backup-20260623/`) should be kept until:
- All 6 phases are complete and stable for 7+ days, OR
- A newer backup is created and verified

Do not delete until you are confident the orchestrator is stable.
