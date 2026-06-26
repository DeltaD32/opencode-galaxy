# /// script
# requires-python = ">=3.10"
# dependencies = ["httpx", "python-dateutil"]
# ///
"""
copilot_llm.py – GitHub Copilot LLM integration
=================================================
Uses the GITHUB_TOKEN (PAT from bmw.ghe.com) to call GitHub Copilot Chat.

Auth flow (tried in order):
  1. Cached Copilot session token (file _copilot_token.json, ~3h TTL)
  2. PAT token-exchange  → GET bmw.ghe.com/api/v3/copilot_internal/v2/token
  3. OAuth device flow   → bmw.ghe.com/login/device  (once per session/day)
  4. Bare PAT as Bearer  → api.githubcopilot.com (fallback)

Device-flow trigger:
  When token exchange returns 401/403, the caller should invoke
  start_device_flow() and display the returned code to the user.
  Call poll_device_flow() every 5 s until authorized.
  After success, get_token() will return a valid token.

Thread-safety: all state is in a single _State object; calls are serialised
by the Flask/eventlet single-thread model.
"""

from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ── Config ───────────────────────────────────────────────────────────────────
GHE_HOST = os.environ.get("GITHUB_HOST", "bmw.ghe.com")
COPILOT_API_URL = os.environ.get(
    "COPILOT_API_URL", "https://api.githubcopilot.com/chat/completions"
)
COPILOT_MODEL = os.environ.get("COPILOT_MODEL", "gpt-4")
# VS Code Copilot extension client_id (for device flow)
_GHE_CLIENT_ID = "Iv1.b507a08c87ecfe98"

# Token cache — check both locations:
#   1. core/_copilot_token.json  (placed by _copilot_auth.py / user)
#   2. virtual-agency/_copilot_token.json  (saved by this module)
_TOKEN_CACHE_CORE = Path(__file__).parent / "_copilot_token.json"
_TOKEN_CACHE_ROOT = Path(__file__).parent.parent / "_copilot_token.json"
_TOKEN_CACHE = _TOKEN_CACHE_ROOT  # default save location

# Effective API URL — may be overridden by endpoints.api from cached token
_effective_api_url: str = COPILOT_API_URL


# ── Internal state ───────────────────────────────────────────────────────────
@dataclass
class _State:
    copilot_token: Optional[str] = None
    token_expires: float = 0.0  # unix timestamp
    oauth_token: Optional[str] = None  # GHE OAuth token (long-lived)
    # device flow in-progress
    device_code: Optional[str] = None
    user_code: Optional[str] = None
    verification_uri: Optional[str] = None
    device_interval: int = 5
    device_expires: float = 0.0


_state = _State()


# ── HTTP helpers ─────────────────────────────────────────────────────────────


def _proxy() -> Optional[str]:
    raw = (
        os.environ.get("HTTPS_PROXY")
        or os.environ.get("https_proxy")
        or os.environ.get("HTTP_PROXY")
        or os.environ.get("http_proxy")
        or ""
    )
    if raw.startswith("https://"):
        raw = "http://" + raw[len("https://") :]
    return raw or None


def _client(timeout: int = 60):
    """Return a httpx.Client configured for the BMW corporate proxy."""
    import httpx  # lazy import — httpx is installed

    proxy = _proxy()
    # BMW corporate proxy performs TLS interception.
    # Set BMW_CA_BUNDLE (or SSL_CERT_FILE) to your corporate CA bundle for proper verification.
    ca_bundle = os.environ.get("BMW_CA_BUNDLE") or os.environ.get("SSL_CERT_FILE")
    verify = ca_bundle if ca_bundle else False  # nosec B501
    if proxy:
        return httpx.Client(verify=verify, proxy=proxy, timeout=timeout)
    return httpx.Client(verify=verify, timeout=timeout)


# ── Token cache (file) ───────────────────────────────────────────────────────


def _save_cache(data: dict):
    """Save full token data dict to cache file."""
    try:
        _TOKEN_CACHE.write_text(json.dumps(data, indent=2))
        logger.debug("Saved Copilot token cache to %s", _TOKEN_CACHE)
    except Exception as e:
        logger.debug("Could not save Copilot token cache: %s", e)


def _load_cache() -> bool:
    """Load cached token if still valid (>5 min margin). Returns True on success.

    Checks ``core/_copilot_token.json`` first (user-placed), then the root
    ``virtual-agency/_copilot_token.json``.  Also reads ``endpoints.api``
    from the cached data and overrides the effective API URL so we use the
    correct BMW GHE Copilot proxy (copilot-api.bmw.ghe.com) instead of
    the public api.githubcopilot.com which is blocked by the BMW proxy.
    """
    global _effective_api_url
    for cache_path in (_TOKEN_CACHE_CORE, _TOKEN_CACHE_ROOT):
        try:
            if not cache_path.exists():
                continue
            data = json.loads(cache_path.read_text())
            exp = data.get("expires_at", 0)
            if isinstance(exp, (int, float)) and time.time() < exp - 300:
                _state.copilot_token = data["token"]
                _state.token_expires = float(exp)
                _state.oauth_token = data.get("oauth_token", "")
                # ── Read endpoints.api from the rich Copilot token response ──
                endpoints = data.get("endpoints", {})
                api_base = endpoints.get("api", "").rstrip("/")
                if api_base:
                    _effective_api_url = f"{api_base}/chat/completions"
                    logger.info("Copilot API URL overridden from cache: %s", _effective_api_url)
                logger.info(
                    "Loaded cached Copilot token from %s (expires %s, API=%s)",
                    cache_path.name,
                    time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(_state.token_expires)),
                    _effective_api_url,
                )
                return True
            # Session token expired but the OAuth token might still be usable
            oauth = data.get("oauth_token", "")
            if oauth:
                _state.oauth_token = oauth
                logger.debug(
                    "Session token expired but cached OAuth token preserved for re-exchange"
                )
        except Exception as e:
            logger.debug("Could not load Copilot cache %s: %s", cache_path, e)
    return False


def _reexchange_cached_oauth() -> bool:
    """Try to get a fresh Copilot session token using a previously cached OAuth token.

    After a successful device flow the long-lived OAuth token is saved in the
    cache file.  When the short-lived session token expires (~3 h), this
    function re-exchanges the OAuth token so the user never has to redo the
    device flow (unless the OAuth token is revoked).
    """
    # Check in-memory first (populated by _load_cache even on expiry)
    oauth = _state.oauth_token
    if not oauth:
        # Scan cache files for a saved oauth_token
        for cache_path in (_TOKEN_CACHE_CORE, _TOKEN_CACHE_ROOT):
            try:
                if not cache_path.exists():
                    continue
                data = json.loads(cache_path.read_text())
                oauth = data.get("oauth_token", "")
                if oauth:
                    break
            except Exception:
                pass
    if not oauth:
        return False
    logger.info("Attempting re-exchange of cached OAuth token for new Copilot session…")
    token = _exchange_pat_for_copilot_token(oauth)
    if token:
        logger.info("OAuth re-exchange succeeded — new Copilot session token obtained")
        return True
    logger.debug("OAuth re-exchange failed (token may be revoked)")
    return False


# ── Token exchange ───────────────────────────────────────────────────────────


def _exchange_pat_for_copilot_token(pat: str) -> Optional[str]:
    """Exchange a GitHub PAT (ghp_...) for a short-lived Copilot session token."""
    global _effective_api_url
    exchange_urls = [
        f"https://{GHE_HOST}/api/v3/copilot_internal/v2/token",
        f"https://{GHE_HOST}/api/v3/copilot_internal/token",
        "https://api.github.com/copilot_internal/v2/token",
    ]
    with _client() as c:
        for url in exchange_urls:
            try:
                r = c.get(
                    url,
                    headers={
                        "Authorization": f"token {pat}",
                        "Editor-Version": "vscode/1.96.0",
                    },
                )
                if r.status_code == 200:
                    data = r.json()
                    token = data.get("token")
                    exp = data.get("expires_at", "")
                    if isinstance(exp, str) and "T" in exp:
                        import dateutil.parser

                        expires = dateutil.parser.parse(exp).timestamp()
                    elif isinstance(exp, (int, float)):
                        expires = float(exp)
                    else:
                        expires = time.time() + 10800
                    if token:
                        _state.copilot_token = token
                        _state.token_expires = expires
                        # Read endpoints.api from the exchange response
                        endpoints = data.get("endpoints", {})
                        api_base = endpoints.get("api", "").rstrip("/")
                        if api_base:
                            _effective_api_url = f"{api_base}/chat/completions"
                        # Save the FULL response (preserves endpoints, sku, etc.)
                        data["oauth_token"] = pat
                        _save_cache(data)
                        logger.info(
                            "Got Copilot token via exchange at %s (API=%s)", url, _effective_api_url
                        )
                        return token
                elif r.status_code in (401, 403):
                    logger.debug("PAT exchange %s: %d (need device flow?)", url, r.status_code)
            except Exception as e:
                logger.debug("PAT exchange %s failed: %s", url, e)
    return None


def _exchange_oauth_for_copilot_token(oauth_token: str) -> Optional[str]:
    """Exchange a GHE OAuth token for a Copilot session token."""
    return _exchange_pat_for_copilot_token(oauth_token)  # same endpoint, same header


# ── Device flow ──────────────────────────────────────────────────────────────


def start_device_flow() -> dict:
    """Start OAuth device flow. Returns {user_code, verification_uri, device_code, interval, expires_in}."""
    with _client() as c:
        try:
            r = c.post(
                f"https://{GHE_HOST}/login/device/code",
                data={"client_id": _GHE_CLIENT_ID, "scope": "copilot"},
                headers={"Accept": "application/json"},
            )
            if r.status_code == 200:
                data = r.json()
                _state.device_code = data.get("device_code")
                _state.user_code = data.get("user_code")
                _state.verification_uri = data.get(
                    "verification_uri", f"https://{GHE_HOST}/login/device"
                )
                _state.device_interval = data.get("interval", 5)
                _state.device_expires = time.time() + data.get("expires_in", 900)
                return {
                    "ok": True,
                    "user_code": _state.user_code,
                    "verification_uri": _state.verification_uri,
                    "interval": _state.device_interval,
                    "expires_in": data.get("expires_in", 900),
                }
            return {
                "ok": False,
                "error": f"Device flow start failed: {r.status_code} {r.text[:200]}",
            }
        except Exception as e:
            return {"ok": False, "error": str(e)}


def poll_device_flow() -> dict:
    """Poll for device flow completion. Returns {ok, authorized, error}."""
    if not _state.device_code:
        return {"ok": False, "error": "No active device flow"}
    if time.time() > _state.device_expires:
        return {"ok": False, "error": "Device flow expired. Please start again."}

    with _client() as c:
        try:
            r = c.post(
                f"https://{GHE_HOST}/login/oauth/access_token",
                data={
                    "client_id": _GHE_CLIENT_ID,
                    "device_code": _state.device_code,
                    "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                },
                headers={"Accept": "application/json"},
            )
            result = r.json()
            if "access_token" in result:
                oauth_token = result["access_token"]
                _state.oauth_token = oauth_token
                # Exchange for Copilot session token
                copilot_token = _exchange_oauth_for_copilot_token(oauth_token)
                if copilot_token:
                    return {"ok": True, "authorized": True}
                # Fallback: save OAuth token itself for use as Bearer
                _state.copilot_token = oauth_token
                _state.token_expires = time.time() + 28800  # 8h
                _save_cache(
                    {
                        "token": oauth_token,
                        "expires_at": _state.token_expires,
                        "oauth_token": oauth_token,
                    }
                )
                return {"ok": True, "authorized": True}
            err = result.get("error", "")
            if err == "authorization_pending":
                return {"ok": True, "authorized": False, "pending": True}
            if err == "slow_down":
                _state.device_interval = min(_state.device_interval + 5, 30)
                return {"ok": True, "authorized": False, "pending": True, "slow_down": True}
            return {"ok": False, "error": result.get("error_description", err)}
        except Exception as e:
            return {"ok": False, "error": str(e)}


# ── Main public interface ─────────────────────────────────────────────────────


def auth_status() -> dict:
    """Return current authentication status.

    Return schema:
      {"ok": True,  "mode": "cached|pat_direct|exchanged",  "model": "..."}
      {"ok": False, "needs_device_flow": True/False,
       "user_code": "...", "verification_uri": "...", "interval": 5}
    """
    # 1. Already have a valid in-memory token
    if _state.copilot_token and time.time() < _state.token_expires - 300:
        return {"ok": True, "mode": "cached", "model": COPILOT_MODEL}

    # 2. Try file cache
    if _load_cache():
        return {"ok": True, "mode": "cached", "model": COPILOT_MODEL}

    # 3. Try re-exchanging a previously cached OAuth token (from earlier device flow)
    if _reexchange_cached_oauth():
        return {"ok": True, "mode": "exchanged", "model": COPILOT_MODEL}

    # 4. Try PAT exchange
    pat = os.environ.get("GITHUB_TOKEN", "")
    if pat:
        token = _exchange_pat_for_copilot_token(pat)
        if token:
            return {"ok": True, "mode": "exchanged", "model": COPILOT_MODEL}
        # Exchange returned 401 → device flow needed
        return {
            "ok": False,
            "needs_device_flow": True,
            "reason": "PAT token exchange returned 401 — OAuth authorisation required once.",
        }

    return {"ok": False, "needs_device_flow": False, "reason": "GITHUB_TOKEN not set in .env"}


def get_token() -> Optional[str]:
    """Return a valid Copilot token or None if unavailable."""
    status = auth_status()
    if status.get("ok"):
        return _state.copilot_token
    return None


def call_copilot(prompt: str, max_tokens: int = 600, system: str = "") -> dict:
    """Call GitHub Copilot chat completions.

    Returns:
      {"ok": True,  "result": "...", "mode": "copilot"}
      {"ok": False, "error": "...", "needs_auth": bool}
    """
    token = get_token()

    # If get_token() returned None, check WHY before falling back.
    # If device flow is needed, signal that immediately instead of
    # trying bare PAT (which will fail against BMW proxy anyway).
    if not token:
        status = auth_status()
        if status.get("needs_device_flow"):
            return {
                "ok": False,
                "error": status.get("reason", "GitHub Copilot authorisation required."),
                "needs_auth": True,
            }
        # Last resort: try bare PAT as Bearer (some GHE configs allow this)
        token = os.environ.get("GITHUB_TOKEN", "")
        if not token:
            return {
                "ok": False,
                "error": "No GitHub token available. Set GITHUB_TOKEN in .env",
                "needs_auth": True,
            }

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Editor-Version": "vscode/1.96.0",
    }
    payload = {
        "model": COPILOT_MODEL,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": 0.4,
    }

    logger.info(
        "Calling Copilot: %s  model=%s  tokens=%d", _effective_api_url, COPILOT_MODEL, max_tokens
    )
    # Use longer timeout for large prompts (compliance audits can take 60s+)
    call_timeout = max(60, max_tokens // 10)
    with _client(timeout=call_timeout) as c:
        try:
            r = c.post(_effective_api_url, headers=headers, json=payload)
            if r.status_code == 200:
                content = r.json()["choices"][0]["message"]["content"].strip()
                return {"ok": True, "result": content, "mode": "copilot"}
            if r.status_code in (401, 403):
                # Token expired or invalid — clear cache and signal re-auth
                _state.copilot_token = None
                _state.token_expires = 0.0
                try:
                    _TOKEN_CACHE.unlink(missing_ok=True)
                except Exception:
                    pass
                return {
                    "ok": False,
                    "error": f"Copilot token rejected ({r.status_code}). Re-authentication required.",
                    "needs_auth": True,
                }
            return {"ok": False, "error": f"Copilot API returned {r.status_code}: {r.text[:300]}"}
        except Exception as e:
            return {"ok": False, "error": str(e)}
