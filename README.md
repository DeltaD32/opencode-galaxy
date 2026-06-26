# OpenCode Configuration for BMW Infrastructure

> **⚠️ BMW INTERNAL USE ONLY**  
> This configuration is **exclusively designed for BMW internal infrastructure** and requires access to BMW corporate networks, authentication systems, and internal APIs. It will not work outside the BMW environment.

Enterprise-grade OpenCode configuration optimized for BMW's internal LLM API gateway with automated OAuth2 authentication, a rich library of 58+ skills, 3 custom agents, 8 slash-command prompts, and a self-learning routing system.

---

## Table of Contents

1. [BMW Infrastructure Requirements](#bmw-infrastructure-requirements)
2. [What This Build Does](#what-this-build-does)
3. [Quick Start (TL;DR)](#quick-start-tldr)
4. [Installation](#installation)
5. [Models Available](#models-available)
6. [MCP Servers](#mcp-servers)
7. [Skills Library](#skills-library)
8. [Slash Commands (Prompts)](#slash-commands-prompts)
9. [Custom Agents](#custom-agents)
10. [TTT — Skills Package Manager](#ttt--skills-package-manager)
11. [GAIA Auto-Routing](#gaia-auto-routing)
12. [Self-Learning Routing Cache](#self-learning-routing-cache)
13. [Configuration Files](#configuration-files)
14. [Troubleshooting](#troubleshooting)
15. [Architecture](#architecture)
16. [Security](#security)
17. [Support](#support)

---

## BMW Infrastructure Requirements

### This configuration REQUIRES:

| Component | BMW Infrastructure | Public Alternative |
|-----------|-------------------|-------------------|
| **LLM API Gateway** | `api.gcp.cloud.bmw/llmapi/v1` | ❌ Not accessible |
| **OAuth2 Endpoint** | `auth.bmwgroup.net/auth/oauth2/...` | ❌ BMW-only |
| **Network Access** | BMW VPN or on-site network | ❌ Corporate firewall |
| **GitHub Enterprise** | `atc-github.azure.cloud.bmw` | ❌ Private instance |
| **Credentials** | BMW client ID/secret from IT Security | ❌ Not publicly issued |

**Without BMW infrastructure access, this configuration will not function.**

---

## What This Build Does

This is a **production-grade OpenCode configuration** that:

1. **Connects to BMW's internal LLM API gateway** instead of public Anthropic/OpenAI/Google APIs
2. **Automatically manages OAuth2 authentication** with BMW's machine-to-machine auth system (~2-hour token rotation)
3. **Routes all requests through the Request Orchestrator agent** — a smart router that picks the right skill, agent, or GAIA app automatically
4. **Provides 56+ specialist skills** covering frontend, video generation, presentations, RAG, web research, and more
5. **Integrates with BMW-specific MCP servers** for Jira, Confluence, Grafana, Wiz, and more
6. **Enforces BMW security policies** (no hardcoded secrets, Keychain storage, audit trails)

### Key Differences from Public OpenCode

| Feature | Public OpenCode | BMW Build |
|---------|----------------|-----------|
| **Model Access** | Direct API calls to Anthropic/OpenAI | Proxied through BMW LLM API gateway |
| **Authentication** | API keys in config | OAuth2 with auto-refresh wrapper |
| **Available Models** | Public models only | 14+ models via BMW enterprise licenses |
| **Default Agent** | General assistant | Request Orchestrator (smart router) |
| **Skills System** | None | 58+ skills via TTT package manager |
| **MCP Servers** | Public MCPs from npm | BMW-internal MCPs + vetted public MCPs |
| **Network** | Public internet | BMW corporate network (VPN required) |
| **Startup time** | ~2-5 seconds | ~10 seconds (MCP health checks) |

---

## Platform Support

| Platform | Status | Approach |
|----------|--------|---------|
| **macOS** | ✅ Fully supported | Native — Homebrew, Keychain, zsh wrapper |
| **Windows (WSL2)** | 🚧 In Progress | WSL2 + mirrored networking; wrapper script + auth diagnostic ready; not yet end-to-end tested |
| **Windows (Native)** | 📋 Stretch goal | PowerShell wrapper + Windows Credential Manager; not yet implemented |
| **Linux** | ⚠️ Should work | Similar to WSL2 path; untested against BMW infra |

> **Windows users:** See [`WINDOWS-SETUP.md`](./WINDOWS-SETUP.md) for the full gap analysis,
> implementation plan, and current status. The WSL2 setup guide will be added here once it
> has been tested end-to-end.

---

## Quick Start (TL;DR)

### macOS

```bash
# 1. Install OpenCode
brew install opencode

# 2. Clone this repo
git clone https://atc-github.azure.cloud.bmw/qte2362/opencode-config.git ~/.config/opencode

# 3. Store BMW credentials in macOS Keychain
security add-generic-password -U -s com.bmw.opencode -a llm_api_key -w "YOUR_API_KEY"
security add-generic-password -U -s com.bmw.opencode -a bmw_client_id -w "YOUR_CLIENT_ID"
security add-generic-password -U -s com.bmw.opencode -a bmw_client_secret -w "YOUR_CLIENT_SECRET"

# 4. Make wrapper script executable — symlink replaces Homebrew binary (no alias needed)
chmod +x ~/bin/opencode-bmw
ln -sf ~/bin/opencode-bmw /opt/homebrew/bin/opencode

# 5. Install TTT and test
brew install ttt   # or follow BMW internal install instructions
~/bin/test-opencode-auth && opencode run "hello"

# 6. Install skills (optional — add what you need)
ttt skills install dx/figma-use --agent-type opencode --global
ttt skills install dx/bmw-pptx --agent-type opencode --global
# ...see Skills Library section for the full catalog
```

### Windows (WSL2) — 🚧 In Progress (not yet end-to-end tested)

> Wrapper script and auth diagnostic are ready. Full guide in [`WINDOWS-SETUP.md`](./WINDOWS-SETUP.md).
> WSL2 uses **mirrored networking** — VPN runs on the Windows host and is shared automatically.

```bash
# --- In PowerShell (Windows host) ---
# Install WSL2 with Ubuntu 24.04 (no admin rights — uses ClientRightsNext)
wsl.exe --set-default-version 2
wsl.exe --update --web-download
wsl.exe --install -d Ubuntu-24.04 --web-download

# Configure mirrored networking in WSL Settings:
#   Networking Mode = Mirrored, Automatic Proxy = Off

# --- Inside WSL2 terminal ---
# 1. Install dependencies + proxy
sudo apt update && sudo apt install -y git curl python3 python3-pip

# Add to ~/.profile (proxy via Proxydetox on Windows host):
export http_proxy=http://localhost:3128/ && export https_proxy=http://localhost:3128/
export no_proxy=localhost,127.0.0.1,.bmwgroup.net,.cloud.bmw

# 2. Install OpenCode
curl -fsSL https://opencode.ai/install | bash

# 3. Install uv + TTT (one-time token from skills.bmwgroup.net → Get Started)
curl -LsSf https://astral.sh/uv/install.sh | sh
curl -fsSL 'https://skills.bmwgroup.net/api/v1/install.py?install_token=<TOKEN>' | uv run --no-project -

# 4. Clone this repo
git clone https://atc-github.azure.cloud.bmw/qte2362/opencode-config.git ~/.config/opencode

# 5. Store credentials (.env replaces Keychain)
nano ~/.config/opencode/.env   # add LLM_API_KEY, BMW_CLIENT_ID, BMW_CLIENT_SECRET, TTT_PAT
chmod 600 ~/.config/opencode/.env

# 6. Install the WSL2 wrapper
mkdir -p ~/bin
cp ~/.config/opencode/bin/opencode-bmw-wsl2 ~/bin/opencode-bmw
chmod +x ~/bin/opencode-bmw
echo 'alias opencode="$HOME/bin/opencode-bmw"' >> ~/.bashrc && source ~/.bashrc

# 7. Run auth diagnostic
bash ~/.config/opencode/bin/test-opencode-auth-wsl2
```

---

## Installation

### Prerequisites (BMW Employees — All Platforms)

1. **BMW Corporate Network Access**
   - On-site: Connected to BMW internal network
   - Remote: Active BMW VPN connection
     - **macOS:** `scutil --nc list` should show "Connected"
     - **Windows:** VPN runs on the Windows host; WSL2 shares Windows networking automatically
   - Network must reach `auth.bmwgroup.net` and `api.gcp.cloud.bmw`

2. **BMW OAuth2 Client Credentials**
   - Obtain from BMW IT Security or your team's credential vault
   - Requires: `client_id` and `client_secret` for machine-to-machine authentication
   - Scope: `llmapi` access via `auth.bmwgroup.net/auth/oauth2/realms/root/realms/machine2machine`

3. **BMW LLM API Key**
   - API key for `api.gcp.cloud.bmw/llmapi/v1`
   - Request via BMW IT Service Portal or your platform team

4. **Development Environment**

   | Requirement | macOS | Windows (WSL2) |
   |-------------|-------|---------------|
   | **OpenCode** | `brew install opencode` | `curl -fsSL https://opencode.ai/install \| bash` (inside WSL2) |
   | **Shell** | zsh (default) | bash or zsh inside WSL2 |
   | **Credential storage** | macOS Keychain | `~/.config/opencode/.env` (chmod 600) |
   | **Git** | Xcode tools or `brew install git` | `sudo apt install git` |
   | **gh CLI** | `brew install gh` | `sudo apt install gh` (see [gh docs](https://cli.github.com)) |
   | **Python3** | Pre-installed | `sudo apt install python3` |
   | **TTT CLI** | BMW internal / `brew install ttt` | BMW internal Linux binary |

**If you don't have credentials, contact your BMW IT administrator or Agile Master.**

### Step-by-Step Setup

> Steps marked **`(macOS)`** or **`(WSL2)`** differ between platforms. Unmarked steps are the same on both.

#### Step 1 — Install OpenCode

**macOS:**
```bash
brew install opencode
```

**Windows (WSL2):** Open a WSL2 terminal, then:
```bash
# Install WSL2 first if needed (PowerShell as Admin): wsl --install
curl -fsSL https://opencode.ai/install | bash
```

#### Step 2 — Clone this repository

```bash
# Same on both platforms (run inside WSL2 terminal on Windows)
git clone https://atc-github.azure.cloud.bmw/qte2362/opencode-config.git ~/.config/opencode
```

#### Step 3 — Store credentials

**macOS — Keychain:**
```bash
security add-generic-password -U -s com.bmw.opencode -a llm_api_key -w "YOUR_API_KEY"
security add-generic-password -U -s com.bmw.opencode -a bmw_client_id -w "YOUR_CLIENT_ID"
security add-generic-password -U -s com.bmw.opencode -a bmw_client_secret -w "YOUR_CLIENT_SECRET"
```

**Windows (WSL2) — `.env` file:**
```bash
# Edit the .env file (already exists in the cloned repo as a template)
nano ~/.config/opencode/.env

# Add your credentials:
# LLM_API_KEY=your_api_key_here
# BMW_CLIENT_ID=your_client_id_here
# BMW_CLIENT_SECRET=your_client_secret_here
# TTT_PAT=your_ttt_pat_here

# Lock down permissions (important — treat like a password file)
chmod 600 ~/.config/opencode/.env
```

> **Security note:** On macOS, credentials are encrypted by the OS Keychain. On WSL2, the
> `.env` file relies on filesystem permissions and BitLocker (Windows full-disk encryption)
> for protection. Do not use on shared or unencrypted machines.

#### Step 4 — Set up the wrapper script

**macOS:**
```bash
chmod +x ~/bin/opencode-bmw

# Replace the Homebrew symlink so the wrapper runs in ALL contexts
# (Terminal, Dock, scripts, non-interactive shells — no alias required)
ln -sf ~/bin/opencode-bmw /opt/homebrew/bin/opencode

# Verify the symlink is in place
ls -la /opt/homebrew/bin/opencode
# Expected: lrwxr-xr-x  opencode -> /Users/<you>/bin/opencode-bmw
```

**Windows (WSL2):**
```bash
# Wrapper script is ready in this repo
cp ~/.config/opencode/bin/opencode-bmw-wsl2 ~/bin/opencode-bmw
chmod +x ~/bin/opencode-bmw
echo 'alias opencode="$HOME/bin/opencode-bmw"' >> ~/.bashrc
source ~/.bashrc
```

#### Step 5 — Verify setup

**macOS:**
```bash
~/bin/test-opencode-auth
opencode run "what models do you have access to?"
```

**Windows (WSL2):**
```bash
# Run the full WSL2 auth diagnostic (checks .env, VPN, proxy, OAuth2, LLM API, TTT)
bash ~/.config/opencode/bin/test-opencode-auth-wsl2

# Then launch
opencode run "what models do you have access to?"
```

#### Step 6 — Configure GitHub Enterprise (for gh CLI tools)

```bash
# Same on both platforms
gh auth login --hostname atc-github.azure.cloud.bmw
gh auth status --hostname atc-github.azure.cloud.bmw
```

#### Step 7 — Configure TTT (Skills Package Manager)

**macOS:**
```bash
# TTT_PAT is already in .env — add it if missing
echo 'TTT_PAT=your_personal_access_token' >> ~/.config/opencode/.env

# Test TTT connection
ttt skills list --page-size 5
```

**Windows (WSL2):**
```bash
# TTT_PAT should already be in .env from Step 3
source ~/.config/opencode/.env
ttt skills list --page-size 5
```

---

## Models Available

All models are accessed via the `llm-api/*` provider (BMW internal LLM API gateway):

| Model ID | Provider | Context | Best For |
|----------|----------|---------|----------|
| `llm-api/claude-sonnet-4-6` | Anthropic | 200K | **Default** — balanced quality & speed |
| `llm-api/claude-sonnet-4-5` | Anthropic | 200K | Stable baseline |
| `llm-api/claude-haiku-4-5` | Anthropic | 200K | Fast, cost-effective |
| `llm-api/claude-sonnet-4` | Anthropic | 200K | Previous generation |
| `llm-api/gpt-5.4` | OpenAI | 922K | Huge context window |
| `llm-api/gpt-5.2` | OpenAI | 922K | Large context |
| `llm-api/gpt-5.1` | OpenAI | 272K | Standard GPT-5 |
| `llm-api/gpt-4o` | OpenAI | 128K | GPT-4 Optimized |
| `llm-api/gpt-4o-mini` | OpenAI | 128K | Cheap + fast |
| `llm-api/o4-mini` | OpenAI | 200K | Complex reasoning |
| `llm-api/o3-mini` | OpenAI | 200K | Reasoning tasks |
| `llm-api/gemini-3.5-flash` | Google | 1M | Blazing fast |
| `llm-api/gemini-3.1-flash-lite` | Google | 1M | Most cost-effective |
| `llm-api/gemini-3.1-pro` | Google | 2M | Largest context window |

```bash
# Override model for a specific request
opencode run "analyse this 500-page document" --model llm-api/gemini-3.1-pro
opencode run "quick rename task" --model llm-api/claude-haiku-4-5
```

> **Rule 1 (AGENTS.md):** All custom agents must use `llm-api/*` or `ollama/*` only. Never configure `anthropic/`, `openai/`, or `google/` directly.

---

## MCP Servers

MCP servers extend OpenCode with tools for external systems. Only `memory` is enabled by default for the fastest possible startup.

### Enabled by Default

| MCP | Purpose | Type |
|-----|---------|------|
| **memory** | Persistent knowledge graph across sessions (`@modelcontextprotocol/server-memory`, invoked via direct node path for reliability) | Local |

### Available (Disabled by Default)

| MCP | Purpose | BMW Infrastructure Required |
|-----|---------|----------------------------|
| **skills-mcp** | TTT skill catalog discovery (`skills.bmwgroup.net/mcp`) — enable when browsing/installing skills | `TTT_PAT` env var + BMW network |
| **jira-atc** | Create/update Jira tickets, read sprints | `atc-jira.azure.cloud.bmw` |
| **confluence-atc** | Read/write Confluence pages | `bmwgroup.atlassian.net` |
| **density-mcp** | Alphabet/Density design system components | BMW Nexus registry |
| **fetch** | Fetch public web pages | BMW npm registry |
| **grafana** | Query Grafana dashboards | BMW Grafana + service account token |
| **wiz** | Security findings, CVEs, cloud posture | `mcp.app.wiz.io` (OAuth via BMW) |
| **playwright** | Browser automation — navigate, click, screenshot, scrape, E2E test | BMW Nexus (`@playwright/mcp`) |

### Enabling an MCP

Edit `~/.config/opencode/opencode.json`:

```json
{
  "mcp": {
    "jira-atc": {
      "enabled": true
    }
  }
}
```

> **Rule 3 (AGENTS.md):** Never add MCPs manually. Use `ttt-mcp-add <namespace/name>` for new MCPs.

⚠️ **BMW Internal MCPs require:** Active VPN, service account credentials, and access to BMW's internal artifact registries (Nexus, DockerHub proxy).

---

## Skills Library

Skills are specialist instructions loaded on-demand for specific tasks. The Request Orchestrator automatically loads the right skill based on your request. You can also reference them explicitly.

Skills are installed to `~/.opencode/skills/` (TTT-managed) or `~/.config/opencode/skills/` (config-managed).

### How to Install a Skill

```bash
# Install from TTT catalog
ttt skills install <namespace/name> --agent-type opencode --global

# Verify installation
ls ~/.opencode/skills/<skill-name>/

# Load manually in a session (usually automatic)
# Type: /skill <skill-name>
```

### Figma / Design

| Skill | When to Use | Install Command |
|-------|-------------|----------------|
| `figma-use` | **MANDATORY** before any Figma write operation | `ttt skills install dx/figma-use --agent-type opencode --global` |
| `figma-generate-design` | Translate app page/view → Figma screen | `ttt skills install dx/figma-generate-design --agent-type opencode --global` |
| `figma-generate-diagram` | Create flowchart, ERD, architecture in FigJam | `ttt skills install dx/figma-generate-diagram --agent-type opencode --global` |
| `figma-implement-design` | Generate production code from a Figma file | `ttt skills install dx/figma-implement-design --agent-type opencode --global` |
| `figma-implement-make` | Generate code from Figma Make prototype | `ttt skills install dx/figma-implement-make --agent-type opencode --global` |
| `figma-create-new-file` | Create a new blank Figma/FigJam file | `ttt skills install dx/figma-create-new-file --agent-type opencode --global` |
| `figma-use-figjam` | FigJam-specific canvas operations | `ttt skills install dx/figma-use-figjam --agent-type opencode --global` |
| `canvas-design` | Poster, infographic, static visual design (.png/.pdf) | `ttt skills install dx/canvas-design --agent-type opencode --global` |
| `frontend-design` | Polished HTML/CSS/React UI prototype | `ttt skills install dx/frontend-design --agent-type opencode --global` |

### UX / Review

| Skill | When to Use |
|-------|-------------|
| `ux-reviewer` | Full UX review (Nielsen heuristics + copy assessment) |
| `ux-report-generation` | Generate formal HTML evaluation report |

### Angular / React (BMW AI4DevOps)

| Skill | When to Use |
|-------|-------------|
| `ai4do-fe-angular` | Angular, NgRx, NX, Vitest, Playwright, BMW standards |
| `ai4do-fe-react` | React, TypeScript, Vite, Zustand, BMW standards |
| `ai4do-fe-code-review` | Frontend PR/code review checklist |
| `ai4do-fe-accessibility` | WCAG 2.1 AA audit — a11y, ARIA, screen readers |
| `ace-angular-developer` | Angular code generation + architectural guidance |
| `ace-angular-core-components` | `@alphabet/core-components` UI library usage |
| `ace-angular-core-components-form` | `@alphabet/core-components` form inputs |
| `ace-angular-core-theme` | Alphabet core-theme CSS utility classes |
| `ace-angular-translations` | Common-first i18n policy enforcement |
| `ace-angular-major-version-migration-preparation` | Plan an Angular major-version upgrade |
| `ace-angular-major-version-migration-execution` | Execute an Angular major-version upgrade |

### Git / GitHub / Jira

| Skill | When to Use |
|-------|-------------|
| `git-commit-reorganization` | Clean up messy commit history into atomic commits |
| `pr-creation` | Create well-structured PRs via `gh` CLI |
| `pr-overview` | Daily PR triage — CI status, review status, dependencies |
| `jira-adhoc-story` | Create Jira story for ad-hoc work from current branch |
| `gh-cli` | GitHub Enterprise CLI operations (`atc-github.azure.cloud.bmw`) |
| `bmw-oss-dual-repo-workflow` | BMW internal mirror + public GitHub PR flow |

### Presentations / Slides

| Skill | When to Use |
|-------|-------------|
| `bmw-pptx` | Create/read/edit PowerPoint with BMW CI branding |
| `bmw-slides` | Markdown → PPTX or HTML slides |
| `bmw-ppt-creator` | Brand-consistent PPT styling |
| `ppt-style-registry` | Clone/save/apply PPT styles from existing files |
| `bmw-github-pages` | BMW-styled static sites with GitHub Pages |

### Video Generation

| Skill | When to Use |
|-------|-------------|
| `clipjoint` | **Main orchestrator** — text/file → full MP4 video |
| `manim-renderer` | Generate Manim animation code and render to MP4 |
| `storyboard-planner` | Pre-render visual style guide for multi-segment videos |
| `tts` | BMW Audio TTS — generate full narration MP3 |
| `audio-generation` | TTS synthesis — imports `audio_generation.synthesise()` directly (no code generation) |
| `transcription` | Narrate transcription + word-level timings for subtitles |
| `text-generation` | Call BMW LLM API for script generation/rewriting |
| `image-generator` | **Dual-mode**: standalone PNG/MP4 from a prompt (`~/.opencode/plugins/clipjoint/.venv/bin/python3 ~/.opencode/plugins/clipjoint/scripts/image_generator.py "prompt"`) **or** pipeline sub-skill for clipjoint `visual_type: "image"` segments |
| `video-merger` | Merge clips + TTS + subtitles → final MP4 |

### RAG / Semantic Search / PDF

| Skill | When to Use |
|-------|-------------|
| `rag` | Embed docs + cosine search + rerank + answer (no external DB) |
| `pdf-chat` | Chat with a local PDF via Claude (base64, max 10 MB) |

### Web Research

| Skill | When to Use |
|-------|-------------|
| `web-research` | Brave Search single-query research |
| `deep-web-research` | Parallel research lanes + Cohere reranker + synthesis |

### Office 365

| Skill | When to Use |
|-------|-------------|
| `morning-briefing` | Daily agenda + email summary from Office 365 |
| `office365-graph-secure` | Microsoft Graph access (token-file secure pattern) |

### Agentic / Orchestration

| Skill | When to Use |
|-------|-------------|
| `bmw-tool-agent` | Build ReAct agents that call BMW internal APIs as tools |
| `gaia-tools` | Call BMW GAIA Tools/Chatbots via Apigee gateway |
| `routing-cache` | Self-learning routing cache — imports `routing_cache` module directly (no code generation) |

### Code Quality

| Skill | When to Use |
|-------|-------------|
| `python-data-quality` | Python data science / ML code review (pandas, numpy, sklearn) |
| `embedded-review` | Embedded C/C++ code review for firmware/ECUs |

### Agent Productivity (from `ad/agent-productivity` plugin)

| Skill | When to Use |
|-------|-------------|
| `feature-contract` | Lock feature contracts before implementation |
| `prompt-enhancement` | Sharpen prompts for better agent results |
| `session-analysis` | Reflect on a session's effectiveness |
| `skill-execution-footprint` | Measure and minimise skill context/token usage |
| `strategic-thinking` | Structured strategic reasoning for complex problems |

### Utilities

| Skill | When to Use |
|-------|-------------|
| `ttt` | Discover and install skills/prompts/agents from TTT |
| `mcp-setup` | MCP server configuration reference |
| `dor-jira-updater` | Populate Jira fields for DoR compliance |
| `bmw-wisdom` | Append BMW management wisdom quote |
| `file-handoff` | Move large context via temp files between agents |

---

## Slash Commands (Prompts)

Slash commands are full workflow prompts invoked by typing `/command-name` in the TUI. They orchestrate multi-step tasks automatically.

### Available Slash Commands

| Command | Purpose | Required Skills |
|---------|---------|----------------|
| `/create-pr` | Stage changes → atomic commits → push → open PR | `git-commit-reorganization`, `pr-creation` |
| `/apply-pr-suggestions` | Read PR review comments and apply accepted ones | `gh-cli` |
| `/nice-git-commits` | Reorganise uncommitted changes into atomic commits | `git-commit-reorganization` |
| `/security-fix` | Autonomously fix GHAS/Wiz Code security findings (`target=ghas` or `target=wiz`) | `aaa-ghas-remediation`, `aaa-wiz-remediation` |
| `/security-explain` | Explain GHAS/Wiz findings without fixing (read-only) | `aaa-ghas-remediation`, `aaa-wiz-remediation` |
| `/bmw-wisdom` | Append a BMW-style management wisdom quote | `bmw-wisdom` |
| `/beast-mode` | Full autonomous execution — zero interruptions, self-correction loops | none |
| `/direct` | Bypass orchestrator routing — answer directly from the general agent | none |

### Installing Slash Commands

```bash
# List available prompts
ttt prompts list

# Install a prompt
ttt prompts download <namespace/name> --agent-type opencode --global

# Prompts install to:
ls ~/.opencode/prompts/
```

---

## Custom Agents

Three production-ready custom agents are included in `~/.config/opencode/agents/`. All follow AGENTS.md security rules (provider lockdown + skills lockdown).

| Agent | Purpose | Trigger Keywords |
|-------|---------|-----------------|
| **request-orchestrator** | **Default agent** — smart router that picks skills, agents, or GAIA apps | All requests |
| **oracle-apex-expert** | Oracle APEX development, PL/SQL, ORA- errors, ORDS | `apex`, `oracle`, `plsql`, `ora-`, `apex page` |
| **uipath-rpa-expert** | UiPath Dispatcher/Worker docs, XAML analysis, bot flows | `uipath`, `rpa`, `dispatcher`, `worker`, `xaml`, `bot` |
| **jirri-data-analyst** | JIRRI RPA cost-savings audit, Python stdlib analysis | `jirri`, `cost savings`, `mb1b`, `lt01` |

### Creating a Custom Agent

```bash
# Use the template
cp ~/.config/opencode/agent-template.md ~/.config/opencode/agents/my-agent.md

# Edit it (must use llm-api/* models only — Rule 1)
# Add to AGENTS.md Rule 7 table when done
```

All agents are also mirrored to `~/.copilot/agents/` for GitHub Copilot compatibility.

---

## TTT — Skills Package Manager

TTT (`ttt`) is the BMW-internal skills package manager. It discovers and installs skills, prompts, agents, and bundles from the Skills Server catalog (`skills.bmwgroup.net`).

### Basic TTT Usage

```bash
# Search for skills
ttt search "angular" --type skill
ttt search "presentation" --type skill

# Get details on a specific skill
ttt skills get dx/bmw-pptx

# Install a skill globally (for use in OpenCode)
ttt skills install dx/bmw-pptx --agent-type opencode --global

# Install a prompt
ttt prompts download dx/create-pr --agent-type opencode --global

# List installed skills
ls ~/.opencode/skills/
ls ~/.config/opencode/skills/

# Browse the full catalog interactively
ttt tui
```

### Installing the Full Skills Bundle

```bash
# Figma skills
for skill in figma-use figma-generate-design figma-generate-diagram figma-implement-design figma-create-new-file figma-use-figjam figma-implement-make; do
  ttt skills install dx/$skill --agent-type opencode --global
done

# Presentation skills
for skill in bmw-pptx bmw-slides bmw-ppt-creator ppt-style-registry bmw-github-pages; do
  ttt skills install dx/$skill --agent-type opencode --global
done

# Angular skills
for skill in ace-angular-developer ace-angular-core-components ace-angular-core-components-form ace-angular-core-theme ace-angular-translations; do
  ttt skills install dx/$skill --agent-type opencode --global
done

# Video skills
for skill in clipjoint manim-renderer storyboard-planner tts audio-generation transcription text-generation image-generator video-merger; do
  ttt skills install dx/$skill --agent-type opencode --global
done

# Research & RAG
for skill in web-research deep-web-research rag pdf-chat gaia-tools; do
  ttt skills install dx/$skill --agent-type opencode --global
done

# Git/GitHub/Jira
for skill in git-commit-reorganization pr-creation pr-overview jira-adhoc-story bmw-oss-dual-repo-workflow; do
  ttt skills install dx/$skill --agent-type opencode --global
done

# Productivity
for skill in python-data-quality embedded-review bmw-tool-agent routing-cache morning-briefing office365-graph-secure; do
  ttt skills install dx/$skill --agent-type opencode --global
done

# Slash commands
for prompt in create-pr apply-pr-suggestions nice-git-commits security-fix security-explain bmw-wisdom beast-mode; do
  ttt prompts download dx/$prompt --agent-type opencode --global
done
```

### MCP Configuration via TTT

```bash
# Add a new MCP (do NOT edit opencode.json manually — Rule 3)
ttt-mcp-add dx/grafana-mcp
ttt-mcp-add dx/jira-atc-mcp
```

---

## GAIA Auto-Routing

The Request Orchestrator can automatically route BMW domain-specific questions to GAIA apps — BMW's internal AI platform hosting 500+ tools and chatbots.

If a request isn't covered by an installed skill, the orchestrator checks the GAIA catalog and calls the best-matching app automatically.

**Covered domains include:** SAP, Jira JQL, TISAX, HR processes, compliance, UX patterns, logistics, and more.

```bash
# Example: TISAX question → routed to "TISAX Supplier & Partner Management" GAIA app
# Example: JQL query help → routed to "JQL Wizard" GAIA app
# All automatic — just ask your question
```

To explore GAIA apps yourself:

```bash
# Load the gaia-tools skill for manual GAIA access
# The skill provides: session creation, prompt sending, response polling
```

---

## Self-Learning Routing Cache

The orchestrator includes a **semantic routing cache** that learns which skill handles each type of request. After a few sessions, common requests are routed instantly without any catalog lookup.

- **Technology:** `text-embedding-3-small` + numpy cosine similarity
- **Threshold:** ≥ 0.82 cosine similarity = cache hit (skip routing pipeline)
- **Storage:** `~/.opencode/skills/routing-cache/cache/` (persistent numpy index)
- **Learning:** Every routing decision is recorded and synced from `opencode.db`
- **Module:** `~/.opencode/skills/routing-cache/routing_cache.py` — imported directly, no bash generation

The cache is loaded automatically at session start — no configuration needed.

### Bootstrapping (first session)

On first use, `sync_from_db()` scans `opencode.db` and seeds the cache from real session history:

```bash
~/.opencode/plugins/clipjoint/.venv/bin/python3 -c "
import sys, pathlib
sys.path.insert(0, str(pathlib.Path.home() / '.opencode/skills/routing-cache'))
from routing_cache import sync_from_db, cache_stats
n = sync_from_db()
s = cache_stats()
print(f'[routing-cache] +{n} new pairs → {s[\"count\"]} total entries')
"
```

---

## Configuration Files

| File | Purpose |
|------|---------|
| `opencode.json` | Main config: models, providers, MCPs, default agent |
| `AGENTS.md` | Global agent rules (security policies, installed agents, skill catalog) |
| `AUTH_MONITORING.md` | 24-hour authentication validation checklist |
| `agent-template.md` | Template for creating new custom agents |
| `agents/` | Custom agent definitions (request-orchestrator, oracle-apex, uipath-rpa, jirri) |
| `skills/` | Config-managed skills (symlinked from TTT installations) |
| `plugins/` | Plugin config files |
| `ppt-styles/` | PPT style registry cache |
| `load-secrets.sh` | Loads credentials from macOS Keychain into env vars (macOS only) |
| `WINDOWS-SETUP.md` | Windows gap analysis, open questions (resolved), and implementation plan |
| `bin/opencode-bmw-wsl2` | WSL2 wrapper script — reads `.env` instead of Keychain, same heal logic |
| `bin/test-opencode-auth-wsl2` | WSL2 auth diagnostic — checks `.env`, proxy, VPN, OAuth2, LLM API, TTT |
| `routing-matrix.md` | Cross-agent routing documentation |
| `.gitignore` | Prevents secrets and generated files from being committed |
| `ai4devops_catalog.md` | BMW AI4DevOps skills catalog reference |
| `available-models-reference.json` | Full model capabilities reference |

---

## Troubleshooting

### OpenCode hangs on startup

**Cause:** BMW OAuth2 endpoint unreachable (VPN disconnected) or credentials not loaded

**macOS:**
```bash
# Check VPN
scutil --nc list  # Must show "Connected"

# Test BMW network
curl -I https://auth.bmwgroup.net  # Should return HTTP 200

# Force token refresh
bmw-refresh

# Run full diagnostic
~/bin/test-opencode-auth
```

**Windows (WSL2):**
```bash
# VPN runs on Windows host — WSL2 shares it automatically
# Test network connectivity from inside WSL2:
curl -I https://auth.bmwgroup.net  # Should return HTTP 200
ping -c 1 api.gcp.cloud.bmw

# Check .env is loaded
source ~/.config/opencode/.env
echo "BMW_CLIENT_ID set: $([ -n "$BMW_CLIENT_ID" ] && echo YES || echo NO)"
```

### Authentication errors — "Invalid bearer token" or "401 Unauthorized"

**macOS:**
```bash
# Verify wrapper is active
type opencode  # Should show: alias for ~/bin/opencode-bmw

# Check Keychain has credentials
security find-generic-password -s com.bmw.opencode -a llm_api_key -w
security find-generic-password -s com.bmw.opencode -a bmw_client_id -w

# Force refresh
bmw-refresh && opencode run "test"

# Confirm config uses {env:...} pattern (NOT hardcoded tokens)
grep '{env:' ~/.config/opencode/opencode.json
```

**Windows (WSL2):**
```bash
# Check .env has credentials
grep -E "^(LLM_API_KEY|BMW_CLIENT_ID|BMW_CLIENT_SECRET)=" ~/.config/opencode/.env

# Check .env permissions (must be 600)
ls -la ~/.config/opencode/.env  # Should show: -rw-------

# Verify wrapper sources .env
source ~/.config/opencode/.env && echo "Credentials loaded OK"
```

### Model not found — "ProviderModelNotFoundError"

```bash
# CORRECT format:
opencode run "task" --model llm-api/claude-sonnet-4-6

# WRONG (missing llm-api/ prefix):
opencode run "task" --model claude-sonnet-4-6
```

### Slow startup (>30 seconds)

**Cause:** Remote MCP servers initializing (Jira ATC, Confluence, Wiz, Density)

```bash
# Disable unused MCPs in opencode.json (set "enabled": false)
# Only memory should be enabled for fastest startup (~10 seconds)
```

### MCP server fails to load

```bash
# Jira/Confluence/Density: Check VPN + credential env vars in .env
# Wiz: Run OAuth setup
opencode mcp auth wiz

# Grafana: Set credentials in .env
echo 'GRAFANA_URL=https://your-grafana.bmw.com' >> ~/.config/opencode/.env
echo 'GRAFANA_SERVICE_ACCOUNT_TOKEN=glsa_...' >> ~/.config/opencode/.env
```

### Cannot clone repository / GitHub auth fails

```bash
gh auth login --hostname atc-github.azure.cloud.bmw
gh auth status --hostname atc-github.azure.cloud.bmw
```

### TTT skill install fails

```bash
# Check TTT_PAT is set
echo $TTT_PAT  # Should show your PAT

# Set it if missing
echo 'TTT_PAT=your_github_pat' >> ~/.config/opencode/.env
source ~/.config/opencode/.env

# Test TTT connection
ttt skills list --page-size 3
```

### skills-mcp auth keeps failing / OAuth loop in terminal

**Cause:** The `skills-mcp` server uses real OAuth2 PKCE. The TTT PAT cannot be used
directly as a Bearer token — the server issues its own short-lived access tokens (1h TTL).
OpenCode needs a valid `access_token` + `refresh_token` in `mcp-auth.json`.

**Fix — one-time browser consent (run once, then automatic forever):**
```bash
~/.opencode/plugins/clipjoint/.venv/bin/python3 ~/bin/opencode-skills-auth
# Opens browser → click Allow → writes access_token + refresh_token to mcp-auth.json
```

**After that, the wrapper auto-refreshes on every launch** using the `refresh_token` —
no browser needed again unless the refresh token is also revoked.

```bash
# If skills-mcp stops working after the initial setup:
# 1. Check wrapper heal output
~/bin/opencode-bmw --version 2>&1 | grep skills-mcp

# 2. If "refresh failed" or token missing — redo one-time auth:
~/.opencode/plugins/clipjoint/.venv/bin/python3 ~/bin/opencode-skills-auth
```

### Skill not loading / routing to wrong skill

```bash
# Check the routing cache isn't stale
~/.opencode/plugins/clipjoint/.venv/bin/python3 - << 'EOF'
import sys, pathlib
sys.path.insert(0, str(pathlib.Path.home() / ".opencode/skills/routing-cache"))
from routing_cache import cache_stats
print(cache_stats())
EOF

# Browse installed skills
ls ~/.opencode/skills/
ls ~/.config/opencode/skills/
```

See **AGENTS.md Rule 6.1** for comprehensive authentication architecture and troubleshooting.

---

## Architecture

### Authentication Flow

**macOS:**
```
User runs 'opencode'
    ↓ /opt/homebrew/bin/opencode → symlink → ~/bin/opencode-bmw (wrapper)
    ↓ reads BMW_CLIENT_ID / BMW_CLIENT_SECRET from macOS Keychain
    ↓ calls auth.bmwgroup.net (OAuth2 M2M) → fresh bearer token
    ↓ writes token back to Keychain
    ↓ exports LLM_API_BEARER_TOKEN env var
    ↓ launches real opencode binary
    ↓ reads ~/.config/opencode/opencode.json
    ↓ substitutes {env:LLM_API_BEARER_TOKEN}
    ↓ routes to request-orchestrator agent
    ↓ API call to api.gcp.cloud.bmw/llmapi/v1 (with fresh token)
```

> **Note:** The Homebrew symlink `/opt/homebrew/bin/opencode` points directly to the wrapper
> script — no shell alias needed. This means the wrapper runs in ALL contexts: interactive
> terminals, macOS Dock launches, scripts, and non-interactive shells.

**Windows (WSL2) — planned:**
```
User runs 'opencode'
    ↓ alias → ~/bin/opencode-bmw (bash wrapper)
    ↓ sources ~/.config/opencode/.env
    ↓ reads BMW_CLIENT_ID / BMW_CLIENT_SECRET from env vars
    ↓ calls auth.bmwgroup.net (OAuth2 M2M) → fresh bearer token
    ↓ exports LLM_API_BEARER_TOKEN env var
    ↓ launches opencode (WSL2 binary)
    ↓ reads ~/.config/opencode/opencode.json  ← same file as macOS
    ↓ substitutes {env:LLM_API_BEARER_TOKEN}
    ↓ routes to request-orchestrator agent
    ↓ API call to api.gcp.cloud.bmw/llmapi/v1 (with fresh token)
```

### Request Routing Flow

```
User request
    ↓
Request Orchestrator
    ├─ P0: Matches a slash command? → Suggest /command
    ├─ P0.5: Routing cache hit (≥ 0.82 cosine)? → Load cached skill directly
    ├─ P1: Trivial single-response? → Answer directly
    ├─ P2: Matches specialist agent? → Delegate to agent
    │       oracle-apex-expert | uipath-rpa-expert | jirri-data-analyst
    │       presentation-builder | aaa-security-fixer | agile-master-* | dor-agent
    ├─ P3: Installed skill covers it? → Load skill + execute
    ├─ P3.5: BMW GAIA app covers it? → Auto-route via gaia_router.py
    ├─ P4: Search TTT catalog → Install + load skill if found
    └─ P5: Nothing found → Best-effort answer
```

### LLM Gateway Architecture

```
┌─────────────────┐      ┌──────────────────┐      ┌─────────────────┐
│   OpenCode CLI  │─────▶│  BMW LLM API     │─────▶│  Anthropic API  │
│  (your laptop)  │      │  Gateway (GCP)   │      │  OpenAI API     │
│                 │      │  OAuth2 + Proxy  │      │  Google API     │
└─────────────────┘      └──────────────────┘      └─────────────────┘
         │                       │
         │                       ├─ Cost tracking per user/team
         │                       ├─ Audit logs
         │                       ├─ Rate limiting
         │                       ├─ DLP scanning
         │                       └─ Model catalog governance
         │
         └─ VPN Required ────────────────────────────────
```

---

## Security

This configuration enforces BMW security policies defined in `AGENTS.md`:

| Rule | Policy |
|------|--------|
| **Rule 1** | Models: only `llm-api/*` or `ollama/*` — no direct provider API keys |
| **Rule 2** | Skills: only from `~/.opencode/skills/` — must be TTT-sourced |
| **Rule 3** | MCPs: only via `ttt-mcp-add` — no manual `opencode.json` edits |
| **Rule 4** | Agents: `llm-api` model, TTT skills, `{env:}` credentials, `~/.config/opencode/agents/` location |
| **Rule 6** | Credentials: stored in macOS Keychain (macOS) or `.env` file chmod 600 (WSL2), referenced as `{env:VAR}` — never hardcoded |

**Security checklist:**
- ✅ No hardcoded secrets in any config file
- ✅ macOS Keychain credential storage (macOS) / protected `.env` file (WSL2)
- ✅ `{env:...}` pattern for all credential references
- ✅ `.gitignore` prevents secret leakage
- ✅ Audit trail via `~/.ttt/installations.json`
- ✅ BMW LLM API gateway provides DLP scanning on all requests

---

## Performance Metrics

| Metric | Before This Config | After | Improvement |
|--------|-------------------|-------|-------------|
| Startup time | 120s (all MCPs loading) | 10s | **12× faster** |
| Auth failures | Every ~2h (token expiry) | 0% | **100% reliable** |
| Manual token updates | Every 2 hours | Never | **Fully automated** |
| Available models | 3 | 14 | **367% more choice** |
| Available skills | 0 | 58+ | **Full specialist library** |

### Skill Invocation Architecture

Skills are classified by how they execute — this affects token cost and reliability:

| Paradigm | Examples | How it works | Relative token cost |
|---|---|---|---|
| 🔴 **Bash subprocess** | `clipjoint`, `bmw-pptx` | Model generates bash commands from SKILL.md instructions | High — model re-generates invocation code each time |
| 🟡 **Python-API inline** | *(none remaining — all migrated)* | SKILL.md contains full Python boilerplate the model adapts inline | Medium-high — boilerplate is large context overhead |
| 🟢 **Module import** | `routing-cache`, `audio-generation`, `rag`, `pdf-chat`, `bmw-tool-agent`, `deep-web-research`, `ux-reviewer`, `dor-jira-updater`, `jira-adhoc-story` | SKILL.md points to a pre-installed `.py` module; model calls `import` + one function | Low — SKILL.md is a short API reference only |
| 🟢 **MCP-native** | `figma-use`, `web-research` (bravesearch) | Model calls a structured MCP tool directly; no code generation at all | Lowest — tool call is structured, fully cached |

**Quick wins shipped (2026-06-24):**
- `routing-cache` — SKILL.md reduced from ~1,400 → ~790 tokens (44%); orchestrator calls `routing_cache.py` directly
- `audio-generation` — new `audio_generation.py` in clipjoint/scripts; model imports `synthesise()` instead of generating raw HTTP code

**High-value refactors shipped (2026-06-24):**
- `rag` — SKILL.md reduced from ~4,114 → ~701 tokens (**83%**); full 300-line implementation extracted to `rag/rag.py`
- `pdf-chat` — SKILL.md reduced from ~2,119 → ~750 tokens (**65%**); `ask_pdf()` / `ask_pdf_stream()` extracted to `pdf-chat/pdf_chat.py`
- `bmw-tool-agent` — SKILL.md reduced from ~4,992 → ~1,492 tokens (**70%**); `run_agent()` / `make_tool()` extracted to `bmw-tool-agent/bmw_tool_agent.py`
- `deep-web-research` — SKILL.md reduced from ~3,260 → ~1,013 tokens (**69%**); async `rerank_findings()` extracted to `deep-web-research/reranker.py`

**Medium-value refactors shipped (2026-06-24, session 2):**
- `ux-reviewer` — 86-line vision analysis block extracted to `ux-reviewer/analyse_ui_screenshot.py`; adds `compare_screenshots()` function; SKILL.md now shows a 6-line import snippet
- `dor-jira-updater` — 55-line structured output block extracted to `scripts/generate_dor_fields.py`; typed `DoRFieldValues` model preserved; SKILL.md reduced ~40%
- `jira-adhoc-story` — 46-line story generation block extracted to `scripts/generate_story.py`; typed `StoryContent` model preserved; SKILL.md reduced ~35%
- `text-generation` — fixed relative `sys.path.insert(0, "scripts")` path bug → absolute `~/.opencode/plugins/clipjoint/scripts` path

**Enforcement tooling shipped (2026-06-24, session 2):**
- `skill-lint.py` — post-install linter; detects inline code blocks >20 lines; supports `<!-- skill-lint: ignore -->` escape for illustrative examples; exit 0 = clean, exit 1 = warnings
- `ttt-skills-install` — shell wrapper in `.zshrc` now auto-runs `skill-lint.py` after every `ttt skills install` call; `ttt-skills-download` forwards to it as a deprecated alias
- `python-data-quality` — all three illustrative example blocks marked `<!-- skill-lint: ignore -->` (correct pattern: examples stay in SKILL.md, implementations go in modules)

**Combined token reduction across all nine migrated skills: ~17,000 tokens saved per invocation cycle.**

**`uv run` → clipjoint venv conversions shipped (2026-06-24, session 3):**
- Added `pyyaml>=6.0.3` and `pygithub>=2.9.1` to clipjoint `pyproject.toml` (7 transitive deps: cffi, cryptography, pycparser, pyjwt, pynacl + the two direct). `rich` was already present.
- `pr-overview` — `uv run skills/.../pr_overview.py` replaced with `~/.opencode/plugins/clipjoint/.venv/bin/python3` invocation; `PROverview` class now documented as importable (`sys.path.insert` snippet added)
- `pr-creation` — `pr_helper.py` now documented as importable; `gh pr create` workflow unchanged; venv CLI invocation added as alternative to `uv run`
- `mcp-setup` — all 6 `uv run scripts/...` references replaced with absolute venv python paths; `detect-workspace-info.py` and `setup-mcp.py` now run without `uv` on PATH
- **Net effect:** these 3 skills no longer require `uv` to be installed or on PATH at invocation time

---

## Documentation

| Document | Contents |
|----------|---------|
| `AGENTS.md` | Security rules, installed agents, routing matrix, auth architecture (Rule 6.1) |
| `AUTH_MONITORING.md` | 24-hour post-setup validation checklist |
| `routing-matrix.md` | Cross-agent handoff documentation |
| `ai4devops_catalog.md` | BMW AI4DevOps skills and tools reference |
| `available-models-reference.json` | Full model capabilities and pricing reference |
| `agent-template.md` | Template for new custom agents |

---

## Contributing

This is a BMW-internal configuration. To contribute:

1. Fork in BMW GitHub Enterprise
2. Make changes on a feature branch
3. Test thoroughly (especially auth flow and skill loading)
4. Run `/create-pr` to open a PR with proper documentation
5. Tag the maintainer for review

**Restrictions:**
- ❌ Do not share outside BMW Group
- ❌ Do not commit BMW credentials or tokens
- ❌ Do not modify AGENTS.md Rules 1–6 without approval
- ✅ Share freely within BMW internal GitHub/Confluence
- ✅ Adapt for your team's custom agents and skills
- ✅ Open issues for bugs or feature requests

---

## Support

| Channel | Use For |
|---------|---------|
| `~/bin/test-opencode-auth` | Automated auth diagnostics |
| `AGENTS.md Rule 6.1` | Full authentication architecture |
| Issues in this repo | Bugs, feature requests (BMW internal only) |
| AI4DevOps team channel | General OpenCode questions at BMW |
| https://github.com/anomalyco/opencode | Upstream OpenCode bugs (non-BMW-specific) |

---

## License & Usage Restrictions

**BMW INTERNAL USE ONLY**

This configuration is proprietary to BMW Group. It contains BMW-internal API endpoints, authentication flows, MCP configurations, security policies, and infrastructure topology.

**License:** BMW Proprietary — Internal Distribution Only
