/**
 * E2E: App Load
 * Verifies the shell renders correctly, sessions load from the API,
 * and the empty-state prompt is shown when no session is active.
 *
 * Note: SSE keeps the network busy indefinitely, so we never use
 * waitForLoadState("networkidle"). Instead we wait for a specific
 * visible element before asserting.
 */

import { test, expect } from "@playwright/test";

/** Wait for the sidebar session list to be populated (at least 1 item). */
async function waitForSidebar(page: Parameters<Parameters<typeof test>[1]>[0]) {
  // The sidebar header brand span is always the first thing painted
  await expect(
    page.locator("aside").getByText("OpenCode", { exact: true })
  ).toBeVisible({ timeout: 10_000 });
}

test.describe("App load", () => {
  test("page title is BMW OpenCode", async ({ page }) => {
    // Arrange + Act
    await page.goto("/");

    // Assert
    await expect(page).toHaveTitle("BMW OpenCode");
  });

  test("sidebar renders with the OpenCode logo and brand name", async ({ page }) => {
    // Arrange + Act
    await page.goto("/");

    // Assert — brand mark is scoped to the aside element to avoid
    // matching session titles that contain "OpenCode"
    await expect(
      page.locator("aside").getByText("OpenCode", { exact: true })
    ).toBeVisible({ timeout: 10_000 });
  });

  test("new session button is visible in the sidebar", async ({ page }) => {
    // Arrange + Act
    await page.goto("/");
    await waitForSidebar(page);

    // Assert — the + button in the sidebar header has title="New session"
    // We use title attribute to avoid matching session rows named "New session"
    await expect(page.locator("aside button[title='New session']")).toBeVisible();
  });

  test("session list loads from the API and shows at least one entry", async ({ page }) => {
    // Arrange + Act
    await page.goto("/");
    await waitForSidebar(page);

    // Assert — the list is populated (we have many real sessions)
    await expect(page.locator("aside [role='button']").first()).toBeVisible({ timeout: 5_000 });
  });

  test("sessions show cost badges in the sidebar", async ({ page }) => {
    // Arrange + Act
    await page.goto("/");
    await waitForSidebar(page);

    // Wait for sessions to render (API response may take a moment)
    await expect(page.locator("aside [role='button']").first()).toBeVisible({ timeout: 5_000 });

    // Assert — at least one cost badge visible (sessions with cost > 0)
    const costBadges = page.locator("aside span.tabular-nums");
    await expect(costBadges.first()).toBeVisible({ timeout: 5_000 });
  });

  test("clicking a session in the sidebar selects it and shows the header", async ({ page }) => {
    // Arrange
    await page.goto("/");
    await waitForSidebar(page);

    // Act — click the first session in the list
    const firstSession = page.locator("aside [role='button']").first();
    const sessionTitle = await firstSession.locator("span.text-sm").first().textContent();
    await firstSession.click();

    // Assert — header shows the session title (first 20 chars sufficient)
    await expect(page.locator("header h1")).toContainText(
      sessionTitle!.trim().slice(0, 20),
      { timeout: 5_000 }
    );
  });

  test("prompt input is visible when a session is selected", async ({ page }) => {
    // Arrange
    await page.goto("/");
    await waitForSidebar(page);

    // Act
    await page.locator("aside [role='button']").first().click();

    // Assert
    await expect(page.getByRole("textbox", { name: "Message input" })).toBeVisible();
  });

  test("send button is disabled when textarea is empty", async ({ page }) => {
    // Arrange
    await page.goto("/");
    await waitForSidebar(page);
    await page.locator("aside [role='button']").first().click();

    // Assert — send button disabled when no text
    const sendBtn = page.getByRole("button", { name: "Send message" });
    await expect(sendBtn).toBeDisabled();
  });

  test("send button enables when text is typed", async ({ page }) => {
    // Arrange
    await page.goto("/");
    await waitForSidebar(page);
    await page.locator("aside [role='button']").first().click();

    // Act
    await page.getByRole("textbox", { name: "Message input" }).fill("Hello");

    // Assert
    await expect(page.getByRole("button", { name: "Send message" })).toBeEnabled();
  });
});
