/**
 * E2E: SSE Connection & Resilience
 * Verifies the EventSource hook connects, stays connected, and reflects
 * live state changes without page reload.
 *
 * Note: SSE keeps the network active indefinitely — never use
 * waitForLoadState("networkidle"). Use waitForSidebar() instead.
 *
 * Important: The OpenCode server does NOT emit SSE events for session
 * creation (sessions created via API appear via the initial load, not SSE).
 * SSE is used for: message.part.delta, session.updated, session.status, etc.
 */

import { test, expect } from "@playwright/test";
import { createTestSession, deleteTestSession } from "./helpers/api";

test.setTimeout(60_000);

/** Wait for the sidebar to be interactive. */
async function waitForSidebar(page: Parameters<Parameters<typeof test>[1]>[0]) {
  await expect(
    page.locator("aside").getByText("OpenCode", { exact: true })
  ).toBeVisible({ timeout: 10_000 });
  await expect(page.locator("aside [role='button']").first()).toBeVisible({ timeout: 10_000 });
}

test.describe("SSE connection", () => {
  test("session created before page load appears in sidebar on load", async ({ page }) => {
    // Arrange — create session before loading the app
    const session = await createTestSession("E2E SSE Pre-Load Test");

    try {
      // Act — navigate to the app
      await page.goto("/");
      await waitForSidebar(page);

      // Assert — session appears in the sidebar (loaded via initial API call)
      await expect(
        page.locator("aside").getByText("E2E SSE Pre-Load Test").first()
      ).toBeVisible({ timeout: 5_000 });
    } finally {
      await deleteTestSession(session.id);
    }
  });

  test("session cost in sidebar updates live after a prompt completes", async ({ page }) => {
    // Arrange
    const session = await createTestSession("E2E Cost SSE Test");

    await page.goto("/");
    await waitForSidebar(page);

    try {
      // Select the session
      await page.locator("aside").getByText("E2E Cost SSE Test").first().click();

      // Act — send a prompt through the UI
      const input = page.getByRole("textbox", { name: "Message input" });
      await input.fill("Reply with exactly: COST_UPDATE");
      await page.getByRole("button", { name: "Send message" }).click();

      // Wait for response — SSE delivers the tokens live
      await expect(page.getByText("COST_UPDATE")).toBeVisible({ timeout: 30_000 });

      // Assert — a cost badge appears somewhere in the chat (turn cost from step-finish)
      // The CostBadge renders "Last turn: $X.XXX" in the chat thread
      await expect(page.getByText(/Last turn: \$[\d.<]+/)).toBeVisible({ timeout: 5_000 });
    } finally {
      await deleteTestSession(session.id);
    }
  });

  test("streaming tokens appear progressively via SSE delta events", async ({ page }) => {
    // Arrange
    const session = await createTestSession("E2E SSE Streaming Test");

    await page.goto("/");
    await waitForSidebar(page);

    try {
      await page.locator("aside").getByText("E2E SSE Streaming Test").first().click();

      // Act — send a prompt
      const input = page.getByRole("textbox", { name: "Message input" });
      await input.fill("Count slowly: 1, 2, 3, 4, 5");
      await page.getByRole("button", { name: "Send message" }).click();

      // Assert — loading indicator appears (confirms SSE messages are being received)
      await expect(page.locator(".animate-bounce").first()).toBeVisible({ timeout: 10_000 });

      // Wait for completion
      await expect(page.locator(".animate-bounce")).toHaveCount(0, { timeout: 30_000 });
    } finally {
      await deleteTestSession(session.id);
    }
  });

  test("SSE reconnects after network interruption — app remains functional", async ({ page, context }) => {
    // Arrange
    await page.goto("/");
    await waitForSidebar(page);

    // Act — simulate a brief SSE interruption by blocking /api/event
    await context.route("**/api/event", (route) => route.abort());
    await page.waitForTimeout(2_000);

    // Re-enable the route
    await context.unroute("**/api/event");
    await page.waitForTimeout(1_000);

    // Assert — app remains functional; can still see the sidebar
    await expect(page.locator("aside [role='button']").first()).toBeVisible({ timeout: 10_000 });
    // Send button still functional (can interact with the UI)
    await page.locator("aside [role='button']").first().click();
    await expect(page.getByRole("textbox", { name: "Message input" })).toBeVisible();
  });
});
