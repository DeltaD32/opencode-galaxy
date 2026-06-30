#!/usr/bin/env python3
"""
density_apex_audit.py
─────────────────────────────────────────────────────────────────────────────
BMW Density Design System — Oracle APEX Live Audit Engine

Reusable module for auditing any APEX application that has the Density CSS/JS
files deployed. Opens a single headed Chromium browser, waits for BMW SSO
login, then crawls every navigable page and modal surface, checking Density
compliance in both light mode AND dark mode.

The browser window stays open until the user explicitly closes it or presses
Enter in the console — avoiding repeat logins across multiple audit runs.

PUBLIC API
──────────
    run_audit(target_url, shots_dir=None, css_files=None, js_files=None)
        → AuditReport

    AuditReport
        .findings     list[Finding]
        .summary()    str  — human-readable markdown summary
        .save(path)   writes JSON + markdown to disk

USAGE (from SKILL.md)
──────────────────────
    import sys, pathlib
    sys.path.insert(0, str(pathlib.Path.home() / ".opencode/skills/density-apex-audit"))
    from density_apex_audit import run_audit
    report = run_audit("https://apextw10.bmwgroup.net/ords/r/ws/myapp/home")
    print(report.summary())
    report.save(pathlib.Path("/tmp/density-audit"))

ENVIRONMENT
───────────
    APEX_HOST       overrides auto-detection (default: infer from target_url)
    AUDIT_SHOTS_DIR default screenshot output directory
    DENSITY_CSS_DIR path to local density CSS/JS files for iframe injection

Requires: playwright (in clipjoint venv)
  ~/.opencode/plugins/clipjoint/.venv/bin/python3
─────────────────────────────────────────────────────────────────────────────
"""

from __future__ import annotations

import json
import os
import pathlib
import re
import time
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urlparse

# ── Playwright import (must run from clipjoint venv) ──────────────────────
try:
    from playwright.sync_api import sync_playwright, Page, BrowserContext, Frame
    from playwright.sync_api import TimeoutError as PWTimeout
except ImportError as e:
    raise ImportError(
        "playwright not found. Run with:\n"
        "  ~/.opencode/plugins/clipjoint/.venv/bin/python3\n"
        f"Original error: {e}"
    )

# ── Default paths ──────────────────────────────────────────────────────────
_SKILL_DIR   = pathlib.Path(__file__).parent
_DEFAULT_CSS = _SKILL_DIR / "density_css"          # symlink or copy dir
_BROWSER_PROFILE = pathlib.Path(
    os.environ.get("AUDIT_BROWSER_PROFILE",
                   "/var/folders/jk/kc2hg2dd1gl91zdj4f8p99sw0000gp/T/opencode/browser_profile")
)

# ── Severity helpers ───────────────────────────────────────────────────────
SEVERITY_RANK = {"critical": 5, "major": 4, "minor": 3, "pass": 2, "info": 1}
SEVERITY_ICON = {
    "critical": "🚨", "major": "🔴", "minor": "🟡",
    "pass": "✅",     "info": "ℹ️",
}


# ══════════════════════════════════════════════════════════════════════════
# DATA CLASSES
# ══════════════════════════════════════════════════════════════════════════

@dataclass
class Finding:
    severity:   str           # "pass" | "minor" | "major" | "critical" | "info"
    label:      str           # short tag  e.g. "FEEDBACK-BODY-BG"
    detail:     str           # human text
    surface:    str = ""      # page/modal context  e.g. "home", "feedback-modal"
    mode:       str = "light" # "light" | "dark"
    screenshot: Optional[str] = None
    fix:        Optional[str] = None  # recommended fix (populated for major/minor)

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if v is not None}

    def __str__(self) -> str:
        icon = SEVERITY_ICON.get(self.severity, "  ")
        mode = f"[{self.mode}]" if self.mode != "light" else ""
        surface = f"({self.surface})" if self.surface else ""
        return f"{icon} {self.label} {surface}{mode}: {self.detail[:110]}"


@dataclass
class AuditReport:
    target_url: str
    findings:   list[Finding] = field(default_factory=list)
    pages_visited: list[str]  = field(default_factory=list)
    modals_visited: list[str] = field(default_factory=list)

    # ── convenience accessors ──────────────────────────────────────────
    def passes(self)   -> list[Finding]: return [f for f in self.findings if f.severity == "pass"]
    def majors(self)   -> list[Finding]: return [f for f in self.findings if f.severity in ("major", "critical")]
    def minors(self)   -> list[Finding]: return [f for f in self.findings if f.severity == "minor"]
    def score(self)    -> int:
        checks = [f for f in self.findings if f.severity != "info"]
        if not checks: return 0
        return round(100 * len(self.passes()) / len(checks))

    def add(self, severity: str, label: str, detail: str, **kwargs) -> Finding:
        f = Finding(severity=severity, label=label, detail=detail, **kwargs)
        self.findings.append(f)
        icon = SEVERITY_ICON.get(severity, "  ")
        mode = f"[{kwargs.get('mode','light')}]" if kwargs.get('mode','light') != "light" else ""
        surface = f"({kwargs.get('surface','')})" if kwargs.get('surface') else ""
        print(f"  {icon} [{label}]{surface}{mode} {detail[:100]}")
        return f

    def summary(self) -> str:
        lines = [
            f"# Density APEX Audit — {self.target_url}",
            f"",
            f"**Score: {self.score()}%** "
            f"({len(self.passes())} pass / {len(self.majors())} major / "
            f"{len(self.minors())} minor)",
            f"",
            f"**Pages visited:** {len(self.pages_visited)}",
            f"**Modals/dialogs audited:** {len(self.modals_visited)}",
            f"",
            f"## 🔴 Critical & Major Findings",
        ]
        for f in self.majors():
            lines.append(f"- **[{f.label}]** ({f.surface}, {f.mode}): {f.detail}")
            if f.fix:
                lines.append(f"  - *Fix:* {f.fix}")
        lines += ["", "## 🟡 Minor Findings"]
        for f in self.minors():
            lines.append(f"- **[{f.label}]** ({f.surface}, {f.mode}): {f.detail}")
            if f.fix:
                lines.append(f"  - *Fix:* {f.fix}")
        lines += ["", "## ✅ Passing Checks"]
        for f in self.passes():
            lines.append(f"- **[{f.label}]** ({f.surface}, {f.mode}): {f.detail}")
        return "\n".join(lines)

    def save(self, output_dir: pathlib.Path) -> pathlib.Path:
        output_dir.mkdir(parents=True, exist_ok=True)
        json_path = output_dir / "audit-findings.json"
        md_path   = output_dir / "audit-report.md"
        json_path.write_text(json.dumps([f.to_dict() for f in self.findings], indent=2))
        md_path.write_text(self.summary())
        print(f"\n💾 Findings JSON: {json_path}")
        print(f"📄 Report MD:    {md_path}")
        return output_dir


# ══════════════════════════════════════════════════════════════════════════
# BROWSER HELPERS
# ══════════════════════════════════════════════════════════════════════════

def _wait_for_apex_host(page: Page, apex_host: str, timeout_s: int = 180) -> bool:
    """
    Poll page.url until it contains apex_host.
    Uses URL polling ONLY — never networkidle (which fires on SSO pages mid-redirect).
    Returns True if landed, False if timed out.
    """
    if apex_host in page.url:
        return True
    print(f"\n{'='*60}")
    print(f"🔐  BMW SSO detected.")
    print(f"    Please log in via the browser window.")
    print(f"    Waiting up to {timeout_s}s for: {apex_host}")
    print(f"{'='*60}\n")
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        time.sleep(2)
        try:
            if apex_host in page.url:
                print(f"  ✅ Landed on APEX: {page.url[:80]}")
                return True
        except Exception:
            pass
    print(f"❌ Timed out. Last URL: {page.url[:80]}")
    return False


def _wait_for_apex_ready(page: Page, retries: int = 3) -> bool:
    """Wait for apex.jQuery + .t-Header to confirm full page hydration."""
    for attempt in range(retries):
        try:
            page.wait_for_function(
                "() => typeof apex !== 'undefined' && !!apex.jQuery "
                "&& !!document.querySelector('.t-Header')",
                timeout=15000
            )
            time.sleep(2)  # let post-auth JS finish
            return True
        except Exception:
            if attempt < retries - 1:
                time.sleep(3)
    time.sleep(3)
    return False


def _inject_css(target, css_text: str, label: str):
    """Inject a <style> tag into page or frame."""
    escaped = css_text.replace("`", "\\`")
    try:
        target.evaluate(f"""() => {{
            const existing = document.getElementById('ds-injected-{label}');
            if (existing) existing.remove();
            const s = document.createElement('style');
            s.id = 'ds-injected-{label}';
            s.textContent = `{escaped}`;
            document.head.appendChild(s);
        }}""")
    except Exception as e:
        print(f"  ⚠️  CSS inject failed ({label}): {e}")


def _screenshot(page: Page, shots_dir: pathlib.Path, name: str) -> Optional[str]:
    """Take a screenshot, return the path string."""
    if shots_dir is None:
        return None
    shots_dir.mkdir(parents=True, exist_ok=True)
    path = shots_dir / name
    try:
        page.screenshot(path=str(path))
        return str(path)
    except Exception as e:
        print(f"  ⚠️  Screenshot failed ({name}): {e}")
        return None


def _close_dialog(page: Page):
    """Close any open jQuery UI dialog."""
    try:
        btn = page.locator('.ui-dialog-titlebar-close').first
        if btn.count() > 0:
            btn.click()
            try:
                page.wait_for_selector('.ui-widget-overlay', state='hidden', timeout=3000)
            except Exception:
                pass
            time.sleep(0.5)
            return
    except Exception:
        pass
    try:
        page.keyboard.press('Escape')
    except Exception:
        pass
    time.sleep(0.6)


# ══════════════════════════════════════════════════════════════════════════
# DENSITY CHECK PRIMITIVES
# ══════════════════════════════════════════════════════════════════════════

_DS_SPOT_TOKENS = [
    "--ds-color-surface-page",
    "--ds-color-surface-base",
    "--ds-color-typography-base",
    "--ds-color-border-neutral",
    "--ds-color-surface-action-strong",
]

def _check_density_assets(page: Page, report: AuditReport, surface: str):
    """Check all 3 Density CSS files + JS are loaded on the current page."""
    assets = page.evaluate("""() => ({
        sheets:  Array.from(document.styleSheets)
                      .map(s => { try { return s.href||''; } catch(e){ return ''; } })
                      .filter(Boolean),
        scripts: Array.from(document.scripts)
                      .map(s => s.src).filter(Boolean),
    })""")
    sheets  = assets["sheets"]
    scripts = assets["scripts"]

    css_names = ["density-apex-theme-standalone.css",
                 "density-apex-overrides.css",
                 "density-dark-mode.css"]
    found_css = [s for s in sheets if any(n in s for n in css_names)]
    found_js  = [s for s in scripts if "density-dark-mode.js" in s]

    if len(found_css) >= 3:
        report.add("pass", "DENSITY-CSS-LOADED",
                   f"All 3 Density CSS files present (v{_extract_version(found_css[0])})",
                   surface=surface)
    elif found_css:
        missing = [n for n in css_names if not any(n in s for s in sheets)]
        report.add("major", "DENSITY-CSS-PARTIAL",
                   f"Only {len(found_css)}/3 Density CSS files. Missing: {', '.join(missing)}",
                   surface=surface,
                   fix="Upload the missing CSS files to APEX Workspace Static Files and add "
                       "them to User Interface Attributes → CSS → File URLs.")
    else:
        report.add("major", "DENSITY-CSS-MISSING",
                   "No Density CSS files found on this page",
                   surface=surface,
                   fix="Deploy all 3 CSS files and reference them in User Interface Attributes.")

    if found_js:
        report.add("pass", "DENSITY-JS-LOADED",
                   f"density-dark-mode.js present (v{_extract_version(found_js[0])})",
                   surface=surface)
    else:
        report.add("major", "DENSITY-JS-MISSING",
                   "density-dark-mode.js not found — dark mode toggle will not appear",
                   surface=surface,
                   fix="Add density-dark-mode.js to User Interface Attributes → JavaScript → File URLs.")


def _check_tokens(page_or_frame, report: AuditReport, surface: str, mode: str = "light"):
    """Spot-check Density CSS custom properties resolve on documentElement."""
    vals = page_or_frame.evaluate("""(tokens) => {
        const cs = getComputedStyle(document.documentElement);
        const r = {};
        tokens.forEach(t => { r[t] = cs.getPropertyValue(t).trim(); });
        return r;
    }""", _DS_SPOT_TOKENS)
    resolved = {k: v for k, v in vals.items() if v}
    if len(resolved) == len(_DS_SPOT_TOKENS):
        report.add("pass", "DENSITY-TOKENS-RESOLVED",
                   f"All {len(_DS_SPOT_TOKENS)} spot-check tokens have values. "
                   f"surface-page={resolved.get('--ds-color-surface-page','?')}",
                   surface=surface, mode=mode)
    else:
        missing = [k for k, v in vals.items() if not v]
        report.add("minor", "DENSITY-TOKENS-PARTIAL",
                   f"{len(resolved)}/{len(_DS_SPOT_TOKENS)} tokens resolve. "
                   f"Missing on :root: {', '.join(missing)}",
                   surface=surface, mode=mode,
                   fix="These tokens may be scoped below :root. Verify density-apex-theme-standalone.css "
                       "declares them on :root, not body or a scoped selector.")


def _check_body_bg(page_or_frame, report: AuditReport, surface: str, mode: str = "light"):
    """Check body background matches expected Density value for the current mode."""
    bg = page_or_frame.evaluate("() => getComputedStyle(document.body).backgroundColor")
    if mode == "light":
        if "245, 246, 246" in bg:
            report.add("pass", "BODY-BG-CORRECT",
                       f"Body bg={bg} ✓ matches surface-page #f5f6f6",
                       surface=surface, mode=mode)
        elif "255, 255, 255" in bg:
            report.add("major", "BODY-BG-WHITE",
                       f"Body bg=pure white. Expected Density surface-page #f5f6f6.",
                       surface=surface, mode=mode,
                       fix="Add `body, .t-PageBody { background-color: var(--ds-color-surface-page) !important; }` "
                           "to density-apex-overrides.css. For dialog pages (body.t-Dialog-page) add a "
                           "separate rule targeting that class.")
        else:
            report.add("info", "BODY-BG-OTHER", f"Body bg={bg}", surface=surface, mode=mode)
    else:  # dark
        if any(x in bg for x in ["11, 13, 16", "0b0d10"]):
            report.add("pass", "BODY-BG-DARK-CORRECT",
                       f"Body bg={bg} ✓ matches dark surface-page",
                       surface=surface, mode=mode)
        elif "255, 255, 255" in bg or "245, 246" in bg:
            report.add("major", "BODY-BG-DARK-WHITE",
                       f"Body bg={bg} — still light in dark mode.",
                       surface=surface, mode=mode,
                       fix="Add body.ds-dark {{ background-color: var(--ds-color-surface-page) !important; }} "
                           "to density-dark-mode.css.")
        else:
            report.add("info", "BODY-BG-DARK-OTHER", f"Body bg={bg}", surface=surface, mode=mode)


def _check_header(page: Page, report: AuditReport, surface: str, mode: str = "light"):
    """Check header bg is not APEX blue."""
    bg = page.evaluate("""() => {
        const h = document.querySelector('.t-Header');
        return h ? getComputedStyle(h).backgroundColor : 'not found';
    }""")
    is_apex_blue = any(x in bg for x in ["0, 124, 195", "007cc3", "22, 104, 171"])
    if mode == "light":
        if is_apex_blue:
            report.add("major", "HEADER-APEX-BLUE",
                       f"Header bg={bg} — APEX default blue. Density override not applied.",
                       surface=surface, mode=mode,
                       fix="Add .t-Header {{ background-color: var(--ds-color-surface-base) !important; }} "
                           "to density-apex-overrides.css.")
        elif bg not in ("not found", "rgba(0, 0, 0, 0)"):
            report.add("pass", "HEADER-BG-OVERRIDDEN",
                       f"Header bg={bg} ✓ (not APEX blue)",
                       surface=surface, mode=mode)
    else:
        if any(x in bg for x in ["31, 35, 40", "1f2328"]):
            report.add("pass", "HEADER-BG-DARK",
                       f"Header bg={bg} ✓ dark surface-base",
                       surface=surface, mode=mode)
        elif is_apex_blue or "255, 255, 255" in bg or "245, 246" in bg:
            report.add("major", "HEADER-BG-DARK-WRONG",
                       f"Header bg={bg} — not dark in dark mode.",
                       surface=surface, mode=mode,
                       fix="Add body.ds-dark .t-Header {{ background-color: var(--ds-color-surface-base) !important; }}")


def _check_dark_mode_toggle(page: Page, report: AuditReport, surface: str):
    """Open user menu, check dark mode toggle exists and switch dimensions."""
    # Find user menu button
    user_li = page.query_selector('.t-NavigationBar-item.has-username')
    if not user_li:
        report.add("info", "USER-MENU-NOT-FOUND",
                   "No .has-username nav item — cannot check dark mode toggle",
                   surface=surface)
        return False

    btn = user_li.query_selector('button')
    if not btn:
        report.add("info", "USER-MENU-BTN-NOT-FOUND", "Button inside .has-username not found",
                   surface=surface)
        return False

    try:
        btn.click()
        time.sleep(0.8)
    except Exception as e:
        report.add("info", "USER-MENU-CLICK-FAILED", str(e), surface=surface)
        return False

    toggle_present = page.evaluate(
        "() => !!document.getElementById('ds-dark-mode-toggle-item')"
    )
    if toggle_present:
        sw = page.evaluate("""() => {
            const sw = document.querySelector('.ds-dark-toggle-switch');
            if (!sw) return null;
            const cs = getComputedStyle(sw);
            return { w: cs.width, h: cs.height, bg: cs.backgroundColor };
        }""")
        report.add("pass", "DARK-MODE-TOGGLE-PRESENT",
                   "#ds-dark-mode-toggle-item in user menu ✓",
                   surface=surface)
        if sw:
            if sw["w"] == "32px" and sw["h"] == "18px":
                report.add("pass", "DARK-MODE-TOGGLE-DIMENSIONS",
                           f"Switch {sw['w']}×{sw['h']} ✓ matches Density spec",
                           surface=surface)
            else:
                report.add("minor", "DARK-MODE-TOGGLE-DIMENSIONS",
                           f"Switch {sw['w']}×{sw['h']} — expected 32×18px",
                           surface=surface,
                           fix="Check .ds-dark-toggle-switch CSS in density-dark-mode.css: "
                               "width:32px; height:18px.")
    else:
        report.add("major", "DARK-MODE-TOGGLE-MISSING",
                   "#ds-dark-mode-toggle-item NOT in user menu. JS not running or menu selector changed.",
                   surface=surface,
                   fix="Open DevTools console, run: document.querySelectorAll('.t-Header [data-menu]') "
                       "— should return 2 buttons. If 0, the APEX version changed the nav bar attribute. "
                       "Update scanForMenuButtons() in density-dark-mode.js.")

    try:
        page.keyboard.press('Escape')
    except Exception:
        pass
    time.sleep(0.3)
    return toggle_present


def _enable_dark_mode(page: Page) -> bool:
    """Enable dark mode via the toggle or direct JS injection."""
    # Try via real toggle first
    user_li = page.query_selector('.t-NavigationBar-item.has-username')
    if user_li:
        btn = user_li.query_selector('button')
        if btn:
            try:
                btn.click()
                time.sleep(0.8)
                toggle = page.locator('#ds-dark-mode-toggle-item').first
                if toggle.count() > 0:
                    toggle.click()
                    time.sleep(0.5)
                    if page.evaluate("() => document.body.classList.contains('ds-dark')"):
                        return True
                page.keyboard.press('Escape')
            except Exception:
                pass
    # Fallback: direct injection
    page.evaluate(
        "() => { document.body.classList.add('ds-dark'); "
        "localStorage.setItem('ds-dark-mode','on'); }"
    )
    time.sleep(0.3)
    return page.evaluate("() => document.body.classList.contains('ds-dark')")


def _disable_dark_mode(page: Page):
    page.evaluate(
        "() => { document.body.classList.remove('ds-dark'); "
        "localStorage.setItem('ds-dark-mode','off'); }"
    )
    time.sleep(0.2)


def _sync_dark_to_iframes(page: Page):
    """Propagate ds-dark class into all open dialog iframes."""
    page.evaluate("""() => {
        const iframes = document.querySelectorAll('.ui-dialog iframe, [role="dialog"] iframe');
        const isDark = document.body.classList.contains('ds-dark');
        for (let i = 0; i < iframes.length; i++) {
            try {
                const doc = iframes[i].contentDocument || iframes[i].contentWindow.document;
                if (!doc || !doc.body) continue;
                if (isDark) doc.body.classList.add('ds-dark');
                else doc.body.classList.remove('ds-dark');
            } catch(e) {}
        }
    }""")


def _check_dialog_iframe(
    page: Page,
    iframe_el,
    report: AuditReport,
    surface: str,
    mode: str,
    shots_dir: Optional[pathlib.Path],
    injected_css: dict,
):
    """Full density check inside a dialog iframe document."""
    frame: Optional[Frame] = None
    try:
        frame = iframe_el.content_frame()
    except Exception:
        pass
    if not frame:
        report.add("info", f"IFRAME-NOT-ACCESSIBLE",
                   "iframe.content_frame() returned None — possibly cross-origin",
                   surface=surface, mode=mode)
        return

    # Inject CSS if we have local copies
    for label, css in injected_css.items():
        _inject_css(frame, css, label)
    time.sleep(0.3)

    # Sync dark mode
    if mode == "dark":
        try:
            frame.evaluate(
                "() => { document.body.classList.add('ds-dark'); }"
            )
        except Exception:
            pass

    # CSS assets in iframe
    sheets = frame.evaluate("""() =>
        Array.from(document.styleSheets)
             .map(s => { try { return s.href||''; } catch(e){ return ''; } })
             .filter(Boolean)
    """)
    density_sheets = [s for s in sheets if "density" in s]
    if len(density_sheets) >= 3:
        report.add("pass", "IFRAME-DENSITY-CSS",
                   f"All 3 Density sheets in iframe ✓",
                   surface=surface, mode=mode)
    else:
        report.add("major", "IFRAME-DENSITY-CSS-MISSING",
                   f"Only {len(density_sheets)}/3 Density sheets inside iframe. "
                   f"iframe body will not be styled.",
                   surface=surface, mode=mode,
                   fix="The iframe page must be part of the same APEX app that references the "
                       "Density CSS via User Interface Attributes. Ensure the dialog page (e.g. "
                       "Feedback page 10040) is in the same app with the same CSS file references.")

    # Body bg
    _check_body_bg(frame, report, surface, mode)

    # Dialog-specific elements
    state = frame.evaluate("""() => {
        const bcs = getComputedStyle(document.body);
        const get = sel => {
            const el = document.querySelector(sel);
            return el ? getComputedStyle(el).backgroundColor : 'n/a';
        };
        return {
            bodyClass:   document.body.className.substring(0, 100),
            bodyBg:      bcs.backgroundColor,
            bodyColor:   bcs.color,
            hasDsDark:   document.body.classList.contains('ds-dark'),
            regionBg:    get('.t-Region, .t-Dialog-body'),
            footerBg:    get('.t-ButtonRegion, .t-Dialog-footer'),
            smileyBg:    get('.u-radio'),
            textareaBg:  get('textarea.apex-item-textarea, textarea'),
            hotBtnBg:    get('.t-Button--hot'),
        };
    }""")

    # Dialog page type detection
    if "t-Dialog-page" in state.get("bodyClass", ""):
        report.add("info", "IFRAME-PAGE-TYPE",
                   "Dialog page (.t-Dialog-page) confirmed",
                   surface=surface, mode=mode)

    # Dark mode class propagation
    if mode == "dark":
        if state.get("hasDsDark"):
            report.add("pass", "IFRAME-DARK-PROPAGATED",
                       "ds-dark class present in iframe body ✓",
                       surface=surface, mode=mode)
        else:
            report.add("major", "IFRAME-DARK-NOT-PROPAGATED",
                       "ds-dark NOT in iframe body. Dark mode CSS cannot apply.",
                       surface=surface, mode=mode,
                       fix="density-dark-mode.js watchDialogIframes() must observe new iframes. "
                           "Ensure density-dark-mode.js v2+ is deployed (contains watchDialogIframes). "
                           "Also call syncDialogIframes() from toggleDarkMode().")

    # Smiley tiles
    sm_bg = state.get("smileyBg", "n/a")
    if sm_bg != "n/a":
        if mode == "light" and "248, 248, 248" in sm_bg:
            report.add("minor", "SMILEY-BG-OFF-WHITE",
                       f"Rating tiles bg={sm_bg} — APEX default near-white, not Density surface-neutral.",
                       surface=surface, mode=mode,
                       fix="Add body.t-Dialog-page .u-radio {{ background-color: var(--ds-color-surface-neutral) "
                           "!important; }} to density-apex-overrides.css.")
        elif mode == "dark" and any(x in sm_bg for x in ["248, 248", "255, 255", "245, 246"]):
            report.add("major", "SMILEY-BG-LIGHT-IN-DARK",
                       f"Rating tiles bg={sm_bg} — still light in dark mode.",
                       surface=surface, mode=mode,
                       fix="Add body.ds-dark.t-Dialog-page .u-radio {{ background-color: "
                           "var(--ds-color-surface-neutral) !important; }} to density-dark-mode.css.")
        else:
            report.add("pass", "SMILEY-BG-CORRECT",
                       f"Rating tiles bg={sm_bg} ✓",
                       surface=surface, mode=mode)

    # Screenshot
    shot = _screenshot(page, shots_dir, f"{surface}-{mode}.png")
    if shot:
        report.findings[-1].screenshot = shot


def _check_a11y(page: Page, report: AuditReport, surface: str):
    """ARIA label spot-check on interactive header elements."""
    a11y = page.evaluate("""() => {
        const interactive = Array.from(document.querySelectorAll(
            'button, a[href], input:not([type=hidden]), select, textarea'
        ));
        const missing = interactive.filter(el => {
            const lab = el.getAttribute('aria-label') || el.getAttribute('aria-labelledby') || el.getAttribute('title');
            const id = el.id;
            const assoc = id ? document.querySelector('label[for="'+id+'"]') : null;
            const wrapped = el.closest('label');
            return !lab && !assoc && !wrapped;
        });
        const hasFocusVisible = Array.from(document.styleSheets).some(ss => {
            try { return Array.from(ss.cssRules||[]).some(r =>
                r.selectorText && r.selectorText.includes(':focus-visible'));
            } catch(e) { return false; }
        });
        return {
            total: interactive.length,
            missing: missing.length,
            missingItems: missing.slice(0,5).map(el => ({
                tag: el.tagName, id: el.id,
                cls: (el.className||'').substring(0,50),
                text: (el.textContent||'').trim().substring(0,30),
                visible: el.offsetParent !== null
            })),
            focusVisible: hasFocusVisible
        };
    }""")

    pct = round(100 * a11y["missing"] / max(a11y["total"], 1))
    if a11y["missing"] == 0:
        report.add("pass", "A11Y-ARIA-LABELS",
                   f"All {a11y['total']} interactive elements have accessible labels ✓",
                   surface=surface)
    elif pct < 25:
        report.add("minor", "A11Y-ARIA-LABELS-MOSTLY-OK",
                   f"{a11y['missing']}/{a11y['total']} ({pct}%) missing labels.",
                   surface=surface,
                   fix="density-dark-mode.js patchA11y() adds labels to APEX header chrome. "
                       "Remaining missing elements may be APEX-generated hidden inputs — inspect "
                       "missingItems list and add aria-label attributes via JS or APEX item properties.")
    else:
        report.add("major", "A11Y-ARIA-LABELS-MISSING",
                   f"{a11y['missing']}/{a11y['total']} ({pct}%) interactive elements missing labels. "
                   f"Sample: {json.dumps(a11y['missingItems'][:3])}",
                   surface=surface,
                   fix="Add patchA11y() function from density-dark-mode.js v2+ which injects aria-labels "
                       "on all APEX-generated header nav buttons, logo link, and footer link.")

    if a11y["focusVisible"]:
        report.add("pass", "A11Y-FOCUS-RING",
                   ":focus-visible rule found in stylesheets ✓",
                   surface=surface)
    else:
        report.add("minor", "A11Y-FOCUS-RING-MISSING",
                   "No :focus-visible CSS rule found.",
                   surface=surface,
                   fix="Add :focus-visible { outline: 2px solid var(--ds-color-border-action-strong) !important; "
                       "outline-offset: 2px !important; } to density-apex-overrides.css.")


def _check_dark_mode_persistence(page: Page, report: AuditReport, surface: str):
    """Enable dark mode, reload, check it persists (FOUC prevention)."""
    _enable_dark_mode(page)
    page.reload(wait_until="networkidle", timeout=20000)
    time.sleep(2)
    state = page.evaluate("""() => ({
        hasDsClass: document.body.classList.contains('ds-dark'),
        ls: localStorage.getItem('ds-dark-mode'),
    })""")
    if state.get("hasDsClass"):
        report.add("pass", "DARK-MODE-PERSISTS",
                   "body.ds-dark present immediately after reload — FOUC risk low ✓",
                   surface=surface)
    else:
        report.add("major", "DARK-MODE-DOES-NOT-PERSIST",
                   f"body.ds-dark missing after reload. localStorage={state.get('ls')!r}. "
                   "applyPreference() is not running before first paint.",
                   surface=surface,
                   fix="Ensure density-dark-mode.js runs before </body> OR add a Global Page "
                       "Dynamic Action (Before Header) that reads localStorage and adds ds-dark "
                       "to body before APEX renders. See setup guide Section 10.")
    _disable_dark_mode(page)


def _enumerate_nav_links(page: Page) -> list[dict]:
    """Return all navigable links from left nav, tree nav, and nav bar."""
    return page.evaluate("""() =>
        Array.from(document.querySelectorAll(
            '.t-Body-nav a[href], .t-TreeNav a[href], .t-NavigationBar a[href], '
            + '.a-TreeView-label[href], .t-Nav-link[href]'
        ))
        .filter(a => {
            const href = a.href || '';
            return href && !href.startsWith('javascript') && !href.startsWith('#action$');
        })
        .map(a => ({
            text: (a.textContent||'').trim().substring(0, 40),
            href: a.href
        }))
        .filter((v, i, arr) => arr.findIndex(x => x.href === v.href) === i)
    """)


def _enumerate_dialog_triggers(page: Page) -> list[dict]:
    """Find nav bar buttons and links that open dialogs (data-menu or #action$)."""
    return page.evaluate("""() => {
        const items = [];
        // Nav bar buttons with data-menu (About/Help, User menu)
        document.querySelectorAll('.t-Header [data-menu]').forEach(btn => {
            items.push({
                type: 'dropdown',
                id:   btn.id,
                menuId: btn.getAttribute('data-menu'),
                text: (btn.textContent||'').trim().substring(0,30)
            });
        });
        // Links that open dialogs
        document.querySelectorAll('a[href*="dialog-open"], a[href*="a-dialog"]').forEach(a => {
            items.push({
                type: 'dialog-link',
                href: a.href,
                text: (a.textContent||'').trim().substring(0,30)
            });
        });
        return items;
    }""")


def _extract_version(url: str) -> str:
    """Extract static file version number from URL like /static/v87/..."""
    m = re.search(r"/v(\d+)/", url)
    return m.group(1) if m else "?"


# ══════════════════════════════════════════════════════════════════════════
# PAGE AUDITOR
# ══════════════════════════════════════════════════════════════════════════

def _audit_page(
    page: Page,
    url: str,
    surface: str,
    report: AuditReport,
    shots_dir: Optional[pathlib.Path],
    injected_css: dict,
    check_assets: bool = True,
):
    """Full audit of a single full-page URL — light mode then dark mode."""
    print(f"\n{'─'*60}")
    print(f"  PAGE: {surface} — {url[:70]}")
    print(f"{'─'*60}")

    try:
        if page.url != url:
            page.goto(url, wait_until="domcontentloaded", timeout=20000)
            time.sleep(2)
    except Exception as e:
        report.add("info", "PAGE-NAV-FAILED", str(e), surface=surface)
        return

    # Inject CSS
    for label, css in injected_css.items():
        _inject_css(page, css, label)

    shot = _screenshot(page, shots_dir, f"{surface}-light.png")
    report.add("info", "PAGE-LOADED", f"URL: {page.url[:80]}", surface=surface)

    # ── Light mode checks ──────────────────────────────────────────────
    if check_assets:
        _check_density_assets(page, report, surface)
    _check_tokens(page, report, surface, "light")
    _check_body_bg(page, report, surface, "light")
    _check_header(page, report, surface, "light")
    _check_a11y(page, report, surface)

    # ── Dark mode checks ───────────────────────────────────────────────
    print(f"  → Dark mode checks...")
    dm_on = _enable_dark_mode(page)
    time.sleep(0.5)

    # Re-inject CSS (some APEX pages clear head on navigation)
    for label, css in injected_css.items():
        _inject_css(page, css, label)
    time.sleep(0.3)

    _check_body_bg(page, report, surface, "dark")
    _check_header(page, report, surface, "dark")
    _check_tokens(page, report, surface, "dark")

    shot_dark = _screenshot(page, shots_dir, f"{surface}-dark.png")

    _disable_dark_mode(page)

    # ── Persistence check (only on pages we can reload) ────────────────
    print(f"  → Persistence check...")
    _check_dark_mode_persistence(page, report, surface)

    # Re-inject after reload
    for label, css in injected_css.items():
        _inject_css(page, css, label)


def _audit_dialogs(
    page: Page,
    report: AuditReport,
    shots_dir: Optional[pathlib.Path],
    injected_css: dict,
    surface_prefix: str,
):
    """
    Audit all dialog/modal surfaces on the current page.
    Handles:
      - Dropdown menus (About/Help nav bar button)
      - Dialog links (Feedback, modal pages)
    Tests each surface in BOTH light mode AND dark mode.
    """
    triggers = _enumerate_dialog_triggers(page)
    print(f"\n  Found {len(triggers)} dialog triggers on page")

    for trigger in triggers:
        ttype = trigger.get("type")
        ttext = trigger.get("text", "")

        # ── DROPDOWN MENU ────────────────────────────────────────────────
        if ttype == "dropdown":
            menu_id = trigger.get("menuId", "")
            btn_id  = trigger.get("id", "")
            safe    = re.sub(r'[^a-z0-9]', '-', ttext.lower())[:20]
            surface = f"{surface_prefix}-dropdown-{safe}"

            print(f"\n  ── Dropdown: '{ttext}' (data-menu={menu_id}) ──")

            # Open the dropdown
            try:
                btn = page.locator(f"#{btn_id}").first if btn_id else page.locator(f"[data-menu='{menu_id}']").first
                btn.click(); time.sleep(0.8)
            except Exception as e:
                report.add("info", f"DROPDOWN-OPEN-FAILED", str(e), surface=surface); continue

            # Light mode dropdown appearance
            menu_state = page.evaluate(f"""() => {{
                const m = document.getElementById('{menu_id}');
                if (!m) return null;
                const cs = getComputedStyle(m);
                return {{ bg: cs.backgroundColor, border: cs.borderColor, visible: m.offsetParent !== null }};
            }}""")
            if menu_state:
                bg = menu_state.get("bg","")
                if "255, 255, 255" in bg:
                    report.add("pass", "DROPDOWN-BG-LIGHT",
                               f"Dropdown bg=surface-base (white) ✓", surface=surface)
                elif "rgba(0, 0, 0, 0)" in bg or not bg:
                    report.add("minor", "DROPDOWN-BG-TRANSPARENT",
                               f"Dropdown bg=transparent — may appear unrooted over content.",
                               surface=surface, mode="light",
                               fix="Add .t-NavigationBar-menu, .t-NavigationBar-menu.a-Menu "
                                   "{{ background-color: var(--ds-color-surface-base) !important; }} "
                                   "to density-apex-overrides.css.")
                else:
                    report.add("info", "DROPDOWN-BG", f"bg={bg}", surface=surface)

            # Screenshot light
            _screenshot(page, shots_dir, f"{surface}-light.png")

            # Get menu items visible
            items = page.evaluate("""() =>
                Array.from(document.querySelectorAll('[role="menuitem"]'))
                    .filter(el => { const r=el.getBoundingClientRect(); return r.width>0 && r.height>0; })
                    .map(el => ({
                        text: (el.textContent||'').trim(),
                        tag:  el.tagName,
                        href: el.href||el.getAttribute('href')||''
                    }))
            """)
            report.add("info", f"DROPDOWN-ITEMS",
                       f"Items: {[i['text'] for i in items]}",
                       surface=surface)

            page.keyboard.press('Escape'); time.sleep(0.4)

            # ── Dark mode dropdown ──────────────────────────────────────
            _enable_dark_mode(page)
            for label, css in injected_css.items():
                _inject_css(page, css, label)
            try:
                btn.click(); time.sleep(0.8)
            except Exception: pass

            dark_menu = page.evaluate(f"""() => {{
                const m = document.getElementById('{menu_id}');
                if (!m) return null;
                const cs = getComputedStyle(m);
                return {{ bg: cs.backgroundColor, visible: m.offsetParent !== null }};
            }}""")
            if dark_menu:
                bg = dark_menu.get("bg","")
                if any(x in bg for x in ["31, 35, 40","1f2328"]):
                    report.add("pass", "DROPDOWN-BG-DARK",
                               f"Dropdown bg={bg} ✓ dark surface-base",
                               surface=surface, mode="dark")
                else:
                    report.add("major", "DROPDOWN-BG-DARK-WRONG",
                               f"Dropdown bg={bg} — not dark.",
                               surface=surface, mode="dark",
                               fix="Add body.ds-dark .t-NavigationBar-menu "
                                   "{{ background-color: var(--ds-color-surface-base) !important; }} "
                                   "to density-dark-mode.css.")

            _screenshot(page, shots_dir, f"{surface}-dark.png")
            page.keyboard.press('Escape'); time.sleep(0.4)
            _disable_dark_mode(page)

            # ── Open each submenu item that opens a dialog ──────────────
            for item in items:
                item_text = item.get("text","")
                item_safe = re.sub(r'[^a-z0-9]', '-', item_text.lower())[:20]
                if not item_text or item_text in ("---",):
                    continue
                _audit_dialog_item(
                    page, trigger, item_text, item_safe,
                    f"{surface}-{item_safe}",
                    report, shots_dir, injected_css
                )

        # ── DIALOG LINK (e.g. Feedback) ──────────────────────────────────
        elif ttype == "dialog-link":
            href   = trigger.get("href","")
            safe   = re.sub(r'[^a-z0-9]', '-', ttext.lower())[:20]
            surface = f"{surface_prefix}-dialog-{safe}"
            print(f"\n  ── Dialog link: '{ttext}' ──")

            for mode in ("light", "dark"):
                _close_dialog(page)
                if mode == "dark":
                    _enable_dark_mode(page)
                    for label, css in injected_css.items():
                        _inject_css(page, css, label)
                    time.sleep(0.3)

                try:
                    link = page.locator(f'a[href*="feedback"], a[href*="{safe}"]').first
                    if link.count() == 0:
                        # Try by text
                        link = page.get_by_text(ttext, exact=False).first
                    link.click(); time.sleep(3)
                except Exception as e:
                    report.add("info", f"DIALOG-LINK-OPEN-FAILED", str(e),
                               surface=surface, mode=mode)
                    if mode == "dark": _disable_dark_mode(page)
                    continue

                iframe_el = page.query_selector('.ui-dialog iframe')
                if iframe_el:
                    if mode == "dark":
                        _sync_dark_to_iframes(page)
                        time.sleep(0.5)
                    _check_dialog_iframe(
                        page, iframe_el, report, surface, mode,
                        shots_dir, injected_css
                    )
                    report.modals_visited.append(f"{surface} ({mode})")
                else:
                    report.add("info", f"DIALOG-NO-IFRAME",
                               "Dialog opened but no iframe found — may be inline content.",
                               surface=surface, mode=mode)

                _screenshot(page, shots_dir, f"{surface}-{mode}.png")
                _close_dialog(page)
                time.sleep(0.8)

                if mode == "dark":
                    _disable_dark_mode(page)


def _audit_dialog_item(
    page, dropdown_trigger, item_text, item_safe, surface,
    report, shots_dir, injected_css
):
    """Open a specific dropdown menu item and audit the resulting dialog/page."""
    btn_id  = dropdown_trigger.get("id","")
    menu_id = dropdown_trigger.get("menuId","")

    for mode in ("light", "dark"):
        _close_dialog(page)
        if mode == "dark":
            _enable_dark_mode(page)
            for label, css in injected_css.items():
                _inject_css(page, css, label)

        # Re-open dropdown
        try:
            btn = page.locator(f"#{btn_id}").first if btn_id else page.locator(f"[data-menu='{menu_id}']").first
            btn.click(); time.sleep(0.7)
        except Exception as e:
            report.add("info", f"ITEM-DROPDOWN-REOPEN-FAILED", str(e),
                       surface=surface, mode=mode)
            if mode == "dark": _disable_dark_mode(page)
            continue

        # Click item
        target = None
        for el in page.query_selector_all('[role="menuitem"]'):
            try:
                bb = el.bounding_box()
                if bb and el.text_content().strip() == item_text:
                    target = el; break
            except Exception: pass

        if not target:
            report.add("info", f"MENU-ITEM-NOT-FOUND",
                       f"'{item_text}' not clickable in menu",
                       surface=surface, mode=mode)
            page.keyboard.press('Escape'); time.sleep(0.3)
            if mode == "dark": _disable_dark_mode(page)
            continue

        original_url = page.url
        try:
            target.click(); time.sleep(2)
        except Exception as e:
            report.add("info", f"MENU-ITEM-CLICK-FAILED", str(e),
                       surface=surface, mode=mode)
            page.keyboard.press('Escape')
            if mode == "dark": _disable_dark_mode(page)
            continue

        # What opened?
        has_dialog = page.evaluate("() => !!document.querySelector('.ui-dialog')")
        has_iframe  = page.evaluate("() => !!document.querySelector('.ui-dialog iframe')")
        new_url     = page.url

        if has_iframe:
            iframe_el = page.query_selector('.ui-dialog iframe')
            if mode == "dark":
                _sync_dark_to_iframes(page)
                time.sleep(0.5)
            _check_dialog_iframe(
                page, iframe_el, report, surface, mode,
                shots_dir, injected_css
            )
            report.modals_visited.append(f"{surface} ({mode})")

        elif has_dialog:
            # Inline dialog (no iframe)
            dstate = page.evaluate("""() => ({
                bg: (() => { const d=document.querySelector('.ui-dialog'); return d ? getComputedStyle(d).backgroundColor : 'n/a'; })(),
                titleBg: (() => { const t=document.querySelector('.ui-dialog-titlebar'); return t ? getComputedStyle(t).backgroundColor : 'n/a'; })(),
            })""")
            if mode == "light":
                if "255, 255, 255" in dstate.get("bg",""):
                    report.add("pass", "DIALOG-BG-CORRECT",
                               f"Dialog bg=surface-base (white) ✓",
                               surface=surface, mode=mode)
                else:
                    report.add("info", "DIALOG-BG",
                               f"Dialog bg={dstate.get('bg')}",
                               surface=surface, mode=mode)
            else:
                bg = dstate.get("bg","")
                if any(x in bg for x in ["31, 35","1f2328"]):
                    report.add("pass", "DIALOG-BG-DARK",
                               f"Dialog bg={bg} ✓ dark",
                               surface=surface, mode=mode)
                else:
                    report.add("major", "DIALOG-BG-DARK-WRONG",
                               f"Dialog bg={bg} — not dark in dark mode.",
                               surface=surface, mode=mode,
                               fix="Add body.ds-dark .ui-dialog {{ background-color: "
                                   "var(--ds-color-surface-base) !important; }} to density-dark-mode.css.")
            report.modals_visited.append(f"{surface} ({mode})")

        elif new_url != original_url:
            # Full page navigation
            report.add("info", f"ITEM-NAVIGATED",
                       f"'{item_text}' navigated to: {new_url[:70]}",
                       surface=surface, mode=mode)
            # Audit as a page
            _check_body_bg(page, report, surface, mode)
            _check_header(page, report, surface, mode)
            report.pages_visited.append(new_url)
            page.go_back(); time.sleep(1.5)

        _screenshot(page, shots_dir, f"{surface}-{mode}.png")
        _close_dialog(page)
        time.sleep(0.6)
        if mode == "dark":
            _disable_dark_mode(page)


# ══════════════════════════════════════════════════════════════════════════
# DARK MODE TOGGLE CHECK (dedicated pass)
# ══════════════════════════════════════════════════════════════════════════

def _audit_dark_mode_toggle(
    page: Page, report: AuditReport, shots_dir, injected_css, surface
):
    """Dedicated dark mode toggle check: inject, click, verify, screenshot."""
    print(f"\n  → Dark mode toggle audit...")
    present = _check_dark_mode_toggle(page, report, surface)
    if not present:
        return

    # Enable and verify full-page dark state
    dm = _enable_dark_mode(page)
    for label, css in injected_css.items():
        _inject_css(page, css, label)
    time.sleep(0.5)

    dm_styles = page.evaluate("""() => ({
        bodyBg:    getComputedStyle(document.body).backgroundColor,
        headerBg:  (() => { const h=document.querySelector('.t-Header'); return h ? getComputedStyle(h).backgroundColor : 'n/a'; })(),
        hasDsDark: document.body.classList.contains('ds-dark'),
    })""")

    body_bg = dm_styles.get("bodyBg","")
    hdr_bg  = dm_styles.get("headerBg","")

    if any(x in body_bg for x in ["11, 13, 16","0b0d10"]):
        report.add("pass", "DARK-MODE-BODY-DARK",
                   f"body bg={body_bg} ✓ dark surface-page",
                   surface=surface, mode="dark")
    else:
        report.add("major", "DARK-MODE-BODY-NOT-DARK",
                   f"body bg={body_bg} — not dark after toggle.",
                   surface=surface, mode="dark",
                   fix="Verify density-dark-mode.css has body.ds-dark rules. "
                       "Check that localStorage 'ds-dark-mode' is being read on page load.")

    if any(x in hdr_bg for x in ["31, 35, 40","1f2328"]):
        report.add("pass", "DARK-MODE-HEADER-DARK",
                   f"Header bg={hdr_bg} ✓ dark surface-base",
                   surface=surface, mode="dark")
    else:
        report.add("minor", "DARK-MODE-HEADER-DARK-WRONG",
                   f"Header bg={hdr_bg} in dark mode.",
                   surface=surface, mode="dark")

    _screenshot(page, shots_dir, f"{surface}-dark-toggle.png")
    _disable_dark_mode(page)


# ══════════════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════

def run_audit(
    target_url: str,
    shots_dir: Optional[pathlib.Path] = None,
    css_dir: Optional[pathlib.Path] = None,
    apex_host: Optional[str] = None,
    max_nav_pages: int = 10,
    close_on_finish: bool = False,
) -> AuditReport:
    """
    Run a full Density compliance audit on any BMW APEX application.

    Parameters
    ──────────
    target_url      : Full URL of the APEX app home page
    shots_dir       : Where to save screenshots (auto-created). None = skip screenshots.
    css_dir         : Local directory containing density-*.css and density-*.js files
                      for injection into iframes. If None, only checks files loaded by APEX.
    apex_host       : Override hostname detection (e.g. 'apextw10.bmwgroup.net').
                      Default: inferred from target_url.
    max_nav_pages   : Maximum number of nav-bar linked pages to follow (default 10).
    close_on_finish : If False (default), browser stays open after audit completes.
                      Press Enter in the console to close it. Set True for headless CI.

    Returns
    ───────
    AuditReport  — call .summary() for markdown, .save(path) for JSON + MD.
    """
    parsed   = urlparse(target_url)
    apex_host = apex_host or parsed.netloc
    report   = AuditReport(target_url=target_url)

    # ── Load local CSS files if available ─────────────────────────────
    injected_css: dict[str, str] = {}
    css_search = css_dir or _DEFAULT_CSS
    if css_search.exists():
        for fname in ["density-apex-overrides.css",
                      "density-dark-mode.css",
                      "density-apex-theme-standalone.css"]:
            p = css_search / fname
            if p.exists():
                injected_css[fname.replace(".", "-")] = p.read_text()
        print(f"  📦 Loaded {len(injected_css)} local CSS files for iframe injection")
    else:
        print(f"  ℹ️  No local CSS dir found at {css_search} — skipping iframe injection")

    if shots_dir:
        shots_dir.mkdir(parents=True, exist_ok=True)
        print(f"  📸 Screenshots → {shots_dir}")

    # ── Launch browser ─────────────────────────────────────────────────
    _BROWSER_PROFILE.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as pw:
        ctx: BrowserContext = pw.chromium.launch_persistent_context(
            str(_BROWSER_PROFILE),
            headless=False,
            slow_mo=150,
            viewport={"width": 1440, "height": 900},
            args=["--start-maximized"],
        )
        page: Page = ctx.pages[0] if ctx.pages else ctx.new_page()

        print(f"\n🌐 Navigating to: {target_url}")
        page.goto(target_url, wait_until="domcontentloaded", timeout=30000)
        time.sleep(2)

        # ── Wait for login ─────────────────────────────────────────────
        if not _wait_for_apex_host(page, apex_host):
            report.add("critical", "AUTH-FAILED",
                       f"Could not land on {apex_host} within 180s. Audit aborted.")
            if not close_on_finish:
                input("\n[Audit aborted — press Enter to close browser]")
            ctx.close()
            return report

        if not _wait_for_apex_ready(page):
            print("  ⚠️  apex.jQuery not confirmed — continuing anyway")

        # Inject CSS into parent page
        for label, css in injected_css.items():
            _inject_css(page, css, label)
        time.sleep(0.5)

        # ══════════════════════════════════════════════════════════════
        # PHASE 1 — HOME PAGE
        # ══════════════════════════════════════════════════════════════
        print(f"\n{'═'*60}")
        print("  PHASE 1: HOME PAGE")
        print(f"{'═'*60}")
        home_url = page.url
        report.pages_visited.append(home_url)

        _check_density_assets(page, report, "home")
        _check_tokens(page, report, "home", "light")
        _check_body_bg(page, report, "home", "light")
        _check_header(page, report, "home", "light")
        _check_a11y(page, report, "home")
        _screenshot(page, shots_dir, "home-light.png")

        # ══════════════════════════════════════════════════════════════
        # PHASE 2 — DARK MODE TOGGLE + PERSISTENCE
        # ══════════════════════════════════════════════════════════════
        print(f"\n{'═'*60}")
        print("  PHASE 2: DARK MODE TOGGLE & PERSISTENCE")
        print(f"{'═'*60}")
        _audit_dark_mode_toggle(page, report, shots_dir, injected_css, "home")
        _check_dark_mode_persistence(page, report, "home")

        # Re-inject after reload
        for label, css in injected_css.items():
            _inject_css(page, css, label)

        # ══════════════════════════════════════════════════════════════
        # PHASE 3 — ALL DIALOG / MODAL SURFACES ON HOME PAGE
        # ══════════════════════════════════════════════════════════════
        print(f"\n{'═'*60}")
        print("  PHASE 3: DIALOGS & MODALS (home page triggers)")
        print(f"{'═'*60}")
        _audit_dialogs(page, report, shots_dir, injected_css, "home")

        # ══════════════════════════════════════════════════════════════
        # PHASE 4 — NAVIGATE EVERY LINKED PAGE
        # ══════════════════════════════════════════════════════════════
        print(f"\n{'═'*60}")
        print("  PHASE 4: NAVIGABLE PAGES")
        print(f"{'═'*60}")

        # Navigate back to home first
        if page.url != home_url:
            page.goto(home_url, wait_until="domcontentloaded", timeout=20000)
            time.sleep(2)
            for label, css in injected_css.items():
                _inject_css(page, css, label)

        nav_links = _enumerate_nav_links(page)
        print(f"  Found {len(nav_links)} navigable links")

        visited_urls = {home_url}
        pages_done   = 0
        for link in nav_links:
            if pages_done >= max_nav_pages:
                report.add("info", "NAV-LIMIT-REACHED",
                           f"Stopped at {max_nav_pages} pages (max_nav_pages limit)")
                break
            href = link.get("href","")
            text = link.get("text","")
            if not href or href in visited_urls:
                continue
            if apex_host not in href:
                continue
            visited_urls.add(href)
            pages_done += 1
            safe = re.sub(r'[^a-z0-9]', '-', text.lower())[:20] or f"page-{pages_done}"

            print(f"\n  → Visiting: '{text}' ({href[:60]})")

            try:
                page.goto(href, wait_until="domcontentloaded", timeout=20000)
                time.sleep(2)
            except Exception as e:
                report.add("info", "NAV-FAILED", f"'{text}': {e}", surface=safe)
                continue

            for label, css in injected_css.items():
                _inject_css(page, css, label)

            report.pages_visited.append(href)
            _check_body_bg(page, report, safe, "light")
            _check_header(page, report, safe, "light")

            # Check for IR / Interactive Grid
            has_ir = page.evaluate(
                "() => !!document.querySelector('.a-IRR-table, .a-IRR-wrapper, .a-GV-table')"
            )
            if has_ir:
                print(f"    ↳ Interactive Report/Grid found — auditing IR components")
                _audit_ir_page(page, report, shots_dir, injected_css, safe)

            # Dark mode on this page
            _enable_dark_mode(page)
            for label, css in injected_css.items():
                _inject_css(page, css, label)
            _check_body_bg(page, report, safe, "dark")
            _check_header(page, report, safe, "dark")
            _screenshot(page, shots_dir, f"{safe}-dark.png")
            _disable_dark_mode(page)

            # Dialogs on this page
            _audit_dialogs(page, report, shots_dir, injected_css, safe)

            # Return home for next link discovery
            page.goto(home_url, wait_until="domcontentloaded", timeout=20000)
            time.sleep(1.5)
            for label, css in injected_css.items():
                _inject_css(page, css, label)
            nav_links = _enumerate_nav_links(page)

        # ══════════════════════════════════════════════════════════════
        # DONE
        # ══════════════════════════════════════════════════════════════
        if shots_dir:
            report.save(shots_dir)

        print(f"\n{'═'*60}")
        print(f"  AUDIT COMPLETE")
        print(f"  Score:   {report.score()}%")
        print(f"  Pass:    {len(report.passes())}")
        print(f"  Major:   {len(report.majors())}")
        print(f"  Minor:   {len(report.minors())}")
        print(f"  Pages:   {len(report.pages_visited)}")
        print(f"  Modals:  {len(report.modals_visited)}")
        print(f"{'═'*60}")

        if not close_on_finish:
            print("\n✅ Audit finished. Browser will stay open.")
            print("   Press Enter here to close it when done reviewing.")
            try:
                input()
            except EOFError:
                pass

        ctx.close()

    return report


# ══════════════════════════════════════════════════════════════════════════
# IR / INTERACTIVE REPORT AUDIT
# ══════════════════════════════════════════════════════════════════════════

def _audit_ir_page(
    page: Page,
    report: AuditReport,
    shots_dir,
    injected_css: dict,
    surface: str,
):
    """Check Interactive Report/Grid specific Density styling."""
    ir_state = page.evaluate("""() => {
        const get = sel => {
            const el = document.querySelector(sel);
            return el ? getComputedStyle(el).backgroundColor : 'n/a';
        };
        return {
            irrBg:       get('.a-IRR, .a-IRR-wrapper'),
            thBg:        get('.a-IRR-table th, .a-GV-header th'),
            tdBorder:    (() => {
                const td = document.querySelector('.a-IRR-table td');
                return td ? getComputedStyle(td).borderTopColor : 'n/a';
            })(),
            toolbarBg:   get('.a-IRR-toolbar, .a-Toolbar, .a-IG-toolbar'),
            rowHoverBg:  'n/a',  // can only check via CSS rule inspection
        };
    }""")

    # Body bg on IR page
    body_bg = page.evaluate("() => getComputedStyle(document.body).backgroundColor")
    if "245, 246, 246" in body_bg:
        report.add("pass", "IR-BODY-BG",
                   f"IR page body bg=surface-page #f5f6f6 ✓",
                   surface=surface)
    elif "255, 255, 255" in body_bg:
        report.add("minor", "IR-BODY-BG-WHITE",
                   f"IR page body bg=white (expected surface-page #f5f6f6)",
                   surface=surface,
                   fix="Verify density-apex-overrides.css body rule loads on this page.")
    else:
        report.add("info", "IR-BODY-BG", f"bg={body_bg}", surface=surface)

    _screenshot(page, shots_dir, f"{surface}-ir-light.png")

    # Dark mode IR
    _enable_dark_mode(page)
    for label, css in injected_css.items():
        _inject_css(page, css, label)
    time.sleep(0.5)

    dark_ir = page.evaluate("""() => ({
        bodyBg: getComputedStyle(document.body).backgroundColor,
        thBg:   (() => { const t=document.querySelector('.a-IRR-table th,.a-GV-header th'); return t ? getComputedStyle(t).backgroundColor : 'n/a'; })(),
        tdCol:  (() => { const t=document.querySelector('.a-IRR-table td'); return t ? getComputedStyle(t).color : 'n/a'; })(),
    })""")

    body_dark = dark_ir.get("bodyBg","")
    if any(x in body_dark for x in ["11, 13","0b0d"]):
        report.add("pass", "IR-BODY-DARK",
                   f"IR page dark body bg={body_dark} ✓",
                   surface=surface, mode="dark")
    else:
        report.add("major", "IR-BODY-DARK-WRONG",
                   f"IR page dark body bg={body_dark}",
                   surface=surface, mode="dark",
                   fix="Ensure body.ds-dark rules apply on this page template.")

    _screenshot(page, shots_dir, f"{surface}-ir-dark.png")
    _disable_dark_mode(page)


# ══════════════════════════════════════════════════════════════════════════
# QUICK-RUN HELPER (for CLI usage)
# ══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys

    url = sys.argv[1] if len(sys.argv) > 1 else input("APEX target URL: ").strip()

    shots = pathlib.Path(
        sys.argv[2] if len(sys.argv) > 2 else
        f"/Users/QTE2362/Desktop/density-apex-howto/screenshots/audit-{int(time.time())}"
    )

    # Try to find density CSS files relative to this script
    css_dir = _SKILL_DIR / "density_css"
    if not css_dir.exists():
        # Try the canonical howto dir
        howto = pathlib.Path("/Users/QTE2362/Desktop/density-apex-howto")
        if howto.exists():
            css_dir = howto
            print(f"  Using CSS from {css_dir}")

    report = run_audit(
        target_url=url,
        shots_dir=shots,
        css_dir=css_dir,
    )

    print("\n" + "="*60)
    print(report.summary())
