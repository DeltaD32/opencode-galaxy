/**
 * Shared UI helpers for Phase 2 E2E tests.
 * Centralises the waitForSidebar pattern so all test files use the same robust approach.
 */
import type { Page } from "@playwright/test";
import { expect } from "@playwright/test";

/**
 * Wait for the sidebar to finish loading.
 * Uses the brand name span with exact match to avoid matching session titles
 * that contain the word "opencode".
 */
export async function waitForSidebar(page: Page): Promise<void> {
  // The brand text is in a <span> with class text-white — use exact match to avoid
  // matching session titles like "Plan web frontend for OpenCode CLI"
  await expect(
    page.locator("aside span.text-white.font-semibold"),
  ).toBeVisible({ timeout: 10_000 });
  await expect(page.locator("aside button").first()).toBeVisible({ timeout: 10_000 });
}
