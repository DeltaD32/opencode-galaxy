/**
 * TtsPipeline.ts — JARVIS TTS decision router.
 *
 * Routes text to the appropriate TTS backend based on length:
 *   text.length <= TTS_LOCAL_MAX_CHARS  →  TtsLocal  (say -v Daniel, ~120ms latency)
 *   text.length >  TTS_LOCAL_MAX_CHARS  →  TtsBmw    (BMW Audio TTS API, quality MP3)
 *
 * The pipeline is a singleton — only one utterance plays at a time.
 * Calling play() while already speaking stops the current utterance first.
 *
 * Orb state integration:
 *   onStart → caller should set orbState = 'SPEAKING'
 *   onEnd   → caller should set orbState = 'IDLE'
 *
 * Usage (inside a React component):
 *   const pipeline = useTtsPipeline({ onStart, onEnd, onError });
 *   pipeline.play("Hello, how can I help?");
 *   pipeline.stop();
 */

import { useRef, useCallback } from 'react';
import { TtsLocal } from './TtsLocal';
import { TtsBmw } from './TtsBmw';

// ─── Config ───────────────────────────────────────────────────────────────────

/** Text at or below this length goes to TtsLocal (say), above goes to TtsBmw */
export const TTS_LOCAL_MAX_CHARS = 120;

// ─── Types ────────────────────────────────────────────────────────────────────

export interface TtsPipelineOptions {
  onStart?: () => void;
  onEnd?: () => void;
  onError?: (err: string) => void;
  /** BMW Audio TTS voice ID — defaults to 'alloy' */
  bmwVoiceId?: string;
}

export interface TtsPipelineHandle {
  play: (text: string) => Promise<void>;
  stop: () => void;
  /** Which backend was used for the last utterance */
  lastBackend: 'local' | 'bmw' | null;
}

// ─── Hook ─────────────────────────────────────────────────────────────────────

export function useTtsPipeline(opts: TtsPipelineOptions = {}): TtsPipelineHandle {
  const { onStart, onEnd, onError, bmwVoiceId } = opts;

  // Lazily instantiated — only create on first play()
  const localRef = useRef<TtsLocal | null>(null);
  const bmwRef = useRef<TtsBmw | null>(null);
  const activeRef = useRef<'local' | 'bmw' | null>(null);
  const lastBackendRef = useRef<'local' | 'bmw' | null>(null);

  // Ensure instances exist with current callbacks
  const getLocal = useCallback((): TtsLocal => {
    if (!localRef.current) {
      localRef.current = new TtsLocal({ onStart, onEnd, onError });
    }
    return localRef.current;
  }, [onStart, onEnd, onError]);

  const getBmw = useCallback((): TtsBmw => {
    if (!bmwRef.current) {
      bmwRef.current = new TtsBmw({ voiceId: bmwVoiceId, onStart, onEnd, onError });
    }
    return bmwRef.current;
  }, [bmwVoiceId, onStart, onEnd, onError]);

  const stop = useCallback(() => {
    localRef.current?.stop();
    bmwRef.current?.stop();
    activeRef.current = null;
  }, []);

  const play = useCallback(
    async (text: string): Promise<void> => {
      // Stop any current playback
      stop();

      // Strip markdown / code blocks for spoken output
      const spoken = sanitizeForSpeech(text);
      if (!spoken.trim()) return;

      if (spoken.length <= TTS_LOCAL_MAX_CHARS) {
        activeRef.current = 'local';
        lastBackendRef.current = 'local';
        await getLocal().play(spoken);
      } else {
        activeRef.current = 'bmw';
        lastBackendRef.current = 'bmw';
        await getBmw().play(spoken);
      }
    },
    [stop, getLocal, getBmw],
  );

  return {
    play,
    stop,
    get lastBackend() {
      return lastBackendRef.current;
    },
  };
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

/**
 * Strip markdown syntax that doesn't translate to speech:
 * code blocks, inline code, bold/italic markers, URLs, headings.
 * Keeps the human-readable text content.
 */
function sanitizeForSpeech(text: string): string {
  return (
    text
      // Code blocks (```...```)
      .replace(/```[\s\S]*?```/g, '')
      // Inline code (`...`)
      .replace(/`[^`]+`/g, '')
      // Markdown headings
      .replace(/^#{1,6}\s+/gm, '')
      // Bold / italic
      .replace(/[*_]{1,3}([^*_]+)[*_]{1,3}/g, '$1')
      // Markdown links [text](url)
      .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
      // Bare URLs
      .replace(/https?:\/\/\S+/g, '')
      // Collapse extra whitespace
      .replace(/\s{2,}/g, ' ')
      .trim()
  );
}
