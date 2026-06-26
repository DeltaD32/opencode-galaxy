// Thin REST wrapper around the OpenCode HTTP API.
// All fetch calls go through /api/* which Vite proxies to localhost:4096.
// No auth headers needed for localhost — server is unsecured by default.

import type { Session, Agent, Model, McpStatus, SlashCommand, Message, MessageResponse } from "../types/opencode";
import { normaliseMessage } from "../types/opencode";

const BASE = "/api";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...init?.headers },
    ...init,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`OpenCode API ${res.status}: ${text}`);
  }
  // 204 No Content — return null cast as T
  if (res.status === 204) return null as T;
  return res.json() as Promise<T>;
}

// --- Sessions ---

export function listSessions(): Promise<Session[]> {
  return request<Session[]>("/session");
}

export function getSession(id: string): Promise<Session> {
  return request<Session>(`/session/${id}`);
}

export function createSession(title?: string): Promise<Session> {
  return request<Session>("/session", {
    method: "POST",
    body: JSON.stringify(title ? { title } : {}),
  });
}

export function updateSessionTitle(id: string, title: string): Promise<Session> {
  return request<Session>(`/session/${id}`, {
    method: "PATCH",
    body: JSON.stringify({ title }),
  });
}

export function deleteSession(id: string): Promise<null> {
  return request<null>(`/session/${id}`, { method: "DELETE" });
}

export function abortSession(id: string): Promise<null> {
  return request<null>(`/session/${id}/abort`, { method: "POST" });
}

// --- Messaging ---

export async function listMessages(sessionID: string): Promise<Message[]> {
  const raw = await request<MessageResponse[]>(`/session/${sessionID}/message`);
  return raw.map(normaliseMessage);
}

export interface PromptPart {
  type: "text";
  text: string;
}

export function sendPromptAsync(
  sessionID: string,
  parts: PromptPart[],
  agent?: string,
): Promise<null> {
  return request<null>(`/session/${sessionID}/prompt_async`, {
    method: "POST",
    body: JSON.stringify({ parts, ...(agent ? { agent } : {}) }),
  });
}

// --- Agents ---

export function listAgents(): Promise<Agent[]> {
  return request<Agent[]>("/agent");
}

// --- Providers ---

// Real API shape: { all: Provider[], connected: string[], default: {...} }
export interface ProviderListResponse {
  all: RawProvider[];
  connected: string[];
  default: { modelID: string; providerID: string } | null;
}

export interface RawProvider {
  id: string;
  name: string;
  models: Record<string, Model>;
}

export function listProviders(): Promise<ProviderListResponse> {
  return request<ProviderListResponse>("/provider");
}

// --- Sessions (extended) ---

export function forkSession(sessionID: string, messageID: string): Promise<Session> {
  return request<Session>(`/session/${sessionID}/fork`, {
    method: "POST",
    body: JSON.stringify({ messageID }),
  });
}

export function shareSession(sessionID: string): Promise<{ url: string }> {
  return request<{ url: string }>(`/session/${sessionID}/share`, { method: "POST" });
}

// --- Diff ---

export interface DiffFile {
  file: string;
  additions: number;
  deletions: number;
  patch: string;
}

export function getSessionDiff(sessionID: string): Promise<DiffFile[]> {
  return request<DiffFile[]>(`/session/${sessionID}/diff`);
}

// --- MCP ---

export function getMcpStatus(): Promise<McpStatus> {
  return request<McpStatus>("/mcp");
}

// --- Commands ---

export function listCommands(): Promise<SlashCommand[]> {
  return request<SlashCommand[]>("/command");
}

// --- VCS ---

export interface VcsInfo {
  branch: string | null;
  default_branch: string | null;
}

export function getVcsInfo(): Promise<VcsInfo> {
  return request<VcsInfo>("/vcs");
}

// --- Permissions ---

export function replyPermission(
  sessionID: string,
  permissionID: string,
  action: "allow" | "deny",
): Promise<null> {
  return request<null>(`/session/${sessionID}/permissions/${permissionID}`, {
    method: "POST",
    body: JSON.stringify({ action }),
  });
}

// --- SSE helpers ---

/** Returns the full URL for the global event stream (used by useSSE hook directly). */
export function eventStreamUrl(): string {
  return `${BASE}/event`;
}
