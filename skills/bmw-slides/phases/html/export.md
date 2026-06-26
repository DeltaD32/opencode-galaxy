# HTML Export (on-demand)

Runs only when the user explicitly asks for a self-contained / shareable HTML file, after the delivery pipeline has completed.

Export the deck as a **self-contained HTML file** with all images base64-encoded. The result is a single portable file that can be shared via email, opened offline, and needs no server.

## When to Run

Run this phase when the user asks to:

- Export / finalize the presentation
- Create a shareable / portable version
- "Make it self-contained"

## How It Works

The assemble script with `--export` flag:

1. Reads all slide fragments from `slides/`
2. Injects `base.css` + `overrides.css` into a single `<style>` block
3. Replaces all `<img src="./assets/...">` with `data:image/...;base64,...`
4. Replaces all CSS `url(./assets/...)` with data URIs
5. Produces one complete HTML file with zero external dependencies

## Running the Export

```bash
node {skill-dir}/scripts/html/assemble.mjs <deck-dir> --export
```

Output: `<deck-dir>/<deck-name>.html`

To specify a custom output path:

```bash
node {skill-dir}/scripts/html/assemble.mjs <deck-dir> --export -o /path/to/output.html
```

## Verification

After export, verify:

| #   | Check                                                     |
| --- | --------------------------------------------------------- |
| 1   | File opens in browser with all slides and navigation      |
| 2   | All images render (no broken image icons)                 |
| 3   | No external requests (check browser DevTools Network tab) |
| 4   | File size is reasonable (base64 adds ~33% to image sizes) |

## Presenting to User

> "Exported self-contained presentation to:
> `[/path/to/deck.html]`
>
> This file contains everything — CSS, JS, and images — and can be opened directly in any browser or shared via email.
>
> Want me to also export to PDF?"
