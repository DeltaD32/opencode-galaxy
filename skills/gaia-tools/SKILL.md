---
name: gaia-tools
description: >
  Call GAIA Tools and Chatbots (BMW's internal AI platform) via the GAIA API.
  Discover public tools available to BMW associates, start chat sessions,
  send prompts, and poll for responses — all through the Apigee gateway.
  Use when the user wants to invoke a GAIA app/tool programmatically, browse
  available public GAIA tools, or integrate a GAIA chatbot into a workflow.
  Also used by the orchestrator to auto-route tasks to relevant GAIA apps.
  Trigger phrases: "call a GAIA tool", "use GAIA", "invoke GAIA app",
  "list GAIA tools", "GAIA chatbot", "send prompt to GAIA app",
  "browse GAIA apps", "GAIA API".
license: Proprietary
metadata:
  authors:
    - OpenCode Config
  version: "2.0.0"
  tags:
    - gaia
    - bmw
    - tools
    - chatbot
    - apigee
    - routing
---

# gaia-tools

Interact with BMW's **GAIA AI platform** programmatically via the GAIA API.
GAIA hosts 500+ public Tools and Chatbots published by BMW associates across
all divisions — callable from any OpenCode workflow via a local catalog cache
and smart keyword routing.

---

## When to use

| Scenario | Action |
|---|---|
| User explicitly asks to call a GAIA tool/app | Load skill → call by name or ID |
| User asks to list or browse GAIA apps | Load skill → `gaia_catalog.py --search` |
| Orchestrator wants to augment a task with a relevant GAIA app | Use `gaia_router.py` (auto-routing) |
| Task has no local skill match AND a GAIA app seems relevant | Try `gaia_router.py` before TTT discovery |

---

## Prerequisites

### Credentials

| Variable | Required | How to get |
|---|---|---|
| `GAIA_API_KEY` | **Always** | Subscribe at the [GAIA Apigee product page](https://api.bmwgroup.net/apim/portal/api-product/b4ad6103-a510-4e78-99e9-7c7bfaadd417) |
| `GAIA_CLIENT_ID` | Optional | Falls back to `BMW_CLIENT_ID` automatically |
| `GAIA_CLIENT_SECRET` | Optional | Falls back to `BMW_CLIENT_SECRET` automatically |

> **Fallback:** If `GAIA_CLIENT_ID`/`GAIA_CLIENT_SECRET` are not set, the client
> automatically uses `BMW_CLIENT_ID`/`BMW_CLIENT_SECRET` — the same M2M identity
> used for the BMW LLM API. No extra setup needed if you already have LLM API access.

Store in `~/.config/opencode/.env`:
```bash
GAIA_API_KEY=APIM_xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

### Network
Must be on BMW intranet or VPN. Gateway: `https://api.bmwgroup.net`.

### App visibility
- **Public apps** (560+) — callable by any BMW associate with a valid API key
- **Private apps** — require member/delegate/owner role in the GAIA portal

---

## Base URLs

| Environment | GAIA API base | Auth endpoint |
|---|---|---|
| **PROD** | `https://api.bmwgroup.net/gaia` | `https://auth.bmwgroup.net/.../machine2machine/access_token` |
| **INT** | `https://api.bmwgroup.net/gaia-int` | `https://auth-i.bmwgroup.net/.../machine2machine/access_token` |

Set `GAIA_ENV=int` to use the integration environment (default: `prod`).

---

## Scripts (in `scripts/`)

| Script | Purpose |
|---|---|
| `gaia_client.py` | Core HTTP client — auth, session, interaction, poll, chat() |
| `gaia_catalog.py` | Local catalog cache — fetch, search, stats |
| `gaia_router.py` | Auto-router — find best GAIA app for a task + optionally call it |

---

## Auto-routing workflow (orchestrator use)

The orchestrator calls `gaia_router.py` to transparently augment any task with
the most relevant public GAIA app — without the user needing to know app IDs.

### How it works

```
User task description
        ↓
gaia_catalog.py loads local cache (560 apps, refreshed every 24h)
        ↓
Keyword scorer matches task against app names
        ↓
Score ≥ 6.0 (high confidence) → auto-call the app
Score 2.0–5.9 (medium)        → present top 3 candidates, ask user
Score < 2.0                   → no match, continue to TTT discovery
        ↓
gaia_client.py: start session → send prompt → poll → return response
        ↓
Weave GAIA response into the ongoing workflow
```

### Agent instructions for auto-routing

1. **Extract a short task phrase** from the user's request (3-6 keywords).
   Example: "create jira ticket" not "I want to create a Jira ticket for the login bug".

2. **Run the router** (use the clipjoint venv for the `requests` dependency):
   ```bash
   GAIA_CLIENT_ID="$BMW_CLIENT_ID" GAIA_CLIENT_SECRET="$BMW_CLIENT_SECRET" \
   ~/.opencode/plugins/clipjoint/.venv/bin/python3 \
   ~/.opencode/skills/gaia-tools/scripts/gaia_router.py \
     --task "<short task phrase>" \
     --prompt "<full user prompt>" \
     --top 3 \
     --json
   ```

3. **Read the JSON result**:
   - `matched: false` → no suitable GAIA app found, proceed to TTT
   - `app_score < 6.0` → show candidates to user, ask which to use
   - `app_score ≥ 6.0` → call was made automatically, use `response`

4. **Present the result** — tell the user which GAIA app was used and show
   the response. Always be transparent.

### Python library usage

```python
import sys, pathlib
sys.path.insert(0, str(pathlib.Path.home() / ".opencode/skills/gaia-tools/scripts"))
from gaia_router import route_to_gaia

result = route_to_gaia(
    task="python code buddy",          # short phrase for catalog matching
    prompt="Write a function that ...", # actual prompt sent to the app
)

if result["matched"]:
    print(f"Used GAIA app: {result['app_name']} (score={result['app_score']})")
    print(result["response"])
else:
    print("No relevant GAIA app found — falling back to TTT discovery.")
```

---

## Manual / explicit workflow

When the user explicitly names a GAIA app or asks to browse:

```python
from gaia_client import GaiaClient
from gaia_catalog import GaiaCatalog

# Browse apps
catalog = GaiaCatalog()
matches = catalog.search("agile coach", top_k=5)
for app in matches:
    print(f"[{app['score']}] {app['name']}  id={app['id']}")

# Call a specific app
client = GaiaClient()
response = client.chat(
    app_id="be675e9d-ca17-4802-ab86-f8f853f900a1",  # AI Agile Coach
    prompt="How should I structure a sprint retrospective for a remote team?",
)
print(response)
```

---

## Catalog cache management

```bash
# Refresh the catalog (run manually or daily via cron)
~/.opencode/plugins/clipjoint/.venv/bin/python3 \
  ~/.opencode/skills/gaia-tools/scripts/gaia_catalog.py --refresh

# Check cache stats
~/.opencode/plugins/clipjoint/.venv/bin/python3 \
  ~/.opencode/skills/gaia-tools/scripts/gaia_catalog.py --stats

# Search without calling any app
~/.opencode/plugins/clipjoint/.venv/bin/python3 \
  ~/.opencode/skills/gaia-tools/scripts/gaia_catalog.py --search "powerpoint" --top 5
```

Cache location: `~/.opencode/skills/gaia-tools/cache/apps.json`
TTL: 24 hours (override with `GAIA_CATALOG_TTL_HOURS=<hours>`)

---

## Core API flow (reference)

```
1. GET  /v1/apps                                               — list all public apps
2. POST /v1/apps/{appId}/sessions                             — start session → sessionId
3. POST /v1/sessions/{sessionId}/interactions                 — send prompt → interactionId
4. GET  /v1/sessions/{sessionId}/interactions/{interactionId} — poll: top-level status field
5. DELETE /v1/sessions/{sessionId}                            — cleanup (auto in chat())
```

Poll response schema (actual, not spec):
```json
{
  "id": "...",
  "sessionId": "...",
  "status": "in_progress" | "finished_successfully" | "error",
  "newAiMessages": [ { "body": { "text": "..." } } ]
}
```

**Apigee gotchas:**
- GET requests must NOT include `Content-Type: application/json` (triggers JSONThreatProtection)
- POST bodies must be sent as raw string (`data=json.dumps(body)`), not `json=body`
- `GET /v1/apps?status=public` returns 500 — use no filter, or `types=` only

---

## Custom tool headers (advanced)

For GAIA apps that call external tools needing their own auth (Jira PAT, etc.):

```python
extra_headers = {
    "tools": {
        "<entity-id-from-manifest>": {
            "Authorization": "Bearer <tool-token>"
        }
    }
}
client.chat(app_id="...", prompt="...", extra_headers=extra_headers)
```

Find the `entity-id` via `GET /v1/apps/{appId}/manifest` → `manifest.entities[].id`.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `401 Unauthorized` | Expired or missing token | Check `BMW_CLIENT_ID/SECRET` or `GAIA_CLIENT_ID/SECRET` |
| `401` with valid token | Wrong `GAIA_API_KEY` | Verify Apigee subscription is approved for PROD |
| `500` on `GET /v1/apps?status=public` | API bug — `status=` filter broken server-side | Remove `status=` param; filter client-side |
| `404 App not found` | Wrong `appId` or private app | Copy UUID from GAIA portal; confirm public status |
| Poll never finishes | Response uses different schema | Check `data["status"]` (top-level), not `data["messages"][].status` |
| Router returns no match | Task phrase too generic or specific | Try different keywords; use `--search` to explore |
| Cache stale | Auto-refresh failed (VPN) | Run `gaia_catalog.py --refresh` manually on VPN |
