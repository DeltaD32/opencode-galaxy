/**
 * TtsBmw.ts — BMW Audio TTS API for longer responses (>120 chars).
 *
 * Proxied through Vite's /api route → opencode server → BMW Audio API.
 * The BMW Audio API streams an MP3 which we play via HTMLAudioElement.
 *
 * Endpoint (via Vite proxy → opencode serve):
 *   POST /api/audio/speech
 *   Body: { model: "tts-1", input: string, voice: "alloy" }
 *   Response: audio/mpeg stream
 *
 * Voice mapping: BMW Audio API uses OpenAI-compatible voices.
 * "alloy" is the neutral/clear default. Can be overridden via voiceId.
 *
 * Autoplay note: waitForAudioUnlock() ensures the browser's autoplay policy
 * is satisfied before calling audio.play().
 */

import { waitForAudioUnlock } from './audioUnlock';

export interface TtsBmwOptions {
  voiceId?: string;
  model?: string;
  onStart?: () => void;
  onEnd?: () => void;
  onError?: (err: string) => void;
}

export class TtsBmw {
  private audio: HTMLAudioElement | null = null;
  private blobUrl: string | null = null;
  private abortController: AbortController | null = null;

  constructor(private opts: TtsBmwOptions = {}) {}

  async play(text: string): Promise<void> {
    this.stop();

    const controller = new AbortController();
    this.abortController = controller;

    let response: Response;
    try {
      response = await fetch('/api/audio/speech', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model: this.opts.model ?? 'tts-1',
          input: text,
          voice: this.opts.voiceId ?? 'alloy',
        }),
        signal: controller.signal,
      });
    } catch (err) {
      if ((err as Error).name === 'AbortError') return;
      this.opts.onError?.(`BMW TTS fetch failed: ${String(err)}`);
      return;
    }

    if (!response.ok) {
      const msg = await response.text().catch(() => response.statusText);
      this.opts.onError?.(`BMW TTS error ${response.status}: ${msg}`);
      return;
    }

    // Ensure autoplay is unlocked before attempting playback
    try {
      await waitForAudioUnlock(5000);
    } catch { /* proceed anyway */ }

    const blob = await response.blob();
    this.blobUrl = URL.createObjectURL(blob);

    const audio = new Audio(this.blobUrl);
    this.audio = audio;

    audio.onplay = () => this.opts.onStart?.();
    audio.onended = () => {
      this.cleanup();
      this.opts.onEnd?.();
    };
    audio.onerror = (e) => {
      console.error('[TtsBmw] audio element error', e);
      this.cleanup();
      this.opts.onError?.('BMW TTS audio playback error');
    };

    try {
      await audio.play();
    } catch (err) {
      this.cleanup();
      this.opts.onError?.(`BMW TTS audio.play() failed: ${String(err)}`);
    }
  }

  stop(): void {
    this.abortController?.abort();
    this.abortController = null;

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
