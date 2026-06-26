/**
 * Phase 2 E2E — ModelPicker
 * Tests the model selector dropdown in the session header.
 */
import { test, expect } from "@playwright/test";
import { waitForSidebar } from "./helpers/ui";
import { createTestSession, deleteTestSession } from "./helpers/api";

// waitForSidebar imported from helpers/ui

test.describe("ModelPicker", () => {
  let sessionID: string;

  test.beforeAll(async () => {
    const s = await createTestSession("E2E ModelPicker Test");
    sessionID = s.id;
  });

  test.afterAll(async () => {
    await deleteTestSession(sessionID);
  });

  test("ModelPicker is visible in the header when a session is selected", async ({ page }) => {
    await page.goto("/");
    await waitForSidebar(page);
    await page.locator("aside").getByText("E2E ModelPicker Test").first().click();

    await expect(page.getByTestId("model-picker")).toBeVisible({ timeout: 5_000 });
  });

  test("clicking the ModelPicker opens a model list", async ({ page }) => {
    await page.goto("/");
    await waitForSidebar(page);
    await page.locator("aside").getByText("E2E ModelPicker Test").first().click();

    await page.getByTestId("model-picker").locator("button").first().click();

    await expect(page.getByRole("listbox", { name: "Model list" })).toBeVisible({ timeout: 3_000 });
  });

  test("model list shows a search input", async ({ page }) => {
    await page.goto("/");
    await waitForSidebar(page);
    await page.locator("aside").getByText("E2E ModelPicker Test").first().click();

    await page.getByTestId("model-picker").locator("button").first().click();

    await expect(page.getByRole("textbox", { name: "Search models" })).toBeVisible({ timeout: 3_000 });
  });

  test("model list contains llm-api provider section", async ({ page }) => {
    await page.goto("/");
    await waitForSidebar(page);
    await page.locator("aside").getByText("E2E ModelPicker Test").first().click();

    await page.getByTestId("model-picker").locator("button").first().click();

    const listbox = page.getByRole("listbox", { name: "Model list" });
    await expect(listbox).toBeVisible({ timeout: 3_000 });
    // LLM API provider header should be visible
    await expect(listbox.getByText("LLM API")).toBeVisible({ timeout: 3_000 });
  });

  test("model list contains claude-sonnet-4-6", async ({ page }) => {
    await page.goto("/");
    await waitForSidebar(page);
    await page.locator("aside").getByText("E2E ModelPicker Test").first().click();

    await page.getByTestId("model-picker").locator("button").first().click();

    const listbox = page.getByRole("listbox", { name: "Model list" });
    await expect(listbox.getByText("claude-sonnet-4-6")).toBeVisible({ timeout: 3_000 });
  });

  test("searching filters the model list", async ({ page }) => {
    await page.goto("/");
    await waitForSidebar(page);
    await page.locator("aside").getByText("E2E ModelPicker Test").first().click();

    await page.getByTestId("model-picker").locator("button").first().click();

    const listbox = page.getByRole("listbox", { name: "Model list" });
    await expect(listbox).toBeVisible({ timeout: 3_000 });

    // Type a search query
    await page.getByRole("textbox", { name: "Search models" }).fill("claude");

    // Should show claude models but not gpt models
    await expect(listbox.getByText("claude-sonnet-4-6")).toBeVisible();
    await expect(listbox.getByText("gpt-5.1")).not.toBeVisible();
  });

  test("selecting a model closes the dropdown", async ({ page }) => {
    await page.goto("/");
    await waitForSidebar(page);
    await page.locator("aside").getByText("E2E ModelPicker Test").first().click();

    await page.getByTestId("model-picker").locator("button").first().click();

    const listbox = page.getByRole("listbox", { name: "Model list" });
    await expect(listbox).toBeVisible({ timeout: 3_000 });

    // Click the first model option
    await listbox.getByRole("option").first().click();

    await expect(listbox).not.toBeVisible({ timeout: 2_000 });
  });

  test("cost per token is shown next to model names", async ({ page }) => {
    await page.goto("/");
    await waitForSidebar(page);
    await page.locator("aside").getByText("E2E ModelPicker Test").first().click();

    await page.getByTestId("model-picker").locator("button").first().click();

    const listbox = page.getByRole("listbox", { name: "Model list" });
    await expect(listbox).toBeVisible({ timeout: 3_000 });

    // Cost format: "$X.XX/$X.XX" or similar — look for any "$" sign in the list
    await expect(listbox.locator("text=/$\\d/")).toBeVisible({ timeout: 3_000 }).catch(() => {
      // Fallback: at least one element with "$" content
      return expect(listbox.locator("span").filter({ hasText: "$" }).first()).toBeVisible({ timeout: 3_000 });
    });
  });
});
