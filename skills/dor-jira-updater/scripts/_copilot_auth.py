# /// script
# requires-python = ">=3.10"
# dependencies = ["httpx"]
# ///
"""Complete the OAuth device flow to get a Copilot access token.

1. User goes to https://bmw.ghe.com/login/device
2. User enters the code shown
3. This script polls until authorized, then exchanges for a Copilot token
4. Tests the Copilot chat completions API
"""

import json
import os
import ssl
import time

import httpx

proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY")
# Proxy speaks plain HTTP even for HTTPS tunneling — force http:// scheme
if proxy and proxy.startswith("https://"):
    proxy = "http://" + proxy[len("https://") :]
ghe = "bmw.ghe.com"
client_id = "Iv1.b507a08c87ecfe98"  # VS Code Copilot extension client_id

# BMW corporate proxy performs TLS interception.
# Set BMW_CA_BUNDLE (or SSL_CERT_FILE) to your corporate CA bundle for proper verification.
ca_bundle = os.environ.get("BMW_CA_BUNDLE") or os.environ.get("SSL_CERT_FILE")
if ca_bundle:
    ctx = ssl.create_default_context(cafile=ca_bundle)
else:
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE  # nosec B501

with httpx.Client(verify=ctx, proxy=proxy, timeout=30) as c:
    # Step 1: Start device flow
    print("=== Step 1: Device code request ===")
    r = c.post(
        f"https://{ghe}/login/device/code",
        data={
            "client_id": client_id,
            "scope": "copilot",
        },
        headers={"Accept": "application/json"},
    )
    data = r.json()
    device_code = data["device_code"]
    user_code = data["user_code"]
    interval = data.get("interval", 5)
    verification_uri = data["verification_uri"]

    print(f"\n  >>> Go to: {verification_uri}")
    print(f"  >>> Enter code: {user_code}")
    print("  >>> Waiting for authorization...\n")

    # Step 2: Poll for authorization
    print("=== Step 2: Polling for authorization ===")
    access_token = None
    for attempt in range(60):
        time.sleep(interval)
        r = c.post(
            f"https://{ghe}/login/oauth/access_token",
            data={
                "client_id": client_id,
                "device_code": device_code,
                "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            },
            headers={"Accept": "application/json"},
        )
        result = r.json()

        if "access_token" in result:
            access_token = result["access_token"]
            token_type = result.get("token_type", "bearer")
            print(f"  Authorized! Token type: {token_type}")
            print(f"  Token: {access_token[:15]}...{access_token[-4:]}")
            break
        elif result.get("error") == "authorization_pending":
            print(
                f"  Attempt {attempt + 1}: waiting... (enter code {user_code} at {verification_uri})"
            )
        elif result.get("error") == "slow_down":
            interval += 5
            print(f"  Slowing down, interval={interval}s")
        else:
            print(f"  Error: {result}")
            break

    if not access_token:
        print("\n  FAILED: No authorization received. Did you enter the code?")
        exit(1)

    # Step 3: Exchange OAuth token for Copilot session token
    print("\n=== Step 3: Copilot token exchange ===")
    copilot_token = None

    exchange_urls = [
        f"https://{ghe}/api/v3/copilot_internal/v2/token",
        f"https://{ghe}/api/v3/copilot_internal/token",
        "https://api.github.com/copilot_internal/v2/token",
    ]
    for url in exchange_urls:
        r = c.get(url, headers={"Authorization": f"token {access_token}"})
        print(f"  {url}: {r.status_code}")
        if r.status_code == 200:
            token_data = r.json()
            copilot_token = token_data.get("token")
            endpoints = token_data.get("endpoints", {})
            api_base = endpoints.get("api", "https://api.githubcopilot.com")
            print(f"  Copilot token: {copilot_token[:25]}...")
            print(f"  API base: {api_base}")
            print(f"  Expires: {token_data.get('expires_at')}")
            with open("_copilot_token.json", "w") as f:
                json.dump(token_data, f, indent=2)
            print("  Saved token data to _copilot_token.json")
            break
        else:
            print(f"    {r.text[:200]}")

    if not copilot_token:
        # Maybe we can use the OAuth token directly?
        print("\n  No Copilot token exchange worked. Trying OAuth token directly...")
        copilot_token = access_token
        api_base = "https://api.githubcopilot.com"

    # Step 4: Test chat completions
    print("\n=== Step 4: Test chat completions ===")
    chat_url = f"{api_base}/chat/completions"
    print(f"  POST {chat_url}")
    r = c.post(
        chat_url,
        headers={
            "Authorization": f"Bearer {copilot_token}",
            "Content-Type": "application/json",
            "Editor-Version": "vscode/1.96.0",
            "Copilot-Integration-Id": "copilot-sdk-agent",
        },
        json={
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Say hello in 5 words"}],
            "max_tokens": 50,
        },
    )
    print(f"  Status: {r.status_code}")
    print(f"  Body:   {r.text[:500]}")

    if r.status_code == 200:
        print("\n  SUCCESS! Copilot API is working!")
        print("\n  Save this OAuth token to .env:")
        print(f"  GITHUB_TOKEN={access_token}")
    else:
        print(f"\n  Chat failed with {r.status_code}. Full response:")
        print(f"  {r.text[:1000]}")
