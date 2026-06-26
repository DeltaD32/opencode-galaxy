import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import fs from "fs";
import path from "path";
import http from "http";
import { spawn, execFileSync, type ChildProcess } from "child_process";
import Database from "better-sqlite3";
import { tmpdir } from "os";

// BMW corporate network sets HTTP_PROXY=http://localhost:3128 (Squid/ZScaler).
// Vite's internal http-proxy respects this env var and tries to route the
// /api/* → localhost:4096 proxy through the corporate proxy, which either
// fails or returns an error page. Node's http-proxy does NOT honour NO_PROXY
// natively, so 127.0.0.1 is NOT exempted automatically.
//
// Fix: use a custom http.Agent with keepAlive that connects directly,
// bypassing the system proxy for local loopback traffic.
const directAgent = new http.Agent({ keepAlive: true });

const MEMORY_JSONL_PATH =
  "/Users/QTE2362/.npm/_npx/15b07286cbcc3329/node_modules/@modelcontextprotocol/server-memory/dist/memory.jsonl";

const AGENTS_DIR = "/Users/QTE2362/.config/opencode/agents";
const SKILLS_DIR = "/Users/QTE2362/.opencode/skills";
const OPENCODE_DB_PATH = "/Users/QTE2362/.local/share/opencode/opencode.db";

/** Read all agent .md files and build a JSON graph of agents + skills. */
function buildAgentGraph(): string {
  type AgentNode = {
    id: string; name: string; nodeType: "agent";
    model: string; mode: string; description: string;
  };
  type SkillNode = {
    id: string; name: string; nodeType: "skill";
  };
  type Link = { source: string; target: string; relationType: string };

  const agents: AgentNode[] = [];
  const skillSet = new Set<string>();
  const links: Link[] = [];

  // Collect installed skill names
  let installedSkills: string[] = [];
  try {
    installedSkills = fs.readdirSync(SKILLS_DIR).filter((f) =>
      fs.statSync(path.join(SKILLS_DIR, f)).isDirectory()
    );
  } catch { /* skip */ }

  // Parse each agent .md file
  let agentFiles: string[] = [];
  try {
    agentFiles = fs.readdirSync(AGENTS_DIR).filter((f) => f.endsWith(".md"));
  } catch { /* skip */ }

  for (const file of agentFiles) {
    const raw = fs.readFileSync(path.join(AGENTS_DIR, file), "utf-8");

    // Extract frontmatter
    const fmMatch = raw.match(/^---\n([\s\S]*?)\n---/);
    const fm = fmMatch ? fmMatch[1] : "";
    const nameMatch = fm.match(/^name:\s*(.+)$/m);
    const modelMatch = fm.match(/^model:\s*(.+)$/m);
    const modeMatch = fm.match(/^mode:\s*(.+)$/m);
    const descMatch = fm.match(/^description:\s*"?(.+?)"?\s*$/m);

    const name = nameMatch?.[1]?.trim() ?? file.replace(".md", "");
    const model = modelMatch?.[1]?.trim() ?? "unknown";
    const mode = modeMatch?.[1]?.trim() ?? "subagent";
    const description = descMatch?.[1]?.trim() ?? "";

    agents.push({ id: `agent:${name}`, name, nodeType: "agent", model, mode, description });

    // Find skill references in the body — look for skill names mentioned
    for (const skill of installedSkills) {
      // Match skill name as a word boundary in the document body
      const regex = new RegExp(`\\b${skill.replace(/-/g, "[-_]?")}\\b`, "i");
      if (regex.test(raw)) {
        skillSet.add(skill);
        links.push({ source: `agent:${name}`, target: `skill:${skill}`, relationType: "uses" });
      }
    }
  }

  const skillNodes: SkillNode[] = [...skillSet].map((s) => ({
    id: `skill:${s}`, name: s, nodeType: "skill",
  }));

  // Add orchestrator → subagent links
  const primaryAgent = agents.find(a => a.mode === "primary");
  if (primaryAgent) {
    for (const agent of agents) {
      if (agent.mode !== "primary") {
        links.push({
          source: primaryAgent.id,
          target: agent.id,
          relationType: "orchestrates",
        });
      }
    }
  }

  return JSON.stringify({
    agents,
    skills: skillNodes,
    links,
    orchestratorId: primaryAgent?.id ?? null,
  });
}

/**
 * Read a snapshot of project/blackboard/decision/conflict tables from
 * opencode.db and return a JSON string. Any missing tables are treated as
 * empty arrays so that the /__db route always responds successfully.
 */
function buildDbSnapshot(): string {
  type Row = Record<string, unknown>;

  const empty = {
    projects: [] as Row[],
    blackboards: [] as Row[],
    decisions: [] as Row[],
    conflicts: [] as Row[],
  };

  let db: Database.Database | null = null;
  try {
    db = new Database(OPENCODE_DB_PATH, { readonly: true, fileMustExist: false });

    const safeAll = (table: string, sql: string): Row[] => {
      try {
        return db!.prepare(sql).all() as Row[];
      } catch (err) {
        // Missing tables are expected on fresh installs; log and continue.
        // eslint-disable-next-line no-console
        console.warn(`[vite:/__db] skipping table ${table}:`, String(err));
        return [];
      }
    };

    const projects = safeAll(
      "projects",
      "SELECT id, name, status, description, created_at FROM projects"
    );
    const blackboards = safeAll(
      "blackboards",
      "SELECT id, project_id, task_description, status, file_path, created_at FROM blackboards"
    );
    const decisions = safeAll(
      "decisions",
      "SELECT id, blackboard_id, made_by, decision, rationale, timestamp FROM decisions"
    );
    const conflicts = safeAll(
      "conflicts",
      "SELECT id, blackboard_id, agent_a, agent_b, description, resolved, resolution FROM conflicts"
    );
    // sections — which agent wrote which part of each blackboard.
    // Used by JARVIS top bar to show per-agent activity status.
    const sections = safeAll(
      "sections",
      "SELECT id, blackboard_id, agent, section_name, written_at FROM sections WHERE compressed = 0 OR compressed IS NULL"
    );

    return JSON.stringify({ projects, blackboards, decisions, conflicts, sections });
  } catch (err) {
    // eslint-disable-next-line no-console
    console.warn("[vite:/__db] failed to open opencode.db:", String(err));
    return JSON.stringify(empty);
  } finally {
    if (db) {
      try {
        db.close();
      } catch {
        // ignore
      }
    }
  }
}

// ─── Whisper Sidecar Plugin ───────────────────────────────────────────────────
// Auto-starts scripts/whisper-sidecar.py when `npm run dev` is used.
// Skips startup if port 5001 is already in use (sidecar already running).

const SIDECAR_SCRIPT = path.resolve(__dirname, "scripts/whisper-sidecar.py");
const SIDECAR_VENV   = path.resolve(__dirname, ".venv-whisper/bin/python3");
const SIDECAR_PORT   = 5001;

function whisperSidecarPlugin() {
  let proc: ChildProcess | null = null;

  return {
    name: "whisper-sidecar",
    async buildStart() { /* no-op in build */ },
    async configureServer() {
      // Check if already running
      const alreadyUp = await new Promise<boolean>((resolve) => {
        const req = http.request(
          { hostname: "127.0.0.1", port: SIDECAR_PORT, path: "/health", method: "GET", timeout: 800 },
          (res) => resolve(res.statusCode === 200)
        );
        req.on("error", () => resolve(false));
        req.on("timeout", () => { req.destroy(); resolve(false); });
        req.end();
      });

      if (alreadyUp) {
        console.log("\x1b[32m[whisper-sidecar]\x1b[0m Already running on port", SIDECAR_PORT);
        return;
      }

      // Check venv + script exist
      if (!fs.existsSync(SIDECAR_SCRIPT)) {
        console.warn("\x1b[33m[whisper-sidecar]\x1b[0m Script not found:", SIDECAR_SCRIPT);
        return;
      }
      const pythonBin = fs.existsSync(SIDECAR_VENV) ? SIDECAR_VENV : "python3";

      console.log("\x1b[36m[whisper-sidecar]\x1b[0m Starting…  (python:", pythonBin, ")");
      proc = spawn(pythonBin, [SIDECAR_SCRIPT], {
        detached: false,
        stdio: ["ignore", "pipe", "pipe"],
      });

      proc.stdout?.on("data", (d: Buffer) => {
        process.stdout.write(`\x1b[2m[sidecar] ${d.toString().trim()}\x1b[0m\n`);
      });
      proc.stderr?.on("data", (d: Buffer) => {
        const msg = d.toString().trim();
        // Only log meaningful lines — suppress uvicorn startup noise
        if (msg && !msg.includes("INFO:") && !msg.startsWith("WARNING")) {
          process.stderr.write(`\x1b[2m[sidecar] ${msg}\x1b[0m\n`);
        }
      });
      proc.on("exit", (code) => {
        if (code !== 0 && code !== null) {
          console.warn(`\x1b[33m[whisper-sidecar]\x1b[0m exited with code ${code}`);
        }
        proc = null;
      });

      // Give the sidecar a moment to boot, then verify
      await new Promise((r) => setTimeout(r, 2500));
      const up = await new Promise<boolean>((resolve) => {
        const req = http.request(
          { hostname: "127.0.0.1", port: SIDECAR_PORT, path: "/health", method: "GET", timeout: 2000 },
          (res) => resolve(res.statusCode === 200)
        );
        req.on("error", () => resolve(false));
        req.on("timeout", () => { req.destroy(); resolve(false); });
        req.end();
      });

      if (up) {
        console.log("\x1b[32m[whisper-sidecar]\x1b[0m Ready on port", SIDECAR_PORT);
      } else {
        console.warn(
          "\x1b[33m[whisper-sidecar]\x1b[0m Not yet ready — first-run setup may still be running.\n" +
          "  If this is the first start, install deps first:\n" +
          "  python3 scripts/whisper-sidecar.py --setup"
        );
      }
    },
    closeBundle() {
      if (proc) { proc.kill(); proc = null; }
    },
  };
}

// ─── TTS Local Plugin ─────────────────────────────────────────────────────────

const TTS_AIFF = path.join(tmpdir(), "jarvis-tts.aiff");
const TTS_WAV  = path.join(tmpdir(), "jarvis-tts.wav");
const SAY_VOICE = "Daniel";
const SAY_RATE = "180";

// Detect ffmpeg location (Homebrew or system PATH)
function findFfmpeg(): string {
  const candidates = ["/opt/homebrew/bin/ffmpeg", "/usr/local/bin/ffmpeg", "ffmpeg"];
  for (const c of candidates) {
    try { execFileSync(c, ["-version"], { stdio: "pipe", timeout: 2000 }); return c; } catch { /* try next */ }
  }
  return "ffmpeg"; // fallback — will fail gracefully
}
const FFMPEG = findFfmpeg();

function ttsLocalPlugin() {
  return {
    name: "tts-local",
    configureServer(server: { middlewares: { use: (path: string, fn: (req: any, res: any, next: () => void) => void) => void } }) {
      server.middlewares.use("/api/tts-local", (req: any, res: any, next: () => void) => {
        if (req.method !== "POST") { next(); return; }

        let body = "";
        req.setEncoding("utf8");
        req.on("data", (chunk: string) => { body += chunk; });
        req.on("end", () => {
          let text = "";
          try {
            const parsed = JSON.parse(body);
            text = String(parsed.text ?? "").trim();
          } catch {
            res.statusCode = 400;
            res.end(JSON.stringify({ error: "invalid JSON body" }));
            return;
          }

          if (!text) {
            res.statusCode = 400;
            res.end(JSON.stringify({ error: "text is required" }));
            return;
          }

          const safeText = text.slice(0, 500);

          try {
            // Step 1: say → AIFF (macOS native)
            for (const f of [TTS_AIFF, TTS_WAV]) {
              if (fs.existsSync(f)) { try { fs.unlinkSync(f); } catch { /* ignore */ } }
            }

            execFileSync("say", ["-v", SAY_VOICE, "-r", SAY_RATE, "-o", TTS_AIFF, safeText], {
              timeout: 10_000,
              stdio: "pipe",
            });

            // Step 2: AIFF → WAV (Chrome/Firefox don't support AIFF)
            execFileSync(FFMPEG, [
              "-y", "-i", TTS_AIFF,
              "-acodec", "pcm_s16le",
              "-ar", "22050",
              "-ac", "1",
              TTS_WAV,
            ], { timeout: 8_000, stdio: "pipe" });

            const audio = fs.readFileSync(TTS_WAV);
            res.setHeader("Content-Type", "audio/wav");
            res.setHeader("Content-Length", audio.length);
            res.setHeader("Cache-Control", "no-store");
            res.statusCode = 200;
            res.end(audio);
          } catch (err) {
            // eslint-disable-next-line no-console
            console.error("[tts-local] say/ffmpeg failed:", err);
            res.statusCode = 500;
            res.end(JSON.stringify({ error: String(err) }));
          }
        });
      });
    },
  };
}

export default defineConfig({
  plugins: [react(), ttsLocalPlugin(), whisperSidecarPlugin()],
  server: {
    port: 3000,
    proxy: {
      "/api": {
        target: `http://127.0.0.1:${process.env.VITE_OPENCODE_PORT ?? 4096}`,
        rewrite: (path) => path.replace(/^\/api/, ""),
        changeOrigin: true,
        // Bypass system HTTP_PROXY (BMW corporate Squid/ZScaler on :3128).
        // Without this, http-proxy routes loopback traffic through the
        // corporate proxy which returns an error, causing Vite to fall back
        // to serving index.html for every /api/* request.
        agent: directAgent,
      },
      // Serves the MCP server-memory knowledge graph file directly.
      "/__memory": {
        target: "http://localhost:3000",
        bypass(_req, res) {
          try {
            const content = fs.readFileSync(MEMORY_JSONL_PATH, "utf-8");
            res.setHeader("Content-Type", "text/plain; charset=utf-8");
            res.setHeader("Access-Control-Allow-Origin", "*");
            res.end(content);
          } catch {
            res.statusCode = 404;
            res.end("memory.jsonl not found");
          }
          return false;
        },
      },
      // Serves the parsed agent+skill graph as JSON.
      "/__agents": {
        target: "http://localhost:3000",
        bypass(_req, res) {
          try {
            const json = buildAgentGraph();
            res.setHeader("Content-Type", "application/json; charset=utf-8");
            res.setHeader("Access-Control-Allow-Origin", "*");
            res.end(json);
          } catch (e) {
            res.statusCode = 500;
            res.end(JSON.stringify({ error: String(e) }));
          }
          return false;
        },
      },
      // Serves a snapshot of projects / blackboards / decisions / conflicts
      // from opencode.db as JSON.
      "/__db": {
        target: "http://localhost:3000",
        bypass(_req, res) {
          try {
            const json = buildDbSnapshot();
            res.setHeader("Content-Type", "application/json; charset=utf-8");
            res.setHeader("Access-Control-Allow-Origin", "*");
            res.end(json);
          } catch (e) {
            res.statusCode = 500;
            res.end(JSON.stringify({ error: String(e) }));
          }
          return false;
        },
      },
    },
  },
  test: {
    environment: "jsdom",
    setupFiles: ["./src/setupTests.ts"],
    globals: true,
  },
});
