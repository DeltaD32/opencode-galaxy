/**
 * Phase 2 E2E — AgentPicker
 * Tests the agent selector dropdown in the session header.
 */
import { test, expect } from "@playwright/test";
import { waitForSidebar } from "./helpers/ui";
import { createTestSession, deleteTestSession } from "./helpers/api";

// waitForSidebar imported from helpers/ui

test.describe("AgentPicker", () => {
  let sessionID: string;

  test.beforeAll(async () => {
    const s = await createTestSession("E2E AgentPicker Test");
    sessionID = s.id;
  });

  test.afterAll(async () => {
    await deleteTestSession(sessionID);
  });

  test("AgentPicker is visible in the header when a session is selected", async ({ page }) => {
    await page.goto("/");
    await waitForSidebar(page);
    await page.locator("aside").getByText("E2E AgentPicker Test").first().click();

    await expect(page.getByTestId("agent-picker")).toBeVisible({ timeout: 5_000 });
  });

  test("AgentPicker button shows an agent name", async ({ page }) => {
    await page.goto("/");
    await waitForSidebar(page);
    await page.locator("aside").getByText("E2E AgentPicker Test").first().click();

    const btn = page.getByTestId("agent-picker").locator("button").first();
    await expect(btn).toBeVisible({ timeout: 5_000 });
    // Should have some text content (agent name)
    const text = await btn.textContent();
    expect(text?.trim().length).toBeGreaterThan(0);
  });

  test("clicking the AgentPicker opens a dropdown list", async ({ page }) => {
    await page.goto("/");
    await waitForSidebar(page);
    await page.locator("aside").getByText("E2E AgentPicker Test").first().click();

    const picker = page.getByTestId("agent-picker");
    await picker.locator("button").first().click();

    await expect(page.getByRole("listbox", { name: "Agent list" })).toBeVisible({ timeout: 3_000 });
  });

  test("agent list contains at least one agent option", async ({ page }) => {
    await page.goto("/");
    await waitForSidebar(page);
    await page.locator("aside").getByText("E2E AgentPicker Test").first().click();

    const picker = page.getByTestId("agent-picker");
    await picker.locator("button").first().click();

    const listbox = page.getByRole("listbox", { name: "Agent list" });
    await expect(listbox).toBeVisible({ timeout: 3_000 });
    const options = listbox.getByRole("option");
    await expect(options.first()).toBeVisible();
    const count = await options.count();
    expect(count).toBeGreaterThan(0);
  });

  test("request-orchestrator is listed in the agent picker", async ({ page }) => {
    await page.goto("/");
    await waitForSidebar(page);
    await page.locator("aside").getByText("E2E AgentPicker Test").first().click();

    const picker = page.getByTestId("agent-picker");
    await picker.locator("button").first().click();

    const listbox = page.getByRole("listbox", { name: "Agent list" });
    await expect(listbox.getByText("request-orchestrator")).toBeVisible({ timeout: 3_000 });
  });

  test("clicking an agent in the list closes the dropdown", async ({ page }) => {
    await page.goto("/");
    await waitForSidebar(page);
    await page.locator("aside").getByText("E2E AgentPicker Test").first().click();

    const picker = page.getByTestId("agent-picker");
    await picker.locator("button").first().click();

    const listbox = page.getByRole("listbox", { name: "Agent list" });
    const firstOption = listbox.getByRole("option").first();
    await firstOption.click();

    await expect(listbox).not.toBeVisible({ timeout: 2_000 });
  });

  test("clicking outside the dropdown closes it", async ({ page }) => {
    await page.goto("/");
    await waitForSidebar(page);
    await page.locator("aside").getByText("E2E AgentPicker Test").first().click();

    const picker = page.getByTestId("agent-picker");
    await picker.locator("button").first().click();

    const listbox = page.getByRole("listbox", { name: "Agent list" });
    await expect(listbox).toBeVisible({ timeout: 3_000 });

    // Click somewhere outside the picker
    await page.locator("header h1").click();
    await expect(listbox).not.toBeVisible({ timeout: 2_000 });
  });
});
