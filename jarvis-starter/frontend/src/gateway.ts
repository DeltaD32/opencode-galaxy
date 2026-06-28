// Typed client for the JARVIS gateway daemon (Module C). Colour comes from data.

export interface AgentNode {
  id: string;
  name: string;
  tier: number;
  colour: string;
}

export interface TaskNode {
  id: string;
  agent: string;
  status: string;
  depends_on: string[];
  active: boolean;
}

const BASE = "http://localhost:8132";

export async function fetchAgents(): Promise<AgentNode[]> {
  const res = await fetch(`${BASE}/api/agents`);
  const json = (await res.json()) as { nodes: AgentNode[] };
  return json.nodes;
}

export async function fetchTasks(): Promise<TaskNode[]> {
  const res = await fetch(`${BASE}/api/tasks`);
  const json = (await res.json()) as { tasks: TaskNode[] };
  return json.tasks;
}

// Standalone fallback so the galaxy renders without a running gateway.
export const MOCK_AGENTS: AgentNode[] = [
  { id: "orchestrator", name: "orchestrator", tier: 0, colour: "#ffb627" },
  { id: "programming-expert", name: "programming-expert", tier: 1, colour: "#9a7bff" },
  { id: "design-expert", name: "design-expert", tier: 1, colour: "#9a7bff" },
  { id: "data-analyst", name: "data-analyst", tier: 1, colour: "#9a7bff" },
];

/** Subagent planets only (tier > 0); the orchestrator is the sun. */
export function toPlanets(agents: AgentNode[]): AgentNode[] {
  return agents.filter((a) => a.tier > 0);
}
