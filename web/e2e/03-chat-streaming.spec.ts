/**
 * E2E: Chat & SSE Streaming
 * The core loop — send a prompt, watch tokens stream in, verify final response.
 * These tests hit the real OpenCode server and BMW LLM API.
 *
 * Note: SSE keeps the network active indefinitely — never use
 * waitForLoadState("networkidle"). Use waitForSidebar() instead.
 */

import { test, expect } from "@playwright/test";
import { createTestSession, deleteTestSession } from "./helpers/api";

// Generous timeout for LLM round-trips
test.setTimeout(60_000);

/** Wait for the sidebar to be interactive. */
async function waitForSidebar(page: Parameters<Parameters<typeof test>[1]>[0]) {
  await expect(
    page.locator("aside").getByText("OpenCode", { exact: true })
  ).toBeVisible({ timeout: 10_000 });
  await expect(page.locator("aside [role='button']").first()).toBeVisible({ timeout: 10_000 });
}

test.describe("Chat streaming", () => {
  let sessionID: string;

  test.beforeEach(async () => {
    // Create a fresh session via API for each test — no UI noise
    const s = await createTestSession("E2E Chat Test");
    sessionID = s.id;
  });

  test.afterEach(async () => {
    await deleteTestSession(sessionID);
  });

  test("typing in the prompt input updates the textarea value", async ({ page }) => {
    // Arrange
    await page.goto("/");
    await waitForSidebar(page);
    await page.locator("aside").getByText("E2E Chat Test").first().click();

    // Act
    const input = page.getByRole("textbox", { name: "Message input" });
    await input.fill("Hello world");

    // Assert
    await expect(input).toHaveValue("Hello world");
  });

  test("Cmd+Enter sends the message", async ({ page }) => {
    // Arrange
    await page.goto("/");
    await waitForSidebar(page);
    await page.locator("aside").getByText("E2E Chat Test").first().click();

    const input = page.getByRole("textbox", { name: "Message input" });
    await input.fill("Reply with exactly: CMD_ENTER_OK");

    // Act
    await input.press("Meta+Enter");

    // Assert — input clears immediately after send
    await expect(input).toHaveValue("");
  });

  test("user message appears in the chat thread immediately after send", async ({ page }) => {
    // Arrange
    await page.goto("/");
    await waitForSidebar(page);
    await page.locator("aside").getByText("E2E Chat Test").first().click();

    // Act
    const input = page.getByRole("textbox", { name: "Message input" });
    await input.fill("Reply with exactly: APPEAR_TEST");
    await page.getByRole("button", { name: "Send message" }).click();

    // Assert — user bubble appears without waiting for LLM
    await expect(page.getByText("Reply with exactly: APPEAR_TEST")).toBeVisible({ timeout: 5_000 });
  });

  test("typing indicator (dots) shows while the LLM is generating", async ({ page }) => {
    // Arrange
    await page.goto("/");
    await waitForSidebar(page);
    await page.locator("aside").getByText("E2E Chat Test").first().click();

    // Act
    const input = page.getByRole("textbox", { name: "Message input" });
    await input.fill("Count to 3 slowly");
    await page.getByRole("button", { name: "Send message" }).click();

    // Assert — bouncing dots appear while model is busy
    await expect(page.locator(".animate-bounce").first()).toBeVisible({ timeout: 10_000 });
  });

  test("abort button appears while generating and stops the stream", async ({ page }) => {
    // Arrange
    await page.goto("/");
    await waitForSidebar(page);
    await page.locator("aside").getByText("E2E Chat Test").first().click();

    const input = page.getByRole("textbox", { name: "Message input" });
    await input.fill("Write a very long essay about the history of BMW");
    await page.getByRole("button", { name: "Send message" }).click();

    // Assert — abort button appears
    const abortBtn = page.getByRole("button", { name: "Abort generation" });
    await expect(abortBtn).toBeVisible({ timeout: 10_000 });

    // Act — click abort
    await abortBtn.click();

    // Assert — abort button disappears and send button returns
    await expect(page.getByRole("button", { name: "Abort generation" })).not.toBeVisible({ timeout: 10_000 });
  });

  test("assistant response appears in the chat thread after streaming completes", async ({ page }) => {
    // Arrange
    await page.goto("/");
    await waitForSidebar(page);
    await page.locator("aside").getByText("E2E Chat Test").first().click();

    // Act
    const input = page.getByRole("textbox", { name: "Message input" });
    await input.fill("Reply with exactly one word: STREAMING_OK");
    await page.getByRole("button", { name: "Send message" }).click();

    // Assert — response contains our expected word
    await expect(page.getByText("STREAMING_OK")).toBeVisible({ timeout: 30_000 });
  });

  test("per-turn cost badge is shown after response completes", async ({ page }) => {
    // Arrange
    await page.goto("/");
    await waitForSidebar(page);
    await page.locator("aside").getByText("E2E Chat Test").first().click();

    // Act
    const input = page.getByRole("textbox", { name: "Message input" });
    await input.fill("Reply with exactly one word: COST_TEST");
    await page.getByRole("button", { name: "Send message" }).click();

    // Wait for response
    await expect(page.getByText("COST_TEST")).toBeVisible({ timeout: 30_000 });

    // Assert — a turn cost badge appears ("Last turn: $X.XXX" rendered by CostBadge)
    await expect(page.getByText(/Last turn: \$[\d.<]+/)).toBeVisible({ timeout: 5_000 });
  });

  test("session total cost updates in the header after a response", async ({ page }) => {
    // Arrange
    await page.goto("/");
    await waitForSidebar(page);
    await page.locator("aside").getByText("E2E Chat Test").first().click();

    // Act
    const input = page.getByRole("textbox", { name: "Message input" });
    await input.fill("Reply with exactly one word: SESSION_COST");
    await page.getByRole("button", { name: "Send message" }).click();

    // Wait for response
    await expect(page.getByText("SESSION_COST")).toBeVisible({ timeout: 30_000 });

    // Assert — header shows "Session: $X.XX" cost badge
    await expect(page.getByText(/Session: \$[\d.]+/)).toBeVisible({ timeout: 5_000 });
  });

  test("input is disabled while the model is generating", async ({ page }) => {
    // Arrange
    await page.goto("/");
    await waitForSidebar(page);
    await page.locator("aside").getByText("E2E Chat Test").first().click();

    const input = page.getByRole("textbox", { name: "Message input" });
    await input.fill("Write a haiku about TypeScript");
    await page.getByRole("button", { name: "Send message" }).click();

    // Assert — textarea is disabled while busy
    await expect(input).toBeDisabled({ timeout: 10_000 });
  });

  test("clicking the abort button stops generation", async ({ page }) => {
    // Arrange
    // Note: Escape key abort requires textarea focus, but the textarea is disabled
    // while isBusy=true (PromptInput disables it). This tests the click-to-abort path.
    await page.goto("/");
    await waitForSidebar(page);
    await page.locator("aside").getByText("E2E Chat Test").first().click();

    const input = page.getByRole("textbox", { name: "Message input" });
    await input.fill("Write a very long story about a car");
    await page.getByRole("button", { name: "Send message" }).click();

    // Wait until the abort button appears
    const abortBtn = page.getByRole("button", { name: "Abort generation" });
    await expect(abortBtn).toBeVisible({ timeout: 10_000 });

    // Act — click the abort button
    await abortBtn.click();

    // Assert — abort button disappears (generation stopped or aborted)
    await expect(abortBtn).not.toBeVisible({ timeout: 10_000 });
  });
});
