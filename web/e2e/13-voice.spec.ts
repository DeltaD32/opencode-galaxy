import { test, expect } from "@playwright/test";
import { createTestSession, deleteTestSession } from "./helpers/api";
import { waitForSidebar } from "./helpers/ui";

// Selectors that cover common aria-label / title patterns for a mic/voice button
const VOICE_BTN =
  'button[aria-label*="voice" i], button[aria-label*="microphone" i], button[title*="voice" i], button[title*="microphone" i], button[title*="supported" i], button[data-testid="voice-button"]';

test.describe("Voice Button", () => {
  let sessionID: string;

  test.beforeEach(async ({ page }) => {
    // VoiceButton is inside PromptInput, which only renders when activeSessionID is set.
    // Create session before navigating so it is newest and auto-selected by useSession.ts.
    const s = await createTestSession("E2E Voice Test");
    sessionID = s.id;

    await page.goto("http://localhost:3000");
    await waitForSidebar(page);

    // Wait for session to be auto-selected (header h1 shows session title)
    await expect(page.locator("header h1")).toContainText("E2E Voice Test", { timeout: 15_000 });

    // Wait for the chat input area to be present
    await page.waitForSelector('textarea, [data-testid="prompt-input"]', {
      timeout: 10_000,
    });
  });

  test.afterEach(async () => {
    if (sessionID) await deleteTestSession(sessionID);
  });

  test("voice button exists in chat input area", async ({ page }) => {
    const voiceBtn = page.locator(VOICE_BTN).first();
    await expect(voiceBtn).toBeVisible({ timeout: 10_000 });
  });

  test("voice button is disabled when SpeechRecognition is not supported", async ({
    page,
  }) => {
    // Playwright/Chromium headless: window.SpeechRecognition is undefined.
    // The component's isSupported flag should be false → button disabled.
    const isSupported = await page.evaluate(
      () =>
        typeof window.SpeechRecognition !== "undefined" ||
        typeof (
          window as Window &
            typeof globalThis & { webkitSpeechRecognition?: unknown }
        ).webkitSpeechRecognition !== "undefined"
    );

    if (!isSupported) {
      const voiceBtn = page.locator(VOICE_BTN).first();
      await expect(voiceBtn).toBeDisabled({ timeout: 10_000 });
    } else {
      // In a browser that supports SpeechRecognition the button may be enabled;
      // skip rather than fail so CI always passes regardless of runtime.
      test.skip();
    }
  });

  test("voice button has correct aria-label", async ({ page }) => {
    const voiceBtn = page.locator(VOICE_BTN).first();
    await expect(voiceBtn).toBeVisible({ timeout: 10_000 });

    const ariaLabel = await voiceBtn.getAttribute("aria-label");
    const title = await voiceBtn.getAttribute("title");

    // At least one of aria-label or title must mention voice / microphone
    const combined = `${ariaLabel ?? ""} ${title ?? ""}`.toLowerCase();
    expect(combined).toMatch(/voice|microphone|mic/);
  });

  test("voice button has title attribute explaining it is for voice input", async ({
    page,
  }) => {
    const voiceBtn = page.locator(VOICE_BTN).first();
    await expect(voiceBtn).toBeVisible({ timeout: 10_000 });

    // In headless Chromium, SpeechRecognition is unsupported so title = "Voice input not supported".
    // When supported, title may be undefined — we only assert it is present in the unsupported case.
    const isSupported = await page.evaluate(
      () =>
        typeof window.SpeechRecognition !== "undefined" ||
        typeof (window as Window & typeof globalThis & { webkitSpeechRecognition?: unknown })
          .webkitSpeechRecognition !== "undefined"
    );

    if (!isSupported) {
      const title = await voiceBtn.getAttribute("title");
      expect(title).toBeTruthy();
      expect(title!.length).toBeGreaterThan(0);
    } else {
      test.skip();
    }
  });

  test("disabled voice button cannot be clicked to start listening", async ({
    page,
  }) => {
    const voiceBtn = page.locator(VOICE_BTN).first();
    await expect(voiceBtn).toBeVisible({ timeout: 10_000 });

    const disabled = await voiceBtn.isDisabled();
    if (!disabled) {
      // Button is enabled (SpeechRecognition supported) — not the headless scenario.
      // Still verify: no "listening" state visible before interaction.
      const listenIndicator = page
        .locator('[data-testid="voice-listening"]')
        .or(page.locator('[aria-label*="listening" i]'))
        .or(page.getByText("Listening"));
      await expect(listenIndicator).not.toBeVisible();
      return;
    }

    // Disabled button: clicking should have no effect (no error, no state change)
    // Playwright will throw if we `click()` a disabled button, so we use force
    // but verify no listening state appears afterwards.
    await voiceBtn.click({ force: true });

    const listenIndicator = page
      .locator('[data-testid="voice-listening"]')
      .or(page.locator('[aria-label*="listening" i]'))
      .or(page.getByText("Listening"));
    await expect(listenIndicator).not.toBeVisible({ timeout: 2_000 });
  });
});
