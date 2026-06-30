# density-apex-audit

Run a full BMW Density design system compliance audit on any live Oracle APEX
application. Opens a **headed Chromium browser** (required for BMW SSO login),
crawls every navigable page and modal surface, checks Density token application
in both **light mode and dark mode**, and produces a scored findings report with
recommended fixes for every failure.

## When to use this skill

Load this skill whenever:
- A user asks to "audit" or "check Density styling" on an APEX app
- A user says "run the density audit" or "check density compliance"
- A user provides an APEX URL and mentions design tokens, dark mode, or BMW branding
- A previous audit was run and the user wants to re-run it after changes

## Runtime requirement

**Always use the clipjoint venv:**
```bash
~/.opencode/plugins/clipjoint/.venv/bin/python3
```

## How to use

```python
import sys, pathlib
sys.path.insert(0, str(pathlib.Path.home() / ".opencode/skills/density-apex-audit"))
from density_apex_audit import run_audit

report = run_audit(
    target_url="https://apextw10.bmwgroup.net/ords/r/ws/myapp/home",
    shots_dir=pathlib.Path("/Users/QTE2362/Desktop/density-apex-howto/screenshots/audit-latest"),
)

print(report.summary())
report.save(pathlib.Path("/Users/QTE2362/Desktop/density-apex-howto/screenshots/audit-latest"))
```

## Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `target_url` | `str` | required | Full URL of the APEX app home page |
| `shots_dir` | `Path \| None` | `None` | Where to save screenshots. Auto-created. |
| `css_dir` | `Path \| None` | auto | Local density CSS/JS dir for iframe injection. Auto-detects `density_css/` symlink. |
| `apex_host` | `str \| None` | inferred | Override hostname detection. |
| `max_nav_pages` | `int` | `10` | Max linked pages to follow from home. |
| `close_on_finish` | `bool` | `False` | Keep browser open after audit (default). Press Enter to close. |

## What the audit checks

### Every full page (home + all nav-linked pages)

| Check | Description |
|---|---|
| DENSITY-CSS-LOADED | All 3 Density CSS files present (theme-standalone, overrides, dark-mode) |
| DENSITY-JS-LOADED | density-dark-mode.js present |
| DENSITY-TOKENS-RESOLVED | 5 spot-check `--ds-*` tokens resolve on `:root` |
| BODY-BG-CORRECT | `body` background = `#f5f6f6` (light) / `#0b0d10` (dark) |
| HEADER-BG-OVERRIDDEN | Header not APEX blue — Density surface-base active |
| DARK-MODE-TOGGLE-PRESENT | `#ds-dark-mode-toggle-item` in user menu |
| DARK-MODE-TOGGLE-DIMENSIONS | Toggle switch = 32×18px per Density spec |
| DARK-MODE-PERSISTS | `body.ds-dark` present immediately after page reload |
| A11Y-ARIA-LABELS | Interactive elements have accessible labels |
| A11Y-FOCUS-RING | `:focus-visible` rule present |
| IR-BODY-BG | Interactive Report page body bg correct (light + dark) |

### Every dialog/modal surface (Feedback, Help, About items)

| Check | Description |
|---|---|
| IFRAME-DENSITY-CSS | All 3 Density sheets loaded inside dialog iframe |
| IFRAME-DARK-PROPAGATED | `ds-dark` class synced into iframe when dark mode is ON |
| BODY-BG-CORRECT (iframe) | Dialog iframe body background = surface-page token |
| DIALOG-BG-DARK | Outer jQuery UI dialog wrapper dark in dark mode |
| SMILEY-BG-CORRECT | `.u-radio` rating tiles use Density surface-neutral |

### Every dropdown menu (About, User)

| Check | Description |
|---|---|
| DROPDOWN-BG-LIGHT | Menu container bg = surface-base (white) in light mode |
| DROPDOWN-BG-DARK | Menu container bg = dark surface-base in dark mode |

## Output — AuditReport

```python
report.score()          # int — percentage of checks passing
report.passes()         # list[Finding] — all passing checks
report.majors()         # list[Finding] — critical + major failures
report.minors()         # list[Finding] — minor issues
report.summary()        # str — full markdown report
report.save(path)       # writes audit-findings.json + audit-report.md
report.pages_visited    # list[str] — all page URLs audited
report.modals_visited   # list[str] — all modal surfaces audited
```

## Finding structure

Each `Finding` has:
- `severity` — `"pass"` | `"minor"` | `"major"` | `"critical"` | `"info"`
- `label` — short tag e.g. `"BODY-BG-CORRECT"`
- `detail` — human-readable description
- `surface` — page/modal context e.g. `"home"`, `"home-dialog-feedback"`
- `mode` — `"light"` or `"dark"`
- `fix` — recommended fix (populated for major/minor findings)
- `screenshot` — path to screenshot if `shots_dir` was set

## BMW SSO login behaviour

- Opens a **headed** Chromium window using a persistent browser profile
- If redirected to BMW SSO, prints a clear message and waits **up to 180 seconds** for the user to log in
- Uses **URL polling only** — never `networkidle` (which fires mid-SSO-redirect and causes false failures)
- After the audit finishes the **browser stays open** by default — the user can inspect results, then press Enter in the terminal to close it
- The persistent profile (`/var/folders/.../browser_profile`) keeps cookies between runs — subsequent audits on the same session often skip the SSO login entirely

## Re-running after uploading new CSS/JS to APEX

```python
report = run_audit(
    target_url="https://apextw10.bmwgroup.net/ords/r/ws_mn_digi_test/supplier-contact-database-next/home",
    shots_dir=pathlib.Path("/Users/QTE2362/Desktop/density-apex-howto/screenshots/audit-latest"),
)
print(report.summary())
```

No parameters need to change — the audit always fetches the live CSS from APEX's own static files
and uses the local `density_css/` symlink only for iframe injection fallback.

## CLI usage (quick audit without Python)

```bash
~/.opencode/plugins/clipjoint/.venv/bin/python3 \
  ~/.opencode/skills/density-apex-audit/density_apex_audit.py \
  "https://apextw10.bmwgroup.net/ords/r/ws_mn_digi_test/supplier-contact-database-next/home" \
  "/Users/QTE2362/Desktop/density-apex-howto/screenshots/audit-latest"
```

## Updating the CSS reference files

The `density_css/` directory inside this skill is a symlink to:
```
/Users/QTE2362/Desktop/density-apex-howto/
```
When you update the local Density CSS/JS files, the audit engine picks them up automatically
on the next run — no reinstall needed.

If the howto directory moves, update the symlink:
```bash
ln -sfn /new/path/to/density-apex-howto \
  ~/.opencode/skills/density-apex-audit/density_css
```

## Known limitations

- **Cross-origin iframes** cannot be inspected (browser security). All BMW APEX dialogs on the
  same host are same-origin and are fully audited.
- **Dynamically rendered content** (charts, maps) requires the page to fully initialise — the
  audit waits 2s after navigation which covers most cases.
- **APEX Developer Toolbar** is excluded from all checks (it has its own theming).
- **Max nav pages** defaults to 10 to keep audit time reasonable. Increase `max_nav_pages`
  for apps with many sections.
