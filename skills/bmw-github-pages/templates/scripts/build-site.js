#!/usr/bin/env node

/**
 * build-site.js
 *
 * Generic static site builder for BMW-styled GitHub Pages sites.
 * Reads site.json config, renders Mustache templates, and outputs to dist/.
 */

const fs = require('fs');
const path = require('path');
const Mustache = require('mustache');

const ROOT = path.resolve(__dirname, '..');
const DIST = path.join(ROOT, 'dist');
const TEMPLATES_DIR = path.join(ROOT, 'templates');
const ASSETS_DIR = path.join(ROOT, 'assets');

// ── Load config ──────────────────────────────────────────────
const configPath = path.join(ROOT, 'site.json');
let config;
try {
  config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
} catch (err) {
  console.error(`Failed to load site configuration: ${configPath}`);
  console.error(`  ${err.message}`);
  process.exit(1);
}
const basePath = process.env.BASE_PATH || '';

// ── Load templates ───────────────────────────────────────────
function loadTemplate(name, { required = false } = {}) {
  const filePath = path.join(TEMPLATES_DIR, name);
  if (!fs.existsSync(filePath)) {
    console.error(`  [ERROR] Template not found: ${name} (expected at ${filePath})`);
    if (required) {
      process.exit(1);
    }
    return '';
  }
  return fs.readFileSync(filePath, 'utf8');
}

const headerPartial = loadTemplate('partials/header.html', { required: true });
const footerPartial = loadTemplate('partials/footer.html', { required: true });

// ── Render page ──────────────────────────────────────────────
function renderPage(template, view) {
  const year = new Date().getFullYear();

  // Build nav pages with active state
  const navPages = (config.pages || [])
    .filter(p => p.nav !== false)
    .map(p => ({
      ...p,
      active: p.id === view.activePageId,
      // Home link: empty output so {{basePath}}/{{output}} renders as "/"
      // or "/my-repo/" when deployed to a subdirectory (basePath handles it)
      output: p.id === 'home' ? '' : p.output,
    }));

  const commonView = {
    ...view,
    basePath,
    year,
    site: config.site,
    hero: config.hero,
    features: config.features,
    stats: config.stats,
    about: config.about,
    contact: config.contact,
    footer: config.footer,
    repo: config.repo,
    navPages,
  };

  // Render header and footer partials
  const header = Mustache.render(headerPartial, commonView);
  const footer = Mustache.render(footerPartial, commonView);

  return Mustache.render(template, {
    ...commonView,
    header,
    footer,
  });
}

// ── Copy directory recursively ───────────────────────────────
function copyDirSync(src, dest) {
  fs.mkdirSync(dest, { recursive: true });
  const entries = fs.readdirSync(src, { withFileTypes: true });
  for (const entry of entries) {
    const srcPath = path.join(src, entry.name);
    const destPath = path.join(dest, entry.name);
    if (entry.isDirectory()) {
      copyDirSync(srcPath, destPath);
    } else {
      fs.copyFileSync(srcPath, destPath);
    }
  }
}

// ── Main ─────────────────────────────────────────────────────
function main() {
  console.log('Building site...\n');

  // Clean & create dist
  if (fs.existsSync(DIST)) {
    fs.rmSync(DIST, { recursive: true });
  }
  fs.mkdirSync(DIST, { recursive: true });

  // Render each page defined in config
  const pages = config.pages || [];
  for (const page of pages) {
    const templateName = page.template || `${page.id}.html`;
    const template = loadTemplate(templateName);

    if (!template) {
      console.warn(`  [skip] No template found for page: ${page.id}`);
      continue;
    }

    console.log(`Rendering ${page.output}...`);
    const html = renderPage(template, {
      activePageId: page.id,
    });
    fs.writeFileSync(path.join(DIST, page.output), html);
  }

  // Copy static assets
  console.log('\nCopying assets...');
  if (fs.existsSync(ASSETS_DIR)) {
    copyDirSync(ASSETS_DIR, path.join(DIST, 'assets'));
  }

  console.log(`\nBuild complete! Output in dist/`);
  console.log(`  ${pages.length} pages rendered`);
}

main();
