/**
 * memory-reader.ts
 *
 * Reads memory.jsonl from the MCP server-memory default path and parses it
 * into a graph structure suitable for 3d-force-graph.
 *
 * memory.jsonl schema (one JSON object per line):
 *   entity:   { type: "entity", name: string, entityType: string, observations: string[] }
 *   relation: { type: "relation", from: string, to: string, relationType: string }
 *
 * The file lives inside an npx cache directory — the path is stable for a
 * given machine but changes when the npx cache is cleared. We expose the
 * default path as a constant and allow the consumer to override it.
 */

/** Default path as observed on the dev machine (npx cache fingerprint). */
export const DEFAULT_MEMORY_PATH =
  "/Users/QTE2362/.npm/_npx/15b07286cbcc3329/node_modules/@modelcontextprotocol/server-memory/dist/memory.jsonl";

// ─── Types ────────────────────────────────────────────────────────────────────

export interface MemoryEntity {
  name: string;
  entityType: string;
  observations: string[];
}

export interface MemoryRelation {
  from: string;
  to: string;
  relationType: string;
}

export interface MemoryGraph {
  entities: MemoryEntity[];
  relations: MemoryRelation[];
}

/** Node shape expected by 3d-force-graph */
export interface GraphNode {
  id: string;
  name: string;
  entityType: string;
  observations: string[];
  color: string;
  val: number; // sphere size — bigger for nodes with more observations

  // Optional cluster hint used for layer toggles & layout seeding
  cluster?: "agents" | "memory" | "projects";

  // Optional initial position hints consumed by d3-force
  x?: number;
  y?: number;
  z?: number;

  // Optional structured metadata for richer side-panel rendering
  // (project / blackboard / decision / conflict details, etc.).
  // Deliberately typed as unknown to avoid coupling this module to
  // project-specific shapes.
  metadata?: unknown;
}

/** Link shape expected by 3d-force-graph */
export interface GraphLink {
  source: string;
  target: string;
  relationType: string;
  color: string;
}

export interface ForceGraphData {
  nodes: GraphNode[];
  links: GraphLink[];
}

// ─── Colour mapping ────────────────────────────────────────────────────────────

const TYPE_COLOURS: Record<string, string> = {
  Agent:          "#1c69d4", // BMW Blue
  Skill:          "#22c55e", // Green
  Project:        "#f97316", // Orange
  KnowledgeBase:  "#a855f7", // Purple
  Offering:       "#14b8a6", // Teal
  feature:        "#eab308", // Yellow
  Artifact:       "#ec4899", // Pink
  Configuration:  "#06b6d4", // Cyan
  ProjectTracker: "#f43f5e", // Rose
  project:        "#f97316", // same as Project (some entries use lowercase)
  script:         "#84cc16", // Lime
  // Project layer specific types (used in legend)
  Blackboard:     "#eab308", // Yellow
  Decision:       "#a855f7", // Purple
  Conflict:       "#f97316", // Orange-red
};

const DEFAULT_NODE_COLOUR = "#6b7280"; // Grey
const DEFAULT_LINK_COLOUR = "#374151"; // Dark grey

const RELATION_COLOURS: Record<string, string> = {
  contains:  "#1c69d4",
  requires:  "#f97316",
  uses:      "#22c55e",
  dependsOn: "#a855f7",
  knows:     "#14b8a6",
};

function nodeColour(entityType: string): string {
  return TYPE_COLOURS[entityType] ?? DEFAULT_NODE_COLOUR;
}

function linkColour(relationType: string): string {
  return RELATION_COLOURS[relationType] ?? DEFAULT_LINK_COLOUR;
}

// ─── Parser ────────────────────────────────────────────────────────────────────

/**
 * Parse a raw memory.jsonl string into MemoryGraph.
 * Skips lines that are empty, comments, or not valid JSON.
 */
export function parseMemoryJsonl(raw: string): MemoryGraph {
  const entities: MemoryEntity[] = [];
  const relations: MemoryRelation[] = [];

  for (const line of raw.split("\n")) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("//") || trimmed.startsWith("#")) continue;

    let obj: unknown;
    try {
      obj = JSON.parse(trimmed);
    } catch {
      continue; // skip malformed lines
    }

    if (typeof obj !== "object" || obj === null) continue;
    const record = obj as Record<string, unknown>;

    if (record.type === "entity") {
      entities.push({
        name: String(record.name ?? ""),
        entityType: String(record.entityType ?? "unknown"),
        observations: Array.isArray(record.observations)
          ? (record.observations as unknown[]).map(String)
          : [],
      });
    } else if (record.type === "relation") {
      relations.push({
        from: String(record.from ?? ""),
        to: String(record.to ?? ""),
        relationType: String(record.relationType ?? ""),
      });
    }
  }

  return { entities, relations };
}

/**
 * Convert a MemoryGraph into the ForceGraphData shape expected by 3d-force-graph.
 * Relations whose from/to names don't match any entity node are silently dropped.
 */
export function toForceGraphData(graph: MemoryGraph): ForceGraphData {
  const entityNames = new Set(graph.entities.map((e) => e.name));

  const nodes: GraphNode[] = graph.entities.map((e) => ({
    id: e.name,
    name: e.name,
    entityType: e.entityType,
    observations: e.observations,
    color: nodeColour(e.entityType),
    val: Math.max(6, Math.min(20, 6 + e.observations.length * 1.5)),
    cluster: "memory",
  }));

  const links: GraphLink[] = graph.relations
    .filter((r) => entityNames.has(r.from) && entityNames.has(r.to))
    .map((r) => ({
      source: r.from,
      target: r.to,
      relationType: r.relationType,
      color: linkColour(r.relationType),
    }));

  return { nodes, links };
}

// ─── Fetch helper (browser) ────────────────────────────────────────────────────

/**
 * Fetch memory.jsonl via a Vite proxy route (see vite.config.ts).
 * The raw file cannot be fetched directly due to file:// restrictions in the
 * browser, so we expose it through the dev server proxy at /__memory.
 *
 * Returns parsed ForceGraphData.
 */
export async function fetchMemoryGraph(): Promise<ForceGraphData> {
  const resp = await fetch("/__memory");
  if (!resp.ok) {
    throw new Error(`Failed to fetch memory graph: ${resp.status} ${resp.statusText}`);
  }
  const raw = await resp.text();
  const graph = parseMemoryJsonl(raw);
  return toForceGraphData(graph);
}

// ─── Colour helpers (exported for legend) ─────────────────────────────────────

export { nodeColour, linkColour, TYPE_COLOURS, RELATION_COLOURS };
