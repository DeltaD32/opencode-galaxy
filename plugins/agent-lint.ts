/**
 * agent-lint.ts
 *
 * Validates agent frontmatter whenever an agents/*.md file is created or
 * updated. Catches configuration errors (like the tools: array bug that
 * prevented secretary.md and worker.md from loading) before they reach a
 * live OpenCode session.
 *
 * Two-layer check:
 *   1. In-process frontmatter parse — fast, catches known bad fields
 *      immediately without spawning a subprocess.
 *   2. opencode agent list — authoritative schema validation from the binary
 *      itself; catches anything layer 1 missed.
 *
 * On any finding:
 *   - console.error() → visible in TUI log panel (Ctrl+L)
 *   - Appends to ~/.local/share/opencode/agent-lint.log for later review
 *
 * Hook used:
 *   file.watcher.updated — fires when any tracked file changes on disk
 *   (same hook used by config-backup.ts)
 */

import type { Plugin, PluginModule } from "@opencode-ai/plugin"
import type { BunShell } from "@opencode-ai/plugin/shell"
import * as fs from "fs/promises"
import * as os from "os"
import * as path from "path"

// ── Constants ─────────────────────────────────────────────────────────────────

const HOME        = os.homedir()
const AGENTS_DIR  = path.join(HOME, ".config", "opencode", "agents")
const LOG_PATH    = path.join(HOME, ".local", "share", "opencode", "agent-lint.log")

/**
 * Frontmatter fields that OpenCode 1.17.5 does NOT support.
 * Sourced from the schema error we hit: "Expected object | undefined, got [...] tools"
 * Add new entries here as we discover additional unsupported fields.
 */
const UNSUPPORTED_ARRAY_FIELDS = ["tools"]

/**
 * The only valid model provider prefixes (Rule 1).
 */
const VALID_MODEL_PREFIXES = [
  "llm-api/",
  "ollama/",
]

/**
 * The only valid mode values (Rule 4).
 */
const VALID_MODES = ["subagent", "primary", "all"]

// ── Log helper ────────────────────────────────────────────────────────────────

async function writeLog(lines: string[]): Promise<void> {
  try {
    const entry = lines.join("\n") + "\n"
    await fs.appendFile(LOG_PATH, entry, "utf8")
  } catch {
    // Never crash opencode
  }
}

// ── Frontmatter parser ────────────────────────────────────────────────────────

interface Frontmatter {
  name?:        string
  model?:       string
  mode?:        string
  description?: string
  [key: string]: unknown
}

/**
 * Extracts the YAML block between the first pair of --- delimiters.
 * Returns null if no frontmatter is found.
 */
function extractFrontmatter(content: string): string | null {
  const lines = content.split("\n")
  if (lines[0].trim() !== "---") return null
  const closeIdx = lines.slice(1).findIndex(l => l.trim() === "---")
  if (closeIdx === -1) return null
  return lines.slice(1, closeIdx + 1).join("\n")
}

/**
 * Minimal YAML parser for agent frontmatter.
 * Only handles the flat key: value pairs we care about —
 * sufficient for our validation needs without a full YAML library.
 * Also detects multi-line list fields (key:\n  - item) as arrays.
 */
function parseFrontmatterFields(yaml: string): { fields: Frontmatter; arrayFields: string[] } {
  const fields: Frontmatter = {}
  const arrayFields: string[] = []

  const lines = yaml.split("\n")
  let i = 0
  while (i < lines.length) {
    const line = lines[i]
    const kvMatch = line.match(/^(\w[\w-]*):\s*(.*)$/)
    if (kvMatch) {
      const key = kvMatch[1]
      const val = kvMatch[2].trim()

      // Check if next lines are list items (YAML array)
      const nextLine = lines[i + 1] ?? ""
      if (!val && nextLine.match(/^\s+-\s/)) {
        // This is a multi-line array field
        arrayFields.push(key)
        // Skip the list items
        i++
        while (i < lines.length && lines[i].match(/^\s+-\s/)) {
          i++
        }
        continue
      }

      // Inline array: tools: [bash, edit]
      if (val.startsWith("[")) {
        arrayFields.push(key)
        i++
        continue
      }

      fields[key] = val
    }
    i++
  }

  return { fields, arrayFields }
}

// ── Validation logic ──────────────────────────────────────────────────────────

interface LintResult {
  file:     string
  errors:   string[]
  warnings: string[]
}

function validateFrontmatter(file: string, content: string): LintResult {
  const result: LintResult = { file, errors: [], warnings: [] }

  const raw = extractFrontmatter(content)
  if (!raw) {
    result.errors.push("No frontmatter found — agent file must start with --- YAML block")
    return result
  }

  const { fields, arrayFields } = parseFrontmatterFields(raw)

  // Check for unsupported array fields (the tools: bug)
  for (const f of arrayFields) {
    if (UNSUPPORTED_ARRAY_FIELDS.includes(f)) {
      result.errors.push(
        `Invalid field '${f}:' is an array — OpenCode 1.17.5 does not support array values ` +
        `in agent frontmatter. Remove the '${f}:' block entirely.`
      )
    } else {
      result.warnings.push(
        `Field '${f}:' has an array value — verify this is supported by your OpenCode version.`
      )
    }
  }

  // Validate model (Rule 1)
  if (!fields.model) {
    result.errors.push("Missing required field 'model:'")
  } else {
    const model = String(fields.model)
    const valid = VALID_MODEL_PREFIXES.some(p => model.startsWith(p))
    if (!valid) {
      result.errors.push(
        `Invalid model '${model}' — must start with one of: ${VALID_MODEL_PREFIXES.join(", ")} ` +
        `(Rule 1: provider lockdown)`
      )
    }
  }

  // Validate mode (Rule 4)
  if (!fields.mode) {
    result.warnings.push("Missing 'mode:' field — defaulting to subagent is fine, but explicit is better")
  } else {
    const mode = String(fields.mode)
    if (!VALID_MODES.includes(mode)) {
      result.errors.push(
        `Invalid mode '${mode}' — must be one of: ${VALID_MODES.join(", ")} (Rule 4)`
      )
    }
  }

  // Check name field present
  if (!fields.name) {
    result.warnings.push("Missing 'name:' field in frontmatter")
  }

  // Check description field present
  if (!fields.description) {
    result.warnings.push("Missing 'description:' field — agent won't be discoverable by routing")
  }

  return result
}

// ── opencode agent list validator ─────────────────────────────────────────────

/**
 * Runs `opencode agent list` and parses any Error: lines.
 * This is the authoritative schema check from the binary.
 * Returns array of error strings (empty = all good).
 */
async function runOfficialValidation($: BunShell): Promise<string[]> {
  try {
    // Use nothrow so a validation error doesn't throw — we want to capture the output
    const result = await $`/opt/homebrew/bin/opencode agent list`.quiet().nothrow()
    const combined = result.stdout.toString() + result.stderr.toString()

    // Parse "Error: Configuration is invalid at <path>" lines
    const errors: string[] = []
    for (const line of combined.split("\n")) {
      if (line.includes("Error:") && line.includes("Configuration is invalid")) {
        errors.push(line.trim())
      }
    }
    return errors
  } catch (err) {
    return [`opencode agent list failed: ${err}`]
  }
}

// ── Plugin ────────────────────────────────────────────────────────────────────

export const server: Plugin = async ({ $ }) => {
  return {
    event: async ({ event }) => {
      if (event.type !== "file.watcher.updated") return

      const file: string = (event as any).properties?.file ?? ""

      // Only care about agent files
      if (!file.startsWith(AGENTS_DIR) || !file.endsWith(".md")) return

      const agentName = path.basename(file)
      const timestamp = new Date().toISOString()

      // ── Layer 1: in-process frontmatter validation ────────────────────────
      let content: string
      try {
        content = await fs.readFile(file, "utf8")
      } catch {
        return // File might have been deleted; ignore
      }

      const result = validateFrontmatter(file, content)

      const hasErrors   = result.errors.length > 0
      const hasWarnings = result.warnings.length > 0

      if (hasErrors || hasWarnings) {
        const logLines = [
          `\n[agent-lint] ${timestamp} — ${agentName}`,
        ]
        for (const e of result.errors)   logLines.push(`  ❌ ERROR:   ${e}`)
        for (const w of result.warnings) logLines.push(`  ⚠️  WARNING: ${w}`)

        for (const line of logLines) console.error(line)
        await writeLog(logLines)
      }

      // ── Layer 2: official opencode agent list validation ──────────────────
      // Only run if layer 1 passed (no point running if we already found errors)
      if (!hasErrors) {
        const officialErrors = await runOfficialValidation($)
        if (officialErrors.length > 0) {
          const logLines = [
            `\n[agent-lint] ${timestamp} — opencode schema validation FAILED`,
          ]
          for (const e of officialErrors) logLines.push(`  ❌ SCHEMA:  ${e}`)
          logLines.push(`  ↳ Run: opencode agent list   for full details`)

          for (const line of logLines) console.error(line)
          await writeLog(logLines)
        } else {
          // All clear — log a brief success
          const ok = `[agent-lint] ${timestamp} — ${agentName}: OK ✅`
          console.log(ok)
          await writeLog([ok])
        }
      }
    },
  }
}

export type { PluginModule }
