# Request Orchestrator — Routing Matrix

**Last updated:** 2026-06-23  
**Router agent:** `request-orchestrator`  
**Version:** Phase 4 complete

---

## Purpose

This document defines the complete routing logic for the `request-orchestrator` agent. It serves as a reference for:
- Understanding which agent handles which domain
- Maintaining consistent handoff contracts across agents
- Troubleshooting routing issues
- Planning future agent additions

---

## Routing Decision Tree

The router executes this logic **in order**, stopping at the first match:

| Priority | Condition | Action |
|---|---|---|
| 0 | Request matches an installed prompt workflow | Suggest the prompt. See Prompt Table below. |
| 1 | Request is trivial (single-response) | Answer directly. No delegation. |
| 2 | Request matches a specialist agent domain | Delegate to that agent. See Agent Domain Table below. |
| 3 | An installed skill covers the task | Load skill via `skill` tool. See Installed Skills Reference. |
| 4 | No local match | Run TTT discovery loop (search → inspect → install → apply). |
| 5 | TTT finds nothing | Answer best-effort. Suggest `ttt tui` for manual search. |

---

## Installed Prompts (Priority 0 — Phase 4)

Prompts are full workflow slash commands. The router **suggests** them but does not invoke them — the user must type the slash command.

| Prompt | Purpose | Trigger Keywords |
|---|---|---|
| `/create-pr` | Full end-to-end: commit changes → push → open PR | "create pr", "open pr", "make a pull request", "commit and push", "pr workflow" |
| `/apply-pr-suggestions` | Apply review comments from an existing PR | "apply pr comments", "apply review feedback", "resolve pr suggestions", "address review" |
| `/nice-git-commits` | Reorganize uncommitted changes into atomic commits | "clean up commits", "reorganize commits", "atomic commits", "fix commit history", "better commit messages" |
| `/security-fix` | Autonomous security remediation (GHAS or Wiz) | "fix security findings", "remediate vulnerabilities", "fix ghas", "fix wiz", "security remediation" |
| `/security-explain` | Explain GHAS/Wiz findings without fixing | "explain security findings", "what are these vulnerabilities", "security review", "ghas report" |
| `/bmw-wisdom` | Append BMW-style management wisdom quote | "bmw wisdom", "bmw saying", "management quote" |
| `/beast-mode` | Fully autonomous execution with zero interruptions | "beast mode", "autonomous mode", "stop asking", "just do it", "full autonomy" |
| `/direct` | Bypass routing, answer directly with general agent | "direct mode", "skip routing", "answer directly", "no delegation" |

---

## Agent Domain Table (Priority 2)

| Agent | Domain Keywords | Trigger Conditions | Context to Pass |
|---|---|---|---|
| `oracle-apex-expert` | oracle, apex, plsql, pl/sql, ora-, oracle sql, apex page, apex region, apex plugin, ords | Any Oracle Database, APEX, or PL/SQL question | APEX version, DB version, error messages, page/region IDs, table/view names |
| `uipath-rpa-expert` | uipath, rpa, dispatcher, worker, xaml, bot, automation workflow, orchestrator | UiPath bot development, XAML analysis, RPA process documentation | Bot name, XAML file paths, error logs, process description |
| `jirri-data-analyst` | jirri, cost savings, mb1b, lt01, jirri_cost_savings.py | JIRRI cost-savings calculations, Python data analysis, statistical work | Data file paths, calculation requirements, business rules |
| `presentation-builder` | slides, ppt, pptx, deck, presentation, powerpoint | Any request to create slides or a presentation | Audience, deck purpose, content outline or data to present |
| `aaa-security-fixer` | ghas, codeql, wiz, security findings, vulnerabilities, cve | Security scan remediation, finding fixes, vulnerability analysis | Scan platform (GHAS/Wiz), repo name, finding IDs |
| `agile-master-pi-planning` | pi planning, sprint health, roam, art sync, program increment, agile release train | PI Planning prep/execution, sprint health, backlog readiness | Sprint number, PI number, team capacity, backlog status |
| `agile-master-catalyst-coaching` | coaching, 1:1, catalyst conversation, team coaching, po coaching | Coaching sessions, 1:1 prep, outcome alignment | Coachee role, session goal, team context |
| `dor-agent` | dor, definition of ready, jira story readiness, backlog compliance | DoR automation, Jira field population, backlog governance | Jira project key, Confluence DoR spec URL |

---

## Cross-Agent Handoff Matrix

This table shows **when one specialist agent delegates to another**. The router does not control these — they are peer-to-peer handoffs.

### Oracle APEX Expert → Others

| To Agent | Trigger | What to Pass |
|---|---|---|
| `jirri-data-analyst` | SQL result sets needing statistical analysis or cost calculations | Query results, column definitions, business context |
| `uipath-rpa-expert` | APEX page/workflow needs UiPath automation or bot documentation | APEX version, page IDs, form field names, workflow steps |
| `presentation-builder` | APEX/DB findings or architecture docs → slide deck | Data tables, architecture diagrams, summary bullets; state audience and deck type |
| `aaa-security-fixer` | APEX security review, SQL injection, exposed ORDS endpoints, Oracle CVEs | APEX version, DB version, affected endpoint URLs or PL/SQL procedure names |
| `agile-master-pi-planning` | APEX features need PI backlog, capacity planning, sprint health | Feature list, complexity estimates, team dependencies |
| `agile-master-catalyst-coaching` | Team needs coaching on APEX adoption or tech debt conversations | Team context, challenge, what has already been tried |
| `dor-agent` | APEX user stories need DoR compliance or Jira field population | Jira project key, story IDs, Confluence DoR spec URL |
| `request-orchestrator` | Request is outside Oracle/APEX/SQL domain | State why + user's original request verbatim |

### UiPath RPA Expert → Others

| To Agent | Trigger | What to Pass |
|---|---|---|
| `oracle-apex-expert` | Bot touches Oracle APEX UI or needs Oracle SQL/PL/SQL | APEX version, DB version, page IDs, form field names, table/view names |
| `jirri-data-analyst` | Bot output data needs statistical analysis or Python post-processing | CSV/tabular output, column definitions, business rules |
| `presentation-builder` | Bot architecture, flow diagrams, or run metrics → slide deck | Architecture diagrams, flow summaries, metrics tables; state audience and deck type |
| `aaa-security-fixer` | XAML or config contains hardcoded credentials or secrets | File paths, credential variable names, affected workflow files |
| `agile-master-pi-planning` | RPA development needs PI-level tracking or sprint health | Bot feature list, complexity estimates, team dependencies |
| `agile-master-catalyst-coaching` | RPA team needs coaching on bot adoption or process change | Team context, challenge, what has already been tried |
| `dor-agent` | RPA user stories need DoR compliance check | Jira project key, story IDs, Confluence DoR spec URL |
| `request-orchestrator` | Request is outside UiPath/RPA domain | State why + user's original request verbatim |

### JIRRI Data Analyst → Others

| To Agent | Trigger | What to Pass |
|---|---|---|
| `oracle-apex-expert` | Analysis requires Oracle SQL queries or APEX page data as source | Oracle/APEX version, table/view names, required query output format |
| `uipath-rpa-expert` | Cost savings data needs to be sourced from or delivered into a UiPath bot | Data schema, input/output format, RPA process description |
| `presentation-builder` | Cost savings results, ROI summary, or charts → slide deck | Data tables, summary figures, audience and deck type |
| `agile-master-pi-planning` | JIRRI analysis results inform PI planning decisions | Summary metrics, key findings, team/feature context |
| `agile-master-catalyst-coaching` | Findings reveal process inefficiencies needing team coaching | Key findings, team context, what has already been tried |
| `dor-agent` | Analysis results become Jira stories needing DoR compliance | Jira project key, story IDs, analysis output to use as acceptance criteria |
| `request-orchestrator` | Request is outside data analysis / Python / JIRRI domain | State why + user's original request verbatim |

---

## Installed Skills Reference (Priority 3)

When the router checks for installed skills, it scans `~/.opencode/skills/`. These are the currently installed skills grouped by category:

### Figma / Design
- `figma-use` — MANDATORY before any `use_figma` tool call
- `figma-create-new-file` — Create blank Figma/FigJam file
- `figma-generate-design` — Translate app page/view to Figma
- `figma-generate-diagram` — Create flowchart, architecture, ERD in FigJam
- `figma-implement-design` — Generate production code from Figma design
- `figma-implement-make` — Generate code from Figma Make prototype
- `figma-use-figjam` — FigJam-specific canvas operations
- `canvas-design` — Static visual design (poster, infographic)
- `frontend-design` — Polished HTML/CSS/React prototype

### UX / Review
- `ux-reviewer` — Full UX review (Nielsen heuristics + copy assessment)
- `ux-report-generation` — Formal evaluation report wrapper

### Angular / React (BMW AI4DevOps)
- `ai4do-fe-angular` — Angular + NgRx + NX + Vitest + Playwright
- `ai4do-fe-react` — React + TypeScript BMW standards
- `ai4do-fe-code-review` — Frontend code review checklist
- `ai4do-fe-accessibility` — WCAG 2.1 AA accessibility audit
- `ace-angular-developer` — Angular code generation + architectural guidance
- `ace-angular-core-components` — Alphabet core-components UI library
- `ace-angular-core-components-form` — Alphabet form inputs
- `ace-angular-core-theme` — Alphabet core-theme utility classes
- `ace-angular-translations` — Common-first i18n policy enforcement
- `ace-angular-major-version-migration-preparation` — Plan Angular upgrade
- `ace-angular-major-version-migration-execution` — Execute Angular upgrade

### Git / GitHub
- `git-commit-reorganization` — Clean up messy commit history
- `pr-creation` — Create well-structured PRs via gh CLI
- `pr-overview` — PR status overview with CI checks
- `jira-adhoc-story` — Create Jira tickets for ad-hoc work
- `bmw-oss-dual-repo-workflow` — BMW internal mirror + public GitHub PR flow

### Code Quality
- `python-data-quality` — Python data science code review
- `embedded-review` — Embedded C/C++ code review

### Presentations / Reports
- `bmw-pptx` — Create/read/edit PowerPoint with BMW CI
- `bmw-slides` — Markdown → PPTX or HTML slides
- `bmw-ppt-creator` — Brand-consistent PPT styling
- `bmw-github-pages` — BMW-styled static sites with GitHub Pages

### Video
- `clipjoint` — Main orchestration: text → MP4 video
- `manim-renderer` — Generate Manim animation code
- `storyboard-planner` — Visual style guide for multi-segment videos
- `tts` — BMW Audio TTS narration
- `audio-generation` — TTS segment synthesis
- `transcription` — Narration transcription + word timings
- `text-generation` — BMW LLM API text generation
- `image-generator` — **Dual-mode**: standalone PNG/MP4 generation from a prompt **OR** pipeline sub-skill (AI image → silent MP4 clip for clipjoint segments with `visual_type: "image"`)
- `video-merger` — Merge clips + TTS + subtitles

### Image Generation (standalone)

When a user asks to generate, create, or make an image/picture without a video context,
route to **`image-generator`** at P3 (installed skill). Do **not** route to `canvas-design`
unless the user specifically wants a poster, infographic, or design artifact with
layout/typography work.

| Trigger | Route | Notes |
|---|---|---|
| "generate an image of X" | `image-generator` standalone | PNG output by default |
| "create a picture of X" | `image-generator` standalone | PNG output by default |
| "make an AI image" | `image-generator` standalone | PNG output by default |
| "generate image + turn it into a clip" | `image-generator` standalone + `--video` flag | MP4 output |
| "create a poster / infographic" | `canvas-design` | Layout + typography work |
| "create a video with images" | `clipjoint` → `image-generator` (pipeline) | Full video pipeline |

### Web Research
- `web-research` — Brave Search single-query research
- `deep-web-research` — Parallel research lanes + synthesis

### Office 365
- `morning-briefing` — Office 365 agenda + email summary
- `office365-graph-secure` — Microsoft Graph access (token-file secure)

### TTT Management
- `ttt` — Discover and install skills/prompts/agents from TTT
- `mcp-setup` — MCP server configuration reference
- `dor-jira-updater` — Populate Jira fields for DoR compliance
- `bmw-wisdom` — Append BMW management wisdom quote

### Utilities
- `file-handoff` — Move large context via temp files
- `customize-opencode` — Edit OpenCode config (agents, skills, MCPs)

---

## TTT Discovery Loop (Priority 4)

When no local skill or agent matches, the router uses a **two-layer discovery stack**:

### Discovery Stack

| Layer | Method | When to Use |
|---|---|---|
| 1 (Primary) | Skills MCP tools | Always try first — real-time, structured JSON, no CLI overhead |
| 2 (Fallback) | `ttt` CLI | MCP unavailable or returns errors |

---

### Layer 1: Skills MCP Discovery (Primary — Phase 3+)

**Step 1: Search the catalog**
Use the `skills-mcp_list_skills` tool:
```
skills-mcp_list_skills(q="<intent keywords>", page_size=10)
```
Returns structured JSON with name, namespace, description, tags, version.

**Step 2: Inspect top candidates**
For each promising result:
```
skills-mcp_get_skill(name="<namespace/name>")
```

**Step 3: Confidence-based install (Option C)**
- **HIGH confidence (≥0.8):** Description closely matches, tags align, no ambiguity
  - Auto-install via `ttt` CLI: `ttt skills download <name> --agent-type opencode --global`
  - *(Note: Use `ttt` CLI for install, not `skills-mcp_download_skill`, to maintain IT audit trail)*
  - Tell user: "I found and installed `<namespace/name>` — applying it now."
  - Load skill via `skill` tool and proceed

- **LOW confidence (<0.8):** Partial match, ambiguous, or multiple candidates
  - Present top 2-3 candidates with descriptions
  - Ask user to confirm
  - Install via `ttt skills download` after confirmation, then load and apply

**Step 4: Verify and apply**
```bash
ls ~/.opencode/skills/<skill-name>/
```
If directory exists → load skill via `skill` tool. If not → report error.

---

### Layer 2: `ttt` CLI Discovery (Fallback)

**Only use if Skills MCP is unavailable or returns errors.**

**Step 1: Search catalog**
```bash
ttt search "<extracted intent keywords>" --type skill
```

**Step 2: Inspect candidates**
```bash
ttt skills get <namespace/name>
```

**Step 3: Install and verify** — same as Layer 1 above.

---

### Why MCP is Primary

- **Structured output:** JSON responses are easier to parse and score
- **No subprocess overhead:** Direct tool calls are faster than CLI spawning
- **Real-time catalog:** Always current, no cache staleness
- **Same auth:** Uses the same `TTT_PAT` credential

**Why `ttt` CLI is still used for install:**
- Maintains `~/.ttt/installations.json` audit trail (IT requirement)
- Handles symlink creation automatically
- Tracks versioning and updates

---

## Out-of-Scope / Dead Ends

### `token-tom`
**Status:** Does not exist in OpenCode (Copilot-only agent).  
**Previous behavior:** Specialist agents referenced it for out-of-domain requests.  
**Current behavior (Phase 2+):** Specialist agents return to `request-orchestrator` instead.

### Plugin Agents
**Location:** `~/.opencode/plugins/*/agents/` (e.g., `clipjoint`, `morning-briefing`, `angular`, `react`)  
**Status:** Not directly invocable by router — not symlinked into standard agent directories.  
**Workaround:** Use the associated skill instead (e.g., use `clipjoint` skill, not `clipjoint` agent).

### Built-in Mode Agents
**Agents:** `build`, `plan`, `explore`, `general`  
**Behavior:** User explicitly selects these in TUI — they bypass the router entirely by design.

---

## Maintenance Notes

### When to Update This Document
- New specialist agent added → update Agent Domain Table and Cross-Agent Handoff Matrix
- New skill installed globally → update Installed Skills Reference (or reference `ttt skills installed`)
- New prompt installed → update Installed Prompts table (or reference `ttt prompts installed`)
- Routing logic changes → update Routing Decision Tree
- New MCP capability impacts routing → add note in relevant section

### Cross-File Dependencies
- `request-orchestrator.md` — Router agent instructions (must stay in sync with this doc)
- `oracle-apex-expert.md`, `uipath-rpa-expert.md`, `jirri-data-analyst.md` — Specialist agents (handoff tables must match)
- `AGENTS.md` — Global policy (all routing must comply with Rules 1-7)

---

## Revision History

| Date | Phase | Change |
|---|---|---|
| 2026-06-23 | Phase 2 | Initial routing matrix created; `token-tom` references removed from specialist agents |
| 2026-06-23 | Phase 3 | Enabled `skills-mcp` MCP; updated discovery procedure to use MCP tools as primary method |
| 2026-06-23 | Phase 4 | Added prompt awareness (Priority 0); router now suggests installed slash commands proactively |
| 2026-06-24 | Phase 4.1 | `image-generator` upgraded to dual-mode (standalone + pipeline); routing table added for standalone image generation |
