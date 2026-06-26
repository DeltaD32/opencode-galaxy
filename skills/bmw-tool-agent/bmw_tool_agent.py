"""
bmw_tool_agent.py
=================
BMW Tool-Calling ReAct Agent — basic mode boilerplate.

Extracted from ~/.opencode/skills/bmw-tool-agent/SKILL.md — single source of truth.
For Advisor-Enhanced mode see bmw_advisor.py in the same directory.

Usage:
    import sys, pathlib
    sys.path.insert(0, str(pathlib.Path.home() / ".opencode/skills/bmw-tool-agent"))
    from bmw_tool_agent import run_agent, make_tool

    TOOLS    = [make_tool("get_jira_issue", "Fetch a Jira issue", {...schema...})]
    DISPATCH = {"get_jira_issue": lambda args: fetch_jira(args["issue_key"])}

    answer = run_agent("What is the status of AI4D-123?", tools=TOOLS, dispatch=DISPATCH)
    print(answer)
"""

from __future__ import annotations

import json
import os
import pathlib

try:
    import httpx
    from openai import OpenAI
except ImportError as exc:
    raise ImportError(
        "bmw_tool_agent requires 'openai' and 'httpx'. "
        "Use the clipjoint venv: ~/.opencode/plugins/clipjoint/.venv/bin/python3"
    ) from exc

_DEFAULT_CA = str(
    pathlib.Path.home() / ".opencode/plugins/clipjoint/BMW_Trusted_Certificates_Latest.pem"
)
_DEFAULT_MODEL  = "gpt-4o"
_DEFAULT_SYSTEM = (
    "You are a helpful assistant with access to tools. "
    "Think step by step before calling a tool."
)


# ─────────────────────────────────────────────
# BMW auth client
# ─────────────────────────────────────────────
def _bmw_client(model: str = _DEFAULT_MODEL) -> tuple[OpenAI, str]:
    """
    Return (configured OpenAI client, model_name) for the BMW LLM API.

    Reads credentials from environment variables:
        LLM_API_BASE_URL       (default: https://api.gcp.cloud.bmw/llmapi/v1)
        LLM_API_BEARER_TOKEN   (OAuth2 token — auto-refreshed by opencode-bmw)
        LLM_API_KEY            (API gateway key)
        BMW_CA_BUNDLE          (optional — path to BMW CA cert)
    """
    ca = os.environ.get("BMW_CA_BUNDLE") or _DEFAULT_CA
    client = OpenAI(
        base_url=os.environ.get("LLM_API_BASE_URL",
                                "https://api.gcp.cloud.bmw/llmapi/v1"),
        api_key=os.environ.get("LLM_API_KEY", "unused"),
        http_client=httpx.Client(
            headers={"x-apikey": os.environ["LLM_API_KEY"]},
            verify=ca if pathlib.Path(ca).exists() else True,
        ),
        default_headers={"Authorization": f"Bearer {os.environ['LLM_API_BEARER_TOKEN']}"},
    )
    return client, model


# ─────────────────────────────────────────────
# ReAct agent loop
# ─────────────────────────────────────────────
def run_agent(
    prompt: str,
    tools: list[dict],
    dispatch: dict[str, callable],
    system: str = _DEFAULT_SYSTEM,
    model: str = _DEFAULT_MODEL,
    max_steps: int = 10,
) -> str:
    """
    Run a ReAct (Reasoning + Acting) agent loop.

    Continues until the model stops calling tools or max_steps is reached.

    Args:
        prompt    : The user's request.
        tools     : Tool definitions in OpenAI function-calling schema.
                    Build them with make_tool().
        dispatch  : Mapping from tool name → callable(args: dict) -> str.
        system    : System prompt for the agent.
        model     : BMW LLM API model name (default: gpt-4o).
        max_steps : Safety cap on iterations (default: 10).

    Returns:
        The model's final text response as a string.

    Raises:
        KeyError    : If LLM_API_KEY / LLM_API_BEARER_TOKEN are not set.
        RuntimeError: If agent does not converge within max_steps.
    """
    client, model = _bmw_client(model)
    messages = [
        {"role": "system", "content": system},
        {"role": "user",   "content": prompt},
    ]

    for _ in range(max_steps):
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools,
            tool_choice="auto",
        )
        msg = response.choices[0].message
        messages.append(msg)

        if not msg.tool_calls:
            return msg.content or ""

        for tc in msg.tool_calls:
            name = tc.function.name
            args = json.loads(tc.function.arguments)
            try:
                fn = dispatch.get(name)
                result = fn(args) if fn else f"Unknown tool: {name}"
            except Exception as exc:
                result = f"Tool error: {exc}"
            messages.append({
                "role":         "tool",
                "tool_call_id": tc.id,
                "content":      str(result),
            })

    return "Agent did not converge within max_steps."


# ─────────────────────────────────────────────
# Tool schema helper
# ─────────────────────────────────────────────
def make_tool(name: str, description: str, parameters: dict) -> dict:
    """
    Build a tool definition in OpenAI function-calling format.

    Args:
        name        : Function name (snake_case).
        description : What this tool does (shown to the model).
        parameters  : JSON Schema object describing the arguments.

    Example:
        make_tool(
            name="get_jira_issue",
            description="Fetch a Jira issue by key.",
            parameters={
                "type": "object",
                "properties": {
                    "issue_key": {"type": "string", "description": "e.g. AI4D-123"}
                },
                "required": ["issue_key"],
            }
        )
    """
    return {
        "type": "function",
        "function": {
            "name":        name,
            "description": description,
            "parameters":  parameters,
        },
    }
