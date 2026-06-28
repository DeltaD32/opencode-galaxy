"""Pluggable LLM providers — run JARVIS at home or on the gateway.

Select with `JARVIS_LLM_PROVIDER`:
  ollama    → local Ollama   (OpenAI-compatible at http://localhost:11434/v1)
  lmstudio  → local LM Studio (OpenAI-compatible at http://localhost:1234/v1)
  bmw       → BMW gateway     (OpenAI-compatible, bearer token)
  anthropic → Claude public API (Messages API; adapted to .content/.tool_calls)

Every path returns a message object exposing `.content` and `.tool_calls`, so the
agent runtime loop (`runtime.py`) is provider-agnostic and unchanged.
"""
from __future__ import annotations
import os, json, types

# OpenAI-compatible providers share one client path.
OPENAI_COMPAT = {
    "ollama":   {"base": "http://localhost:11434/v1", "key_env": None, "bearer_env": None,
                 "default_model": "llama3.1"},
    "lmstudio": {"base": "http://localhost:1234/v1",  "key_env": None, "bearer_env": None,
                 "default_model": "local-model"},
    "bmw":      {"base": "https://api.gcp.cloud.bmw/llmapi/v1", "key_env": "LLM_API_KEY",
                 "bearer_env": "LLM_API_BEARER_TOKEN", "default_model": "anthropic/claude-sonnet-4-6"},
}
DEFAULT_PROVIDER = "ollama"  # home-first


def provider_name() -> str:
    return os.environ.get("JARVIS_LLM_PROVIDER", DEFAULT_PROVIDER).lower()


def default_model(provider: str | None = None) -> str:
    provider = provider or provider_name()
    if provider in OPENAI_COMPAT:
        return os.environ.get("JARVIS_MODEL", OPENAI_COMPAT[provider]["default_model"])
    if provider == "anthropic":
        return os.environ.get("JARVIS_MODEL", "claude-sonnet-4-6")
    return os.environ.get("JARVIS_MODEL", OPENAI_COMPAT[DEFAULT_PROVIDER]["default_model"])


# ── OpenAI-compatible path (ollama / lmstudio / bmw) ────────────────────────
def make_openai_client(provider: str, *, _factory=None):
    cfg = OPENAI_COMPAT[provider]
    # bmw's base may be overridden by env; local providers are fixed.
    base = os.environ.get("LLM_API_BASE_URL", cfg["base"]) if provider == "bmw" else cfg["base"]
    headers = {}
    bearer_env = cfg.get("bearer_env")
    if bearer_env and os.environ.get(bearer_env):
        headers["Authorization"] = f"Bearer {os.environ[bearer_env]}"
    key = os.environ.get(cfg["key_env"], "unused") if cfg.get("key_env") else "unused"
    factory = _factory
    if factory is None:
        from openai import OpenAI  # lazy — only the chosen provider's SDK is needed
        factory = OpenAI
    return factory(base_url=base, api_key=key, default_headers=headers or None)


def complete_openai(provider: str, messages, tools, model, *, _factory=None):
    client = make_openai_client(provider, _factory=_factory)
    resp = client.chat.completions.create(model=model, messages=messages, tools=tools or None)
    return resp.choices[0].message


# ── Anthropic public API path (adapted to the OpenAI-style message shape) ────
def _split_system(messages):
    system, conv = "", []
    for m in messages:
        if m.get("role") == "system":
            system += (m.get("content") or "") + "\n"
        else:
            conv.append({"role": m["role"], "content": m.get("content") or ""})
    return system.strip(), conv


def _to_anthropic_tool(t):
    f = t["function"]
    return {"name": f["name"], "description": f.get("description", ""),
            "input_schema": f.get("parameters", {})}


class _AnthropicMessage:
    """Normalizes an Anthropic response to .content (text) + .tool_calls."""
    def __init__(self, resp):
        text, calls = "", []
        for block in getattr(resp, "content", None) or []:
            btype = getattr(block, "type", None)
            if btype == "text":
                text += getattr(block, "text", "")
            elif btype == "tool_use":
                calls.append(types.SimpleNamespace(
                    id=getattr(block, "id", ""), type="function",
                    function=types.SimpleNamespace(
                        name=getattr(block, "name", ""),
                        arguments=json.dumps(getattr(block, "input", {}) or {}))))
        self.content = text or None
        self.tool_calls = calls or None


def complete_anthropic(messages, tools, model, *, _factory=None):
    factory = _factory
    if factory is None:
        from anthropic import Anthropic  # lazy
        factory = Anthropic
    client = factory(api_key=os.environ.get("ANTHROPIC_API_KEY", "unused"))
    system, conv = _split_system(messages)
    a_tools = [_to_anthropic_tool(t) for t in tools] if tools else None
    resp = client.messages.create(model=model, max_tokens=4096,
                                  system=system or None, messages=conv, tools=a_tools)
    return _AnthropicMessage(resp)
