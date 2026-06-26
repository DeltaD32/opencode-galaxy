---
name: ttt
description: Find, evaluate, and install AI agent skills, prompts, agents, and bundles from the Skills Server using the `ttt` CLI (Skills Server API Client). Use when the user asks to search for or install a skill/prompt/agent, when you suspect a useful skill exists on the server, or when you need to manage the local skills installation. Supersedes the older `skills-client` CLI.
license: Proprietary
compatibility: Requires `ttt` CLI and network access to the Skills Server. A PAT is usually needed for private namespaces. Get `ttt` at https://skills.bmwgroup.net if not installed.
metadata:
  authors:
    - Matthias Bilger <matthias.bilger@bmw.de>
  version: "1.0.1"
  short_description: Token Tom's Toolbelt, a CLI for discovering and installing skills, prompts, agents, and bundles from the Skills Server and git repositories.
  tags:
    - skills
    - discovery
    - install
    - cli
    - github-copilot
---

# ttt

`ttt` is the **Skills Server API Client** — the primary CLI for discovering, inspecting, and installing AI agent skills, prompts, agents, and bundles.

## When to use

- User asks to find or install a skill, prompt, agent, or bundle
- You suspect a relevant skill exists on the server for a user's task
- User needs to update or list installed artifacts
- User needs to configure their PAT or default namespace
- User wants to manage git-based artifact sources

## Installation

If `ttt` is not installed, get it from **https://skills.bmwgroup.net**.

## Common Workflows

### 0) Check health / one-time setup

```bash
ttt health
```

If authentication is required (private namespace), store a PAT:

```bash
ttt config set-pat "YOUR_PAT"
```

Set a default namespace to avoid typing it on every command:

```bash
ttt config set-namespace dx
```

### 1) Search

Prefer **semantic** mode for natural-language queries; use **keyword** (default) for exact names:

```bash
ttt search "<query>" --mode semantic --type skill
ttt search "<query>" --type skill          # keyword (default)
```

Or browse all skills:

```bash
ttt skills list
```

### 2) Inspect a candidate

```bash
ttt skills get <name>            # e.g. ttt skills get dx/workspace-info
```

### 3) Install (download)

> **OpenCode users — always use `ttt-skills-download` instead of bare `ttt skills download`.**
> The wrapper installs the skill globally, then immediately syncs `~/.opencode/skills/` to the
> repo at `~/.config/opencode/skills/` and commits + pushes, so the repo never goes stale.

```bash
ttt-skills-download <name>
# e.g. ttt-skills-download dx/workspace-info
```

Any extra `ttt` flags are forwarded transparently:

```bash
ttt-skills-download dx/workspace-info --force
```

The wrapper is defined in `~/.zshrc` and is available in every shell session.

---

If you ever need to install **without** the auto-sync (rare), use the raw commands directly:

Install into the **current repository** (default — recommended for project-scoped skills):

```bash
ttt skills download <name>
# e.g. ttt skills download dx/workspace-info
```

Install **globally** into `~/.github/copilot/skills/`:

```bash
ttt skills download <name> --global
```

Target a specific agent type (default: `github-copilot`):

```bash
ttt skills download <name> --agent-type claude-code   # or: opencode, custom
```

Override output directory:

```bash
ttt skills download <name> --output /path/to/dir
```

### 4) Install bundles, prompts, or agents

Same pattern applies:

```bash
ttt bundles download <bundle-name>
ttt prompts download <prompt-name>
ttt agents  download <agent-name>
```

### 5) Check what's installed

```bash
ttt installed            # all artifact types
ttt skills installed     # skills only
ttt prompts installed
ttt agents  installed
```

### 6) Interactive TUI

For browsing and installing via an interactive interface:

```bash
ttt tui
```

## Repo tracking

`ttt` tracks which artifacts are installed per repository, enabling reproducibility:

```bash
ttt repos list                        # repos with tracked installations
ttt repos show <repo>                 # artifacts installed for a repo
ttt repos copy-from <source-repo>     # mirror another repo's installations
```

## Git-based artifact sources

Add a git repository as an additional artifact source:

```bash
ttt git-repos add <url>
ttt git-repos list
ttt git-repos update    # pull latest from all git sources
ttt git-repos remove <url>
```

## Troubleshooting

| Symptom                            | Fix                                                       |
| ---------------------------------- | --------------------------------------------------------- |
| `ttt: command not found`           | Install from **https://skills.bmwgroup.net**              |
| `Connection refused` / no response | Check `SKILLS_API_URL` env var; run `ttt health`          |
| `401` / auth error                 | Run `ttt config set-pat "YOUR_PAT"`                       |
| Skill not found                    | Try `--namespace dx` or use `namespace/name` format       |
| Wrong install location             | Use `--global` for home-dir or `--output` for custom path |
