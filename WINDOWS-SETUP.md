# Windows Setup Guide — OpenCode BMW Configuration

> **Status:** 📋 PLANNED — Windows support is not yet implemented.  
> This document captures the full gap analysis, recommended approach, and implementation
> plan for bringing Windows users to parity with the macOS setup.

---

## Recommended Approach: WSL2

OpenCode's own documentation [recommends WSL2](https://opencode.ai/docs/windows-wsl) for
Windows — it gives better file system performance, full terminal support, and compatibility
with all the tooling this config depends on (Python, curl, bash scripts, TTT, gh CLI).

**The BMW config follows the same recommendation:** install OpenCode inside WSL2, keep
all config and credentials in the WSL2 filesystem, and run everything from a WSL2 terminal.

> **Native Windows (PowerShell only) is a stretch goal** — it requires rewriting the
> wrapper script in PowerShell and replacing Keychain with Windows Credential Manager.
> See [Option B](#option-b-native-windows-powershell) below.

---

## Platform Comparison

| Component | macOS (current) | Windows WSL2 (planned) | Windows Native (stretch) |
|-----------|----------------|----------------------|------------------------|
| **Shell** | zsh + `~/.zshrc` | bash/zsh + `~/.bashrc` or `~/.zshrc` | PowerShell + `$PROFILE` |
| **OpenCode install** | `brew install opencode` | `curl -fsSL https://opencode.ai/install \| bash` | `choco install opencode` / `scoop install opencode` |
| **OpenCode binary** | `/opt/homebrew/bin/opencode` | `/usr/local/bin/opencode` or `~/.local/bin/opencode` | `C:\ProgramData\...` or `%LOCALAPPDATA%\...` |
| **Config location** | `~/.config/opencode/` | `~/.config/opencode/` ✅ same | `%APPDATA%\opencode\` ⚠️ different |
| **Data location** | `~/.local/share/opencode/` | `~/.local/share/opencode/` ✅ same | `%LOCALAPPDATA%\opencode\` ⚠️ different |
| **Credential store** | macOS Keychain (`security` CLI) | `.env` file (600 perms) or pass env vars | Windows Credential Manager (`cmdkey`) |
| **Wrapper script** | `~/bin/opencode-bmw` (zsh) | `~/bin/opencode-bmw` (bash) — minor edits | `opencode-bmw.ps1` (PowerShell) — full rewrite |
| **Token refresh** | OAuth2 via `curl` | OAuth2 via `curl` ✅ same | OAuth2 via `curl.exe` or `Invoke-RestMethod` |
| **VPN check** | `scutil --nc list` | check via `/mnt/c/Windows/System32/rasdial.exe` or `ip route` | `Get-VpnConnection` (PowerShell) |
| **Python3** | pre-installed | `sudo apt install python3` | `winget install Python.Python.3` |
| **TTT CLI** | BMW internal / brew | BMW internal Linux binary | BMW internal Windows binary |
| **gh CLI** | `brew install gh` | `sudo apt install gh` or official binary | `winget install GitHub.cli` |
| **Git** | Xcode tools / brew | `sudo apt install git` | Git for Windows |
| **mcp-auth.json** | `~/.local/share/opencode/mcp-auth.json` | `~/.local/share/opencode/mcp-auth.json` ✅ same | `%LOCALAPPDATA%\opencode\mcp-auth.json` |
| **Cron / auto-refresh** | `crontab -e` | `crontab -e` ✅ same | Task Scheduler (`schtasks`) |

---

## Option A: Windows + WSL2 (Recommended)

### Why this works well

- **Config is identical** — same `~/.config/opencode/` path, same `opencode.json`, same skills
- **Wrapper script needs only minor changes** — replace `security` CLI calls with `.env` reads
- **All tooling works natively** — Python, curl, bash, TTT, gh, git all available via `apt`
- **Skills-mcp heal function works unchanged** — same Python and file paths
- **OpenCode data paths are identical** — `~/.local/share/opencode/` works the same

### What needs to change for WSL2

#### 1. Credential storage: Keychain → `.env` file

macOS uses the `security` CLI to read from Keychain. Under WSL2, we use a **protected `.env` file** instead:

```bash
# Windows WSL2: store credentials in ~/.config/opencode/.env (chmod 600)
# This file is already in .gitignore — never committed
cat ~/.config/opencode/.env
# Should contain:
# LLM_API_KEY=your_api_key
# BMW_CLIENT_ID=your_client_id
# BMW_CLIENT_SECRET=your_client_secret
# TTT_PAT=your_ttt_pat
```

Set permissions immediately after writing:
```bash
chmod 600 ~/.config/opencode/.env
```

Security note: `.env` is less secure than Keychain (no encryption at rest), but acceptable for
BMW development laptops with full-disk encryption (BitLocker). Do not use on shared machines.

**Alternative (more secure):** Use `pass` (GNU pass) or `secret-tool` (libsecret) if your
WSL2 distro has D-Bus running — but this is complex to set up. `.env` is the pragmatic choice.

#### 2. Wrapper script: replace `security` calls with `.env` reads

The current `~/bin/opencode-bmw` uses `security find-generic-password` everywhere. The
WSL2 version replaces those with `source ~/.config/opencode/.env`:

**macOS wrapper (current):**
```zsh
client_id=$(security find-generic-password -s "com.bmw.opencode" -a "bmw_client_id" -w)
client_secret=$(security find-generic-password -s "com.bmw.opencode" -a "bmw_client_secret" -w)
```

**WSL2 wrapper (needed):**
```bash
# Source the .env file
set -a
source ~/.config/opencode/.env
set +a
client_id="$BMW_CLIENT_ID"
client_secret="$BMW_CLIENT_SECRET"
```

The rest of the token refresh logic (curl to `auth.bmwgroup.net`, Python JSON parsing,
writing the refreshed token) works **identically** — no changes needed.

#### 3. Shell alias: `~/.zshrc` or `~/.bashrc`

```bash
# Add to ~/.bashrc or ~/.zshrc (depending on your WSL2 default shell)
alias opencode="$HOME/bin/opencode-bmw"
```

#### 4. VPN check: `scutil` → Linux equivalent

```bash
# macOS: scutil --nc list
# WSL2: check if BMW gateway is reachable
ping -c 1 api.gcp.cloud.bmw > /dev/null 2>&1 && echo "Connected" || echo "Check VPN"

# Or check via Windows rasdial.exe (accessible from WSL2):
/mnt/c/Windows/System32/rasdial.exe 2>/dev/null | grep -i "connected\|verbunden"
```

### WSL2 Installation Steps (planned)

> ⚠️ These steps are not yet tested end-to-end. They represent the intended implementation,
> confirmed by internal Confluence documentation.

#### Prerequisites

1. **Install WSL2** (Windows 11 required — no admin rights needed, but requires
   [ClientRightsNext](https://clientrightsnext.azure.bmw.cloud/) approval for WSL):
   ```powershell
   # In PowerShell — set WSL version and install Ubuntu 24.04
   wsl.exe --set-default-version 2
   wsl.exe --update --web-download
   wsl.exe --install -d Ubuntu-24.04 --web-download
   ```
   > Full guide: [DX WSL2 Setup Guide](https://atc.bmwgroup.net/confluence/spaces/DX/pages/5858114478)
   > (Confluence ID 5858114478) — covers CyberArk, mirrored networking, proxy, APT mirrors.

2. **Configure mirrored networking + proxy** (WSL Settings → Networking Mode = Mirrored):
   ```bash
   # Add to ~/.profile (inside WSL2)
   export http_proxy=http://localhost:3128/
   export https_proxy=http://localhost:3128/
   export no_proxy=localhost,127.0.0.1,.bmwgroup.net,.cloud.bmw
   export HTTP_PROXY=${http_proxy}
   export HTTPS_PROXY=${https_proxy}
   export NO_PROXY=${no_proxy}
   ```
   Also add to `/etc/environment` for non-interactive processes.
   > Proxy runs on the **Windows host** (Proxydetox or Px on port 3128).
   > WSL2 mirrored networking shares the Windows network stack — VPN on Windows
   > is automatically visible inside WSL2. No separate VPN client needed.

3. **Install dependencies in WSL2:**
   ```bash
   sudo apt update && sudo apt upgrade
   sudo apt install -y git curl python3 python3-pip build-essential unzip net-tools jq
   ```

4. **Install OpenCode in WSL2:**
   ```bash
   curl -fsSL https://opencode.ai/install | bash
   # Verify:
   opencode --version
   ```

5. **Install gh CLI in WSL2:**
   ```bash
   type -p curl > /dev/null || sudo apt install curl -y
   curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg \
     | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
   echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] \
     https://cli.github.com/packages stable main" \
     | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
   sudo apt update && sudo apt install gh -y
   ```

6. **Install `uv` (Python package runner — required for TTT):**
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   # Restart terminal or: source ~/.bashrc
   uv --version
   ```

7. **Install TTT CLI** (via one-time token from [skills.bmwgroup.net](https://skills.bmwgroup.net)):
   ```bash
   # 1. Open skills.bmwgroup.net → "Get Started" → "Generate one-time install link"
   # 2. The link is valid for only 5 minutes — copy and run immediately:
   curl -fsSL 'https://skills.bmwgroup.net/api/v1/install.py?install_token=<TOKEN>' \
     | uv run --no-project -
   # Verify:
   ttt health
   ```
   > `ttt` is Python-based and delivered via `uv` — identical install command on macOS/Linux/WSL2.
   > No separate Linux binary needed.

8. **Install BMW corporate CA certificates** (needed for HTTPS to BMW-internal services):
   ```bash
   # Download the BMW Root CA bundle (ask your team for the .crt files, or get from
   # https://atc.bmwgroup.net/confluence/spaces/CERTMGMT/pages/634062584)
   # Then trust them in Ubuntu:
   sudo cp BmwGroup*.crt /usr/local/share/ca-certificates/
   sudo update-ca-certificates
   # Verify:
   curl -I https://atc.bmwgroup.net
   # Expected: HTTP/2 301 (not a certificate error)
   ```
   > In practice this is often not needed because the proxy (localhost:3128) handles
   > TLS termination for BMW-internal endpoints on the Windows side. If you see
   > `SSL: CERTIFICATE_VERIFY_FAILED`, add the certs.

#### Configuration

After completing the Prerequisites above, continue with:

9. **Clone this repo:**
   ```bash
   git clone https://atc-github.azure.cloud.bmw/qte2362/opencode-config.git ~/.config/opencode
   ```

10. **Store credentials in `.env`:**
    ```bash
    # Edit the .env file (already exists, add your values)
    nano ~/.config/opencode/.env

    # Add these lines:
    # LLM_API_KEY=your_api_key
    # BMW_CLIENT_ID=your_client_id
    # BMW_CLIENT_SECRET=your_client_secret
    # TTT_PAT=your_ttt_pat

    # Lock down permissions
    chmod 600 ~/.config/opencode/.env
    ```

11. **Create WSL2 wrapper script** (see `bin/opencode-bmw-wsl2` — TO BE CREATED):
    ```bash
    mkdir -p ~/bin
    # Copy the WSL2 version of the wrapper
    cp ~/.config/opencode/bin/opencode-bmw-wsl2 ~/bin/opencode-bmw
    chmod +x ~/bin/opencode-bmw
    ```

12. **Add alias:**
    ```bash
    echo 'alias opencode="$HOME/bin/opencode-bmw"' >> ~/.bashrc
    source ~/.bashrc
    ```

13. **Authenticate GitHub Enterprise:**
    ```bash
    gh auth login --hostname atc-github.azure.cloud.bmw
    ```

14. **Test TTT connectivity:**
    ```bash
    source ~/.config/opencode/.env
    ttt health
    ttt skills list --page-size 3
    ```

15. **Test OpenCode:**
    ```bash
    ~/bin/test-opencode-auth-wsl2  # TO BE CREATED: WSL2 auth diagnostic
    opencode run "hello"
    ```

---

## Option B: Native Windows / PowerShell (Stretch Goal)

> ⚠️ This approach is significantly more work and is not currently planned.
> Document here for future reference.

### What needs to be built

1. **`opencode-bmw.ps1`** — full rewrite of the wrapper in PowerShell
   - Replace `security` → `[System.Security.CredentialManagement.PasswordCredential]` or
     `Get-StoredCredential` from the `CredentialManager` module
   - Token refresh via `Invoke-RestMethod` instead of `curl`
   - Write refreshed token back to Credential Manager

2. **Credential setup:**
   ```powershell
   # Install CredentialManager module
   Install-Module -Name CredentialManager -Force

   # Store credentials
   New-StoredCredential -Target "opencode_llm_api_key" -UserName "bmw" -Password "YOUR_KEY" -Type Generic -Persist LocalMachine
   New-StoredCredential -Target "opencode_bmw_client_id" -UserName "bmw" -Password "YOUR_ID" -Type Generic -Persist LocalMachine
   New-StoredCredential -Target "opencode_bmw_client_secret" -UserName "bmw" -Password "YOUR_SECRET" -Type Generic -Persist LocalMachine
   ```

3. **Config path difference:**
   - OpenCode on Windows native uses `%APPDATA%\opencode\` not `~/.config/opencode/`
   - The git repo would need to be cloned there instead

4. **VPN check:**
   ```powershell
   $vpn = Get-VpnConnection | Where-Object { $_.ConnectionStatus -eq "Connected" }
   if (-not $vpn) { Write-Warning "BMW VPN not connected" }
   ```

5. **Python dependency:**
   - skills-mcp heal script requires Python — `winget install Python.Python.3`
   - The heal function would need to call `python.exe` instead of `python3`

**Estimated effort:** 3-4 hours for a working prototype, plus testing time.

---

## Files To Create (WSL2 Implementation)

| File | Purpose | Status |
|------|---------|--------|
| `bin/opencode-bmw-wsl2` | WSL2 wrapper script (bash, reads `.env` instead of Keychain) | 📋 TODO — next |
| `bin/test-opencode-auth-wsl2` | WSL2 auth diagnostic script | 📋 TODO |
| `WINDOWS-SETUP.md` | This document | ✅ Done (gap analysis + research complete) |
| `README.md` | Platform tabs, per-step macOS/WSL2 callouts | ✅ Done (partial — experimental callout added) |

---

## Open Questions — Resolved ✅

| Question | Status | Source |
|----------|--------|--------|
| Does BMW distribute a Linux TTT binary? | ✅ **No binary needed** — `ttt` is Python-based, installed via `uv` using a one-time token from `skills.bmwgroup.net`. Same curl command on macOS/Linux/WSL2. | DAAI Setup Guide (Confluence 8438528444), Team Turing guide (8084471792) |
| Does the BMW VPN client work in WSL2 or only on Windows host? | ✅ **Windows host — but WSL2 sees it automatically** via mirrored networking. VPN runs on Windows; WSL2 shares the full Windows network stack. Confirmed working by DX WSL2 guide. | DX WSL2 Setup Guide (Confluence 5858114478) |
| Is `.env` acceptable credential storage for WSL2? | ✅ **Yes, pragmatically acceptable** — DX guide uses `~/.profile` for similar-sensitivity proxy credentials. Windows laptops use BitLocker by default. No IT Security objection in official BMW guides. Use `chmod 600`. | DX WSL2 Setup Guide, DAAI Setup Guide |
| Does the BMW GitHub Enterprise cert work in WSL2's cert store? | ✅ **Proxy handles it** — requests via `localhost:3128` (proxydetox/Px on Windows host) don't need BMW certs in the WSL2 cert store. If direct TLS is needed, copy BMW CA `.crt` files to `/usr/local/share/ca-certificates/` and run `sudo update-ca-certificates`. | BMW Linux CA guide (Confluence 940429266) |
| Can the macOS Keychain be queried from WSL2? | ❌ **No** — Keychain is macOS-only. `.env` (chmod 600) is the correct WSL2 credential store. | Architecture constraint |
| Is `pass` (GPG-based password manager) preferred over `.env` in WSL2? | ⚠️ **More secure but not needed** — `.env` chmod 600 is sufficient for BMW dev laptops. `pass` is an option if your distro has D-Bus running, but adds significant setup complexity. | Best practice analysis |

---

## README Sections That Need Windows Notes (Progress Tracker)

| README Section | macOS-only? | Windows note added? |
|----------------|------------|-------------------|
| Quick Start (TL;DR) | ✅ Yes | 📋 TODO |
| Prerequisites | ✅ Yes | 📋 TODO |
| Step 1 — Clone | ✅ Yes (path) | 📋 TODO |
| Step 2 — Credentials | ✅ Keychain | 📋 TODO |
| Step 3 — Wrapper script | ✅ Yes | 📋 TODO |
| Step 4 — Shell alias | ✅ `.zshrc` | 📋 TODO |
| Step 6 — GitHub Enterprise | ⚠️ Mostly portable | 📋 TODO |
| Troubleshooting — auth | ✅ `security find-...` | 📋 TODO |
| Troubleshooting — VPN | ✅ `scutil` | 📋 TODO |
| Architecture diagram | ✅ macOS paths | 📋 TODO |

---

## Implementation Priority

1. **P1 — README planning section** ← current PR
   - Add "Platform Support" table showing macOS (supported) vs Windows WSL2 (planned)
   - Add Windows WSL2 quickstart section (labeled "coming soon / experimental")
   - Make macOS-specific commands clearly labelled

2. **P2 — WSL2 wrapper script** (`bin/opencode-bmw-wsl2`)
   - Bash version of wrapper with `.env` instead of Keychain
   - Auth test script for WSL2
   - Test on an actual Windows + WSL2 machine

3. **P3 — README full Windows section**
   - Complete step-by-step WSL2 guide (once P2 is tested)
   - Mark macOS steps clearly with `(macOS)` callouts
   - Add side-by-side comparison tables

4. **P4 — Native Windows / PowerShell** (stretch)
   - Only if WSL2 approach has blockers (e.g. VPN doesn't route through WSL2)
