# /// script
# requires-python = ">=3.10"
# dependencies = ["requests"]
# ///
"""
gaia_client.py
==============
Reusable Python client for the BMW GAIA API.

Authentication: M2M WebEAM OAuth2 (client_credentials) — same flow as bmw_client.py.
Gateway: Apigee at https://api.bmwgroup.net/gaia (PROD)

Required environment variables:
    GAIA_API_KEY        — Apigee x-apikey for the GAIA product
    GAIA_CLIENT_ID      — WebEAM M2M client ID
    GAIA_CLIENT_SECRET  — WebEAM M2M client secret

Optional:
    GAIA_ENV            — 'int' or 'prod' (default: prod)
    GAIA_CA_BUNDLE      — path to BMW CA cert (default: clipjoint bundle)

Usage:
    from gaia_client import GaiaClient

    client = GaiaClient()
    apps = client.list_apps(types="tool,bot", status="public")
    answer = client.chat(app_id="<uuid>", prompt="What is the BMW EV strategy?")
    print(answer)
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

import requests

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_ENVIRONMENTS = {
    "prod": {
        "base_url": "https://api.bmwgroup.net/gaia",
        "auth_endpoint": (
            "https://auth.bmwgroup.net/auth/oauth2/realms/root/realms/"
            "machine2machine/access_token"
        ),
    },
    "int": {
        "base_url": "https://api.bmwgroup.net/gaia-int",
        "auth_endpoint": (
            "https://auth-i.bmwgroup.net/auth/oauth2/realms/root/realms/"
            "machine2machine/access_token"
        ),
    },
}

_DEFAULT_CA = str(
    Path.home()
    / ".opencode/plugins/clipjoint/BMW_Trusted_Certificates_Latest.pem"
)

_POLL_INTERVAL_S = 2
_POLL_MAX_ATTEMPTS = 30  # 60s total


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------


class GaiaClient:
    """Thin wrapper around the GAIA REST API.

    All credentials are read from environment variables on construction.
    The OAuth2 token is fetched lazily on first API call and cached for reuse.
    """

    def __init__(self) -> None:
        env_name = os.environ.get("GAIA_ENV", "prod").lower()
        env = _ENVIRONMENTS.get(env_name, _ENVIRONMENTS["prod"])

        self.base_url: str = env["base_url"]
        self._auth_endpoint: str = env["auth_endpoint"]

        self._api_key: str = self._require("GAIA_API_KEY")
        self._client_id: str = self._require_with_fallback(
            "GAIA_CLIENT_ID", "BMW_CLIENT_ID"
        )
        self._client_secret: str = self._require_with_fallback(
            "GAIA_CLIENT_SECRET", "BMW_CLIENT_SECRET"
        )

        ca = os.environ.get("GAIA_CA_BUNDLE") or _DEFAULT_CA
        self._verify: str | bool = ca if Path(ca).exists() else True

        self._token: str | None = None

    # ------------------------------------------------------------------
    # Auth
    # ------------------------------------------------------------------

    @staticmethod
    def _require(name: str) -> str:
        val = os.environ.get(name, "").strip()
        if not val:
            raise EnvironmentError(
                f"[gaia_client] Required env var '{name}' is not set.\n"
                f"  Add it to ~/.config/opencode/.env or export it before running."
            )
        return val

    @staticmethod
    def _require_with_fallback(name: str, fallback: str) -> str:
        """Return the value of env var ``name``, or ``fallback`` if not set.

        Useful for credentials that are shared with the BMW LLM API M2M identity:
            GAIA_CLIENT_ID     → falls back to BMW_CLIENT_ID
            GAIA_CLIENT_SECRET → falls back to BMW_CLIENT_SECRET
        """
        val = os.environ.get(name, "").strip()
        if val:
            return val
        val = os.environ.get(fallback, "").strip()
        if val:
            return val
        raise EnvironmentError(
            f"[gaia_client] Neither '{name}' nor '{fallback}' is set.\n"
            f"  Set '{name}' explicitly, or ensure '{fallback}' is available\n"
            f"  (loaded via load-secrets.sh or exported in the shell)."
        )

    def _get_token(self) -> str:
        """Fetch (or return cached) OAuth2 bearer token from WebEAM."""
        if self._token:
            return self._token
        resp = requests.post(
            self._auth_endpoint,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "grant_type": "client_credentials",
                "client_id": self._client_id,
                "client_secret": self._client_secret,
                "scope": "machine2machine",
            },
            verify=self._verify,
            timeout=30,
        )
        resp.raise_for_status()
        self._token = resp.json()["access_token"]
        return self._token

    def _headers(self, extra: dict | None = None, include_content_type: bool = False) -> dict:
        """Build request headers.

        Args:
            extra:                Optional dict serialised into X-Gaia-Extra-Headers.
            include_content_type: Set True for POST/PUT requests that send a JSON body.
                                  Leave False (default) for GET/DELETE — Apigee's
                                  JSONThreatProtection policy rejects GET requests that
                                  carry a Content-Type without a body.
        """
        h = {
            "Authorization": f"Bearer {self._get_token()}",
            "x-apikey": self._api_key,
        }
        if include_content_type:
            h["Content-Type"] = "application/json"
        if extra:
            h["X-Gaia-Extra-Headers"] = json.dumps(extra)
        return h

    # ------------------------------------------------------------------
    # App discovery
    # ------------------------------------------------------------------

    def list_apps(
        self,
        status: str | None = "public",
        types: str | None = None,
    ) -> dict:
        """Return all GAIA apps, optionally filtered by status and type.

        Args:
            status: e.g. 'public' — filter by app status.
            types:  comma-separated, e.g. 'tool,bot' — filter by app type.

        Returns:
            dict with key 'apps': list of App objects.
        """
        params: dict[str, str] = {}
        if status:
            params["status"] = status
        if types:
            params["types"] = types

        resp = requests.get(
            f"{self.base_url}/v1/apps",
            headers=self._headers(),
            params=params,
            verify=self._verify,
            timeout=60,   # catalog can be large (500+ apps)
        )
        resp.raise_for_status()
        raw = resp.json()
        # API returns a raw list, not {"apps": [...]}.  Normalise to list.
        return raw if isinstance(raw, list) else raw.get("apps", [])

    def get_app(self, app_id: str) -> dict:
        """Get full details for a single app by its UUID."""
        resp = requests.get(
            f"{self.base_url}/v1/apps/{app_id}",
            headers=self._headers(),
            verify=self._verify,
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()

    def get_app_tools(self, app_id: str) -> dict:
        """Return the tools configured for a specific app."""
        resp = requests.get(
            f"{self.base_url}/v1/apps/{app_id}/tools",
            headers=self._headers(),
            verify=self._verify,
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()

    def get_app_manifest(self, app_id: str) -> dict:
        """Return the manifest for an app (includes entity IDs for extra headers)."""
        resp = requests.get(
            f"{self.base_url}/v1/apps/{app_id}/manifest",
            headers=self._headers(),
            verify=self._verify,
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()

    # ------------------------------------------------------------------
    # Resource registry — discover public MCP / A2A tools
    # ------------------------------------------------------------------

    def list_resources(
        self,
        visibility: str = "public",
        resource_type: str | None = None,
        search: str | None = None,
        limit: int = 50,
    ) -> list[dict]:
        """List public resources (MCP servers, A2A tools) from the GAIA registry.

        Args:
            visibility:     'public', 'private', 'all', or 'accessible'.
            resource_type:  'MCP' or 'A2A' (optional filter).
            search:         text search in name/description.
            limit:          max results (1–500).

        Returns:
            List of RegistryResource objects.
        """
        params: dict[str, Any] = {"visibility": visibility, "limit": limit}
        if resource_type:
            params["resource_type"] = resource_type
        if search:
            params["search"] = search

        resp = requests.get(
            f"{self.base_url}/v1/resources",
            headers=self._headers(),
            params=params,
            verify=self._verify,
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()

    # ------------------------------------------------------------------
    # Session lifecycle
    # ------------------------------------------------------------------

    def start_session(self, app_id: str) -> str:
        """Create a new session for an app. Returns sessionId.

        Note: we send data="{}" (raw string) rather than json={} to satisfy
        Apigee's JSONThreatProtection policy, which rejects empty body POSTs.
        """
        resp = requests.post(
            f"{self.base_url}/v1/apps/{app_id}/sessions",
            headers=self._headers(include_content_type=True),
            data="{}",           # raw string — avoids Apigee JSONThreatProtection rejection
            verify=self._verify,
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()["sessionId"]

    def delete_session(self, session_id: str) -> None:
        """Delete a session and release its resources."""
        requests.delete(
            f"{self.base_url}/v1/sessions/{session_id}",
            headers=self._headers(),
            verify=self._verify,
            timeout=30,
        )

    # ------------------------------------------------------------------
    # Interaction (send prompt + poll)
    # ------------------------------------------------------------------

    def create_interaction(
        self,
        session_id: str,
        prompt: str,
        chat_history: list[dict] | None = None,
        extra_headers: dict | None = None,
    ) -> str:
        """Send a prompt to a session. Returns interactionId."""
        body: dict[str, Any] = {"prompt": prompt}
        if chat_history:
            body["chatHistory"] = chat_history

        resp = requests.post(
            f"{self.base_url}/v1/sessions/{session_id}/interactions",
            headers=self._headers(extra=extra_headers, include_content_type=True),
            data=json.dumps(body),   # raw string — consistent with Apigee policy
            verify=self._verify,
            timeout=60,
        )
        resp.raise_for_status()
        return resp.json()["interactionId"]

    def poll_interaction(
        self,
        session_id: str,
        interaction_id: str,
        interval: float = _POLL_INTERVAL_S,
        max_attempts: int = _POLL_MAX_ATTEMPTS,
    ) -> dict:
        """Poll until the interaction finishes. Returns the final Interaction object.

        The GAIA API response schema uses a top-level ``status`` field and a
        ``newAiMessages`` list, not a nested ``messages[].status`` structure:

            {
                "id": "...",
                "sessionId": "...",
                "status": "in_progress" | "finished_successfully" | "error",
                "newAiMessages": [ { "body": { "text": "..." }, ... } ],
                ...
            }

        Raises:
            TimeoutError: if max_attempts is exceeded without a terminal status.
            RuntimeError: if the interaction ends with status 'error'.
        """
        for attempt in range(max_attempts):
            resp = requests.get(
                f"{self.base_url}/v1/sessions/{session_id}/interactions/{interaction_id}",
                headers=self._headers(),
                verify=self._verify,
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()

            top_status = data.get("status", "")
            if top_status == "finished_successfully":
                return data
            if top_status == "error":
                raise RuntimeError(f"GAIA interaction failed: {data}")

            time.sleep(interval)

        raise TimeoutError(
            f"GAIA interaction did not finish after {max_attempts * interval:.0f}s. "
            f"interactionId={interaction_id}"
        )

    # ------------------------------------------------------------------
    # High-level: chat() — all-in-one
    # ------------------------------------------------------------------

    def chat(
        self,
        app_id: str,
        prompt: str,
        chat_history: list[dict] | None = None,
        extra_headers: dict | None = None,
        poll_interval: float = _POLL_INTERVAL_S,
        poll_max_attempts: int = _POLL_MAX_ATTEMPTS,
    ) -> str:
        """Send a prompt to a GAIA app and return the final text response.

        This method handles the full session → interaction → poll → cleanup cycle.

        Args:
            app_id:            UUID of the GAIA app to call.
            prompt:            The user's message.
            chat_history:      Optional prior messages for multi-turn context.
            extra_headers:     Optional tool/knowledge headers (X-Gaia-Extra-Headers).
            poll_interval:     Seconds between poll attempts (default 2s).
            poll_max_attempts: Max poll attempts before TimeoutError (default 30).

        Returns:
            The assistant's response text (str).

        Raises:
            EnvironmentError: if required env vars are missing.
            requests.HTTPError: on API errors (4xx/5xx).
            RuntimeError: if the interaction ends with an error status.
            TimeoutError: if the interaction takes too long.
        """
        session_id = self.start_session(app_id)
        try:
            interaction_id = self.create_interaction(
                session_id,
                prompt,
                chat_history=chat_history,
                extra_headers=extra_headers,
            )
            result = self.poll_interaction(
                session_id,
                interaction_id,
                interval=poll_interval,
                max_attempts=poll_max_attempts,
            )
            # Extract the final assistant text from newAiMessages
            new_msgs = result.get("newAiMessages", [])
            for msg in new_msgs:
                body = msg.get("body", {})
                if isinstance(body, dict):
                    text = body.get("text", "")
                else:
                    text = str(body)
                if text:
                    return text
            return ""
        finally:
            self.delete_session(session_id)
