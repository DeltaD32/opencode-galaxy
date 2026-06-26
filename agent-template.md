---
name: your-agent-name
description: "One sentence describing what this agent does AND when to trigger it. Front-load keywords the user is likely to say. USE FOR: trigger phrase 1, trigger phrase 2."
model: llm-api/claude-sonnet-4-6
mode: subagent
---

<!--
  SECURITY CHECKLIST — read before saving this file
  ──────────────────────────────────────────────────
  1. MODEL: must be llm-api/... or ollama/... only.
     Allowed values:
       llm-api/claude-sonnet-4-6   (default, recommended)
       llm-api/claude-sonnet-4-5
       llm-api/claude-haiku-4-5
       llm-api/claude-sonnet-4
       llm-api/gpt-5.1 / gpt-5.2 / gpt-5.4
       llm-api/gpt-4o / gpt-4o-mini
       llm-api/o3-mini / o4-mini
       llm-api/gemini-3.5-flash / gemini-3.1-flash-lite / gemini-3.1-pro
       ollama/<any-locally-served-model>

  2. MODE: set correctly or the routing architecture breaks.
       mode: subagent   — specialist agents invoked by the orchestrator or @mention (DEFAULT for new agents)
       mode: primary    — user-facing agents selectable via Tab (ONLY request-orchestrator uses this)
       mode: all        — visible as both (rarely needed)

  3. SKILLS: only reference skills installed in ~/.opencode/skills/
     Run `ls ~/.opencode/skills/` to see all currently installed skills.
     As of 2026-06-25 (58 skills total):

     Figma / Design:
       figma-use, figma-create-new-file, figma-generate-design, figma-generate-diagram
       figma-implement-design, figma-implement-make, figma-use-figjam
       canvas-design, frontend-design

     UX / Review:
       ux-reviewer, ux-report-generation

     Angular / React (BMW AI4DevOps):
       ai4do-fe-angular, ai4do-fe-react, ai4do-fe-code-review, ai4do-fe-accessibility
       ace-angular-developer, ace-angular-core-components, ace-angular-core-components-form
       ace-angular-core-theme, ace-angular-translations
       ace-angular-major-version-migration-preparation
       ace-angular-major-version-migration-execution

     Git / GitHub:
       git-commit-reorganization, pr-creation, pr-overview
       jira-adhoc-story, bmw-oss-dual-repo-workflow, gh-cli

     Code Quality:
       python-data-quality, embedded-review

     Presentations / Reports:
       bmw-pptx, bmw-slides, bmw-ppt-creator, bmw-github-pages, ppt-style-registry

     Video:
       clipjoint, manim-renderer, storyboard-planner, tts, audio-generation
       transcription, text-generation, image-generator, video-merger

     Agentic:
       bmw-tool-agent, routing-cache

     RAG / Semantic Search:
       rag, pdf-chat, gaia-tools

     Web Research:
       web-research, deep-web-research

     Office 365:
       morning-briefing, office365-graph-secure

     Agent Productivity (from ad/agent-productivity plugin):
       feature-contract, prompt-enhancement, session-analysis
       skill-execution-footprint, strategic-thinking

     TTT Management / Utilities:
       ttt, mcp-setup, dor-jira-updater, bmw-wisdom, file-handoff

     To add a new skill before referencing it:
       ttt skills install <namespace/name> --agent-type opencode --global
     Then verify: ls ~/.opencode/skills/

  4. CREDENTIALS: never put raw tokens or keys in this file.
     Store secrets in ~/.config/opencode/.env and reference as {env:VAR_NAME}

  5. LOCATION: save this file to ~/.config/opencode/agents/<your-agent-name>.md

  6. MCPs: do not add MCP entries to opencode.json manually.
     Use: ttt-mcp-add <namespace/name>

     Currently enabled MCPs in opencode.json:
       memory          — local, knowledge graph (pre-approved exception)
       skills-mcp      — remote, TTT Skills catalog (Phase 3, OAuth auto-refresh)

     Currently disabled MCPs (enable via ttt-mcp-add or opencode.json):
       jira-atc        — remote, Jira @ atc.bmwgroup.net
       confluence-atc  — remote, Confluence @ atc.bmwgroup.net
       density-mcp     — remote, BMW Density design system
       fetch           — local (dx/fetch-mcp), web fetch via BMW npm registry
       github          — local (dx/github-mcp), GitHub @ atc-github.azure.cloud.bmw
       grafana         — local (dx/grafana-mcp), Grafana dashboards/monitoring
       wiz             — remote (dx/wiz-mcp), Wiz cloud security (OAuth)
       playwright      — local (dx/playwright-mcp), browser automation
-->

# Agent Title

One paragraph describing the agent's purpose, expertise, and approach.

## Core Behaviour

- Bullet point 1 — what this agent always does
- Bullet point 2 — how it approaches problems
- Bullet point 3 — what it never does

## When to Use

Describe the specific scenarios and trigger phrases that should activate this agent.

## Constraints

- List any hard limits on what this agent will or won't do
- Reference any skills it uses (must be from the approved list above)
- Note any external tools or MCPs it depends on
