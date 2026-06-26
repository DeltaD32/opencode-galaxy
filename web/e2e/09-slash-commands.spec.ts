/**
 * Phase 2 E2E — SlashCommandPalette
 * Tests the "/" command palette in the prompt input area.
 */
import { test, expect } from "@playwright/test";
import { waitForSidebar } from "./helpers/ui";
import { createTestSession, deleteTestSession } from "./helpers/api";

// waitForSidebar imported from helpers/ui

test.describe("SlashCommandPalette", () => {
  let sessionID: string;

  test.beforeAll(async () => {
    const s = await createTestSession("E2E SlashCommand Test");
    sessionID = s.id;
  });

  test.afterAll(async () => {
    await deleteTestSession(sessionID);
  });

  test("typing / in the prompt input shows the command palette", async ({ page }) => {
    await page.goto("/");
    await waitForSidebar(page);
    await page.locator("aside").getByText("E2E SlashCommand Test").first().click();

    const input = page.getByRole("textbox", { name: "Message input" });
    await input.fill("/");

    await expect(page.getByTestId("slash-command-palette")).toBeVisible({ timeout: 3_000 });
  });

  test("palette shows 'Commands' header label", async ({ page }) => {
    await page.goto("/");
    await waitForSidebar(page);
    await page.locator("aside").getByText("E2E SlashCommand Test").first().click();

    const input = page.getByRole("textbox", { name: "Message input" });
    await input.fill("/");

    const palette = page.getByTestId("slash-command-palette");
    await expect(palette).toBeVisible({ timeout: 3_000 });
    await expect(palette.getByText(/Commands/i)).toBeVisible();
  });

  test("palette lists at least one command", async ({ page }) => {
    await page.goto("/");
    await waitForSidebar(page);
    await page.locator("aside").getByText("E2E SlashCommand Test").first().click();

    const input = page.getByRole("textbox", { name: "Message input" });
    await input.fill("/");

    const palette = page.getByTestId("slash-command-palette");
    await expect(palette).toBeVisible({ timeout: 3_000 });
    const options = palette.getByRole("option");
    await expect(options.first()).toBeVisible({ timeout: 3_000 });
    const count = await options.count();
    expect(count).toBeGreaterThan(0);
  });

  test("filtering by typing after / narrows the list", async ({ page }) => {
    await page.goto("/");
    await waitForSidebar(page);
    await page.locator("aside").getByText("E2E SlashCommand Test").first().click();

    const input = page.getByRole("textbox", { name: "Message input" });
    await input.fill("/create-pr");

    const palette = page.getByTestId("slash-command-palette");
    await expect(palette).toBeVisible({ timeout: 3_000 });
    // Should match "create-pr"
    await expect(palette.getByText("/create-pr")).toBeVisible({ timeout: 3_000 });
  });

  test("no match message shown when query has no results", async ({ page }) => {
    await page.goto("/");
    await waitForSidebar(page);
    await page.locator("aside").getByText("E2E SlashCommand Test").first().click();

    const input = page.getByRole("textbox", { name: "Message input" });
    await input.fill("/xyzzy-nonexistent-command");

    const palette = page.getByTestId("slash-command-palette");
    await expect(palette).toBeVisible({ timeout: 3_000 });
    await expect(palette.getByText(/No commands match/i)).toBeVisible({ timeout: 3_000 });
  });

  test("Escape key closes the palette", async ({ page }) => {
    await page.goto("/");
    await waitForSidebar(page);
    await page.locator("aside").getByText("E2E SlashCommand Test").first().click();

    const input = page.getByRole("textbox", { name: "Message input" });
    await input.fill("/");

    const palette = page.getByTestId("slash-command-palette");
    await expect(palette).toBeVisible({ timeout: 3_000 });

    await input.press("Escape");
    await expect(palette).not.toBeVisible({ timeout: 2_000 });
  });

  test("clicking a command fills it into the input and closes palette", async ({ page }) => {
    await page.goto("/");
    await waitForSidebar(page);
    await page.locator("aside").getByText("E2E SlashCommand Test").first().click();

    const input = page.getByRole("textbox", { name: "Message input" });
    await input.fill("/");

    const palette = page.getByTestId("slash-command-palette");
    await expect(palette).toBeVisible({ timeout: 3_000 });

    // Click the first command — get the command name from the blue-light span (e.g. "/init")
    const firstOption = palette.getByRole("option").first();
    // The command name is in the font-mono span with class text-bmw-blue-light
    const cmdSpan = firstOption.locator("span.font-mono").first();
    const cmdText = await cmdSpan.textContent();
    await firstOption.click();

    // Palette should close
    await expect(palette).not.toBeVisible({ timeout: 2_000 });

    // Input should now contain the selected command name
    const inputVal = await input.inputValue();
    expect(inputVal).toContain("/");
    // cmdText is like "/init" — strip the leading slash
    if (cmdText) {
      const cmdName = cmdText.trim().replace(/^\//, "").split(/\s/)[0];
      if (cmdName) expect(inputVal.toLowerCase()).toContain(cmdName.toLowerCase());
    }
  });

  test("palette disappears when input is cleared", async ({ page }) => {
    await page.goto("/");
    await waitForSidebar(page);
    await page.locator("aside").getByText("E2E SlashCommand Test").first().click();

    const input = page.getByRole("textbox", { name: "Message input" });
    await input.fill("/");

    const palette = page.getByTestId("slash-command-palette");
    await expect(palette).toBeVisible({ timeout: 3_000 });

    // Clear the input
    await input.fill("");
    await expect(palette).not.toBeVisible({ timeout: 2_000 });
  });
});
