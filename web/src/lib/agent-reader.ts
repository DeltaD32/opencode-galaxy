/**
 * agent-reader.ts
 *
 * Fetches the parsed agent+skill graph from the Vite /__agents proxy and
 * converts it into ForceGraphData nodes/links ready for 3d-force-graph.
 *
 * Node hierarchy in the galaxy:
 *   Primary agent  (mode: primary)  — large BMW-blue sphere
 *   Subagent        (mode: subagent) — medium purple sphere
 *   Skill           (nodeType: skill)— small green sphere
 *
 * Links:
 *   agent → skill   relationType: "uses"   (directional, animated particles)
 */

import { ForceGraphData, GraphLink, GraphNode } from "./memory-reader";

// ─── Raw types from /__agents ─────────────────────────────────────────────────

export interface RawAgentNode {
  id: string;
  name: string;
  nodeType: "agent";
  model: string;
  mode: string;       // "primary" | "subagent"
  description: string;
}

export interface RawSkillNode {
  id: string;
  name: string;
  nodeType: "skill";
}

export interface RawAgentGraph {
  agents: RawAgentNode[];
  skills: RawSkillNode[];
  links: Array<{ source: string; target: string; relationType: string }>;
  orchestratorId: string | null;
}

// ─── Colour constants ─────────────────────────────────────────────────────────

export const AGENT_PRIMARY_COLOUR = "#1c69d4";        // BMW Blue
export const AGENT_SUBAGENT_COLOUR = "#a855f7";       // Purple
export const SKILL_COLOUR = "#22c55e";                // Green
export const AGENT_LINK_COLOUR = "#4ade80";           // Light green for agent→skill edges
export const ORCHESTRATOR_LINK_COLOUR = "#1c69d4";    // BMW Blue for orchestrator→subagent edges

// ─── Converter ────────────────────────────────────────────────────────────────

export interface AgentGraphResult {
  data: ForceGraphData;
  orchestratorId: string | null;
}

export function toForceGraphNodes(raw: RawAgentGraph): AgentGraphResult {
  const nodes: GraphNode[] = [];
  const links: GraphLink[] = [];

  // Track which agent first uses each skill (for group hints)
  const skillFirstAgent = new Map<string, string>(); // skill id → agent id
  for (const l of raw.links) {
    if (l.relationType === "uses" && !skillFirstAgent.has(l.target)) {
      skillFirstAgent.set(l.target, l.source);
    }
  }

  for (const a of raw.agents) {
    const isPrimary = a.mode === "primary";
    nodes.push({
      id: a.id,
      name: a.name,
      entityType: isPrimary ? "PrimaryAgent" : "Subagent",
      observations: [
        `Model: ${a.model}`,
        `Mode: ${a.mode}`,
        ...(a.description ? [a.description] : []),
      ],
      color: isPrimary ? AGENT_PRIMARY_COLOUR : AGENT_SUBAGENT_COLOUR,
      val: isPrimary ? 40 : 22,
      cluster: "agents",
    });
  }

  for (const s of raw.skills) {
    const groupAgent = skillFirstAgent.get(s.id) ?? "unowned";
    nodes.push({
      id: s.id,
      name: s.name,
      entityType: "Skill",
      observations: [
        `Group: ${groupAgent}`,
      ],
      color: SKILL_COLOUR,
      val: 8,
      cluster: "agents",
    });
  }

  for (const l of raw.links) {
    const isOrchestrates = l.relationType === "orchestrates";
    links.push({
      source: l.source,
      target: l.target,
      relationType: l.relationType,
      color: isOrchestrates ? ORCHESTRATOR_LINK_COLOUR : AGENT_LINK_COLOUR,
    });
  }

  return {
    data: { nodes, links },
    orchestratorId: raw.orchestratorId,
  };
}

// ─── Fetch helper ─────────────────────────────────────────────────────────────

export async function fetchAgentGraph(): Promise<AgentGraphResult> {
  const resp = await fetch("/__agents");
  if (!resp.ok) {
    throw new Error(`Failed to fetch agent graph: ${resp.status} ${resp.statusText}`);
  }
  const raw: RawAgentGraph = await resp.json() as RawAgentGraph;
  return toForceGraphNodes(raw);
}

// ─── Merge helper ─────────────────────────────────────────────────────────────

/**
 * Merge the agent graph and the memory graph into a single ForceGraphData.
 * IDs are namespaced (agent:*, skill:*, memory nodes use their raw name)
 * so there are no collisions.
 * Passes through orchestratorId from the agent graph.
 */
export function mergeGraphs(
  agentResult: AgentGraphResult,
  memoryGraph: ForceGraphData
): { data: ForceGraphData; orchestratorId: string | null } {
  return {
    data: {
      nodes: [...agentResult.data.nodes, ...memoryGraph.nodes],
      links: [...agentResult.data.links, ...memoryGraph.links],
    },
    orchestratorId: agentResult.orchestratorId,
  };
}
