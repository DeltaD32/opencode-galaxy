/**
 * routing-enforcer.ts
 *
 * Two responsibilities:
 *
 * 1. SYSTEM PROMPT INJECTION — On every LLM turn for the `request-orchestrator`
 *    agent, injects a compact routing-enforcement block into the system prompt.
 *    This prevents the routing rules from being compacted away mid-session and
 *    anchors the orchestrator to its delegation table on every turn.
 *
 * 2. DELEGATION LOG — Before every `task` tool call, appends a JSONL entry to
 *    ~/.local/share/opencode/delegation.jsonl for observability. Entries record:
 *    timestamp, sessionID, subagent_type, and the first 120 chars of the prompt.
 *
 * Hook dependency:
 *   - `experimental.chat.system.transform` → inject enforcement block for orchestrator sessions
 *     Identified via model ID: orchestrator uses claude-haiku-4-5 (unique to it).
 *     Payload confirmed from OpenCode v1.17.5 source:
 *       input:  { sessionID: string, model: { id: string, ... } }
 *       output: { system: string[] }  (mutate in place)
 *   - `tool.execute.before` on `task`      → write JSONL delegation log entry
 *     Payload confirmed from OpenCode v1.17.5 source:
 *       input:  { tool: string, sessionID: string, callID: string }
 *       output: { args: Record<string, unknown> }
 */

import type { Plugin, PluginModule } from "@opencode-ai/plugin"
import * as fs from "fs/promises"
import * as os from "os"
import * as path from "path"

// ── Constants ─────────────────────────────────────────────────────────────────

const HOME = os.homedir()
const LOG_PATH = path.join(HOME, ".local", "share", "opencode", "delegation.jsonl")
/**
 * The orchestrator is identified by its unique model ID rather than agent name.
 * `experimental.chat.system.transform` provides `input.model` but not `input.agent`.
 * Since request-orchestrator is the only agent using claude-haiku-4-5, this is reliable.
 * Update this if the orchestrator model changes.
 */
const ORCHESTRATOR_MODEL_ID = "claude-haiku-4-5"

/**
 * Compact routing-enforcement block injected into orchestrator system prompts.
 * Kept intentionally brief to minimise token overhead per turn.
 * Full routing logic lives in the agent's own .md file — this is a reminder anchor only.
 */
const ROUTING_ENFORCEMENT_BLOCK = `
<routing_enforcement>
You are request-orchestrator. On EVERY user message you MUST:

1. Check if the request matches any specialist domain below — if yes, delegate immediately via the task tool.
   Do NOT answer directly for specialist domains.

SPECIALIST DELEGATION TABLE (delegate when keywords match):
- oracle / apex / plsql / pl/sql / ora- / oracle sql         → oracle-apex-expert
- uipath / rpa / dispatcher / worker / xaml / bot             → uipath-rpa-expert
- jirri / cost savings / mb1b / lt01                         → jirri-data-analyst
- slides / ppt / pptx / deck / presentation / powerpoint      → presentation-builder
- ghas / codeql / wiz / security findings / vulnerabilities / cve → aaa-security-fixer
- pi planning / sprint health / roam / art sync / program increment → agile-master-pi-planning
- coaching / 1:1 / catalyst conversation / team coaching      → agile-master-catalyst-coaching
- dor / definition of ready / jira story readiness            → dor-agent
- opencode upgrade / brew upgrade / wrapper script / skill install / mcp setup / opencode development → opencode-dev-expert

2. For SKILL-routable requests (not specialist), load the skill via the skill tool — do not implement inline.

3. NEVER skip delegation to avoid tool overhead. Delegation is always correct when keywords match.
</routing_enforcement>
`.trim()

// ── JSONL log helper ──────────────────────────────────────────────────────────

async function appendDelegationLog(entry: Record<string, unknown>): Promise<void> {
  try {
    const line = JSON.stringify(entry) + "\n"
    // fs.appendFile creates the file if it doesn't exist, appends otherwise
    await fs.appendFile(LOG_PATH, line, "utf8")
  } catch (err) {
    console.error("[routing-enforcer] delegation log write failed:", err)
  }
}

// ── Plugin ────────────────────────────────────────────────────────────────────

export const server: Plugin = async () => {
  return {
    /**
     * Inject the routing enforcement block into the system prompt for
     * request-orchestrator sessions on every LLM turn.
     *
     * Identification strategy: match on model ID rather than agent name.
     * `experimental.chat.system.transform` exposes `input.model` (not `input.agent`).
     * The orchestrator is the only agent using claude-haiku-4-5, so this is reliable.
     *
     * Confirmed payload from OpenCode v1.17.5 binary:
     *   trigger("experimental.chat.system.transform", {sessionID, model}, {system: n})
     */
    "experimental.chat.system.transform": async (input, output) => {
      // input.model may be a string ID or an object with an id/modelID field
      const model = (input as any).model
      const modelId: string =
        typeof model === "string"
          ? model
          : (model?.id ?? model?.modelID ?? model?.name ?? "")

      if (!modelId.includes(ORCHESTRATOR_MODEL_ID)) return

      // Append enforcement block — placed last so it anchors the end of the system prompt
      output.system.push(ROUTING_ENFORCEMENT_BLOCK)
    },

    /**
     * Log every `task` tool invocation to delegation.jsonl.
     *
     * The `task` tool args typically include:
     *   - subagent_type: string  (the target agent name)
     *   - description:   string  (the task prompt)
     *
     * We record a trimmed snapshot for observability without storing full prompts.
     */
    "tool.execute.before": async (input, output) => {
      if (input.tool !== "task") return

      const args = output.args as Record<string, unknown>
      const subagentType = typeof args?.subagent_type === "string" ? args.subagent_type : "unknown"
      const description = typeof args?.description === "string"
        ? args.description.slice(0, 120)
        : ""

      await appendDelegationLog({
        ts: new Date().toISOString(),
        sessionID: input.sessionID,
        subagent_type: subagentType,
        prompt_preview: description,
      })
    },
  }
}

export type { PluginModule }
