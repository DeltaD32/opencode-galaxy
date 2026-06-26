// OpenCode API types — derived from validation testing against 1.17.5
// Key field: agents use `name` not `id`

export interface Session {
  id: string;
  slug: string;
  projectID: string;
  directory: string;
  path: string;
  title?: string;
  agent?: string;
  cost: number;
  summary: {
    additions: number;
    deletions: number;
    files: number;
  };
  time: {
    created: number;
    updated: number;
  };
}

export interface Agent {
  name: string;
  description?: string;
  mode: "primary" | "subagent" | "all";
  color?: string | null;
  hidden?: boolean | null;
  model?: unknown;
}

export interface Provider {
  id: string;
  name: string;
  models: Model[];
}

export interface Model {
  id: string;
  name: string;
  cost?: {
    input: number;
    output: number;
  };
}

export interface McpStatus {
  [name: string]: {
    status: "connected" | "disabled" | "error" | "connecting";
    error?: string;
  };
}

export interface SlashCommand {
  name: string;
  description?: string;
}

// --- Message & Part types ---

export type PartType =
  | "text"
  | "reasoning"
  | "tool"
  | "tool-invocation"  // legacy alias — not used by 1.17.5 API; kept for forward compat
  | "step-start"
  | "step-finish"
  | "file"
  | "image";

export interface BasePart {
  id: string;
  messageID: string;
  sessionID: string;
  type: PartType;
}

export interface TextPart extends BasePart {
  type: "text";
  text: string;
}

export interface ReasoningPart extends BasePart {
  type: "reasoning";
  text: string;
  time?: { start: number; end?: number };
}

// ToolPart — the real shape emitted by OpenCode 1.17.5
// type: "tool", tool: "<tool name>", callID: "<id>", state: { status, input, output, ... }
export interface ToolPartState {
  status: "running" | "completed" | "error" | "pending";
  input?: unknown;
  output?: string;
  title?: string;
  error?: string;
  time?: { start: number; end?: number };
}

export interface ToolPart extends BasePart {
  type: "tool";
  tool: string;          // e.g. "bash", "read", "write"
  callID: string;
  state: ToolPartState;
}

// ToolInvocationPart — legacy / AI-SDK shape (not emitted by 1.17.5 but kept for compat)
export interface ToolInvocationPart extends BasePart {
  type: "tool-invocation";
  toolName: string;
  toolCallId: string;
  state: "call" | "result" | "partial-call";
  args?: unknown;
  result?: unknown;
}

export interface StepStartPart extends BasePart {
  type: "step-start";
}

export interface StepFinishPart extends BasePart {
  type: "step-finish";
  reason: "stop" | "tool-calls" | "error" | "length";
  tokens: {
    total: number;
    input: number;
    output: number;
    reasoning: number;
    cache: { write: number; read: number };
  };
  cost: number;
}

export type Part =
  | TextPart
  | ReasoningPart
  | ToolPart
  | ToolInvocationPart
  | StepStartPart
  | StepFinishPart;

// MessageInfo is the metadata object nested inside the API's { info, parts } response shape
// and also what SSE message.updated carries in its `info` field
export interface MessageInfo {
  id: string;
  sessionID: string;
  parentID?: string;
  role: "user" | "assistant";
  time: { created: number };
  agent?: string;
  model?: { modelID?: string; providerID?: string };
  summary?: { diffs: unknown[] };
}

// MessageResponse is the raw API shape from GET /session/{id}/message
export interface MessageResponse {
  info: MessageInfo;
  parts: Part[];
}

// Message is our normalised shape used throughout the app (info fields merged with parts)
export interface Message {
  id: string;
  sessionID: string;
  parentID?: string;
  role: "user" | "assistant";
  parts: Part[];
  time: { created: number };
  agent?: string;
  model?: { modelID?: string; providerID?: string };
}

// Flatten MessageResponse → Message
export function normaliseMessage(raw: MessageResponse): Message {
  return {
    ...raw.info,
    parts: raw.parts ?? [],
  };
}

// --- SSE Event types ---

export type SSEEvent =
  | { type: "server.connected"; properties: Record<string, never> }
  | { type: "server.heartbeat"; properties: Record<string, never> }
  | { type: "session.created";  properties: { info: Session } }
  | { type: "session.updated";  properties: { sessionID: string; info: Session } }
  | { type: "session.deleted";  properties: { sessionID: string } }
  | { type: "session.status";   properties: { sessionID: string; status: { type: "busy" | "idle" | "retry" } } }
  | { type: "session.idle";     properties: { sessionID: string } }
  | { type: "session.diff";     properties: { sessionID: string; diff: unknown[] } }
  | { type: "message.updated";  properties: { sessionID: string; info: MessageInfo } }
  | { type: "message.removed";  properties: { sessionID: string; messageID: string } }
  | { type: "message.part.updated"; properties: { sessionID: string; part: Part } }
  | { type: "message.part.removed"; properties: { sessionID: string; partID: string } }
  | { type: "message.part.delta";   properties: { sessionID: string; messageID: string; partID: string; delta: string } }
  | { type: "permission.v2.asked";  properties: { id: string; sessionID: string; action: string; path?: string; description?: string } }
  | { type: "todo.updated";         properties: { sessionID: string; todos: Todo[] } }
  | { type: "file.edited";          properties: { path: string } };

export interface Todo {
  id: string;
  content: string;
  status: "pending" | "in_progress" | "completed" | "cancelled";
  priority: "high" | "medium" | "low";
}
