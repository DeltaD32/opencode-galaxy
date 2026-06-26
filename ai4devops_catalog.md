# Ai4DevOps Offerings Catalog

> Sourced from Confluence space AOS, root page ID: 7892685836
> Last updated: 2026-06-19
> Base URL: https://atc.bmwgroup.net/confluence/rest/api/content/

---

## Skills Marketplace

- **Page ID:** 7983726857
- **Type:** Platform / Catalog
- **Description:** Prebuilt AI skills catalog, searchable by name, tag, or description. CLI-integrated via the `ttt` CLI. Features usage metrics and a publish/share model for team distribution.
- **Access:** Web dashboard or `ttt` CLI

---

## Agents, Skills & Actions

### FastAPI Backend Developer Agent

- **Page ID:** 8013819397
- **Tiny URL:** https://atc.bmwgroup.net/confluence/x/BS6p3QE
- **Type:** Agent + Skills bundle
- **Description:** AI-assisted automation agent for backend service development. Streamlines FastAPI backend development within AI4DevOps.

### Front-End Developer Agent

- **Page ID:** 8219664843
- **Tiny URL:** https://atc.bmwgroup.net/confluence/x/yyHu6QE
- **Type:** Copilot Agent Plugin
- **Description:** BMW-aware Angular and React development agent for GitHub Copilot. Catches framework misuse, enforces accessibility, applies BMW conventions.

### ClipJoint Video Maker Agent

- **Page ID:** 8219684077
- **Tiny URL:** https://atc.bmwgroup.net/confluence/x/7Wzu6QE
- **Type:** Copilot Agent Plugin
- **Description:** Full video production pipeline driven from a single conversation in VS Code. Features: structured scripting, TTS narration, Manim animations, AI imagery, subtitles, final assembly.
- **Local installation:** `/Users/QTE2362/.opencode/plugins/clipjoint/`

### Agent Skill Builder

- **Page ID:** 8087853264
- **Tiny URL:** https://atc.bmwgroup.net/confluence/x/0NgS4gE
- **Type:** Agent
- **Description:** Turns workflow descriptions into reusable agent skills and documentation. For end users and platform teams.

### FastMCP Agent and Plugin Server

- **Page ID:** 8219683983
- **Tiny URL:** https://atc.bmwgroup.net/confluence/x/j2zu6QE
- **Type:** Template / Agent
- **Description:** Template for rapidly building MCP servers using the FastMCP framework.

### AgentSkill Eval Plugin

- **Page ID:** 8382912539
- **Tiny URL:** https://atc.bmwgroup.net/confluence/x/Gxip8wE
- **Type:** Plugin
- **Description:** Write, validate, run, and iterate eval suites against targets. Supports: installed skills, plugin agents, plugin-agent-plus-skill combos, and subprocess commands.

---

## GitHub Actions

### Sonarqube Autofix GitHub Action

- **Page ID:** 8079815471
- **Tiny URL:** https://atc.bmwgroup.net/confluence/x/LzOY4QE
- **Type:** GitHub Action (reusable composite)
- **Description:** Scans code with SonarQube and lets GitHub Copilot fix issues automatically.

### Jira Xray Test Sync GitHub Action

- **Page ID:** 8079816200
- **Tiny URL:** https://atc.bmwgroup.net/confluence/x/CDaY4QE
- **Type:** GitHub Action
- **Description:** Automatically runs team tests and syncs results directly to Jira Xray.

### Document Generator Action

- **Page ID:** 8219683633
- **Tiny URL:** https://atc.bmwgroup.net/confluence/x/MWvu6QE
- **Type:** GitHub Action
- **Description:** Uses Copilot coding agent for automatic documentation. Creates a GitHub issue with embedded skill instructions, assigns to Copilot agent, and the agent produces documentation as a pull request.

---

## Copilot Skills

### SonarQube Auto Fix Skill

- **Page ID:** 8079815339
- **Tiny URL:** https://atc.bmwgroup.net/confluence/x/qzKY4QE
- **Type:** Copilot Skill
- **Description:** AI-assisted code quality enforcement. Integrates with SonarQube findings in PRs.

### doc-generator Skill

- **Page ID:** 8135786920
- **Tiny URL:** https://atc.bmwgroup.net/confluence/x/qEHu5AE
- **Type:** Copilot Skill
- **Description:** Generates high-quality structured developer documentation. Introspects codebase and applies the Diataxis framework.

---

## Toolkits

### Repository Migration Toolkit

- **Tiny URL:** https://atc.bmwgroup.net/confluence/x/wUHu5AE
- **Type:** Toolkit / GitHub Action
- **Description:** Automates migration of repositories between GitHub Enterprise instances. Preserves full Git history, settings, and metadata.

---

## GAIA Browser Plugin Features

> **Prerequisite for all features below:** Install the GAIA Browser Plugin from https://gaia.bmwgroup.net/public/browser-extension/index.html (disable JoyCode plugin first).

### GAIA Browser Plugin

- **Page ID:** 7956310494
- **Type:** Browser Extension
- **Description:** Required base plugin. Enables all GAIA-powered browser features below.

### Jira Assistant

- **Page ID:** 8162022741
- **Type:** GAIA Browser Plugin Feature
- **Description:** AI-powered Jira ticket creation, acceptance criteria, and test case generation. Requires: GAIA plugin + Jira PAT.

### Confluence Assistant

- **Page ID:** 8344743201
- **Type:** GAIA Browser Plugin Feature
- **Description:** "Chat With Page" feature on ATC/CodeCraft Confluence. Requires: Jira Assistant prerequisites.

### GitHub PR Code Review

- **Page ID:** 7956310331
- **Type:** GAIA Browser Plugin Feature
- **Description:** AI code review on GitHub pull requests. Requires: GAIA plugin + GitHub PAT + Jira PAT.

### Test Recorder

- **Page ID:** 7956310423
- **Type:** GAIA Browser Plugin Feature
- **Description:** Records browser actions and generates Gherkin code.

---

## Apps

### Release Track

- **Page ID:** 7956310383
- **Type:** Application (SCP.Apps)
- **Description:** App for planning, managing, and publishing releases. Integrates Jira, GitHub, and Confluence. 5-step release workflow.
- **Access:** SCP.Apps

---

## Notes

- All offerings are accessible to BMW employees with appropriate PAT/API access.
- The `ttt` CLI is the primary interface for Skills Marketplace: `ttt skills search <query>`, `ttt skills install <namespace/name>`.
- ClipJoint requires `BMW_CLIENT_ID`, `BMW_CLIENT_SECRET`, `BMW_API_KEY` in `~/.config/opencode/.env`.
