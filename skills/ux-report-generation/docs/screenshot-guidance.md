# Screenshot Guidance

This document defines how to capture, embed, and handle screenshots in all DesignOps evaluation reports.

---

## Capture First, Write Second

Always attempt to capture Playwright screenshots **before** writing the HTML report file. This ensures relative `src` paths in the report resolve correctly when the file is opened.

Save every screenshot to:

```
reports/<skill-folder>/screenshots/<descriptive-name>.png
```

Reference them in the report using a relative path:

```html
<img src="screenshots/<descriptive-name>.png" alt="[SCREENSHOT_ALT]" />
```

---

## Capture Workflow

> ⚠️ **Always use `run_playwright_code` with `page.screenshot({ path })` to save PNGs to disk.** Do NOT use the `screenshot_page` tool — it saves to temporary VS Code chat resource URIs that cannot be referenced from HTML reports.

1. Use `run_playwright_code` to navigate to the relevant page or state that demonstrates the finding.
2. Wait for the page to settle (animations, lazy-loaded images):
   ```js
   await page.waitForTimeout(500);
   ```
3. Capture a viewport or element-scoped screenshot and write it directly to the `screenshots/` subfolder:
   ```js
   await page.screenshot({
     path: "/absolute/path/to/reports/<skill-folder>/screenshots/<finding-name>.png",
     fullPage: false,
   });
   ```
4. Note the filename for use in the corresponding finding card's `<div class="screenshot">` block.

Capture one screenshot per finding where visual evidence adds value. Not every finding needs a screenshot — prioritise Critical and High severity findings.

**If the live browser session has expired between evaluation and report writing:**
Re-open a new session with `open_browser_page`, navigate back to each URL that surfaced a finding, and re-capture. For SSO/OIDC-protected apps, see the SSO section below.

---

## SSO / OIDC-Protected Applications

If the target application requires SSO or OIDC login:

1. Launch a **visible** (non-headless) browser session:
   ```js
   const browser = await chromium.launch({ headless: false });
   ```
2. Pause and prompt the user to authenticate in the browser window before continuing.
3. Once the user confirms they are logged in, proceed with screenshot capture.
4. If the session expires or authentication fails, fall back to the placeholder approach below.

---

## Placeholder Blocks

When a screenshot cannot be captured (SSO failure, app unavailable, page not found), insert a labelled placeholder block in place of the `<img>` element:

```html
<div class="screenshot">
  <div
    style="
    background: var(--color-surface-page);
    border: 2px dashed var(--color-border-neutral);
    padding: 2rem;
    text-align: center;
    color: var(--color-cool-grey-600);
    font-size: 0.85rem;
  "
  >
    📷 Screenshot unavailable — [REASON]<br />
    <span style="font-size:0.75rem;opacity:0.7">[PAGE_URL_OR_CONTEXT]</span>
  </div>
  <div class="screenshot-caption">[SCREENSHOT_CAPTION]</div>
</div>
```

Replace `[REASON]` with a brief explanation (e.g. `SSO login required`, `Application unreachable`).

---

## Screenshot Block HTML

Use the following markup for every embedded screenshot:

```html
<div class="screenshot">
  <img src="screenshots/[SCREENSHOT_FILE]" alt="[SCREENSHOT_ALT]" />
  <div class="screenshot-caption">[SCREENSHOT_CAPTION]</div>
</div>
```

- `[SCREENSHOT_FILE]` — filename only, e.g. `h1-no-loading-state.png`
- `[SCREENSHOT_ALT]` — descriptive alt text for accessibility (describe what is shown)
- `[SCREENSHOT_CAPTION]` — short human-readable label, e.g. `H1.1 — No spinner visible during data fetch`

Omit the screenshot block entirely for findings where visual evidence is not applicable (e.g. code-only issues, architecture concerns).
