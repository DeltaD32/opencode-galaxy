# OpenCode BMW Auth Monitoring Guide

## 24-Hour Validation Plan

Test scenarios to verify auto-refresh system works over time:

### Immediate Tests (✓ Completed)

| Test | Result | Notes |
|------|--------|-------|
| Current shell launch | ✓ PASS | Token refresh + OpenCode launch successful |
| Unset env vars | ✓ PASS | Wrapper re-exports from Keychain |
| Model format | ✓ PASS | llm-api/claude-sonnet-4-5 works |
| Config validation | ✓ PASS | JSON valid, {env:...} pattern active |

### Ongoing Monitoring (Next 24 Hours)

| Time Checkpoint | Test | Command | Expected Result |
|-----------------|------|---------|-----------------|
| Every 2 hours | New terminal session | `opencode run "test"` | No hangs, <5s response |
| T+3h | After token would expire | `opencode --version` | Wrapper refreshes automatically |
| T+24h | Multiple expirations | Check wrapper always refreshes | No manual intervention needed |

### Monitoring Commands

**Check token age in Keychain:**
```bash
security find-generic-password -s com.bmw.opencode -a llm_api_bearer_token -g 2>&1 | grep "mdat"
```

**Verify wrapper is being used:**
```bash
type opencode
# Should show: opencode is an alias for /Users/QTE2362/bin/opencode-bmw
```

**Test token validity manually:**
```bash
TOKEN=$(security find-generic-password -s com.bmw.opencode -a llm_api_bearer_token -w)
curl -s -w "%{http_code}" -o /dev/null \
  -H "Authorization: Bearer $TOKEN" \
  -H "x-apikey: $(security find-generic-password -s com.bmw.opencode -a llm_api_key -w)" \
  https://api.gcp.cloud.bmw/llmapi/v1/models
# Should return: 200
```

**If cron configured, check refresh logs:**
```bash
tail -20 ~/Library/Logs/opencode/token-refresh.log
```

## Success Criteria

After 24 hours, all of these must be true:

- [ ] No authentication hangs in any OpenCode session
- [ ] Token in Keychain is never older than 2 hours (or 90 min if cron enabled)
- [ ] Wrapper executes on every `opencode` command invocation
- [ ] Works across terminal emulators (iTerm, Terminal.app, VSCode)
- [ ] Works after VPN disconnect → reconnect cycle

## Troubleshooting Quick Reference

### Symptom: "Token refresh failed" warning
**Cause:** VPN disconnected or OAuth2 endpoint unreachable  
**Fix:**
1. Check VPN: `scutil --nc list | grep Connected`
2. Test manually: `bmw-refresh`
3. If persistent, check corporate network/firewall

### Symptom: OpenCode hangs despite wrapper
**Cause:** Config reverted to hardcoded values  
**Fix:**
```bash
# Verify {env:...} pattern still active
grep '{env:LLM_API_BEARER_TOKEN}' ~/.config/opencode/opencode.json

# If not found, restore from backup
cp ~/.config/opencode/opencode.json.hardcoded-backup-* ~/.config/opencode/opencode.json
# Then manually re-apply {env:...} pattern (see AGENTS.md Rule 6.1)
```

### Symptom: "Could not load LLM_API_BEARER_TOKEN"
**Cause:** Keychain locked or empty  
**Fix:**
```bash
# Re-initialize token
bmw-refresh

# Verify stored
security find-generic-password -s com.bmw.opencode -a llm_api_bearer_token -w
```

### Symptom: Alias not working in new terminals
**Cause:** .zshrc not sourced or alias removed  
**Fix:**
```bash
# Check if alias exists
grep "alias opencode" ~/.zshrc

# If missing, re-add:
echo 'alias opencode="$HOME/bin/opencode-bmw"' >> ~/.zshrc
source ~/.zshrc
```

## Rollback (Emergency)

If system is completely broken and you need OpenCode NOW:

```bash
# 1-minute emergency fix (restores hardcoded tokens)
cp ~/.config/opencode/opencode.json.hardcoded-backup-20260623-103126 \
   ~/.config/opencode/opencode.json

unalias opencode 2>/dev/null
/opt/homebrew/bin/opencode
```

**Warning:** Emergency rollback uses stale tokens. Run `bmw-refresh` immediately after successful launch, then re-implement auth system when possible.

---

**Implementation Date:** 2026-06-23  
**Last Validated:** 2026-06-23 10:35 UTC  
**System Status:** ✓ OPERATIONAL
