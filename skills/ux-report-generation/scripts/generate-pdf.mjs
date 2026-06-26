/*
  generate-pdf.mjs — Playwright PDF export script for DesignOps reports
  ───────────────────────────────────────────────────────────────────────
  Copy this file into the target report folder and replace [REPORT_FILE_NAME]
  with the actual report filename (without .html extension).

  Usage:
    cd reports/<skill-folder> && node generate-pdf.mjs

  Requirements:
    - Node.js 18+
    - @playwright/test installed (npx playwright install chromium)
    - Google Chrome at the default macOS path, OR update executablePath below
*/

import { chromium } from '@playwright/test';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';
import { existsSync } from 'fs';
import { platform } from 'os';

const __dirname = dirname(fileURLToPath(import.meta.url));

/**
 * Returns the first existing Chrome/Chromium executable path for the current OS,
 * or null to fall back to Playwright's bundled Chromium.
 */
function findChrome() {
  const candidates = {
    darwin: [
      '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
      '/Applications/Chromium.app/Contents/MacOS/Chromium',
    ],
    linux: [
      '/usr/bin/google-chrome',
      '/usr/bin/google-chrome-stable',
      '/usr/bin/chromium',
      '/usr/bin/chromium-browser',
      '/snap/bin/chromium',
    ],
    win32: [
      'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
      'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
    ],
  };
  const paths = candidates[platform()] ?? [];
  return paths.find(p => existsSync(p)) ?? null;
}

const executablePath = findChrome();
const browser = await chromium.launch({
  headless: true,
  ...(executablePath ? { executablePath } : {}),
});
const page = await browser.newPage();

const htmlPath = resolve(__dirname, '[REPORT_FILE_NAME].html');
const pdfPath  = resolve(__dirname, '[REPORT_FILE_NAME].pdf');

await page.goto(`file://${htmlPath}`, { waitUntil: 'networkidle' });
await page.waitForTimeout(1000);

await page.pdf({
  path: pdfPath,
  format: 'A4',
  printBackground: true,
  margin: { top: '1cm', bottom: '1cm', left: '1cm', right: '1cm' },
  displayHeaderFooter: true,
  headerTemplate: '<span></span>',
  footerTemplate: '<div style="font-size:8px;text-align:center;width:100%;color:#999;">Page <span class="pageNumber"></span> of <span class="totalPages"></span></div>',
});

console.log(`PDF generated: ${pdfPath}`);
await browser.close();
