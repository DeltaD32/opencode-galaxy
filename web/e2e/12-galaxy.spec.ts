import { test, expect } from "@playwright/test";
import { createTestSession, deleteTestSession } from "./helpers/api";
import { waitForSidebar } from "./helpers/ui";

// App.tsx renders: <button aria-label="Toggle memory galaxy" ...>
const MEMORY_BTN = [
  'button[aria-label*="memory" i]',
  'button[aria-label*="galaxy" i]',
  'button[title*="Memory"]',
  'button:has-text("Memory")',
  'button:has-text("🌌")',
].join(", ");

// Panel selector — matches the <p> header text "Memory Galaxy" rendered inside the aside
const PANEL = '[aria-label="Memory galaxy"], [data-testid="galaxy-panel"], :text("Memory Galaxy")';

test.describe("Galaxy View", () => {
  let sessionID: string;

  test.beforeEach(async ({ page }) => {
    // Create session BEFORE navigating so it is the newest — useSession.ts auto-selects newest.
    const s = await createTestSession("E2E Galaxy Test");
    sessionID = s.id;

    await page.goto("/");
    await waitForSidebar(page);

    // useSession.ts auto-selects sorted[0] (newest) on load — wait for header to confirm.
    await expect(page.locator("header h1")).toContainText("E2E Galaxy Test", { timeout: 15_000 });
  });

  test.afterEach(async () => {
    if (sessionID) await deleteTestSession(sessionID);
  });

  test("memory button exists in toolbar", async ({ page }) => {
    const memoryBtn = page.locator(MEMORY_BTN).first();
    await expect(memoryBtn).toBeVisible({ timeout: 10_000 });
  });

  test("clicking memory button opens galaxy panel", async ({ page }) => {
    await page.locator(MEMORY_BTN).first().click();

    // Panel should appear with "Memory Galaxy" header text
    await expect(page.locator(PANEL).first()).toBeVisible({ timeout: 10_000 });
  });

  test("galaxy panel has a canvas element (3D graph)", async ({ page }) => {
    // 3D canvas requires WebGL — skip in headless CI
    test.skip(true, "3D canvas requires WebGL — skip in headless CI");

    await page.locator(MEMORY_BTN).first().click();
    await page.locator(PANEL).first().waitFor({ state: "visible", timeout: 10_000 });

    // The 3D force-graph library renders into a <canvas>
    const canvas = page.locator("canvas");
    await expect(canvas.first()).toBeVisible({ timeout: 15_000 });
  });

  test("galaxy panel has a legend section", async ({ page }) => {
    await page.locator(MEMORY_BTN).first().click();
    await page.locator(PANEL).first().waitFor({ state: "visible", timeout: 10_000 });

    // GalaxyView renders "Entity types" as the legend heading (not "Legend")
    const legend = page.locator(
      '[data-testid="galaxy-legend"], [aria-label*="Legend"], :text("Entity types"), :text("Legend")'
    );
    await expect(legend.first()).toBeVisible({ timeout: 10_000 });
  });

  test("clicking memory button again closes the panel", async ({ page }) => {
    const memoryBtn = page.locator(MEMORY_BTN).first();

    // Open
    await memoryBtn.click();
    await page.locator(PANEL).first().waitFor({ state: "visible", timeout: 10_000 });

    // Toggle close
    await memoryBtn.click();
    await expect(page.locator(PANEL).first()).not.toBeVisible({ timeout: 5_000 });
  });

  test("galaxy panel has a refresh button", async ({ page }) => {
    await page.locator(MEMORY_BTN).first().click();
    await page.locator(PANEL).first().waitFor({ state: "visible", timeout: 10_000 });

    // GalaxyView renders a "Refresh" text button
    const refreshBtn = page.locator(
      'button:has-text("Refresh"), button[aria-label*="refresh" i], button[title*="refresh" i], [data-testid="galaxy-refresh"]'
    );
    await expect(refreshBtn.first()).toBeVisible({ timeout: 10_000 });
  });

  test("galaxy panel has a close button that closes it", async ({ page }) => {
    await page.locator(MEMORY_BTN).first().click();
    await page.locator(PANEL).first().waitFor({ state: "visible", timeout: 10_000 });

    // App.tsx renders: <button aria-label="Close panel"> with an SVG icon (no text)
    const closeBtn = page.locator(
      'button[aria-label="Close panel"], button:has-text("✕"), [data-testid="galaxy-close"]'
    );
    await closeBtn.first().click();

    await expect(page.locator(PANEL).first()).not.toBeVisible({ timeout: 5_000 });
  });
});
