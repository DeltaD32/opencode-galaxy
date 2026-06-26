# PDF Export (on-demand)

Runs only when the user explicitly asks for a PDF, after the delivery pipeline has completed (and optionally after HTML Export).

Convert the assembled HTML slide deck to a multi-page landscape PDF — one page per slide.

## When to Run

Run this phase when the user asks for a PDF. The PDF export works against the **assembled HTML** — either the preview or the exported self-contained version. If the deck uses images via relative paths, use the preview HTML (which resolves them locally via `file://`).

## Prerequisites

```bash
npx playwright install chromium   # one-time, downloads headless Chromium
pip install pypdf                  # for merging PDFs
```

## Running the Export

First, ensure an assembled HTML exists. If not, assemble it:

```bash
# Assemble preview (if not already done)
node {skill-dir}/scripts/html/assemble.mjs <deck-dir>

# Then export to PDF
node {skill-dir}/scripts/html/html_slides_to_pdf.mjs <deck-dir>/<deck-name>-preview.html <deck-dir>/<deck-name>.pdf
```

Or use the self-contained export as source:

```bash
node {skill-dir}/scripts/html/html_slides_to_pdf.mjs <deck-dir>/<deck-name>.html <deck-dir>/<deck-name>.pdf
```

## How It Works

The assembled HTML is a single-page app where only one `.slide` div is visible at a time. The PDF script uses Playwright to:

1. Open the HTML file in headless Chromium
2. For each `.slide` div: show it, hide all others, print to a single-page PDF
3. Merge all single-page PDFs into one multi-page PDF using pypdf

The script:

- Auto-detects all `.slide` elements
- Renders at 1280x720 px with `deviceScaleFactor: 2` (retina quality)
- Hides navigation dots during export
- Merges with pypdf (falls back to qpdf if available)

## Output

- **Format:** 1280x720 px landscape (13.33 x 7.5 inches)
- **One page per slide** — no blank pages, no margins
- **Full backgrounds** — dark slides, gradients, all rendered correctly
- **No headers/footers** from the browser — only the slide's own footer

## Troubleshooting

| Problem          | Cause                                                        | Fix                                                                         |
| ---------------- | ------------------------------------------------------------ | --------------------------------------------------------------------------- |
| Broken images    | Preview HTML with relative paths opened from wrong directory | Use exported self-contained HTML instead, or ensure CWD is correct          |
| Text cut off     | Content overflows slide dimensions                           | Check that content fits within `.content` flex container                    |
| Missing fonts    | BMW Group TT not installed                                   | Falls back to Helvetica Neue / Arial — acceptable                           |
| Merge fails      | Neither pypdf nor qpdf installed                             | `pip install pypdf`                                                         |
| Script not found | Wrong path                                                   | Script is at `./scripts/html/html_slides_to_pdf.mjs` relative to skill root |

## Presenting to User

After export:

> "PDF exported to:
> `[/path/to/deck-name.pdf]`
>
> — X pages, one per slide, landscape 16:9"
