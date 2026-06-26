/**
 * tts-server.mjs — Vite plugin helper: /api/tts-local middleware.
 *
 * Called from vite.config.ts as a custom server middleware.
 * Handles: POST /api/tts-local  { text: string }
 *
 * Flow:
 *   1. Read JSON body
 *   2. Shell out: say -v Daniel -r 180 -o /tmp/jarvis-tts.aiff "<text>"
 *   3. Read /tmp/jarvis-tts.aiff
 *   4. Respond with audio/aiff bytes
 *
 * Security: text is passed as a shell argument via an array (execFileSync),
 * NOT via string interpolation — avoids shell injection.
 */

import { execFileSync } from 'child_process';
import { readFileSync, unlinkSync, existsSync } from 'fs';
import { tmpdir } from 'os';
import { join } from 'path';

const TTS_OUTPUT = join(tmpdir(), 'jarvis-tts.aiff');
const SAY_VOICE = 'Daniel';
const SAY_RATE = '180';

/**
 * Vite plugin that adds the /api/tts-local route.
 * Import and spread into the `plugins` array in vite.config.ts.
 */
export function ttsLocalPlugin() {
  return {
    name: 'tts-local',
    configureServer(server) {
      server.middlewares.use('/api/tts-local', (req, res, next) => {
        if (req.method !== 'POST') {
          next();
          return;
        }

        let body = '';
        req.setEncoding('utf8');
        req.on('data', (chunk) => { body += chunk; });
        req.on('end', () => {
          let text = '';
          try {
            const parsed = JSON.parse(body);
            text = String(parsed.text ?? '').trim();
          } catch {
            res.statusCode = 400;
            res.end(JSON.stringify({ error: 'invalid JSON body' }));
            return;
          }

          if (!text) {
            res.statusCode = 400;
            res.end(JSON.stringify({ error: 'text is required' }));
            return;
          }

          // Truncate safety — say can hang on very long text
          const safeText = text.slice(0, 500);

          try {
            // Clean up previous output file
            if (existsSync(TTS_OUTPUT)) {
              try { unlinkSync(TTS_OUTPUT); } catch { /* ignore */ }
            }

            // Shell out to say — uses execFileSync (array args, no shell injection)
            execFileSync('say', ['-v', SAY_VOICE, '-r', SAY_RATE, '-o', TTS_OUTPUT, safeText], {
              timeout: 10_000,
              stdio: 'pipe',
            });

            const audio = readFileSync(TTS_OUTPUT);

            res.setHeader('Content-Type', 'audio/aiff');
            res.setHeader('Content-Length', audio.length);
            res.setHeader('Cache-Control', 'no-store');
            res.statusCode = 200;
            res.end(audio);
          } catch (err) {
            console.error('[tts-local] say failed:', err);
            res.statusCode = 500;
            res.end(JSON.stringify({ error: String(err) }));
          }
        });
      });
    },
  };
}
