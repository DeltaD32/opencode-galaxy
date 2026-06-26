# BMW Static Site

A BMW-branded static site built with [Mustache](https://mustache.github.io/) templates and deployed to GitHub Pages.

## Quick Start

```bash
npm install
npm run build              # Build to dist/
npx --yes serve dist       # Preview locally
```

## Configuration

Edit `site.json` to customize:
- Site name, subtitle, description
- Navigation pages
- Hero section content
- Features, stats, about, and contact content
- Footer links

## Adding Pages

1. Create a new `.html` template in `templates/`
2. Add a page entry to `site.json` under `pages`
3. Run `npm run build`

## Deployment

This site deploys automatically to GitHub Pages via GitHub Actions on every push to `main`.

To set up:
1. Go to repo Settings > Pages
2. Set Source to "GitHub Actions"
3. Push to `main`

## Project Structure

```
├── assets/
│   ├── styles.css       # BMW design system CSS
│   └── bmw-logo.svg     # BMW logo
├── templates/
│   ├── index.html       # Homepage template
│   ├── about.html       # About page template
│   ├── contact.html     # Contact page template
│   └── partials/
│       ├── header.html  # Shared header with nav
│       └── footer.html  # Shared footer
├── scripts/
│   └── build-site.js    # Static site generator
├── site.json            # Site configuration
├── package.json
└── .github/
    └── workflows/
        └── deploy.yml   # GitHub Pages deployment
```
