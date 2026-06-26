# Delivery Step 1 — Asset Sourcing

This is the first step of the internal delivery pipeline. It runs right after storyline approval and flows directly into the build step (`delivery-build.md`) without a separate user gate.

Asset sourcing has two modes: **local** (default, fast) and **web** (optional, for custom images).

Search for license-safe images and icons that strengthen the visual story. This phase produces an **asset manifest** and a local `assets/` folder next to the output deck.

## Local Asset Mode (Default — Always Run First)

Before any web search, check what cover images are already available in the shared project `assets/` folder.

### Step 0 — Local Cover Image Selection

1. List all files matching `cover_*.{png,jpg,jpeg}` in the shared `assets/` directory at the project root (two levels above the deck dir — `../../assets/` relative to the deck).
2. Pick the **default cover image** using this priority:
   - If the storyline specifies `**Cover Image:** <filename>`, use that file.
   - Otherwise, use `cover_default.jpg` if it exists.
   - If `cover_default.jpg` is missing, use the alphabetically first `cover_*` file found.
3. Record the chosen file as `cover_image` in the manifest.
4. **Outro slide**: if the last slide in the storyline is of type `cover-bmw`, it automatically reuses the same cover image (no separate asset needed).

Present the local cover selection to the user:

> **Cover image selected:** `cover_default.jpg` (from shared assets)
> Available alternatives: `cover_bmw4cylnight.jpg`, `cover_city.jpg`, `cover_mountains.jpg`, …
>
> You can change the cover image by saying "use cover_mountains.jpg" or request web search for a custom image.

Then **continue immediately to Step 1** (scan storyline for additional image needs). Do not wait for user confirmation unless they respond.

---

## Web Asset Mode (Optional — On User Request)

If the user says "search for images", "find a photo of…", or a slide's storyline contains a description requiring a web image (see format-specific rules below), offer to run the web search.

**Do not run web search automatically** unless slides explicitly need images (see Step 1).

If the user requests it, offer:

> I can search for images on Unsplash/Pexels/Pixabay for the following slides:
>
> - Slide 3: background photo of a city at night
> - Slide 7: chart/dashboard screenshot
>
> Shall I proceed with web search? This may take a moment.

Only after user confirms, launch the web search subagent (see Step 2 below).

---

## Step 1 — Scan Storyline for Image Needs

Read the storyline from disk. How you determine which slides need images depends on the output format:

<!-- FORMAT: PPTX -->

### PPTX format

Scan by **layout type**:

- **Always need images:** layouts 0, 1, 13, 14, 18, 19
- **Conditional:** layouts 2, 12 — only when the storyline explicitly specifies an image
- **Never need images:** layouts 7-11 (text-only)

Build a list of slides that need images, with their topic/description.

<!-- /FORMAT: PPTX -->

<!-- FORMAT: HTML -->

### HTML format

For each slide, check:

- Does the slide have an `**Image:**` field? If yes, it needs an image.
- Is the `**Image:**` value an existing file path (user-provided)? If yes, copy it to `assets/` — no search needed.
- Is the `**Image:**` value a description or placeholder (e.g., `./assets/metrics-chart.png`)? If yes, note it as needing web search.

Build a list of slides that need images, with their topic/description.

<!-- /FORMAT: HTML -->

If **no slides need images** (beyond the cover already handled in Step 0), produce a minimal manifest with just the cover image, inform the user, and proceed directly to the build step.

Read `./references/asset-sourcing.md` for full details:

- **What to Source** — which slides need images based on the rules above
- **Approved Sources** — Unsplash, Pexels, Pixabay, Wikimedia, icon libraries (all license-safe, commercial-use)
- **Search Process** — how to formulate queries, evaluate candidates, download assets
- **Asset Manifest** — format and example tables to present to the user
- **Preferred Download Helper** — use `./scripts/download_assets.py` for robust downloads
- **Attribution Handling** — speaker notes format and credits slide (PPTX), or HTML comments in fragments for traceability (HTML)

### GitHub Copilot: use a sub-agent for web search

**⚠️ Copilot only (skip this section in Claude / OpenCode):** Copilot's 120K context window fills up fast when fetching web pages inline. Delegate all web browsing and downloading to a **single Task sub-agent** so HTML content stays out of the main conversation.

<!-- FORMAT: PPTX -->

1. Scan the storyline to list which slides need images (layouts 0, 1, 13, 14, 18, 19 need them; 2/12 only if storyline specifies one; 7-11 never).
   <!-- /FORMAT: PPTX -->
   <!-- FORMAT: HTML -->
1. Scan the storyline to list which slides have `**Image:**` fields that need sourcing.
<!-- /FORMAT: HTML -->

1. Launch **one** sub-agent with the prompt in Step 2.

## Step 2 — Search and Download Assets

Launch **one Task subagent** to handle all web searching and downloading. This keeps HTML content from web pages out of the main conversation context.

### Subagent Prompt Template

````
You are an image sourcing assistant. Your job is to find and download
license-safe images for a slide presentation.

## Instructions

Read `{skill-dir}/references/asset-sourcing.md` for:
- Approved sources (Unsplash, Pexels, Pixabay, etc.)
- Search process and evaluation criteria
- License and attribution rules
- URL quality gate and fail-fast rules

## Assets to source

{list each slide number, component type, topic/description, and what kind of image is needed}

## Download folder

{deck-dir}/assets/

Create the folder if it doesn't exist. Download each image there.
Prefer landscape orientation, min 1920px wide for backgrounds.
Use `./scripts/download_assets.py` for downloading (retries + timeout + optional JPG conversion).

```bash
uv run python {skill-dir}/scripts/download_assets.py \
  --manifest {deck-dir}/assets-manifest.json \
  --assets-dir {deck-dir}/assets \
  --output-manifest {deck-dir}/assets-manifest.resolved.json \
  --convert-jpg
```

Before running the script, write the manifest JSON file at `{deck-dir}/assets-manifest.json`.

### Search rules
- Avoid `source.unsplash.com` URLs. Prefer direct image URLs (`images.unsplash.com`, `images.pexels.com`, `upload.wikimedia.org`).
- For Wikimedia queries, use `site:commons.wikimedia.org/wiki/File:` pages, never `site:upload.wikimedia.org`.
- For background searches, include exclusions: `-logo -icon -svg -clipart -illustration`.
- Prefer dark/low-detail imagery for backgrounds so text remains readable.

## Output

Reply with an asset manifest table in this exact format:

| Slide | Type | File | Source | License | Attribution |
|-------|------|------|--------|---------|-------------|
| 1 | background | title_bg.jpg | Unsplash / @photographer | Unsplash License | Photo by Name on Unsplash |

If you cannot find a suitable image for a slide, note it with Type = "MISSING".
Confirm which files were downloaded to the assets folder.
````

### Download implementation rule

Use `./scripts/download_assets.py` for batch downloads. Avoid ad-hoc inline downloader code unless the helper script is unavailable.

<!-- FORMAT: PPTX -->

Use required-slide fail-fast for picture layouts:

```bash
uv run python ./scripts/download_assets.py \
  --manifest /absolute/path/to/assets-manifest.json \
  --assets-dir /absolute/path/to/assets \
  --output-manifest /absolute/path/to/assets-manifest.resolved.json \
  --require-slides "$(uv run python ./scripts/pptx/storyline_required_picture_slides.py /absolute/path/to/<deck>-storyline.md)" \
  --convert-jpg
```

<!-- /FORMAT: PPTX -->

## Step 3 — Review Results

After the subagent returns:

1. **Check** that all required images were downloaded (no "MISSING" entries for critical slides).
2. **Verify** files exist in `{deck-dir}/assets/` using the filesystem.
3. **Present** the manifest table to the user.

If any required image is missing:

- Try alternative search terms or sources
- If still missing, note it for the user and continue — build sub-agents will add `<!-- TODO -->` comments for missing images

## Handoff to the Build Step

This step runs internally. Do not stop for a separate user approval (unless images are missing).

<!-- FORMAT: PPTX -->

1. Source assets only for relevant slides (0, 1, 13, 14, 18, 19 always; 2/12 only when storyline explicitly requires an image; 7-11 never).
2. Keep attribution metadata in the manifest for final notes/credits handling.
3. Do NOT proceed if any required picture slide is missing an asset (`Type = MISSING` for layouts 0, 1, 13, 14, 18, 19).
4. Continue directly to the build step (`./phases/pptx/delivery-build.md`) with per-slide loops as defined in `./references/delivery.md`.
<!-- /FORMAT: PPTX -->

<!-- FORMAT: HTML -->

1. Source assets only for slides with `**Image:**` fields in the storyline.
2. Keep attribution metadata in the manifest for traceability.
3. Continue directly to the build step (`./phases/html/delivery-build.md`).
<!-- /FORMAT: HTML -->
