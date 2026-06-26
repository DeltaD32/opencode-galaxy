import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,       // SSE tests share a real server — run sequentially
  retries: process.env["CI"] ? 2 : 0,
  workers: 1,                 // one worker: tests hit the same OpenCode session state
  reporter: [
    ["html", { outputFolder: "playwright-report", open: "never" }],
    ["list"],
  ],
  // Global test timeout — covers both individual tests AND beforeAll/afterAll hooks.
  // File 11 uses a real LLM call in beforeAll that needs up to 90s; set generous global limit.
  timeout: 120_000,
  use: {
    baseURL: "http://localhost:3000",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
    video: "on-first-retry",
    // Give SSE-backed operations generous timeouts
    actionTimeout: 10_000,
    navigationTimeout: 15_000,
  },
  projects: [
    {
      // Primary: Chromium — Edge-compatible (same engine)
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  // Re-use the already-running Vite dev server; start it if not up
  webServer: {
    command: "npm run dev",
    url: "http://localhost:3000",
    reuseExistingServer: true,   // always reuse in dev; CI will start fresh
    timeout: 30_000,
  },
});
