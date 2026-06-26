/**
 * E2E test helpers — thin wrappers around the OpenCode REST API.
 * Tests call these directly (not through the browser) to set up and
 * tear down state without relying on the UI for fixtures.
 */

const BASE = "http://localhost:4096";

export interface SessionFixture {
  id: string;
  title: string;
}

/** Create a real session on the OpenCode server and return its ID. */
export async function createTestSession(title = "E2E test session"): Promise<SessionFixture> {
  const res = await fetch(`${BASE}/session`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title }),
  });
  if (!res.ok) throw new Error(`Failed to create session: ${res.status}`);
  const data = await res.json();
  return { id: data.id, title: data.title ?? title };
}

/** Create a session with a specific agent (e.g. "build"). */
export async function createTestSessionWithAgent(
  title: string,
  agentID: string,
): Promise<SessionFixture> {
  const res = await fetch(`${BASE}/session`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title, agentID }),
  });
  if (!res.ok) throw new Error(`Failed to create session: ${res.status}`);
  const data = await res.json();
  return { id: data.id, title: data.title ?? title };
}

/**
 * Send a prompt async and poll messages until a tool part appears (type === "tool").
 * Returns when at least one tool part is found, or throws on timeout.
 */
export async function sendAndWaitForToolCall(
  sessionID: string,
  text: string,
  waitMs = 90_000,
): Promise<void> {
  const res = await fetch(`${BASE}/session/${sessionID}/message`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ parts: [{ type: "text", text }] }),
  });
  if (!res.ok) throw new Error(`POST /message returned ${res.status}`);

  const deadline = Date.now() + waitMs;
  while (Date.now() < deadline) {
    await new Promise((r) => setTimeout(r, 1_500));
    const msgRes = await fetch(`${BASE}/session/${sessionID}/message`);
    if (!msgRes.ok) continue;
    const messages = await msgRes.json();
    for (const m of messages) {
      const parts: Array<{ type: string }> = m.parts ?? [];
      if (parts.some((p) => p.type === "tool")) return;
    }
  }
  throw new Error(`No tool call found after ${waitMs}ms`);
}

/** Delete a session by ID — used in afterEach cleanup. */
export async function deleteTestSession(id: string): Promise<void> {
  await fetch(`${BASE}/session/${id}`, { method: "DELETE" });
}

/** Send a prompt to a session and wait for session.idle via SSE (max waitMs). */
export async function sendAndWait(
  sessionID: string,
  text: string,
  waitMs = 20_000,
): Promise<void> {
  // Fire the prompt
  const res = await fetch(`${BASE}/session/${sessionID}/prompt_async`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      parts: [{ type: "text", text }],
      agent: "request-orchestrator",
    }),
  });
  if (res.status !== 204) throw new Error(`prompt_async returned ${res.status}`);

  // Wait for session.idle on the SSE stream
  await new Promise<void>((resolve, reject) => {
    const es = new EventSource(`${BASE}/event`);
    const timer = setTimeout(() => {
      es.close();
      reject(new Error(`Timed out waiting for session.idle after ${waitMs}ms`));
    }, waitMs);

    es.onmessage = (e) => {
      try {
        const evt = JSON.parse(e.data);
        if (evt.type === "session.idle" && evt.properties?.sessionID === sessionID) {
          clearTimeout(timer);
          es.close();
          resolve();
        }
      } catch { /* ignore parse errors */ }
    };

    es.onerror = () => {
      clearTimeout(timer);
      es.close();
      reject(new Error("SSE connection error while waiting for session.idle"));
    };
  });
}

/** Fetch all messages for a session and return the last assistant text. */
export async function getLastAssistantText(sessionID: string): Promise<string> {
  const res = await fetch(`${BASE}/session/${sessionID}/message`);
  const messages = await res.json();
  const assistantMsgs = messages.filter(
    (m: { info: { role: string }; parts: { type: string; text?: string }[] }) =>
      m.info?.role === "assistant",
  );
  if (assistantMsgs.length === 0) return "";
  const lastMsg = assistantMsgs[assistantMsgs.length - 1];
  return lastMsg.parts
    .filter((p: { type: string }) => p.type === "text")
    .map((p: { text?: string }) => p.text ?? "")
    .join("")
    .trim();
}
