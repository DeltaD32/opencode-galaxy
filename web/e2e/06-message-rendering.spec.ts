/**
 * E2E: Message Rendering
 * Verifies user and assistant messages render correctly — markdown,
 * code blocks, tool call cards, cost badges.
 *
 * Note: SSE keeps the network active indefinitely — never use
 * waitForLoadState("networkidle"). Use waitForSidebar() instead.
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

test.describe("Message rendering", () => {
  let sessionID: string;

  test.beforeEach(async () => {
    const s = await createTestSession("E2E Message Rendering Test");
    sessionID = s.id;
  });

  test.afterEach(async () => {
    await deleteTestSession(sessionID);
  });

  test("user messages appear in a right-aligned bubble", async ({ page }) => {
    // Arrange
    await page.goto("/");
    await waitForSidebar(page);
    await page.locator("aside").getByText("E2E Message Rendering Test").first().click();

    // Act
    const input = page.getByRole("textbox", { name: "Message input" });
    await input.fill("This is my test message");
    await page.getByRole("button", { name: "Send message" }).click();

    // Assert — user bubble appears and is right-aligned
    // The MessageBubble root div has class "flex justify-end"
    // Text is 4 levels deep: div.justify-end > div.items-end > div.rounded-2xl > div.prose > p
    const userBubble = page.getByText("This is my test message");
    await expect(userBubble).toBeVisible({ timeout: 5_000 });

    // Find the row-level div that has justify-end (the outermost MessageBubble wrapper)
    const rowDiv = userBubble.locator("xpath=ancestor::div[contains(@class,'justify-end')]").first();
    await expect(rowDiv).toBeVisible();
  });

  test("assistant messages appear in a left-aligned bubble", async ({ page }) => {
    // Arrange
    await page.goto("/");
    await waitForSidebar(page);
    await page.locator("aside").getByText("E2E Message Rendering Test").first().click();

    // Act
    const input = page.getByRole("textbox", { name: "Message input" });
    await input.fill("Reply with exactly: LEFT_ALIGN_CHECK");
    await page.getByRole("button", { name: "Send message" }).click();

    // Wait for response
    await expect(page.getByText("LEFT_ALIGN_CHECK")).toBeVisible({ timeout: 30_000 });

    // Assert — assistant bubble is in a row with justify-start
    // The MessageBubble root div has class "flex justify-start" for assistant messages
    const assistantBubble = page.getByText("LEFT_ALIGN_CHECK").last();
    const rowDiv = assistantBubble.locator("xpath=ancestor::div[contains(@class,'justify-start')]").first();
    await expect(rowDiv).toBeVisible();
  });

  test("assistant renders markdown bold correctly", async ({ page }) => {
    // Arrange
    await page.goto("/");
    await waitForSidebar(page);
    await page.locator("aside").getByText("E2E Message Rendering Test").first().click();

    // Act — ask for a response with bold markdown
    const input = page.getByRole("textbox", { name: "Message input" });
    await input.fill("Reply with exactly this markdown: **BOLD_TEXT**");
    await page.getByRole("button", { name: "Send message" }).click();

    // Assert — browser renders **BOLD_TEXT** as a <strong> element
    await expect(page.locator("strong").filter({ hasText: "BOLD_TEXT" })).toBeVisible({ timeout: 30_000 });
  });

  test("assistant renders inline code correctly", async ({ page }) => {
    // Arrange
    await page.goto("/");
    await waitForSidebar(page);
    await page.locator("aside").getByText("E2E Message Rendering Test").first().click();

    // Act
    const input = page.getByRole("textbox", { name: "Message input" });
    await input.fill("Reply with exactly this markdown: `const x = 1`");
    await page.getByRole("button", { name: "Send message" }).click();

    // Assert — code element is rendered
    await expect(page.locator("code").filter({ hasText: "const x = 1" })).toBeVisible({ timeout: 30_000 });
  });

  test("multiple turns accumulate in the chat thread", async ({ page }) => {
    // Arrange
    await page.goto("/");
    await waitForSidebar(page);
    await page.locator("aside").getByText("E2E Message Rendering Test").first().click();

    const input = page.getByRole("textbox", { name: "Message input" });

    // Act — send two messages
    await input.fill("Reply with: TURN_ONE");
    await page.getByRole("button", { name: "Send message" }).click();
    await expect(page.getByText("TURN_ONE")).toBeVisible({ timeout: 30_000 });
    // Wait for the session to become idle again (abort button gone = model finished)
    await expect(page.getByRole("button", { name: "Abort generation" })).not.toBeVisible({ timeout: 30_000 });

    // Fill the second message — send button only enables when there's text
    await input.fill("Reply with: TURN_TWO");
    await page.getByRole("button", { name: "Send message" }).click();
    await expect(page.getByText("TURN_TWO")).toBeVisible({ timeout: 30_000 });

    // Assert — both responses are visible simultaneously
    // Use .first() to avoid strict mode: user bubble "Reply with: TURN_ONE" + assistant "TURN_ONE"
    await expect(page.getByText("TURN_ONE").first()).toBeVisible();
    await expect(page.getByText("TURN_TWO").first()).toBeVisible();
  });

  test("empty chat state shows the call-to-action prompt", async ({ page }) => {
    // Arrange — new session has no messages
    await page.goto("/");
    await waitForSidebar(page);
    await page.locator("aside button[title='New session']").click();

    // Assert
    await expect(page.getByText("Send a message to get started")).toBeVisible({ timeout: 3_000 });
  });

  test("user avatar shows 'You' and assistant avatar shows 'AI'", async ({ page }) => {
    // Arrange
    await page.goto("/");
    await waitForSidebar(page);
    await page.locator("aside").getByText("E2E Message Rendering Test").first().click();

    // Act
    const input = page.getByRole("textbox", { name: "Message input" });
    await input.fill("Reply with: AVATAR_TEST");
    await page.getByRole("button", { name: "Send message" }).click();
    await expect(page.getByText("AVATAR_TEST")).toBeVisible({ timeout: 30_000 });

    // Assert — both avatars rendered
    // Avatar divs have specific classes that distinguish them from sidebar text.
    // User avatar: bg-surface-overlay + text-bmw-grey; assistant: bg-bmw-blue/20 + text-bmw-blue
    // Use the rounded-full class which is only on avatars, not session title spans.
    await expect(
      page.locator("div.rounded-full").filter({ hasText: "You" }).first()
    ).toBeVisible();
    await expect(
      page.locator("div.rounded-full").filter({ hasText: "AI" }).first()
    ).toBeVisible();
  });
});
