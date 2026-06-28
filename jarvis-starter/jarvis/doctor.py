"""Home preflight ("doctor") — verify a fully-local setup and FAIL on any cloud
dependency. Run before a home session:  python -m jarvis.doctor

Checks: profile=home; LLM provider is local; the local endpoint is reachable and
serves the configured (tool-capable) model; embeddings are local; the egress
allowlist carries no cloud host; and no cloud credentials are set.
"""
from __future__ import annotations
import os, sys, json, urllib.request
from . import profile, egress
from . import llm_providers as providers

# Local models known to support OpenAI-style tool/function calling (the agent loop needs it).
TOOL_CAPABLE = ("qwen2.5-coder", "qwen2.5", "llama3.1", "llama3.2",
                "mistral-nemo", "command-r", "firefunction", "hermes3")


def _probe(url: str, timeout: float = 2.0):
    """GET a URL and parse JSON; return None on any failure. Injectable for tests."""
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:  # noqa: S310 (localhost only)
            return json.loads(r.read().decode("utf-8", "replace"))
    except Exception:
        return None


def _models_url(provider: str) -> str:
    return providers.OPENAI_COMPAT[provider]["base"].rstrip("/") + "/models"


def check(*, probe=_probe) -> dict:
    """Run all home-preflight checks. Returns {ok, checks:[{ok,label,detail}]}."""
    checks: list[dict] = []

    def add(ok, label, detail=""):
        checks.append({"ok": bool(ok), "label": label, "detail": detail})

    add(profile.is_home(), "JARVIS_PROFILE=home", os.environ.get("JARVIS_PROFILE", "(unset)"))

    provider = providers.provider_name()
    local_provider = provider in profile.LOCAL_PROVIDERS
    add(local_provider, f"LLM provider is local ({provider})",
        "" if local_provider else "set JARVIS_LLM_PROVIDER=ollama or lmstudio")

    if local_provider:
        model = providers.default_model(provider)
        data = probe(_models_url(provider))
        add(data is not None, f"{provider} endpoint reachable", _models_url(provider))
        if data is not None:
            ids = [m.get("id", "") for m in (data.get("data") or [])]
            present = any(model.split(":")[0] in mid or model in mid for mid in ids)
            add(present, f"model '{model}' available locally", f"served: {ids[:6]}")
        tool_ok = any(model.startswith(t) or t in model for t in TOOL_CAPABLE)
        add(tool_ok, f"model '{model}' is tool-capable",
            "" if tool_ok else f"agent loop needs function-calling; known-good: {TOOL_CAPABLE}")

    embed = os.environ.get("JARVIS_EMBED_ENGINE", "local")
    add(embed in profile.LOCAL_EMBED, f"embeddings are local ({embed})")

    al = egress.allowlist()
    add(egress.GATEWAY_HOST not in al, "egress allowlist has no cloud host", f"allow={sorted(al)}")

    leaked = [k for k in ("LLM_API_BEARER_TOKEN", "LLM_API_KEY", "ANTHROPIC_API_KEY") if os.environ.get(k)]
    add(not leaked, "no cloud credentials set", f"set: {leaked}" if leaked else "")

    return {"ok": all(c["ok"] for c in checks), "checks": checks}


def main(argv=None):
    report = check()
    for c in report["checks"]:
        mark = "OK" if c["ok"] else "XX"
        line = f"  [{mark}] {c['label']}"
        if c["detail"]:
            line += f"  — {c['detail']}"
        print(line)
    print("\nHOME PREFLIGHT:", "PASS ✅" if report["ok"] else "FAIL ❌")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
