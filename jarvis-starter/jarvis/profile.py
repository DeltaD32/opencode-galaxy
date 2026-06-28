"""Run profile — `JARVIS_PROFILE=home` enforces a fully-local, no-cloud setup.

This is an ENFORCED switch, not just defaults: cloud LLM providers and the cloud
embedding engine are refused in code (the OpenAI/Anthropic SDKs open their own
connections that never pass through `egress.check`, so defaults alone would not
guarantee privacy). No effect unless the env var is set — non-home runs are
unchanged.
"""
from __future__ import annotations
import os

LOCAL_PROVIDERS = {"ollama", "lmstudio"}
LOCAL_EMBED = {"local", "hash"}


def is_home() -> bool:
    return os.environ.get("JARVIS_PROFILE", "").lower() == "home"


def enforce_provider(name: str) -> str:
    """Raise in home mode if `name` is a cloud LLM provider; else return it."""
    if is_home() and name not in LOCAL_PROVIDERS:
        raise RuntimeError(
            f"JARVIS_PROFILE=home forbids cloud LLM provider '{name}'. "
            f"Use one of {sorted(LOCAL_PROVIDERS)} (Ollama / LM Studio).")
    return name


def enforce_embed(name: str) -> str:
    """Raise in home mode if `name` is the cloud embedding engine; else return it."""
    if is_home() and name not in LOCAL_EMBED:
        raise RuntimeError(
            f"JARVIS_PROFILE=home forbids cloud embedding engine '{name}'. "
            f"Use one of {sorted(LOCAL_EMBED)}.")
    return name
