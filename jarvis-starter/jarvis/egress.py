"""Egress allowlist (Module E / build-guide Phase 8).

Default-deny network policy: outbound is allowed ONLY to the LLM gateway and the
local home-LLM endpoints (Ollama / LM Studio on localhost). Everything else is
denied. This is the single source of truth — `check()` is called at every egress
point (see `tools.http_get`). Widening the allowlist is part of the immutable
floor (Module F.4): the system must not relax it autonomously.

Extra hosts may be permitted operationally via `JARVIS_EGRESS_ALLOW` (comma-sep).
"""
from __future__ import annotations
import os
from urllib.parse import urlparse

# Gateway + localhost (ollama 11434, lmstudio 1234 — ports are not part of host matching).
DEFAULT_ALLOW = {"api.gcp.cloud.bmw", "localhost", "127.0.0.1", "::1"}


def allowlist() -> set[str]:
    hosts = set(DEFAULT_ALLOW)
    extra = os.environ.get("JARVIS_EGRESS_ALLOW", "")
    hosts |= {h.strip().lower() for h in extra.split(",") if h.strip()}
    return hosts


def host_of(url_or_host: str) -> str:
    """Extract the bare hostname from a URL, host:port, or bare host."""
    s = (url_or_host or "").strip()
    if "://" in s:
        return (urlparse(s).hostname or "").lower()
    netloc = s.split("/")[0]
    if "@" in netloc:
        netloc = netloc.split("@")[-1]
    if netloc.startswith("["):  # bracketed IPv6, optional :port
        return netloc[1:].split("]")[0].lower()
    if ":" in netloc:           # host:port
        netloc = netloc.rsplit(":", 1)[0]
    return netloc.lower()


def is_allowed(url_or_host: str) -> bool:
    return host_of(url_or_host) in allowlist()


def check(url: str) -> str:
    """Return the url if its host is allowed; raise PermissionError otherwise."""
    host = host_of(url)
    if host not in allowlist():
        raise PermissionError(
            f"egress to '{host}' denied (default-deny; allow: {sorted(allowlist())})")
    return url
