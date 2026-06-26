---
name: bmw-github-pages
version: "1.0.0"
description: Create BMW-styled static websites with GitHub Pages deployment. Trigger on requests to "create a website", "new GitHub Pages site", "BMW static site", "scaffold a site", or similar.
metadata:
  authors:
    - Kristaps Dreija <Kristaps.Dreija@bmw.de>
  tags:
    - bmw
    - github-pages
    - static-site
    - scaffold
    - web
deps:
  internal:
    - gh-account-switching
  external:
    - name: gh
      check: gh --version
      install_hint: "brew install gh"
    - name: node
      check: node --version
      install_hint: "brew install node"
    - name: tsx
      check: npx tsx --version
      install_hint: "npm install -g tsx"
---

# BMW GitHub Pages

## Overview

This skill scaffolds a complete BMW-branded static website and deploys it to GitHub Pages. It creates a new GitHub repository, populates it with a Mustache-based static site using BMW 2025 design tokens (colors, typography, spacing, dark mode), and configures automatic deployment via GitHub Actions.

The generated site includes:
- BMW CI-compliant design system (CSS custom properties, responsive layout, dark mode)
- Mustache-based templating with shared header/footer partials
- Config-driven content via `site.json`
- GitHub Actions workflow for automatic deployment on push
- Homepage with hero section, stats, and feature cards (bento grid)
- About page with content sections
- Contact page with team cards

## When to Use

- When the user wants to create a new BMW-branded static website
- When the user asks to "set up a GitHub Pages site", "create a project site", or "scaffold a BMW site"
- When the user wants a quick, professional-looking static site with BMW branding
- When the user needs a landing page, project showcase, or documentation site

## When NOT to Use

- When the user wants a dynamic web application (React, Next.js, etc.)
- When the user is working on an existing site and just needs CSS/design help
- When the user wants to modify the hackathon showcase site specifically (use the repo directly)
- When the user needs a presentation deck (use `bmw-pptx` skill instead)

## Bundled Resources

This skill includes a complete project template in the `templates/` subdirectory and a TypeScript scaffold script (`scaffold.ts`) that copies and customizes the templates.

```
bmw-github-pages/
├── SKILL.md              # This file
├── scaffold.ts           # Cross-platform TypeScript scaffold script
└── templates/            # Project template files
    ├── package.json
    ├── site.json          # Central configuration
    ├── .gitignore
    ├── README.md
    ├── assets/
    │   ├── styles.css     # BMW 2025 design system CSS
    │   └── bmw-logo.svg   # BMW logo (white, for dark header)
    ├── templates/
    │   ├── index.html     # Homepage (hero, stats, feature cards)
    │   ├── about.html     # About page
    │   ├── contact.html   # Contact page
    │   └── partials/
    │       ├── header.html  # Sticky nav, dark mode toggle
    │       └── footer.html  # Footer with links
    ├── scripts/
    │   └── build-site.js  # Mustache static site generator
    └── .github/
        └── workflows/
            └── deploy.yml # GitHub Pages deployment
```

## Instructions

### Step 1: Gather requirements

Ask the user for:

1. **Project name** (required) -- e.g., "My Dashboard"
2. **GitHub owner/org** (required) -- e.g., "my-org" or "username"
3. **GitHub host** -- Ask which GitHub instance to use. Options: `github.com`, `cc-github.bmwgroup.net`, `bmw.ghe.com`, or other. Default to whatever `gh` is currently authenticated against.
4. **Repository visibility** -- public or private (default: private for enterprise, public for github.com)
5. **Project description** (optional) -- short tagline
6. **Project subtitle** (optional) -- shown in header under the name

If the user provides all details upfront, skip the questions and proceed.

### Step 2: Scaffold the project

Run the TypeScript scaffold script to create the project files. The script is located relative to this SKILL.md file.

Determine the skill directory path (where this SKILL.md lives) and run:

```bash
SKILL_DIR="<path-to-this-skill-directory>"
npx tsx "$SKILL_DIR/scaffold.ts" \
  --name "<project-name>" \
  --dir "<target-directory>" \
  --description "<description>" \
  --subtitle "<subtitle>" \
  --organization "<organization>"
```

The target directory should typically be a temporary directory or a new directory in the user's workspace.

If `npx tsx` is not available, fall back to manually copying the `templates/` directory contents to the target directory and updating `site.json` with the user's project details using the Edit tool.

### Step 3: Customize site.json

After scaffolding, help the user customize `site.json` if they want to:
- Change the hero heading, tagline, or CTA button
- Add/remove/reorder pages in the `pages` array
- Update feature cards (icon, name, description)
- Update stats numbers
- Edit about page sections
- Update contact information
- Set the repo URL (will be set automatically in Step 5)

### Step 4: Verify the build

Run the build to make sure everything works:

```bash
cd <target-directory>
npm install
npm run build
```

This should produce a `dist/` directory with the rendered HTML files and copied assets. Verify the output looks correct.

### Step 5: Create GitHub repository and push

Use the `gh` CLI to create the repo and push:

```bash
# If targeting a specific GitHub host, ensure gh is authenticated:
# gh auth login --hostname <host>

# Initialize git and create the first commit
cd <target-directory>
git init
git add .
git commit -m "Initial commit"

# Create the repository (use --public or --private as appropriate)
gh repo create <owner>/<repo-name> --private --description "<description>" --source . --push
# For public repos:
# gh repo create <owner>/<repo-name> --public --description "<description>" --source . --push

# Update site.json repo.url and footer link using Edit tool
```

After pushing, update `site.json` with the actual repo URL and commit the change.

### Step 6: Enable GitHub Pages

Configure GitHub Pages to deploy from GitHub Actions:

```bash
# Enable Pages with GitHub Actions as the source
gh api repos/<owner>/<repo-name>/pages \
  --method POST \
  --field "build_type=workflow" \
  -H "Accept: application/vnd.github+json" 2>/dev/null || \
gh api repos/<owner>/<repo-name>/pages \
  --method PUT \
  --field "build_type=workflow" \
  -H "Accept: application/vnd.github+json"
```

Note: On some GitHub Enterprise instances, you may need to enable Pages in the repository settings UI manually.

### Step 7: Trigger deployment and verify

The GitHub Actions workflow will trigger automatically on push. To trigger manually:

```bash
gh workflow run deploy.yml --repo <owner>/<repo-name>
```

Wait for the workflow to complete and report the Pages URL to the user:

```bash
gh api repos/<owner>/<repo-name>/pages --jq '.html_url'
```

### Step 8: Report results

Tell the user:
- The repository URL
- The GitHub Pages URL
- How to customize: edit `site.json` and push
- How to add pages: create a template in `templates/`, add entry to `site.json`
- How to preview locally: `npm run dev`

## Customization Guide

### Adding a new page

1. Create `templates/my-page.html` following the pattern of existing pages
2. Add to `site.json` pages array:
   ```json
   { "id": "my-page", "title": "My Page", "template": "my-page.html", "output": "my-page.html", "nav": true }
   ```
3. Run `npm run build`

### Changing colors

Edit `assets/styles.css` -- the BMW design tokens are in the `:root` block at the top. Key variables:
- `--bmw-dark-teal`: Primary brand color
- `--bmw-light-blue`: Accent color
- `--bmw-medium-blue`: Secondary accent
- Dark mode overrides are in the `[data-theme="dark"]` block

### Replacing the logo

Replace `assets/bmw-logo.svg` with your own SVG. The header expects a white logo that works on the dark teal background.

## CSS Component Reference

The bundled CSS includes these ready-to-use components:

| Component | Class | Description |
|---|---|---|
| Hero | `.hero`, `.hero-eyebrow`, `.hero-tagline` | Full-width gradient hero section |
| Bento Grid | `.bento-grid`, `.bento-card` | 3-column responsive card grid |
| Feature Cards | `.feature-grid`, `.feature-card` | Auto-fill card grid with hover accent bar |
| Stats Row | `.stats-row`, `.stat` | Centered statistics display |
| Content Page | `.content-page` | Long-form content with styled headings |
| Callouts | `.callout`, `.callout--info/warning/tip` | Info/warning/tip boxes with left border |
| Steps | `.steps`, `.step` | Numbered step-by-step guide |
| Buttons | `.btn`, `.btn--primary/outline/ghost/sm` | Button variants |
| Section | `.section`, `.section--subtle/dark` | Page sections with background variants |
| Section Header | `.section-header` | Centered section title + subtitle |
| Contact Form | `.contact-form`, `.form-group` | Styled form inputs |
| Tags | `.member-tag` | Small inline tag/badge |

## Error Handling

| Error | Cause | Fix |
|---|---|---|
| `gh: command not found` | GitHub CLI not installed | `brew install gh` |
| `HTTP 404 ... /pages` | Pages not available on this repo | Enable Pages in repo Settings manually |
| `HTTP 422 ... /pages` | Pages already configured | Use PUT instead of POST, or ignore |
| `npx tsx: command not found` | tsx not installed | `npm install -g tsx` or use fallback (manual copy) |
| Build fails: `Cannot find module 'mustache'` | Dependencies not installed | Run `npm install` in the target directory |
