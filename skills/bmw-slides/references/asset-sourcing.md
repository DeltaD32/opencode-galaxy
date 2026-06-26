# Asset Sourcing

## What to Source

For every slide in the approved storyline, determine what assets are needed:

**If PPTX mode:**

- **Layouts with picture placeholders (0, 1, 13, 14, 18, 19):** These have empty picture placeholders that need an image. Always source an image for these.
- **Free-area layouts (2, 12):** Source an image if the storyline plans one and the free area has room after text content.
- **Content-only layouts (7-11):** Do not source images. These layouts are designed for text; images would compete with content.

**If HTML mode:**

- **Slides with `**Image:**` field in storyline:** Always source an image. The storyline explicitly requests one.
- **Cover slides (`[cover]`):** Source a background image only if the storyline's `**Image:**` field requests one. Default cover uses a CSS gradient — no image needed.
- **Dark-background slides (`dark-metrics`, `custom` with dark bg):** Good candidates for background images to add visual depth. Source if `**Image:**` is present.
- **Content slides without `**Image:**` field:** Do not source images. These slides are designed for text and visual components; images would compete with content.

If the user has provided their own images (file paths in the storyline or otherwise), use those instead of searching. Note this in the manifest.

If no slide in the deck needs an image, this phase produces an empty manifest. Still present the result to the user — do not silently skip.

## Approved Sources (License-Safe)

Only use sources with permissive licenses that allow commercial use without per-image fees:

| Source                             | License                            | Attribution Required         | Best For                   |
| ---------------------------------- | ---------------------------------- | ---------------------------- | -------------------------- |
| **Unsplash**                       | Unsplash License (free commercial) | No (credit appreciated)      | Hero photos, backgrounds   |
| **Pexels**                         | Pexels License (free commercial)   | No                           | Photos, backgrounds        |
| **Pixabay**                        | Pixabay License (free commercial)  | No                           | Photos, illustrations      |
| **Wikimedia Commons**              | Varies (check per file)            | Yes (use exact license text) | Diagrams, logos, technical |
| **Simple Icons** (simpleicons.org) | CC0                                | No                           | Brand/tech SVG icons       |
| **Material Symbols** (Google)      | Apache 2.0                         | No                           | UI/concept icons           |
| **Lucide** (lucide.dev)            | ISC                                | No                           | Clean line icons           |
| **Heroicons** (heroicons.com)      | MIT                                | No                           | UI icons                   |

**Never use:** Getty, Shutterstock, Adobe Stock, or any rights-managed source. If license is unclear, skip the image.

## Search Process

For each slide that needs an image:

1. **Formulate search queries** based on slide topic (not the raw title):

   - Use 2-3 English keyword variations
   - Prefer abstract/conceptual over literal (e.g., "team collaboration abstract" over "people in meeting")
   - For tech topics: search for related diagrams, architecture visuals, or abstract tech imagery

2. **Search using `websearch_cited`** with queries like:

   - `site:unsplash.com/photos {topic} dark background`
   - `site:pexels.com/photo {topic} background`
   - `site:commons.wikimedia.org/wiki/File: {topic} photograph`
   - For icons: `site:simpleicons.org {brand}` or search icon libraries directly

3. **Query quality rules (mandatory):**

   - Do **not** query `site:upload.wikimedia.org` directly. That is a raw file host and yields noisy results.
   - For Wikimedia, query `site:commons.wikimedia.org/wiki/File:` pages first, then resolve to direct image URL.
   - Prefer photo-intent terms for backgrounds: `photo`, `photograph`, `long exposure`, `dark`, `minimal`, `background`.
   - Add exclusion terms for hero/background searches to avoid clipart-style assets:
     - `-logo -icon -flag -svg -clipart -illustration`
   - For title/closing backgrounds, bias toward dark/low-detail imagery so title text remains readable.

4. **Provider priority by slide type:**

   - Hero/title/closing background: `Unsplash -> Pexels -> Pixabay -> Wikimedia`
   - Content-side photo: `Pexels -> Unsplash -> Pixabay -> Wikimedia`
   - Factual/technical diagram: `Wikimedia -> Pixabay -> Pexels -> Unsplash`

5. **Evaluate candidates:**

   - Confirm license is permissive (check the source page)
   - Prefer landscape orientation for slides (16:9)
   - Prefer high resolution (min 1920px wide for backgrounds)
   - Prefer clean, uncluttered images with space for text overlay
     - **If PPTX mode:** especially for layout 0/18
     - **If HTML mode:** especially for cover and dark-background slides
   - For icons: prefer SVG or high-res PNG, monochrome or simple color

6. **Download** approved assets:
   - **If PPTX mode:** into `{output_dir}/assets/` folder
   - **If HTML mode:** into `{deck-dir}/assets/` folder

## URL Quality Gate (Critical)

Before downloading, ensure URLs are fetchable binaries:

- Prefer direct image hosts: `images.unsplash.com`, `images.pexels.com`, `upload.wikimedia.org`.
- Avoid `source.unsplash.com` (frequent 401/blocked for automated requests).
- Avoid raw page URLs in final manifest. If only a page URL is available, provide it and let the resolver convert it.
- Provide `fallback_urls` whenever possible (provider diversity: Unsplash -> Pexels -> Pixabay/Wikimedia).

### Query templates by intent

- Hero/title background:
  - `site:unsplash.com/photos abstract technology dark background -logo -icon -svg -clipart -illustration`
  - `site:pexels.com/photo abstract technology dark background`
- Collaboration/people:
  - `site:unsplash.com/photos collaboration teamwork office photo -logo -icon -svg -clipart`
  - `site:pexels.com/photo team collaboration office`
- Factual/diagram (Wikimedia):
  - `site:commons.wikimedia.org/wiki/File: data center photograph`
  - `site:commons.wikimedia.org/wiki/File: network architecture diagram`

## Asset Manifest

After sourcing, present the manifest to the user as a table:

```
Assets for: [Presentation Title]
Download folder: /path/to/output/assets/

| Slide | Type | File | Source | License | Attribution |
|-------|------|------|--------|---------|-------------|
| 1 | background | title_bg.jpg | Unsplash / @photographer | Unsplash License | Photo by Name on Unsplash |
| 3 | photo | evolution.jpg | Pexels / Author | Pexels License | - |
| 5 | icon | arrow_right.png | Material Symbols | Apache 2.0 | - |
```

If no images were needed, present:

**If PPTX mode:**

```
Assets for: [Presentation Title]
No image assets needed — all slides use text-only layouts (7-11).
```

**If HTML mode:**

```
Assets for: [Presentation Title]
No image assets needed — no slides reference images.
```

## Preferred Download Helper

Use the bundled helper script instead of ad-hoc `urllib` snippets. It adds retries, timeouts, partial-failure handling, and optional JPG conversion.

Script: `./scripts/download_assets.py`

### Input manifest JSON

```json
[
  {
    "slide": 1,
    "type": "background",
    "file": "title_bg.jpg",
    "url": "https://images.unsplash.com/photo-xxxx?w=1920&q=80",
    "fallback_urls": [
      "https://images.pexels.com/photos/xxxx/pexels-photo-xxxx.jpeg?auto=compress&cs=tinysrgb&w=1920"
    ],
    "source": "Unsplash / @photographer",
    "license": "Unsplash License",
    "attribution": "Photo by Name on Unsplash"
  }
]
```

### Command

**If PPTX mode:**

```bash
uv run python ./scripts/download_assets.py \
  --manifest /absolute/path/to/assets-manifest.json \
  --assets-dir /absolute/path/to/assets \
  --output-manifest /absolute/path/to/assets-manifest.resolved.json \
  --require-slides "$(uv run python ./scripts/pptx/storyline_required_picture_slides.py /absolute/path/to/<deck>-storyline.md)" \
  --convert-jpg
```

**If HTML mode:**

```bash
uv run python {skill-dir}/scripts/download_assets.py \
  --manifest /absolute/path/to/assets-manifest.json \
  --assets-dir /absolute/path/to/deck/assets \
  --output-manifest /absolute/path/to/assets-manifest.resolved.json \
  --convert-jpg
```

Use the resolved manifest (`*.resolved.json`) as the source for the user-facing table.

Fail-fast behavior:

- The downloader performs URL resolution + preflight checks before full download.
- **If PPTX mode:** If `--require-slides` is set, the command fails when any required picture slide is missing/failed.
- **If HTML mode:** Use `--require-slides` to make the script fail if specific slides are missing.

## Attribution Handling

**If PPTX mode:**

- Add attribution per slide in **Speaker Notes** (append to existing notes):
  `"Image: [description] by [author] on [source] ([license])"`.
- If 3+ images have attribution requirements, add a final **"Image Credits"** slide (layout 7) listing all attributions.
- For CC0/Unsplash/Pexels: attribution is appreciated but not legally required. Still add it to speaker notes for traceability.

**If HTML mode:**

- For slides with sourced images, add attribution as an HTML comment in the slide fragment:
  `<!-- Image: [description] by [author] on [source] ([license]) -->`
- If 3+ images have attribution requirements, mention in the handoff to the user that credits may be needed.
- For CC0/Unsplash/Pexels: attribution is appreciated but not legally required. Still add it to HTML comments for traceability.

## Image Paths in Slide Fragments (HTML mode only)

All image references in HTML fragments use **relative paths**: `./assets/filename.jpg`

The assemble script handles the rest:

- **Preview mode:** paths stay relative (works when opened locally via `file://`)
- **Export mode:** images are base64-encoded into the HTML (self-contained)
