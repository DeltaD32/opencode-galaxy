---
name: mcp-setup
description: MCP Server Setup Guide with searchable server configurations
license: Proprietary
compatibility: Requires uv (which provides Python 3.11+), npm/npx for running MCP servers, and appropriate MCP client configuration
metadata:
  author: Matthias Bilger <matthias.bilger@bmw.de>
  version: "1.1.2"
  tags:
    - mcp
    - model-context-protocol
    - server
    - setup
    - configuration
    - integration
---

# MCP Server Setup Guide

<!-- AI INSTRUCTIONS: When the user triggers MCP setup with keywords like "setup mcp",
"install server", "configure mcp", or asks about a specific MCP server perform the following steps
while automating as much as possible and start immediately with the setup process:

MANDATORY ENFORCEMENT (NON-OPTIONAL):
- These steps are hard requirements, not suggestions.
- Do NOT run any setup command before reading at least one matching file from references/setup-*-mcp.yaml.
- Do NOT declare setup complete after creating/updating mcp.json only.
- For localhost-based servers (for example, http://localhost:*), setup is incomplete until runtime is started and endpoint reachability is verified.
- If reference parsing is missing or incomplete, STOP and ask for clarification instead of proceeding.
- If runtime validation fails, continue remediation; do not end with a "setup complete" message.

1. FIRST, discover available MCP servers by scanning the references folder:
   - Look in references/ for setup-*-mcp.yaml files
   - Each YAML file represents a setup guide for one MCP server
   - Parse the YAML structure to understand available servers (see structure below)

2. THEN, run the workspace detection script to check the environment:
   - Execute: `~/.opencode/plugins/clipjoint/.venv/bin/python3 ~/.opencode/skills/mcp-setup/scripts/detect-workspace-info.py --json`
   - Parse the JSON output to check:
     - vscode_remote.is_remote: Whether running in remote VS Code
     - bmw_instance: Detected BMW tool instance (ATC, CC, or unknown)
       - Determined from git remote URL (cc-github → CC, atc-github/bmw.ghe.com → ATC)
     - git_remote: The git remote URL used for detection

3. If VS Code is running in a remote setup (Remote-SSH, Dev Container, WSL, Codespaces):
   - DEFAULT to project-level MCP configuration (.vscode/settings.json)
   - INFORM the user: "Detected remote VS Code setup. Using project-level MCP configuration,
     which is the recommended approach for remote environments as it ensures proper path
     resolution and environment isolation."
   - Do NOT ask whether to use global vs project setup - proceed with project setup

4. If VS Code is NOT remote (local setup):
   - Ask user preference: global (~/.config) or project-level (.vscode/) configuration

5. YAML Structure in references/ files:
   - name: Human-readable server name (e.g., "Setup GitHub MCP Server")
   - objective: Description of what the server enables
   - prerequisites: List of required tools/tokens
   - estimated_time: Time needed for setup
   - server_definition: MACHINE-READABLE config for unified setup script
     - server_key: Key in mcp.json servers section
     - default_scope: "global" or "project"
     - prerequisites: List of check names (node, npx, docker, docker_daemon, uvx)
     - docker_image: Image to pull (null if not Docker-based)
     - features: Special hooks (proxy_detection, wsl_detection)
     - mcp_config: The actual JSON config to write into mcp.json
     - inputs: VS Code input variable definitions
     - instances: For multi-transport servers (e.g., GitHub GHE vs ATC)
       - Use detected bmw_instance from workspace detection to auto-select instance
       - For GitHub: ATC detection → use github-atc instance, CC → use github-ghe
     - instance_selection: For URL-variant servers (e.g., SonarQube instances)
   - actions: Step-by-step setup instructions
   - tools_used: Scripts and tools involved
   - expected_outcome: What success looks like
   - validation: How to verify the setup worked

6. PREFERRED: Use the unified setup script to configure any server:
   - `~/.opencode/plugins/clipjoint/.venv/bin/python3 ~/.opencode/skills/mcp-setup/scripts/setup-mcp.py --server <name> [--scope <global|project>] [--instance <name>]`
   - Examples:
     - `~/.opencode/plugins/clipjoint/.venv/bin/python3 ~/.opencode/skills/mcp-setup/scripts/setup-mcp.py --server fetch`
     - `~/.opencode/plugins/clipjoint/.venv/bin/python3 ~/.opencode/skills/mcp-setup/scripts/setup-mcp.py --server github --instance ghe`
     - `~/.opencode/plugins/clipjoint/.venv/bin/python3 ~/.opencode/skills/mcp-setup/scripts/setup-mcp.py --server sonarqube --instance ito`
   - The unified script reads server_definition from YAML and handles setup automatically

7. If no specific server is mentioned, list available MCP servers from the references/ folder
   and ask which one to set up. Extract server names from the YAML filenames and 'name' field.
   You can also run: `~/.opencode/plugins/clipjoint/.venv/bin/python3 ~/.opencode/skills/mcp-setup/scripts/setup-mcp.py --list`

8. Match keywords from the user's query to server names and descriptions from the YAML files.
   Present the most relevant server(s) found and guide through the setup process.

9. For detailed setup instructions, read the full YAML file from references/ and follow the
   'actions' field step by step. Run the unified setup script from scripts/ folder.

10. BEFORE running setup commands, output a short "Reference Parse Summary" that includes:
   - selected_server
   - reference_file
   - required_runtime_actions (for example: clone, build, start)
   - validation_commands
   - completion_criteria

11. Completion criteria is satisfied only when all are true:
   - configuration written (mcp.json)
   - runtime prerequisites/actions completed from the selected reference
   - endpoint or transport is reachable based on reference validation steps
   - a simple MCP interaction test is attempted (for example: @<server> help)

12. Unified setup script rule:
   - The unified setup script is preferred for configuration generation,
     but it does not imply runtime is running.
   - Reference `actions` and `validation` are authoritative for end-to-end completion.

This approach discovers MCP servers directly from the skill's references folder,
making the skill self-contained and independent of external configuration files. -->

## Mandatory Enforcement Checklist

Before any setup command is executed, the assistant must confirm all items below:

1. Reference file selected from `references/setup-*-mcp.yaml`
2. Reference file was read and parsed
3. Runtime actions extracted from `actions` (if any)
4. Validation commands extracted from `validation`
5. Scope decision made (remote default project-level, local ask user)

If one item is missing, setup must pause and request clarification.

## How to Use This Guide

This document provides setup instructions for MCP (Model Context Protocol) servers
that extend GitHub Copilot's capabilities. Ask about a specific server or describe
what functionality you need, and I'll guide you through the setup.

**Available MCP servers are dynamically discovered** from the `references/` folder
within this skill. Each server has a dedicated setup guide stored as a YAML file
(e.g., `setup-github-mcp.yaml`) with complete instructions, prerequisites, and
validation steps.

## What are MCP Servers?

MCP servers are tools that extend AI capabilities by providing access to external
services, APIs, and data sources. They enable GitHub Copilot to interact with
enterprise systems like GitHub, Atlassian, SonarQube, and Wiz directly from chat.

## Available MCP Servers

The available MCP servers are **automatically discovered** from the skill's `references/` folder.
Each setup guide is stored as a YAML file (e.g., `setup-github-mcp.yaml`) containing complete
setup instructions, prerequisites, and validation steps.

To see all available servers, list the files in `references/setup-*-mcp.yaml`.

## General Setup Process

Most MCP servers follow this pattern:

1. **Verify Prerequisites** - Ensure required tokens, URLs, and permissions
2. **Read Server Reference** - Parse `references/setup-*-mcp.yaml` for server-specific runtime actions
3. **Run Unified Setup Script** - Execute `~/.opencode/plugins/clipjoint/.venv/bin/python3 ~/.opencode/skills/mcp-setup/scripts/setup-mcp.py --server <name>` for configuration
4. **Run Runtime Actions** - Complete clone/build/start or equivalent actions from the reference
5. **Configure Settings** - Provide required credentials and endpoints
6. **Restart Copilot** - Reload VS Code or GitHub Copilot to activate the server
7. **Test Connection** - Verify endpoint reachability and run a simple MCP query

### Unified Setup Script

The unified script `scripts/setup-mcp.py` reads server configuration from YAML reference files
and handles setup for all servers. It replaces individual `setup-*-mcp.py` scripts.

```bash
SETUP=~/.opencode/skills/mcp-setup/scripts/setup-mcp.py
PYTHON=~/.opencode/plugins/clipjoint/.venv/bin/python3

# List available servers
$PYTHON $SETUP --list

# Setup a server (reads config from YAML)
$PYTHON $SETUP --server <name> [--scope global|project] [--instance <name>]
```

## Configuration Scope Options

All MCP servers support two configuration scopes:

| Scope       | Location (Linux/macOS)                       | Location (Windows)                           | Use Case                                                   |
| ----------- | -------------------------------------------- | -------------------------------------------- | ---------------------------------------------------------- |
| **global**  | `~/.config/Code/User/globalStorage/mcp.json` | `%APPDATA%\Code\User\globalStorage\mcp.json` | Working on multiple projects that all need this MCP server |
| **project** | `.vscode/mcp.json`                           | `.vscode/mcp.json`                           | Team collaboration (can be committed to git)               |

**Remote VS Code**: When running in Remote-SSH, Dev Containers, WSL, or Codespaces,
project-level configuration is recommended for proper path resolution and environment isolation.

## Support

- **Teams Channel**: GitHub Copilot | Agile Toolchain (ATC)
- **Issues**: https://bmw.ghe.com/DX/token-toms-toolbelt/issues

## Common Issues

### Server Not Starting

- Check VS Code Output panel → "GitHub Copilot Chat" for error messages
- Verify all required environment variables are set
- Ensure tokens have appropriate permissions
- Check proxy settings if behind corporate firewall

### Docker Daemon Not Running

- **Linux**: `sudo systemctl start docker`
- **macOS/Windows**: Start Docker Desktop application
- Verify with: `docker ps`

### Authentication Failures (401 Unauthorized)

- Regenerate API tokens if expired
- Verify token has required scopes/permissions
- Check token is correctly formatted in configuration
- Ensure no extra spaces in token strings
- Update token in mcp.json and restart MCP server

### Network/Proxy Issues

- Configure proxy settings with the <skill>proxy-setup</skill> skill.
- Verify firewall allows connections to required endpoints
- Test connectivity with curl/wget to the API endpoint
- For BMW corporate network, check Proxydetox on port 3128

### Docker Image Pull Failures

- Check internet connection and Docker proxy settings
- Manually pull: `docker pull <image-name>`
- See https://docs.docker.com/network/proxy/ for Docker proxy configuration

## Common Security Best Practices

- **Token expiration**: Set tokens to expire after 90 days
- **Minimal scopes**: Only grant the permissions you need
- **Rotate regularly**: Generate new tokens periodically
- **Secure storage**: Tokens are stored in MCP config file — never commit to git
- **File permissions**: Config file is automatically set to mode 600 (owner only)

## Need Help?

If you encounter issues during setup:

1. Check the specific YAML reference file for server-specific troubleshooting
2. Review the prerequisites guide for required tokens
3. Run `~/.opencode/plugins/clipjoint/.venv/bin/python3 ~/.opencode/skills/mcp-setup/scripts/setup-mcp.py --server <name>` for automated validation
