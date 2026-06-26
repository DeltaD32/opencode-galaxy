/**
 * db-reader.ts
 *
 * Fetches project / blackboard / decision / conflict data from the Vite
 * /__db proxy (backed by opencode.db) and converts it into ForceGraphData
 * suitable for 3d-force-graph.
 */

import type { ForceGraphData, GraphLink, GraphNode } from "./memory-reader";

// ─── Raw shapes from /__db ─────────────────────────────────────────────────────

export interface ProjectRow {
  id: string | number;
  name: string;
  status: string | null;
  description: string | null;
  created_at: string | null;
}

export interface BlackboardRow {
  id: string | number;
  project_id: string | number | null;
  task_description: string | null;
  status: string | null;
  file_path: string | null;
  created_at: string | null;
}

export interface DecisionRow {
  id: string | number;
  blackboard_id: string | number | null;
  made_by: string | null;
  decision: string | null;
  rationale: string | null;
  timestamp: string | null;
}

export interface ConflictRow {
  id: string | number;
  blackboard_id: string | number | null;
  agent_a: string | null;
  agent_b: string | null;
  description: string | null;
  resolved: number | null; // 0/1
  resolution: string | null;
}

export interface SectionRow {
  id: string;
  blackboard_id: string | null;
  agent: string | null;
  section_name: string | null;
  written_at: string | null;
}

export interface DbSnapshot {
  projects: ProjectRow[];
  blackboards: BlackboardRow[];
  decisions: DecisionRow[];
  conflicts: ConflictRow[];
  sections: SectionRow[];
}

// ─── Agent status derived from sections + blackboards ─────────────────────────

export type AgentActivityStatus = 'active' | 'idle';

export interface AgentStatus {
  agent: string;
  /** 'active' = has a section on a non-done blackboard right now */
  status: AgentActivityStatus;
  /** The task they're working on, if active */
  taskDescription: string | null;
  /** Blackboard status for colour coding */
  blackboardStatus: string | null;
  /** When they last wrote a section */
  lastActive: string | null;
}

/**
 * Derive per-agent status from a DB snapshot.
 * An agent is "active" if it has written a section on any blackboard
 * whose status is not 'done'. Most-recently-written section wins if
 * an agent appears on multiple active boards.
 */
export function deriveAgentStatuses(snapshot: DbSnapshot, knownAgents: string[]): AgentStatus[] {
  const activeBoardIds = new Set(
    (snapshot.blackboards ?? [])
      .filter(b => b.status && b.status !== 'done')
      .map(b => b.id)
  );

  const boardById = new Map(
    (snapshot.blackboards ?? []).map(b => [String(b.id), b])
  );

  // For each agent, find their most recent section on an active board
  const agentLatest = new Map<string, { section: SectionRow; board: BlackboardRow }>();

  for (const s of snapshot.sections ?? []) {
    if (!s.agent || s.agent === 'unknown') continue;
    if (!s.blackboard_id || !activeBoardIds.has(String(s.blackboard_id))) continue;
    const board = boardById.get(String(s.blackboard_id));
    if (!board) continue;

    const existing = agentLatest.get(s.agent);
    if (!existing || (s.written_at ?? '') > (existing.section.written_at ?? '')) {
      agentLatest.set(s.agent, { section: s, board });
    }
  }

  // Build full list — all known agents, mark active ones
  const allAgents = new Set([...knownAgents, ...agentLatest.keys()]);
  const statuses: AgentStatus[] = [];

  for (const agent of allAgents) {
    if (agent === 'unknown') continue;
    const active = agentLatest.get(agent);
    statuses.push({
      agent,
      status: active ? 'active' : 'idle',
      taskDescription: active?.board.task_description ?? null,
      blackboardStatus: active?.board.status ?? null,
      lastActive: active?.section.written_at ?? null,
    });
  }

  // Active first, then idle; alphabetical within each group
  statuses.sort((a, b) => {
    if (a.status !== b.status) return a.status === 'active' ? -1 : 1;
    return a.agent.localeCompare(b.agent);
  });

  return statuses;
}

/**
 * Fetch the full /__db snapshot and return derived agent statuses.
 * knownAgents is the list from GET /agent so we show all agents, not just those with sections.
 */
export async function fetchAgentStatuses(knownAgents: string[]): Promise<AgentStatus[]> {
  try {
    const resp = await fetch('/__db');
    if (!resp.ok) return knownAgents.map(a => ({ agent: a, status: 'idle', taskDescription: null, blackboardStatus: null, lastActive: null }));
    const snapshot = await resp.json() as DbSnapshot;
    return deriveAgentStatuses(snapshot, knownAgents);
  } catch {
    return knownAgents.map(a => ({ agent: a, status: 'idle', taskDescription: null, blackboardStatus: null, lastActive: null }));
  }
}

// ─── Metadata shapes used in GalaxyView side panel ─────────────────────────────

export interface ProjectNodeMetadata {
  type: "project";
  status: string;
  description: string | null;
  blackboards: Array<{ id: string | number; name: string }>;
}

export interface BlackboardNodeMetadata {
  type: "blackboard";
  status: string;
  taskDescription: string;
  filePath: string | null;
  decisions: Array<{
    id: string | number;
    madeBy: string;
    decision: string;
    rationale: string | null;
  }>;
  conflicts: Array<{
    id: string | number;
    agentA: string | null;
    agentB: string | null;
    description: string;
    resolved: boolean;
    resolution: string | null;
  }>;
}

export interface DecisionNodeMetadata {
  type: "decision";
  madeBy: string;
  decision: string;
  rationale: string | null;
  timestamp: string | null;
}

export interface ConflictNodeMetadata {
  type: "conflict";
  agentA: string | null;
  agentB: string | null;
  description: string;
  resolved: boolean;
  resolution: string | null;
}

export type ProjectClusterMetadata =
  | ProjectNodeMetadata
  | BlackboardNodeMetadata
  | DecisionNodeMetadata
  | ConflictNodeMetadata;

// ─── Fetch helper ──────────────────────────────────────────────────────────────

export async function fetchProjectsGraph(): Promise<ForceGraphData> {
  let resp: Response;
  try {
    resp = await fetch("/__db");
  } catch (err) {
    // When the dev server bypass is not available we treat projects as absent.
    console.warn("[Galaxy] /__db fetch failed:", err);
    return { nodes: [], links: [] };
  }

  if (!resp.ok) {
    console.warn("[Galaxy] /__db returned non-ok status:", resp.status, resp.statusText);
    return { nodes: [], links: [] };
  }

  let payload: DbSnapshot | null = null;
  try {
    payload = (await resp.json()) as DbSnapshot;
  } catch (err) {
    console.warn("[Galaxy] /__db JSON parse failed:", err);
    return { nodes: [], links: [] };
  }

  if (!payload) return { nodes: [], links: [] };
  return dbSnapshotToForceGraph(payload);
}

// ─── Converter ─────────────────────────────────────────────────────────────────

function dbSnapshotToForceGraph(snapshot: DbSnapshot): ForceGraphData {
  const nodes: GraphNode[] = [];
  const links: GraphLink[] = [];

  const sid = (v: string | number | null | undefined) => String(v ?? '');

  const blackboardsByProject = new Map<string, BlackboardRow[]>();
  for (const b of snapshot.blackboards ?? []) {
    if (b.project_id == null) continue;
    const k = sid(b.project_id);
    if (!blackboardsByProject.has(k)) blackboardsByProject.set(k, []);
    blackboardsByProject.get(k)!.push(b);
  }

  const decisionsByBlackboard = new Map<string, DecisionRow[]>();
  for (const d of snapshot.decisions ?? []) {
    if (d.blackboard_id == null) continue;
    const k = sid(d.blackboard_id);
    if (!decisionsByBlackboard.has(k)) decisionsByBlackboard.set(k, []);
    decisionsByBlackboard.get(k)!.push(d);
  }

  const conflictsByBlackboard = new Map<string, ConflictRow[]>();
  for (const c of snapshot.conflicts ?? []) {
    if (c.blackboard_id == null) continue;
    const k = sid(c.blackboard_id);
    if (!conflictsByBlackboard.has(k)) conflictsByBlackboard.set(k, []);
    conflictsByBlackboard.get(k)!.push(c);
  }

  const projectNodeIds = new Map<string, string>();
  const blackboardNodeIds = new Map<string, string>();
  const decisionNodeIds = new Map<string, string>();

  const projects = snapshot.projects ?? [];
  const projectCount = projects.length || 1;

  // Projects – large sun-like nodes in a centre-right band
  projects.forEach((p, index) => {
    const nodeId = `project:${p.id}`;
    projectNodeIds.set(sid(p.id), nodeId);

    const projectBlackboards = blackboardsByProject.get(sid(p.id)) ?? [];

    const meta: ProjectNodeMetadata = {
      type: "project",
      status: (p.status ?? "unknown").trim() || "unknown",
      description: p.description,
      blackboards: projectBlackboards.map((b) => ({
        id: b.id,
        name: (b.task_description ?? `Blackboard ${b.id}`).trim(),
      })),
    };

    const xBase = 260;
    const xJitter = (Math.random() - 0.5) * 80;
    const ySpread = 80;
    const yOffset = (index - (projectCount - 1) / 2) * ySpread;
    const zJitter = (Math.random() - 0.5) * 80;

    nodes.push({
      id: nodeId,
      name: p.name ?? `Project ${p.id}`,
      entityType: "Project",
      observations: [
        `Status: ${meta.status}`,
        `Blackboards: ${projectBlackboards.length}`,
        ...(p.description ? [truncate(p.description, 120)] : []),
      ],
      color: "#f97316", // Orange — aligns with TYPE_COLOURS.Project
      val: 35,
      cluster: "projects",
      metadata: meta,
      x: xBase + xJitter,
      y: yOffset,
      z: zJitter,
    });
  });

  // Blackboards – medium octahedrons orbiting their project
  for (const b of snapshot.blackboards ?? []) {
    const nodeId = `blackboard:${b.id}`;
    blackboardNodeIds.set(sid(b.id), nodeId);

    const projectNodeId = b.project_id != null ? projectNodeIds.get(sid(b.project_id)) : undefined;

    const status = (b.status ?? "unknown").trim().toLowerCase();
    const color = blackboardColourForStatus(status);

    const decisions = decisionsByBlackboard.get(sid(b.id)) ?? [];
    const conflicts = conflictsByBlackboard.get(sid(b.id)) ?? [];

    const meta: BlackboardNodeMetadata = {
      type: "blackboard",
      status,
      taskDescription: (b.task_description ?? "Untitled task").trim(),
      filePath: b.file_path,
      decisions: decisions.map((d) => ({
        id: d.id,
        madeBy: (d.made_by ?? "unknown").trim(),
        decision: (d.decision ?? "").trim(),
        rationale: d.rationale,
      })),
      conflicts: conflicts.map((c) => ({
        id: c.id,
        agentA: c.agent_a,
        agentB: c.agent_b,
        description: (c.description ?? "").trim(),
        resolved: Boolean(c.resolved),
        resolution: c.resolution,
      })),
    };

    // Position: near its project, slightly offset
    const baseProject = projectNodeId
      ? nodes.find((n) => n.id === projectNodeId)
      : undefined;
    const radius = 60 + Math.random() * 40;
    const angle = Math.random() * Math.PI * 2;

    const baseX = baseProject?.x ?? 260;
    const baseY = baseProject?.y ?? 0;
    const baseZ = baseProject?.z ?? 0;

    nodes.push({
      id: nodeId,
      name: meta.taskDescription,
      entityType: "Blackboard",
      observations: [
        `Status: ${status || "unknown"}`,
        `Decisions: ${decisions.length}`,
        `Conflicts: ${conflicts.length}`,
      ],
      color,
      val: 18,
      cluster: "projects",
      metadata: meta,
      x: baseX + Math.cos(angle) * radius,
      y: baseY + (Math.random() - 0.5) * 40,
      z: baseZ + Math.sin(angle) * radius,
    });

    if (projectNodeId) {
      links.push({
        source: projectNodeId,
        target: nodeId,
        relationType: "project:blackboard",
        color: "#1c69d4", // BMW blue
      });
    }
  }

  // Decisions – small purple diamonds below their blackboard
  for (const d of snapshot.decisions ?? []) {
    if (d.blackboard_id == null) continue;

    const nodeId = `decision:${d.id}`;
    decisionNodeIds.set(sid(d.id), nodeId);

    const blackboardNodeId = blackboardNodeIds.get(sid(d.blackboard_id));

    const meta: DecisionNodeMetadata = {
      type: "decision",
      madeBy: (d.made_by ?? "unknown").trim(),
      decision: (d.decision ?? "").trim(),
      rationale: d.rationale,
      timestamp: d.timestamp,
    };

    const baseBlackboard = blackboardNodeId
      ? nodes.find((n) => n.id === blackboardNodeId)
      : undefined;

    const baseX = baseBlackboard?.x ?? 260;
    const baseY = (baseBlackboard?.y ?? 0) - 50 - Math.random() * 20;
    const baseZ = (baseBlackboard?.z ?? 0) + (Math.random() - 0.5) * 40;

    nodes.push({
      id: nodeId,
      name: truncate(meta.decision || `Decision ${d.id}`, 60),
      entityType: "Decision",
      observations: [
        `By: ${meta.madeBy}`,
        ...(meta.rationale ? [truncate(meta.rationale, 120)] : []),
      ],
      color: "#a855f7", // Purple
      val: 8,
      cluster: "projects",
      metadata: meta,
      x: baseX,
      y: baseY,
      z: baseZ,
    });

    if (blackboardNodeId) {
      links.push({
        source: blackboardNodeId,
        target: nodeId,
        relationType: "blackboard:decision",
        color: "#c084fc", // Light purple
      });
    }
  }

  // Conflicts – small spiky orange/red nodes near blackboard
  for (const c of snapshot.conflicts ?? []) {
    if (c.blackboard_id == null) continue;

    const nodeId = `conflict:${c.id}`;
    const blackboardNodeId = blackboardNodeIds.get(sid(c.blackboard_id));
    const resolved = Boolean(c.resolved);

    const color = resolved ? "#6b7280" : "#f97316";

    const meta: ConflictNodeMetadata = {
      type: "conflict",
      agentA: c.agent_a,
      agentB: c.agent_b,
      description: (c.description ?? "").trim(),
      resolved,
      resolution: c.resolution,
    };

    const baseBlackboard = blackboardNodeId
      ? nodes.find((n) => n.id === blackboardNodeId)
      : undefined;

    const baseX = (baseBlackboard?.x ?? 260) + (Math.random() - 0.5) * 40;
    const baseY = (baseBlackboard?.y ?? 0) + 40 + Math.random() * 20;
    const baseZ = (baseBlackboard?.z ?? 0) + (Math.random() - 0.5) * 40;

    nodes.push({
      id: nodeId,
      name: meta.description || `Conflict ${c.id}`,
      entityType: "Conflict",
      observations: [
        `Agents: ${(c.agent_a ?? "?")} vs ${(c.agent_b ?? "?")}`,
        `Resolved: ${resolved ? "yes" : "no"}`,
      ],
      color,
      val: 8,
      cluster: "projects",
      metadata: meta,
      x: baseX,
      y: baseY,
      z: baseZ,
    });

    if (blackboardNodeId) {
      links.push({
        source: blackboardNodeId,
        target: nodeId,
        relationType: "blackboard:conflict",
        color: "#fb923c", // Orange
      });
    }
  }

  // Cross-task decision edges (killer visual feature)
  // Group decisions by (made_by, rationale) and connect them with arced links.
  const decisionGroups = new Map<string, DecisionRow[]>();
  for (const d of snapshot.decisions ?? []) {
    const madeBy = (d.made_by ?? "").trim();
    const rationale = (d.rationale ?? "").trim();
    if (!madeBy || !rationale) continue;
    const key = `${madeBy}::${rationale.toLowerCase()}`;
    if (!decisionGroups.has(key)) {
      decisionGroups.set(key, []);
    }
    decisionGroups.get(key)!.push(d);
  }

  for (const group of decisionGroups.values()) {
    if (group.length < 2) continue;
    // Connect sequentially to avoid dense cliques
    group.sort((a, b) => {
      const ta = a.timestamp ?? "";
      const tb = b.timestamp ?? "";
      return ta.localeCompare(tb);
    });

    for (let i = 0; i < group.length - 1; i += 1) {
      const a = group[i];
      const b = group[i + 1];
      const sourceId = decisionNodeIds.get(sid(a.id));
      const targetId = decisionNodeIds.get(sid(b.id));
      if (!sourceId || !targetId) continue;
      links.push({
        source: sourceId,
        target: targetId,
        relationType: "decision-cross",
        color: "#c084fc", // light purple
      });
    }
  }

  return { nodes, links };
}

// ─── Helpers ───────────────────────────────────────────────────────────────────

function truncate(value: string, max: number): string {
  if (value.length <= max) return value;
  return `${value.slice(0, max - 1)}…`;
}

function blackboardColourForStatus(status: string): string {
  const normalized = status.toLowerCase();
  if (normalized === "executing") return "#22c55e"; // bright green
  if (normalized === "blocked") return "#ef4444"; // red
  if (normalized === "done") return "#6b7280"; // grey
  if (normalized === "awaiting-approval" || normalized === "deliberating") {
    return "#eab308"; // yellow
  }
  return "#6b7280"; // default grey
}
