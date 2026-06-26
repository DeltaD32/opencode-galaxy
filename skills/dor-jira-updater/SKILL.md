---
name: dor-jira-updater
description: "Uses backlog story data and DoR specification (from dor-backlog-reader and dor-confluence-reader) to populate missing Jira story fields so each story becomes Definition-of-Ready compliant. Performs Jira write operations via Jira REST API v3. Activate when users want to apply DoR rules to Jira stories. Part of the dor bundle — intended for use together with dor-backlog-reader, dor-confluence-reader, dor-governance, and dor-test-stories."
compatibility: Requires Jira REST API v3 access (Bearer token). Python >=3.10 with uv for terminal commands. GITHUB_TOKEN environment variable must be set for GitHub Copilot SDK authentication.
metadata:
  author: "JJ Loubser <JJ.Loubser@bmw.de>"
  version: "1.0.0"
  tags:
    - dor
    - jira
    - definition-of-ready
    - agile
    - automation
    - bmw
---

# Populate Jira Stories (DoR) Skill

## Purpose

Use the backlog output from `dor-backlog-reader` and the DoR specification from
`dor-confluence-reader` to populate missing Jira story fields so each story
becomes Definition-of-Ready compliant.

## Setup

> **Prerequisite:** Complete the shared token setup in `dor-backlog-reader` first (Steps 1–3 and 6).

### Jira Personal Access Token (`JIRA_TOKEN`)

ATC Jira uses **Personal Access Tokens**, not username/password or Confluence tokens:

1. Open [atc.bmwgroup.net/jira](https://atc.bmwgroup.net/jira) → **Profile icon** → **Account Settings** → **Security** → **Personal Access Tokens**
2. Click **Create token**, give it a name (e.g. `DoR-Automation`), set expiry to 1 year
3. Copy the token immediately — it is only shown once
4. Set `JIRA_TOKEN=<token>` in `.env`

> **Note:** This is a separate credential from your `CONFLUENCE_TOKEN`. Both are required.

### Set your project key

Set `JIRA_PROJECT_KEY=<your key>` in `.env` (e.g. `AI4DEVOPS`, `DX`, `MYPROJ`).

### Authenticate (once per session)

```shell
uv run scripts/_copilot_auth.py
```

---

## Template Values

Set these as environment variables (see `.env.example` in the bundle root):

| Variable           | Description                      |
| ------------------ | -------------------------------- |
| `JIRA_BASE_URL`    | Base URL of the Jira instance    |
| `JIRA_PROJECT_URL` | Full URL to the Jira project     |
| `JIRA_PROJECT_KEY` | Jira project key (e.g. `AI4D`)   |
| `JIRA_TOKEN`       | Jira API bearer token            |
| `GITHUB_TOKEN`     | BMW GHE PAT for Copilot SDK auth |

## Runtime

- SDK: GitHub Copilot SDK (`gpt-4o` via BMW GHE Copilot)
- Auth: `GITHUB_TOKEN` → exchanged for a Copilot session token via `copilot_llm.py`
- Tool: Jira REST API v3

## Steps

1. Load the backlog stories produced by `dor-backlog-reader` (agent artifact).
2. Load the DoR field requirements produced by `dor-confluence-reader` (agent artifact).
3. For each story:
   a. Read the current Jira issue: `GET {{JIRA_BASE_URL}}/rest/api/3/issue/{issueKey}`
   b. Compare current fields against DoR requirements.
   c. Generate missing or invalid values using **structured output** (see section below).
   d. Build the update payload via `scripts/build_jira_payload.py`.
   e. Update the issue: `PUT {{JIRA_BASE_URL}}/rest/api/3/issue/{issueKey}`
4. Emit a summary of all updates performed.

## Structured Output — LLM Field Generation (Step 3c)

Use `generate_dor_fields()` from the co-located module. Returns a typed `DoRFieldValues`
object that maps directly to `build_jira_payload.py` — no JSON extraction or string parsing.

```python
import sys, pathlib
sys.path.insert(0, str(pathlib.Path.home() / ".opencode/skills/dor-jira-updater/scripts"))
from generate_dor_fields import generate_dor_fields, DoRFieldValues

result = generate_dor_fields(issue_key, current_fields, dor_requirements)
payload = build_payload(
    issue_key=result.issue_key,
    dor_fields=[f.model_dump() for f in result.fields],
    description_template=description,
    acceptance_criteria=ac,
)
```

Module: `scripts/generate_dor_fields.py`
Functions: `generate_dor_fields(issue_key, current_fields, dor_requirements, model="gpt-4o")`
Returns: `DoRFieldValues` — typed Pydantic model with `.issue_key`, `.fields` (list of `DoRField`), `.compliance_notes`

## Jira API Integration

```text
GET  {{JIRA_BASE_URL}}/rest/api/3/issue/{issueKey}
PUT  {{JIRA_BASE_URL}}/rest/api/3/issue/{issueKey}
Authorization: Bearer {{JIRA_TOKEN}}
```

## Scripts

| Script                          | Purpose                                       |
| ------------------------------- | --------------------------------------------- |
| `scripts/copilot_llm.py`        | GitHub Copilot LLM integration (auth + chat)  |
| `scripts/build_jira_payload.py` | Build DoR-compliant Jira field update payload |
| `scripts/parse_backlog_page.py` | Confluence XHTML parser (shared utility)      |
| `scripts/_copilot_auth.py`      | OAuth device-flow helper (one-time auth)      |

## Output Schema

```json
{
  "project": "{{JIRA_PROJECT_KEY}}",
  "updates": [
    {
      "jira_key": "{{JIRA_PROJECT_KEY}}-123",
      "fields_updated": ["summary", "description", "acceptance_criteria"],
      "status": "success|partial|skipped",
      "dor_compliance_score": 0.95
    }
  ],
  "total_updated": 0,
  "total_skipped": 0,
  "completed_at": "ISO8601"
}
```

## Notes

- This skill **writes to Jira** — always run `dor-backlog-reader` and `dor-confluence-reader` first.
- All environment-specific values must come from environment variables, never hardcoded.
- Log all updates so the governance and test skills can verify them.
- See [references/jira-update-patterns.md](references/jira-update-patterns.md) for field update patterns.
- See [references/mcp-jira-tools.md](references/mcp-jira-tools.md) for available Jira MCP tools.
