---
name: bmw-tool-agent
description: >
  Build BMW-internal tool-calling agents using the ReAct (Reasoning + Acting)
  loop pattern via the BMW LLM API. Wraps any internal system (SAP, Jira,
  GAIA, REST APIs) as a typed tool and runs a multi-turn agent loop with
  exponential backoff retry. Provides complete boilerplate: BMW auth client,
  tool schema builder, dispatch router, and the ReAct loop itself.
  Also provides an Advisor-Enhanced mode (bmw_advisor.py) where a fast executor
  model is guided mid-run by a higher-intelligence advisor model — a client-side
  implementation of the Anthropic advisor-tool pattern using any two BMW LLM API
  models. Includes 7 named profiles (speed/balanced/quality/deep/claude/gpt/economy),
  full model catalogue with tier ratings, recommend() heuristic, and RunStats tracking.
  Use when a user wants to build an agent that calls internal BMW APIs as tools,
  automate multi-step workflows that need external data lookups, scaffold
  a new agentic Python script from scratch, or wants advisor-enhanced quality.
  Trigger phrases: "build a tool-calling agent", "react agent", "tool calling",
  "multi-step agent", "agent loop", "function calling", "wrap an API as a tool",
  "agentic workflow", "bmw tool agent", "advisor agent", "advisor model",
  "executor advisor", "dual model agent".
license: Proprietary
metadata:
  authors:
    - OpenCode Config
  version: "2.1.0"
  tags:
    - agent
    - tool-calling
    - react
    - bmw-llm-api
    - agentic
    - advisor
    - dual-model
---

# bmw-tool-agent

Build multi-turn **ReAct** agents that call BMW-internal systems as tools.
Both modules are pre-installed — **no code generation needed**.

| Mode | Module | When to use |
|---|---|---|
| **Basic ReAct** | `bmw_tool_agent.py` | Simple loops; known workflow; cost-sensitive |
| **Advisor-Enhanced** | `bmw_advisor.py` | Complex tasks; high-stakes; quality matters |

## Python path

```python
import sys, pathlib
sys.path.insert(0, str(pathlib.Path.home() / ".opencode/skills/bmw-tool-agent"))
from bmw_tool_agent import run_agent, make_tool
from bmw_advisor   import run_agent_advised, recommend, PROFILES
```

Use the clipjoint venv: `~/.opencode/plugins/clipjoint/.venv/bin/python3`

## Basic mode — minimal example

```python
TOOLS = [make_tool(
    name="get_jira_issue",
    description="Fetch a Jira issue by key.",
    parameters={
        "type": "object",
        "properties": {"issue_key": {"type": "string"}},
        "required": ["issue_key"],
    }
)]
DISPATCH = {"get_jira_issue": lambda args: fetch_jira(args["issue_key"])}

answer = run_agent("What is the status of AI4D-123?", tools=TOOLS, dispatch=DISPATCH)
```

## Advisor mode — pick a profile then run

```python
profile = recommend("analyse Jira epic and identify blockers")  # → "quality"
result  = run_agent_advised(prompt="...", tools=TOOLS, dispatch=DISPATCH, profile=profile)

# With cost stats
result, stats = run_agent_advised(..., return_stats=True)
print(stats.summary())
```

## Named profiles

| Profile | Executor | Advisor | Best for |
|---|---|---|---|
| `speed` | `claude-haiku-4-5` | `gpt-4o` | Fast, low-stakes |
| `economy` | `gpt-4o-mini` | `gpt-4o` | Batch / high-volume |
| `balanced` | `gpt-4o` | `claude-sonnet-4-6` | **Default — most workflows** |
| `claude` | `claude-haiku-4-5` | `claude-sonnet-4-6` | Pure Anthropic |
| `gpt` | `gpt-4o` | `gpt-5` | Pure OpenAI |
| `quality` | `claude-sonnet-4-6` | `gpt-5` | Code / research / review |
| `deep` | `claude-sonnet-4-6` | `o3` | Risk / planning / architecture |

## Model catalogue (16 models, tool-calling support)

| Model | Tier | Best as |
|---|---|---|
| `anthropic/claude-sonnet-4-6` | 1 | Executor (complex) · Advisor |
| `openai/gpt-5` | 1 | Executor (complex) · Advisor |
| `openai/gpt-5.4` | 1 | Executor (complex) · Advisor |
| `openai/o3` | 1 | Advisor (deep reasoning) |
| `anthropic/claude-sonnet-4-5` | 2 | Executor · Advisor (light) |
| `openai/gpt-5.1` | 2 | Executor · Advisor (light) |
| `openai/gpt-4o` | 2 | Executor (default) |
| `openai/o4-mini` | 2 | Advisor (lighter reasoning) |
| `anthropic/claude-haiku-4-5` | 3 | Executor (simple/fast) |
| `openai/gpt-4o-mini` | 3 | Executor (simple) |

**Rule:** advisor tier ≤ executor tier.

## Agent instructions (when a user asks to build one)

1. Identify tools — what external systems are called (Jira, SAP, GAIA, REST)?
2. Run `recommend(task_description)` to suggest a profile.
3. Build tool schemas with `make_tool()`.
4. Write dispatch callables — thin API wrappers.
5. Choose mode: simple/cost-sensitive → `run_agent()`; complex/quality → `run_agent_advised()`.

For GAIA tools specifically, use the `gaia-tools` skill — it handles session/interaction/poll auth.

## Environment variables

| Variable | Description |
|---|---|
| `LLM_API_BASE_URL` | `https://api.gcp.cloud.bmw/llmapi/v1` |
| `LLM_API_BEARER_TOKEN` | OAuth2 token (auto-refreshed by `opencode-bmw`) |
| `LLM_API_KEY` | BMW API gateway key |
| `BMW_CA_BUNDLE` | Path to BMW CA cert (optional) |

## Key details

- **Max steps default: 10** — increase for complex multi-tool workflows
- **Parallel tool calls** — if model calls multiple tools in one step, all execute before next LLM call
- **Claude + multiple system prompts** — `bmw_advisor.py` handles this automatically (BMW LLM API constraint)
- **Streaming** — not supported in loop (tool call IDs require complete responses)

## Troubleshooting

| Symptom | Fix |
|---|---|
| `KeyError: 'LLM_API_KEY'` | `source ~/.config/opencode/load-secrets.sh` |
| Agent loops without stopping | Add tool-use guard in system prompt or lower `max_steps` |
| `Unknown tool: <name>` | Check `dispatch` keys match `tools[].function.name` exactly |
| `400: multiple system prompts` | Use `bmw_advisor.py` — it handles this automatically |
| `ValueError: Unknown profile` | Valid: `speed`, `economy`, `balanced`, `claude`, `gpt`, `quality`, `deep` |
