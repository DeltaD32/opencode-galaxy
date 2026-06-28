"""LLM client — provider-swappable so JARVIS runs at home or on the gateway.

Select the backend with `JARVIS_LLM_PROVIDER` (default `ollama` for home use):
  ollama | lmstudio  → local, OpenAI-compatible (no key)
  bmw                → BMW gateway, OpenAI-compatible (bearer token)
  anthropic          → Claude public API (Messages API; adapted)

`complete()` keeps a stable surface — it returns an assistant message with
`.content` and `.tool_calls` — so the agent runtime loop is provider-agnostic.
  NOTE: no streaming inside the tool loop (tool_call ids need complete responses).
"""
from __future__ import annotations
import os, time
from . import llm_providers as providers
from . import profile

# Back-compat constant (selection actually happens per call, honouring env changes).
DEFAULT_MODEL = os.environ.get("JARVIS_MODEL", providers.default_model())


def complete(messages, tools=None, model=None, max_retries=4):
    """One completion call against the configured provider. Returns the assistant
    message object (`.content`, `.tool_calls`). Retries with backoff on errors."""
    provider = providers.provider_name()
    profile.enforce_provider(provider)  # home mode: refuse cloud before any network
    chosen = model or providers.default_model(provider)
    delay = 1.0
    for attempt in range(max_retries):
        try:
            if provider == "anthropic":
                return providers.complete_anthropic(messages, tools, chosen)
            compat = provider if provider in providers.OPENAI_COMPAT else providers.DEFAULT_PROVIDER
            return providers.complete_openai(compat, messages, tools, chosen)
        except Exception:  # noqa: BLE001 — narrow in production (RateLimit/APIError)
            if attempt == max_retries - 1:
                raise
            time.sleep(delay)
            delay *= 2
