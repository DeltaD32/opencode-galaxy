/**
 * TtsLocal.ts — macOS `say` TTS via Vite dev-server middleware.
 *
 * POST /api/tts-local  { text: string }
 *   → server shells out: say -v Daniel -r 180 -o /tmp/jarvis.aiff <text>
 *   → ffmpeg converts to WAV (browser-compatible: Chrome doesn't play AIFF)
 *   → responds with WAV bytes (Content-Type: audio/wav)
 *   → we play it via HTMLAudioElement with a blob URL
 *
 * Best for short phrases (<= 120 chars) — very low latency (~200ms with WAV).
 * Falls back silently if the endpoint is unreachable (e.g. vite build / prod).
 *
 * Autoplay note: waitForAudioUnlock() ensures the browser's autoplay policy
 * is satisfied before calling audio.play(). ensureAudioUnlocked() must be
 * called once on app mount (done in main.tsx) to register the gesture listener.
 */

import { waitForAudioUnlock } from './audioUnlock';

export interface TtsLocalOptions {
  onStart?: () => void;
  onEnd?: () => void;
  onError?: (err: string) => void;
}

export class TtsLocal {
  private audio: HTMLAudioElement | null = null;
  private blobUrl: string | null = null;

  constructor(private opts: TtsLocalOptions = {}) {}

  async play(text: string): Promise<void> {
    this.stop();

    // Ensure browser autoplay policy is satisfied before fetching audio.
    // If the user has clicked/typed anything, this resolves instantly.
    try {
      await waitForAudioUnlock(5000);
    } catch {
      // If no interaction in 5s, proceed anyway — play() may still work
      // (e.g. if browser policy is lenient or already unlocked previously).
    }

    let response: Response;
    try {
      response = await fetch('/api/tts-local', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text }),
      });
    } catch (err) {
      this.opts.onError?.(`tts-local fetch failed: ${String(err)}`);
      return;
    }

    if (!response.ok) {
      const msg = await response.text().catch(() => response.statusText);
      this.opts.onError?.(`tts-local error ${response.status}: ${msg}`);
      return;
    }

    const blob = await response.blob();
    this.blobUrl = URL.createObjectURL(blob);

    const audio = new Audio();
    this.audio = audio;

    audio.onplay  = () => this.opts.onStart?.();
    audio.onended = () => { this.cleanup(); this.opts.onEnd?.(); };
    audio.onerror = (e) => {
      console.error('[TtsLocal] audio element error', e);
      this.cleanup();
      this.opts.onError?.('audio playback error');
    };

    // Wait for canplaythrough before calling play() — avoids "not enough data" DOMException
    await new Promise<void>((resolve, reject) => {
      audio.oncanplaythrough = () => resolve();
      audio.onerror = (e) => { reject(e); };
      audio.src = this.blobUrl!;
      audio.load();
    }).catch((e) => {
      this.cleanup();
      throw new Error(`audio load failed: ${String(e)}`);
    });

    // Reset onerror to the proper handler after load
    audio.onerror = (e) => {
      console.error('[TtsLocal] audio element error', e);
      this.cleanup();
      this.opts.onError?.('audio playback error');
    };

    try {
      await audio.play();
    } catch (err) {
      this.cleanup();
      this.opts.onError?.(`audio.play() failed: ${String(err)}`);
    }
  }

  stop(): void {
    if (this.audio) {
      this.audio.pause();
      this.audio.onplay = null;
      this.audio.onended = null;
      this.audio.onerror = null;
      this.audio = null;
    }
    this.cleanup();
  }

  private cleanup(): void {
    if (this.blobUrl) {
      URL.revokeObjectURL(this.blobUrl);
      this.blobUrl = null;
    }
  }
}
