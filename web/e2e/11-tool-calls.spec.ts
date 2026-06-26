/**
 * Phase 2 E2E — ToolCallCard rendering
 *
 * Tests the ToolCallCard component by sending a prompt to the `build` agent,
 * which reliably calls the bash tool. The beforeAll uses the API directly
 * (no browser) to fire the prompt and poll until a tool part appears.
 * Each test then navigates via the browser to assert on the rendered cards.
 *
 * Strategy:
 *   1. beforeAll: create session with build agent, send bash prompt via API,
 *      poll until GET /session/{id}/message returns a part with type === "tool"
 *   2. Each test: navigate to the session URL directly and assert on ToolCallCards
 *
 * Timeout: 120s (from playwright.config.ts global), covers the LLM call in beforeAll.
 */
import { test, expect, type Page } from "@playwright/test";
import { waitForSidebar } from "./helpers/ui";
import {
  createTestSessionWithAgent,
  deleteTestSession,
  sendAndWaitForToolCall,
} from "./helpers/api";

let sessionID: string;
const SESSION_TITLE = "E2E ToolCall Test";

async function navigateToSession(page: Page): Promise<void> {
  await page.goto(`http://localhost:3000`);
  await waitForSidebar(page);
  // Click the session in the sidebar
  await page.locator("aside").getByText(SESSION_TITLE).first().click();
  await expect(page.locator("header h1")).toContainText(SESSION_TITLE, { timeout: 8_000 });
}

test.describe("ToolCallCard", () => {
  test.beforeAll(async () => {
    // Create session with the `build` agent — it has bash tool and will call it
    const s = await createTestSessionWithAgent(SESSION_TITLE, "build");
    sessionID = s.id;

    // Send a simple bash command and wait (via API polling) until a tool part appears
    await sendAndWaitForToolCall(
      sessionID,
      "Run: echo hello_e2e_tool_test",
      90_000,
    );
  });

  test.afterAll(async () => {
    if (sessionID) await deleteTestSession(sessionID);
  });

  test("ToolCallCard is visible in the chat thread", async ({ page }) => {
    await navigateToSession(page);
    const card = page.getByTestId("tool-call-card").first();
    await expect(card).toBeVisible({ timeout: 10_000 });
  });

  test("ToolCallCard has a non-empty tool name attribute", async ({ page }) => {
    await navigateToSession(page);
    const card = page.getByTestId("tool-call-card").first();
    await expect(card).toBeVisible({ timeout: 10_000 });

    const toolName = await card.getAttribute("data-tool-name");
    expect(toolName?.trim().length).toBeGreaterThan(0);
  });

  test("clicking ToolCallCard header expands the args", async ({ page }) => {
    await navigateToSession(page);
    const card = page.getByTestId("tool-call-card").first();
    await expect(card).toBeVisible({ timeout: 10_000 });

    const headerBtn = card.locator("button").first();
    await expect(headerBtn).toHaveAttribute("aria-expanded", "false");

    await headerBtn.click();
    await expect(headerBtn).toHaveAttribute("aria-expanded", "true");
    await expect(card.getByText("Input")).toBeVisible({ timeout: 2_000 });
  });

  test("at least one ToolCallCard shows state=result (completed)", async ({ page }) => {
    await navigateToSession(page);
    // data-state="result" means the tool completed (mapped from status === "completed")
    const completedCard = page.locator('[data-testid="tool-call-card"][data-state="result"]');
    await expect(completedCard.first()).toBeVisible({ timeout: 15_000 });
  });
});
