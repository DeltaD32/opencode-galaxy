/**
 * html_slides_to_pdf.mjs
 * Renders each .slide div from an HTML presentation as a separate PDF page.
 * Usage: node scripts/html_slides_to_pdf.mjs <input.html> <output.pdf>
 *
 * Requires: npx playwright (Chromium)
 */

import { chromium } from "playwright";
import { readFileSync, writeFileSync } from "fs";
import { resolve, dirname } from "path";
import { fileURLToPath } from "url";

const [, , inputHtml, outputPdf] = process.argv;
if (!inputHtml || !outputPdf) {
  console.error("Usage: node html_slides_to_pdf.mjs <input.html> <output.pdf>");
  process.exit(1);
}

const absInput = resolve(inputHtml);
const absOutput = resolve(outputPdf);

// Slide dimensions: 1280×720 (16:9)
const W = 1280;
const H = 720;

// PDF page size in inches at 96 dpi
const PAGE_W_IN = W / 96; // 13.333...
const PAGE_H_IN = H / 96; // 7.5

(async () => {
  const browser = await chromium.launch({
    args: [
      "--force-color-profile=srgb", // prevent ICC profile shifting blues to pink in PDF
      "--disable-pdf-tagging",
    ],
  });
  const context = await browser.newContext({
    viewport: { width: W, height: H },
    deviceScaleFactor: 2, // retina for sharper text
  });
  const page = await context.newPage();

  const fileUrl = `file://${absInput}`;
  await page.goto(fileUrl, { waitUntil: "networkidle" });

  // Find all slide IDs
  const slideIds = await page.evaluate(() =>
    [...document.querySelectorAll(".slide")].map((el) => el.id),
  );

  console.log(`Found ${slideIds.length} slides: ${slideIds.join(", ")}`);

  const pdfBuffers = [];

  for (const id of slideIds) {
    // Show only this slide, hide others
    await page.evaluate((currentId) => {
      document.querySelectorAll(".slide").forEach((el) => {
        el.style.display = el.id === currentId ? "flex" : "none";
      });
      // Also hide nav dots if present
      const nav = document.querySelector(".nav-dots, #nav, .nav");
      if (nav) nav.style.display = "none";
    }, id);

    // Wait a tick for any CSS transitions
    await page.waitForTimeout(200);

    // Print to PDF — one page exactly
    const pdf = await page.pdf({
      width: `${W}px`,
      height: `${H}px`,
      printBackground: true,
      margin: { top: 0, bottom: 0, left: 0, right: 0 },
      pageRanges: "1",
    });

    pdfBuffers.push(pdf);
    console.log(`  Rendered slide #${id} (${pdf.length} bytes)`);
  }

  await browser.close();

  // Merge all single-page PDFs into one using basic PDF concatenation
  // Each Playwright PDF is a valid single-page PDF; we merge them with a
  // simple approach: re-open with the PDF library if available, or use
  // a raw stream merge.
  if (pdfBuffers.length === 1) {
    writeFileSync(absOutput, pdfBuffers[0]);
  } else {
    // Use qpdf or pypdf via child_process for merging
    const { execSync, spawnSync } = await import("child_process");
    const { mkdtempSync, rmSync } = await import("fs");
    const { tmpdir } = await import("os");
    const { join } = await import("path");

    const tmpDir = mkdtempSync(join(tmpdir(), "slides-"));
    const tmpFiles = [];

    for (let i = 0; i < pdfBuffers.length; i++) {
      const f = join(tmpDir, `slide-${String(i).padStart(3, "0")}.pdf`);
      writeFileSync(f, pdfBuffers[i]);
      tmpFiles.push(f);
    }

    // Try qpdf first, then pypdf
    let merged = false;

    // Try qpdf
    const qpdf = spawnSync("qpdf", [
      "--empty",
      "--pages",
      ...tmpFiles,
      "--",
      absOutput,
    ]);
    if (qpdf.status === 0) {
      merged = true;
      console.log("Merged with qpdf");
    }

    if (!merged) {
      // Try pypdf via uv run python
      const script = `
import sys
from pypdf import PdfWriter
w = PdfWriter()
for f in sys.argv[1:-1]:
    from pypdf import PdfReader
    r = PdfReader(f)
    for p in r.pages:
        w.add_page(p)
with open(sys.argv[-1], 'wb') as out:
    w.write(out)
print(f'Merged {len(sys.argv)-2} pages')
`;
      const py = spawnSync("uv", [
        "run",
        "--with",
        "pypdf",
        "python",
        "-c",
        script,
        ...tmpFiles,
        absOutput,
      ]);
      if (py.status === 0) {
        merged = true;
        console.log("Merged with pypdf:", py.stdout.toString().trim());
      } else {
        console.error("pypdf error:", py.stderr.toString());
      }
    }

    // Cleanup tmp files
    rmSync(tmpDir, { recursive: true, force: true });

    if (!merged) {
      console.error(
        "Could not merge PDFs — writing first slide only as fallback",
      );
      writeFileSync(absOutput, pdfBuffers[0]);
    }
  }

  console.log(`\nDone: ${absOutput}`);
})();
