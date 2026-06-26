"""
bmw_client.py
=============
Shared BMW LLM API authentication and HTTP client setup.
All other modules import from here — no credentials are duplicated.
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import requests

try:
    from openai import OpenAI
except ImportError:
    sys.exit("openai SDK not found. Install it with:  pip install openai>=1.0")

try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:
    pass

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_PLUGIN_DIR = Path(__file__).resolve().parent.parent
CA_CERT_PATH = str(_PLUGIN_DIR / "BMW_Trusted_Certificates_Latest.pem")
CA_CERT_URL = "https://trustbundle.bmwgroup.net/BMW_Trusted_Certificates_Latest.pem"
MAX_RETRIES = 3

ENVIRONMENTS = {
    "int": {
        "auth_endpoint": "https://auth.bmwgroup.net/auth/oauth2/realms/root/realms/machine2machine/access_token",
        "base_url": "https://api.int.gcp.cloud.bmw/llmapi",
    },
    "prod": {
        "auth_endpoint": "https://auth.bmwgroup.net/auth/oauth2/realms/root/realms/machine2machine/access_token",
        "base_url": "https://api.gcp.cloud.bmw/llmapi",
    },
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        sys.exit(
            f"[ERROR] Required environment variable '{name}' is not set.\n"
            f"  PowerShell : $env:{name} = '...'\n"
            f"  bash/zsh   : export {name}='...'\n"
            f"  .env file  : {name}=..."
        )
    return value


def retry(fn, *args, label: str = "call", **kwargs):
    """Call fn(*args, **kwargs) up to MAX_RETRIES times. Raises last exception on failure."""
    last_exc = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return fn(*args, **kwargs)
        except Exception as exc:
            last_exc = exc
            if attempt < MAX_RETRIES:
                wait = 2 ** (attempt - 1)
                print(
                    f"  [WARN] {label} failed (attempt {attempt}/{MAX_RETRIES}): {exc}  — retrying in {wait}s…"
                )
                time.sleep(wait)
            else:
                print(f"  [ERROR] {label} failed after {MAX_RETRIES} attempts: {exc}")
    raise last_exc


def download_ca_cert() -> str:
    if os.path.exists(CA_CERT_PATH):
        return CA_CERT_PATH
    print("Downloading BMW CA certificate…")
    r = requests.get(CA_CERT_URL)
    r.raise_for_status()
    with open(CA_CERT_PATH, "wb") as f:
        f.write(r.content)
    return CA_CERT_PATH


def get_oauth_token(client_id: str, client_secret: str, auth_endpoint: str, ca_cert: str) -> str:
    r = requests.post(
        auth_endpoint,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": "machine2machine",
        },
        verify=ca_cert,
    )
    r.raise_for_status()
    return r.json()["access_token"]


def bmw_setup() -> tuple:
    """Return (openai_client, api_key, base_url, ca_cert, token)."""
    client_id = require_env("BMW_CLIENT_ID")
    client_secret = require_env("BMW_CLIENT_SECRET")
    api_key = require_env("BMW_API_KEY")
    env_name = os.environ.get("BMW_ENV", "prod").lower()
    env = ENVIRONMENTS.get(env_name, ENVIRONMENTS["prod"])
    ca_cert = download_ca_cert()
    token = get_oauth_token(client_id, client_secret, env["auth_endpoint"], ca_cert)

    import httpx

    http_client = httpx.Client(headers={"x-apikey": api_key}, verify=ca_cert)
    client = OpenAI(base_url=env["base_url"] + "/v1", api_key=token, http_client=http_client)
    return client, api_key, env["base_url"], ca_cert, token


def async_bmw_setup(api_key: str, base_url: str, ca_cert: str, token: str):
    """Return an AsyncOpenAI client using credentials already obtained by bmw_setup().

    Call bmw_setup() first to get (client, api_key, base_url, ca_cert, token),
    then pass the last four values here to get the async counterpart.

    Example::

        client, api_key, base_url, ca_cert, token = bmw_setup()
        async_client = async_bmw_setup(api_key, base_url, ca_cert, token)
    """
    try:
        from openai import AsyncOpenAI
    except ImportError:
        sys.exit("openai SDK not found. Install it with:  pip install openai>=1.0")

    import httpx

    async_http = httpx.AsyncClient(headers={"x-apikey": api_key}, verify=ca_cert)
    return AsyncOpenAI(
        base_url=base_url + "/v1",
        api_key=token,
        http_client=async_http,
    )


async def async_retry(coro_fn, *args, label: str = "call", max_retries: int = MAX_RETRIES, **kwargs):
    """Async version of retry(): await coro_fn(*args, **kwargs) up to max_retries times.

    Uses exponential backoff with asyncio.sleep so the event loop is not blocked.

    Example::

        result = await async_retry(
            client.chat.completions.create,
            model="gpt-4o",
            messages=[...],
            label="storyboard LLM call",
        )
    """
    import asyncio

    last_exc = None
    for attempt in range(1, max_retries + 1):
        try:
            return await coro_fn(*args, **kwargs)
        except Exception as exc:
            last_exc = exc
            if attempt < max_retries:
                wait = 2 ** (attempt - 1)
                print(
                    f"  [WARN] {label} failed (attempt {attempt}/{max_retries}): {exc}"
                    f"  — retrying in {wait}s…"
                )
                await asyncio.sleep(wait)
            else:
                print(f"  [ERROR] {label} failed after {max_retries} attempts: {exc}")
    raise last_exc
