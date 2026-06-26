/**
 * assemble.mjs — Assemble slide fragments into a complete HTML presentation.
 *
 * Usage:
 *   node assemble.mjs <deck-dir>              → preview (relative image paths)
 *   node assemble.mjs <deck-dir> --export     → self-contained (base64 images)
 *   node assemble.mjs <deck-dir> --export -o out.html
 *
 * Expects:
 *   <deck-dir>/
 *     slides/slide-1.html, slide-2.html, ...   (HTML fragments)
 *     overrides.css                             (optional)
 *     assets/                                   (optional, images)
 *     config.yaml or ../config.yaml             (footer, confidentiality)
 *
 * The skill's references/ dir is resolved relative to this script:
 *   <script-dir>/../../references/html/template.html
 *   <script-dir>/../../references/html/base.css
 */

import { readFileSync, writeFileSync, readdirSync, existsSync, statSync } from 'fs';
import { resolve, dirname, join, basename, extname, relative } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// ── Parse arguments ─────────────────────────────────────────────────────────

const args = process.argv.slice(2);
let deckDir = null;
let exportMode = false;
let outputPath = null;

for (let i = 0; i < args.length; i++) {
  if (args[i] === '--export') {
    exportMode = true;
  } else if (args[i] === '-o' && args[i + 1]) {
    outputPath = args[++i];
  } else if (!deckDir) {
    deckDir = args[i];
  }
}

if (!deckDir) {
  console.error('Usage: node assemble.mjs <deck-dir> [--export] [-o output.html]');
  process.exit(1);
}

deckDir = resolve(deckDir);

if (!existsSync(deckDir) || !statSync(deckDir).isDirectory()) {
  console.error(`Error: ${deckDir} is not a directory`);
  process.exit(1);
}

// ── Resolve paths ───────────────────────────────────────────────────────────

const skillRef = resolve(__dirname, '..', '..', 'references', 'html');
const templatePath = join(skillRef, 'template.html');
const baseCssPath = join(skillRef, 'base.css');
const slidesDir = join(deckDir, 'slides');
const overridesPath = join(deckDir, 'overrides.css');
const assetsDir = join(deckDir, 'assets');

// Config: check deck-local first, then skill-level
const configPaths = [
  join(deckDir, 'config.yaml'),
  resolve(__dirname, '..', '..', 'config.yaml'),
];

// ── Load template + base CSS ────────────────────────────────────────────────

if (!existsSync(templatePath)) {
  console.error(`Error: template.html not found at ${templatePath}`);
  process.exit(1);
}
if (!existsSync(baseCssPath)) {
  console.error(`Error: base.css not found at ${baseCssPath}`);
  process.exit(1);
}

let template = readFileSync(templatePath, 'utf-8');
const baseCss = readFileSync(baseCssPath, 'utf-8');

// ── Load slide fragments ────────────────────────────────────────────────────

if (!existsSync(slidesDir)) {
  console.error(`Error: slides/ directory not found in ${deckDir}`);
  process.exit(1);
}

const slideFiles = readdirSync(slidesDir)
  .filter(f => /^slide-\d+\.html$/.test(f))
  .sort((a, b) => {
    const numA = parseInt(a.match(/\d+/)[0]);
    const numB = parseInt(b.match(/\d+/)[0]);
    return numA - numB;
  });

if (slideFiles.length === 0) {
  console.error(`Error: no slide-*.html files found in ${slidesDir}`);
  process.exit(1);
}

console.log(`Found ${slideFiles.length} slides: ${slideFiles.join(', ')}`);

const slideHtmlParts = slideFiles.map(f =>
  readFileSync(join(slidesDir, f), 'utf-8').trim()
);

const total = slideFiles.length;

// ── Load overrides CSS (optional) ───────────────────────────────────────────

let overridesCss = '';
if (existsSync(overridesPath)) {
  overridesCss = readFileSync(overridesPath, 'utf-8');
  console.log('Loaded overrides.css');
}

// ── Load config (simple YAML key: value parser) ─────────────────────────────

function parseSimpleYaml(text) {
  const result = {};
  for (const line of text.split('\n')) {
    const m = line.match(/^(\w+)\s*:\s*"?(.+?)"?\s*$/);
    if (m) result[m[1]] = m[2];
  }
  return result;
}

let config = { footer: '', confidentiality: '', department: '', author: '' };
for (const cp of configPaths) {
  if (existsSync(cp)) {
    config = { ...config, ...parseSimpleYaml(readFileSync(cp, 'utf-8')) };
    console.log(`Loaded config from ${cp}`);
    break;
  }
}

// Replace {date} in footer
const today = new Date().toISOString().slice(0, 10);
if (config.footer) {
  config.footer = config.footer.replace('{date}', today);
}

// ── Extract title from first slide or config ────────────────────────────────

let title = 'Presentation';
// Try to find a cover-title in slide-1
const titleMatch = slideHtmlParts[0]?.match(/class="cover-title"[^>]*>(.+?)<\/div>/s);
if (titleMatch) {
  // Strip HTML tags for <title>
  title = titleMatch[1].replace(/<[^>]+>/g, '').trim();
}

// ── Base64-encode images (export mode) ──────────────────────────────────────

const MIME_TYPES = {
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.gif': 'image/gif',
  '.svg': 'image/svg+xml',
  '.webp': 'image/webp',
  '.ico': 'image/x-icon',
};

function toDataUri(filePath) {
  const ext = extname(filePath).toLowerCase();
  const mime = MIME_TYPES[ext];
  if (!mime) {
    console.warn(`  Warning: unknown image type ${ext} for ${filePath}, skipping base64`);
    return null;
  }
  const buf = readFileSync(filePath);
  if (ext === '.svg') {
    // SVG can be inlined as UTF-8
    return `data:${mime};charset=utf-8,${encodeURIComponent(buf.toString('utf-8'))}`;
  }
  return `data:${mime};base64,${buf.toString('base64')}`;
}

function replaceImageRefs(html, baseDir) {
  // Replace <img src="..." /> — handles ./assets/, assets/, ../../assets/ paths
  html = html.replace(
    /(<img\s[^>]*?src=["'])((?:\.\.\/)*\.?\/?assets\/[^"']+)(["'])/gi,
    (match, pre, srcPath, post) => {
      const absPath = resolve(baseDir, srcPath);
      if (!existsSync(absPath)) {
        console.warn(`  Warning: image not found: ${absPath}`);
        return match;
      }
      const dataUri = toDataUri(absPath);
      if (!dataUri) return match;
      console.log(`  Encoded: ${srcPath} (${readFileSync(absPath).length} bytes)`);
      return pre + dataUri + post;
    }
  );
  // Also replace background-image:url('...') in style attributes — same path variants
  html = html.replace(
    /(background-image\s*:\s*url\(["']?)((?:\.\.\/)*\.?\/?assets\/[^"')]+)(["']?\))/gi,
    (match, pre, srcPath, post) => {
      const absPath = resolve(baseDir, srcPath);
      if (!existsSync(absPath)) {
        console.warn(`  Warning: bg image not found: ${absPath}`);
        return match;
      }
      const dataUri = toDataUri(absPath);
      if (!dataUri) return match;
      console.log(`  Encoded bg: ${srcPath} (${readFileSync(absPath).length} bytes)`);
      return pre + dataUri + post;
    }
  );
  return html;
}

function replaceCssImageRefs(css, baseDir) {
  // Replace url(./assets/...), url(assets/...), url(../../assets/...)
  return css.replace(
    /(url\(["']?)((?:\.\.\/)*\.?\/?assets\/[^"')]+)(["']?\))/gi,
    (match, pre, srcPath, post) => {
      const absPath = resolve(baseDir, srcPath);
      if (!existsSync(absPath)) {
        console.warn(`  Warning: CSS image not found: ${absPath}`);
        return match;
      }
      const dataUri = toDataUri(absPath);
      if (!dataUri) return match;
      console.log(`  Encoded CSS: ${srcPath}`);
      return pre + dataUri + post;
    }
  );
}

// ── Assemble ────────────────────────────────────────────────────────────────

// 1. Inject base CSS
template = template.replace('/* {base-css} */', baseCss);

// 2. Inject overrides CSS
template = template.replace('/* {overrides-css} */', overridesCss);

// 3. Join slide fragments and inject
let slidesHtml = slideHtmlParts.join('\n\n');

// Normalize ../../assets/<file> paths written by slide fragments (which live in
// slides/ — two levels below the project root). The assembled HTML lives in
// <deck>/, so we must decide which prefix to use:
//
//   ../../assets/<file>  from slides/ perspective =  <deck>/../assets/<file>
//                                                  = <project>/assets/<file>  (skill-level)
//   assets/<file>        from <deck>/ perspective =  <deck>/assets/<file>     (deck-level)
//
// Rule: if the file exists in <deck>/assets/, rewrite to assets/ (deck-level, relative to <deck>/).
//       Otherwise keep as ../../assets/ → still resolves to <project>/assets/ (skill-level).
slidesHtml = slidesHtml.replace(/\.\.\/(\.\.\/assets\/[^"')]+)/g, (match, rest) => {
  const filename = rest.replace(/^\.\.\/assets\//, '');
  const deckAsset = join(assetsDir, filename);
  if (existsSync(deckAsset)) {
    return 'assets/' + filename;      // deck-local asset (relative to <deck>/)
  }
  return '../../assets/' + filename;  // skill/project-level asset — keep as-is
});

// 4. Replace config placeholders in slides
slidesHtml = slidesHtml.replace(/\{footer\}/g, config.footer);
slidesHtml = slidesHtml.replace(/\{confidentiality\}/g, config.confidentiality);
slidesHtml = slidesHtml.replace(/\{total\}/g, String(total));
slidesHtml = slidesHtml.replace(/\{department\}/g, config.department || '');

// 5. Inject slides
template = template.replace('<!-- {slides} -->', slidesHtml);

// 6. Replace remaining template-level placeholders
template = template.replace(/\{title\}/g, title);
template = template.replace(/\{total\}/g, String(total));

// ── Determine output path ───────────────────────────────────────────────────

if (!outputPath) {
  const deckName = basename(deckDir);
  if (exportMode) {
    outputPath = join(deckDir, `${deckName}.html`);
  } else {
    outputPath = join(deckDir, `${deckName}-preview.html`);
  }
}
outputPath = resolve(outputPath);

// 7. In export mode: base64-encode all image references
// baseDir = directory of the output HTML file, so relative paths (../../assets/)
// resolve correctly from the HTML file's perspective.
if (exportMode) {
  const htmlDir = dirname(outputPath);
  console.log('\nExport mode: encoding images as base64...');
  template = replaceImageRefs(template, htmlDir);
  template = replaceCssImageRefs(template, htmlDir);
}

// ── Write ───────────────────────────────────────────────────────────────────

writeFileSync(outputPath, template, 'utf-8');
console.log(`\n${exportMode ? 'Exported' : 'Preview'}: ${outputPath}`);
console.log(`${total} slides assembled.`);
