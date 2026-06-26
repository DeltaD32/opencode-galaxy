# GPT Model Audit — Subagents + Skill Load Cost

Date: 2026-06-26

## Summary

- **Agents audited:** 5 (`~/.config/opencode/agents/*.md`)
- **Agents using `llm-api/gpt-*`:** 0
- **Default model (opencode.json):** `llm-api/claude-sonnet-4-5`
- **Small model (opencode.json):** `llm-api/claude-haiku-4-5`

No sub-agent model switches were made because no agents are configured on GPT models.

## Per-agent report

### Agent: jirri-data-analyst
- Model: `llm-api/claude-sonnet-4-6`
- Skills loaded: none implicitly; references BMW presentation + design skills for handoffs
- Approx skill token cost: N/A (skills are loaded by orchestrator on demand)
- Prompt caching: YES (Claude via anthropic-auto-cache integration)
- Recommendation: keep

### Agent: opencode-dev-expert
- Model: `llm-api/claude-sonnet-4-6`
- Skills loaded: none
- Approx skill token cost: N/A
- Prompt caching: YES
- Recommendation: keep

### Agent: oracle-apex-expert
- Model: `llm-api/claude-sonnet-4-6`
- Skills loaded: none
- Approx skill token cost: N/A
- Prompt caching: YES
- Recommendation: keep

### Agent: uipath-rpa-expert
- Model: `llm-api/claude-sonnet-4-6`
- Skills loaded: none
- Approx skill token cost: N/A
- Prompt caching: YES
- Recommendation: keep

### Agent: request-orchestrator
- Model: `llm-api/claude-sonnet-4-6`
- Skills loaded: routes to skills on demand; does not embed any SKILL.md by default
- Expensive-ish skill loads (order-of-magnitude from SKILL.md bytes/4):
  - `pr-creation` ~2,858 tokens
  - `git-commit-reorganization` ~2,310 tokens
  - `gaia-tools` ~2,266 tokens
  - `web-research` ~1,536 tokens
  - `bmw-tool-agent` ~1,492 tokens
  - `deep-web-research` ~1,013 tokens
  - `gh-cli` ~933 tokens
  - `routing-cache` ~789 tokens
  - `ttt` ~1,286 tokens
- Prompt caching: YES
- Recommendation: keep (Claude cache is a net win given frequent skill/tool usage)

## bmw_advisor.py check — “no prompt caching on GPT”

`~/.config/opencode/skills/bmw-tool-agent/bmw_advisor.py` tracks usage via token counts returned by the API and does **not** currently model prompt-caching differences (e.g. GPT vs Claude) in its cost estimates/summary.

Implication:
- RunStats is accurate for **tokens** but not for **billing nuances** when caching is present/absent.
