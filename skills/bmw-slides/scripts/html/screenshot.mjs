/**
 * screenshot.mjs — Screenshot each slide from an assembled HTML deck.
 *
 * Usage:
 *   node screenshot.mjs <assembled.html> [--out-dir <dir>]
 *
 * Outputs:
 *   <out-dir>/slide-1.png, slide-2.png, ...
 *
 * Default out-dir: same directory as the HTML file, in a _review/ subfolder.
 *
 * Requires: playwright (npm install playwright)
 */

import { chromium } from 'playwright';
import { resolve, dirname, join, basename } from 'path';
import { mkdirSync, existsSync } from 'fs';

const args = process.argv.slice(2);
let htmlPath = null;
let outDir = null;

for (let i = 0; i < args.length; i++) {
  if (args[i] === '--out-dir' && args[i + 1]) {
    outDir = args[++i];
  } else if (!htmlPath) {
    htmlPath = args[i];
  }
}

if (!htmlPath) {
  console.error('Usage: node screenshot.mjs <assembled.html> [--out-dir <dir>]');
  process.exit(1);
}

htmlPath = resolve(htmlPath);
if (!existsSync(htmlPath)) {
  console.error(`Error: file not found: ${htmlPath}`);
  process.exit(1);
}

if (!outDir) {
  outDir = join(dirname(htmlPath), '_review');
}
outDir = resolve(outDir);
mkdirSync(outDir, { recursive: true });

// ── Launch browser and screenshot each slide ────────────────────────────────

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });

await page.goto(`file://${htmlPath}`, { waitUntil: 'networkidle' });

// Hide navigation chrome
await page.evaluate(() => {
  const nav = document.querySelector('.nav');
  if (nav) nav.style.display = 'none';
});

const slideCount = await page.locator('.slide').count();
console.log(`Found ${slideCount} slides`);

const results = [];

for (let i = 1; i <= slideCount; i++) {
  await page.evaluate((n) => {
    document.querySelectorAll('.slide').forEach(s => s.classList.remove('active'));
    const slide = document.getElementById('slide-' + n);
    if (slide) slide.classList.add('active');
  }, i);

  // Small wait for CSS transitions / repaints
  await page.waitForTimeout(50);

  const outPath = join(outDir, `slide-${i}.png`);
  await page.screenshot({ path: outPath });
  results.push(outPath);
  console.log(`  slide-${i}.png`);
}

await browser.close();

console.log(`\nScreenshots saved to: ${outDir}`);
console.log(JSON.stringify({ outDir, slideCount, files: results }));
