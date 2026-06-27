"""LLM client over the BMW LLM API (OpenAI-compatible chat/completions).

Verified against the stored docs:
  base_url = https://api.gcp.cloud.bmw/llmapi/v1
  auth     = Authorization: Bearer $LLM_API_BEARER_TOKEN  (+ LLM_API_KEY)
  tool use = OpenAI function-calling (tools[], msg.tool_calls, role:'tool')
  models   = provider/model  (default: anthropic/claude-sonnet-4-6)
  NOTE: no streaming inside the tool loop (tool_call ids need complete responses).
"""
from __future__ import annotations
import os, time

DEFAULT_MODEL = os.environ.get("JARVIS_MODEL", "anthropic/claude-sonnet-4-6")
BASE_URL = os.environ.get("LLM_API_BASE_URL", "https://api.gcp.cloud.bmw/llmapi/v1")


def _client():
    from openai import OpenAI  # imported lazily so tests can run without the package
    headers = {}
    tok = os.environ.get("LLM_API_BEARER_TOKEN")
    if tok:
        headers["Authorization"] = f"Bearer {tok}"
    return OpenAI(base_url=BASE_URL, api_key=os.environ.get("LLM_API_KEY", "unused"),
                  default_headers=headers or None)


def complete(messages, tools=None, model=None, max_retries=4):
    """One chat/completions call. Returns the assistant message object
    (has .content and .tool_calls). Retries with backoff on transient errors."""
    model = model or DEFAULT_MODEL
    client = _client()
    delay = 1.0
    for attempt in range(max_retries):
        try:
            resp = client.chat.completions.create(
                model=model, messages=messages,
                tools=tools or None,
            )
            return resp.choices[0].message
        except Exception as e:  # noqa: BLE001 — narrow in production (RateLimit/APIError)
            if attempt == max_retries - 1:
                raise
            time.sleep(delay)
            delay *= 2
