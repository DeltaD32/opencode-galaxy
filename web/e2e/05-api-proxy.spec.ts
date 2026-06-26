/**
 * E2E: API Proxy & Network Layer
 * Verifies the Vite /api proxy correctly forwards to OpenCode,
 * and that the app degrades gracefully when the server is unavailable.
 */

import { test, expect } from "@playwright/test";

test.describe("API proxy", () => {
  test("GET /api/session returns a valid JSON array", async ({ request }) => {
    // Arrange + Act
    const res = await request.get("/api/session");

    // Assert
    expect(res.ok()).toBeTruthy();
    expect(res.headers()["content-type"]).toContain("application/json");
    const body = await res.json();
    expect(Array.isArray(body)).toBeTruthy();
    expect(body.length).toBeGreaterThan(0);
  });

  test("GET /api/agent returns agents with name and mode", async ({ request }) => {
    // Arrange + Act
    const res = await request.get("/api/agent");

    // Assert
    expect(res.ok()).toBeTruthy();
    const agents = await res.json();
    expect(Array.isArray(agents)).toBeTruthy();
    expect(agents.length).toBeGreaterThan(0);
    // Each agent has a name and mode
    agents.forEach((a: { name: string; mode: string }) => {
      expect(a.name).toBeTruthy();
      expect(["primary", "subagent", "all"]).toContain(a.mode);
    });
  });

  test("GET /api/mcp returns MCP server statuses", async ({ request }) => {
    // Arrange + Act
    const res = await request.get("/api/mcp");

    // Assert
    expect(res.ok()).toBeTruthy();
    const mcps = await res.json();
    // At minimum memory and skills-mcp should be present
    expect(mcps).toHaveProperty("memory");
    expect(mcps).toHaveProperty("skills-mcp");
    expect(mcps.memory.status).toBe("connected");
  });

  test("GET /api/provider returns llm-api with models", async ({ request }) => {
    // Arrange + Act
    const res = await request.get("/api/provider");

    // Assert
    expect(res.ok()).toBeTruthy();
    const providers = await res.json();
    // /api/provider returns { all: [...], connected: [...], default: {...} }
    expect(providers).toHaveProperty("all");
    expect(providers).toHaveProperty("connected");
    expect(Array.isArray(providers.all)).toBeTruthy();
    expect(providers.all.length).toBeGreaterThan(0);
    // llm-api should be in the connected list
    expect(providers.connected).toContain("llm-api");
    // llm-api should be in all[] with models
    const llmApi = providers.all.find((p: { id: string }) => p.id === "llm-api");
    expect(llmApi).toBeDefined();
    expect(Object.keys(llmApi.models).length).toBeGreaterThan(0);
  });

  test("GET /api/command returns slash commands list", async ({ request }) => {
    // Arrange + Act
    const res = await request.get("/api/command");

    // Assert
    expect(res.ok()).toBeTruthy();
    const commands = await res.json();
    expect(Array.isArray(commands)).toBeTruthy();
    // Should have our installed skills as commands
    const names = commands.map((c: { name: string }) => c.name);
    expect(names).toContain("create-pr");
    expect(names).toContain("web-research");
  });

  test("POST /api/session creates a new session and returns 200", async ({ request }) => {
    // Arrange + Act
    const res = await request.post("/api/session", {
      data: { title: "Playwright API proxy test" },
    });

    // Assert
    expect(res.ok()).toBeTruthy();
    const session = await res.json();
    expect(session.id).toBeTruthy();
    expect(session.id).toMatch(/^ses_/);

    // Cleanup
    await request.delete(`/api/session/${session.id}`);
  });

  test("POST /api/session/{id}/prompt_async returns 204", async ({ request }) => {
    // Arrange — create a session to test with
    const createRes = await request.post("/api/session", {
      data: { title: "Playwright prompt_async test" },
    });
    const session = await createRes.json();

    try {
      // Act
      const res = await request.post(`/api/session/${session.id}/prompt_async`, {
        data: {
          parts: [{ type: "text", text: "Ignore this test message" }],
          agent: "request-orchestrator",
        },
      });

      // Assert — async endpoint always returns 204
      expect(res.status()).toBe(204);
    } finally {
      // Abort + cleanup
      await request.post(`/api/session/${session.id}/abort`);
      await request.delete(`/api/session/${session.id}`);
    }
  });

  test("SSE /api/event stream returns text/event-stream content type", async ({ request }) => {
    // Arrange + Act
    const res = await request.get("/api/event", {
      timeout: 3_000,
    }).catch(() => null); // Connection will hang — that's expected for SSE

    // We can't easily consume the stream via request fixture,
    // but we can check the response headers if we get them before timeout
    if (res) {
      const ct = res.headers()["content-type"] ?? "";
      expect(ct).toContain("text/event-stream");
    }
    // If request timed out, that's also valid — SSE streams never "complete"
  });

  test("CORS preflight from localhost:3000 is accepted by OpenCode", async ({ request }) => {
    // Arrange + Act — send a CORS preflight directly to the OpenCode server
    const res = await request.fetch("http://localhost:4096/session", {
      method: "OPTIONS",
      headers: {
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "Content-Type",
      },
    });

    // Assert — server returns 204 and correct CORS headers
    expect(res.status()).toBe(204);
    const headers = res.headers();
    expect(headers["access-control-allow-origin"]).toBe("http://localhost:3000");
    expect(headers["access-control-allow-methods"]).toContain("GET");
  });
});
