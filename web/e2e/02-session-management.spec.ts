/**
 * E2E: Session Management
 * Creating, switching, title display, and deleting sessions via the UI.
 *
 * Note: SSE keeps the network active indefinitely — never use
 * waitForLoadState("networkidle"). Use waitForSidebar() instead.
 *
 * Strict mode note: many text strings appear in both the sidebar span AND the
 * header h1 once a session is selected. Always scope locators to `aside` when
 * targeting sidebar rows to avoid strict mode violations.
 */

import { test, expect } from "@playwright/test";
import { createTestSession, deleteTestSession } from "./helpers/api";

/** Wait for the sidebar to be interactive (brand name visible). */
async function waitForSidebar(page: Parameters<Parameters<typeof test>[1]>[0]) {
  await expect(
    page.locator("aside").getByText("OpenCode", { exact: true })
  ).toBeVisible({ timeout: 10_000 });
  // Also wait for at least one session row so we know the list loaded
  await expect(page.locator("aside [role='button']").first()).toBeVisible({ timeout: 10_000 });
}

test.describe("Session management", () => {
  test("creates a new session when New session button is clicked", async ({ page }) => {
    // Arrange
    await page.goto("/");
    await waitForSidebar(page);

    // Act — click the + (New session) button in the sidebar header
    await page.locator("aside button[title='New session']").click();

    // Assert — prompt input appears (reliable indicator a new session is active)
    await expect(page.getByRole("textbox", { name: "Message input" })).toBeVisible({ timeout: 5_000 });
    // The empty-state message appears since the new session has no messages
    await expect(page.getByText("Send a message to get started")).toBeVisible({ timeout: 5_000 });
  });

  test("newly created session is immediately selected", async ({ page }) => {
    // Arrange
    await page.goto("/");
    await waitForSidebar(page);

    // Act
    await page.locator("aside button[title='New session']").click();

    // Assert — chat empty state is shown (new session has no messages)
    await expect(page.getByText("Send a message to get started")).toBeVisible({ timeout: 5_000 });
  });

  test("switching sessions updates the header title", async ({ page }) => {
    // Arrange — create two sessions via API so we have known titles
    const s1 = await createTestSession("E2E Switch Test A");
    const s2 = await createTestSession("E2E Switch Test B");

    try {
      await page.goto("/");
      await waitForSidebar(page);

      // Wait for the new sessions to appear (SSE may push them in after load)
      await expect(
        page.locator("aside").getByText("E2E Switch Test A")
      ).toBeVisible({ timeout: 5_000 });

      // Act — click session A in the sidebar
      await page.locator("aside").getByText("E2E Switch Test A").click();
      await expect(page.locator("header h1")).toContainText("E2E Switch Test A");

      // Act — click session B
      await page.locator("aside").getByText("E2E Switch Test B").click();
      await expect(page.locator("header h1")).toContainText("E2E Switch Test B");
    } finally {
      await deleteTestSession(s1.id);
      await deleteTestSession(s2.id);
    }
  });

  test("session shows agent name in sidebar row", async ({ page }) => {
    // Arrange
    await page.goto("/");
    await waitForSidebar(page);

    // Assert — at least one session row shows an agent name (small text)
    const agentText = page.locator("aside span.text-xs").first();
    await expect(agentText).toBeVisible({ timeout: 3_000 });
  });

  test("session deleted via UI disappears from sidebar immediately", async ({ page }) => {
    // Arrange — create a session so we have a known title to work with
    const session = await createTestSession("E2E UI Delete Test");

    await page.goto("/");
    await waitForSidebar(page);
    await expect(
      page.locator("aside").getByText("E2E UI Delete Test").first()
    ).toBeVisible({ timeout: 5_000 });

    // Select the session so the header + delete context is active
    await page.locator("aside").getByText("E2E UI Delete Test").first().click();

    // Find the session row and hover to reveal the delete button
    const sessionRow = page.locator("aside [role='button']").filter({ hasText: "E2E UI Delete Test" }).first();
    await sessionRow.hover();

    // Click the delete button (reveals confirmation state)
    const deleteBtn = sessionRow.getByRole("button");
    await deleteBtn.click();

    // If a confirmation step exists, click again
    const confirmText = await deleteBtn.textContent().catch(() => "");
    if (confirmText === "!" || confirmText?.includes("?")) {
      await deleteBtn.click();
    }

    // Assert — session is removed from the sidebar (optimistic removal)
    await expect(
      page.locator("aside").getByText("E2E UI Delete Test")
    ).toHaveCount(0, { timeout: 5_000 });

    // Note: session was already deleted via UI; skip API cleanup
    // (deleteTestSession would return 404 — safe to ignore)
    await deleteTestSession(session.id).catch(() => {});
  });

  test("session count in sidebar increases after creating a new session", async ({ page }) => {
    // Arrange
    await page.goto("/");
    await waitForSidebar(page);
    const initialCount = await page.locator("aside [role='button']").count();

    // Act — create a new session via API so we have a known title to wait for
    const session = await createTestSession("E2E Count Test Session");

    try {
      // Assert — count increased and new session appears
      await expect(
        page.locator("aside").getByText("E2E Count Test Session")
      ).toBeVisible({ timeout: 5_000 });
      const newCount = await page.locator("aside [role='button']").count();
      expect(newCount).toBeGreaterThan(initialCount);
    } finally {
      await deleteTestSession(session.id);
    }
  });

  test("selecting a session via API-created session renders messages pane", async ({ page }) => {
    // Arrange — create session via API
    const session = await createTestSession("E2E Select Session Test");

    try {
      await page.goto("/");
      await waitForSidebar(page);
      await expect(
        page.locator("aside").getByText("E2E Select Session Test")
      ).toBeVisible({ timeout: 5_000 });

      // Act — click the session row
      await page.locator("aside").getByText("E2E Select Session Test").click();

      // Assert — message pane is now shown with empty state
      await expect(page.getByRole("textbox", { name: "Message input" })).toBeVisible();
      await expect(page.getByText("Send a message to get started")).toBeVisible();
    } finally {
      await deleteTestSession(session.id);
    }
  });
});
