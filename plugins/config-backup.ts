import type { Plugin, PluginModule } from "@opencode-ai/plugin"
import type { BunShell } from "@opencode-ai/plugin/shell"
import * as path from "path"
import * as os from "os"

// ── Constants ────────────────────────────────────────────────────────────────

const HOME = os.homedir()
const CONFIG_DIR = path.join(HOME, ".config", "opencode")
const OPENCODE_DIR = path.join(HOME, ".opencode")
const REPO_DIR = path.join(HOME, "opencode-config-backup")
const GH_HOST = "atc-github.azure.cloud.bmw"
const REPO_NAME = "opencode-config-backup"
const DEBOUNCE_MS = 2000

// ── Helpers ──────────────────────────────────────────────────────────────────

async function ensureRepo($: BunShell): Promise<void> {
  // Create repo subdirs
  await $`mkdir -p ${REPO_DIR}/config ${REPO_DIR}/opencode`

  // Check if already a git repo
  const check = await $`git -C ${REPO_DIR} rev-parse --is-inside-work-tree`.quiet().nothrow()
  if (check.exitCode === 0) {
    return // already initialised
  }

  // Init repo
  await $`git -C ${REPO_DIR} init -b main`

  // Write .gitignore
  const gitignore = `node_modules/\n.env\n`
  await Bun.write(path.join(REPO_DIR, ".gitignore"), gitignore)

  // Initial rsync of both dirs
  await rsyncDirs($)

  // Initial commit
  await $`git -C ${REPO_DIR} add -A`
  await $`git -C ${REPO_DIR} commit -m "initial backup"`

  // Create private remote repo and push
  await $`env GH_HOST=${GH_HOST} gh repo create ${REPO_NAME} --private --source ${REPO_DIR} --remote origin --push`
}

async function rsyncDirs($: BunShell): Promise<void> {
  // Trailing slash on source = sync contents into dest dir
  await $`rsync -a --delete --exclude=node_modules --exclude=.env ${CONFIG_DIR}/ ${REPO_DIR}/config/`
  await $`rsync -a --delete --exclude=node_modules ${OPENCODE_DIR}/ ${REPO_DIR}/opencode/`
}

async function commitAndPush($: BunShell): Promise<void> {
  try {
    await rsyncDirs($)

    await $`git -C ${REPO_DIR} add -A`

    // Check if anything is staged
    const diff = await $`git -C ${REPO_DIR} diff --cached --stat`.quiet()
    const statOutput = diff.stdout.toString().trim()
    if (!statOutput) {
      return // nothing to commit
    }

    // Build commit message from first line of stat summary (last line is the summary)
    const lines = statOutput.split("\n").filter(Boolean)
    const summary = lines[lines.length - 1].trim()
    const raw = `auto-backup: ${summary}`
    const message = raw.length > 72 ? raw.slice(0, 72) : raw

    await $`git -C ${REPO_DIR} commit -m ${message}`
    await $`env GH_HOST=${GH_HOST} git -C ${REPO_DIR} push origin main`
  } catch (err) {
    // Log but never crash opencode
    console.error("[config-backup] commit/push failed:", err)
  }
}

// ── Plugin ───────────────────────────────────────────────────────────────────

export const server: Plugin = async ({ $ }) => {
  let timer: ReturnType<typeof setTimeout> | null = null

  // Fire-and-forget startup: ensure repo + sweep for offline changes.
  // Do NOT await — this must not block opencode from opening.
  ;(async () => {
    try {
      await ensureRepo($)
      await commitAndPush($)
    } catch (err) {
      console.error("[config-backup] startup failed:", err)
    }
  })()

  return {
    event: async ({ event }) => {
      if (event.type !== "file.watcher.updated") return

      const file: string = (event as any).properties?.file ?? ""
      if (!file.startsWith(CONFIG_DIR)) return

      // Debounce — wait for rapid saves to settle
      if (timer) clearTimeout(timer)
      timer = setTimeout(() => {
        timer = null
        commitAndPush($).catch((err) => {
          console.error("[config-backup] debounced commit failed:", err)
        })
      }, DEBOUNCE_MS)
    },
  }
}

export type { PluginModule }
