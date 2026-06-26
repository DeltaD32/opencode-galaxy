/**
 * VoiceController.tsx — Phase 2 voice pipeline orchestrator.
 *
 * Renders as a transparent wrapper (passes children through). Wires together:
 *   - TtsPipeline: speaks JARVIS responses via macOS say or BMW Audio TTS
 *   - SttBridge: ONE instance, published via SttProvider so InputBar can share it
 *   - SessionContext: sends transcripts as messages, sets orbState
 *   - ToastStore: surfaces voice status and errors as toasts
 *   - SSE session.idle: triggers TTS when JARVIS finishes responding
 *
 * CRITICAL — single STT instance:
 *   useSttBridge is called ONLY here. The SttBridgeResult is published via
 *   SttProvider so InputBar (and any future consumer) reads from context instead
 *   of calling useSttBridge themselves.
 *   Two concurrent SpeechRecognition / MediaRecorder objects kill each other
 *   after ~500 ms — this architecture prevents that entirely.
 *
 * Usage in JarvisShell:
 *   <VoiceController>
 *     ... rest of shell JSX ...
 *   </VoiceController>
 *
 * TTS trigger:
 *   session.idle SSE event → extract last assistant message text → pipeline.play(text)
 *
 * STT transcript flow:
 *   PTT → stt.start() → onTranscript chunks → buffer → onStop → sendMessage(buffer)
 */

import { useCallback, useEffect, useRef, useState, type ReactNode } from 'react';
import { useSessionContext } from '../session/SessionContext';
import { useSttBridge } from '../input/SttBridge';
import { SttProvider } from '../input/SttContext';
import { useTtsPipeline } from './TtsPipeline';
import { useToastStore } from './toastStore';
import { useSSE } from '../../hooks/useSSE';
import { useSettingsStore } from '../panel/settingsStore';
import type { SttMode } from '../input/SttBridge';

// ─── mlx-whisper health probe ─────────────────────────────────────────────────

const MLX_WHISPER_URL = 'http://localhost:5001';
const MLX_PROBE_TIMEOUT_MS = 1500;

async function probeWhisper(): Promise<boolean> {
  try {
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), MLX_PROBE_TIMEOUT_MS);
    const res = await fetch(`${MLX_WHISPER_URL}/health`, { signal: ctrl.signal });
    clearTimeout(timer);
    return res.ok;
  } catch {
    return false;
  }
}

// ─── VoiceController ─────────────────────────────────────────────────────────

interface VoiceControllerProps {
  /** Shell children — wrapped in SttProvider so they can consume useSttContext(). */
  children?: ReactNode;
}

export function VoiceController({ children }: VoiceControllerProps) {
  const { isBusy, sendMessage, setOrbState, activeSessionID } = useSessionContext();
  const { push: pushToast } = useToastStore();
  const { ttsEnabled } = useSettingsStore();

  // ── Accumulate latest assistant text via SSE (avoids stale closure) ─────────
  // We cannot read `messages` from context inside a useSSE callback — the closure
  // captures the value at render time and it's always stale. Instead we accumulate
  // the live text directly from message.part.updated events into a ref.
  const latestAssistantTextRef = useRef<{ msgId: string; text: string } | null>(null);

  // ── STT mode probe ────────────────────────────────────────────────────────
  // Default: 'none' — PTT is disabled until mlx-whisper is confirmed reachable.
  // We never fall back to webspeech: it requires Google's cloud endpoint which
  // is blocked on BMW corporate network and produces a 'network' error.
  const [sttMode, setSttMode] = useState<SttMode>('none');
  const whisperProbed = useRef(false);

  useEffect(() => {
    if (whisperProbed.current) return;
    whisperProbed.current = true;
    console.log('[VoiceController] Probing mlx-whisper at', MLX_WHISPER_URL);
    probeWhisper().then((available) => {
      console.log('[VoiceController] mlx-whisper probe result:', available);
      if (available) {
        setSttMode('mlxwhisper');
        pushToast({ message: '🎙 mlx-whisper ready — mic button enabled', level: 'success', duration: 4000 });
      } else {
        setSttMode('none');
        pushToast({
          message: '⚠ Voice unavailable — run: python scripts/whisper-sidecar.py',
          level: 'warning',
          duration: 10000,
        });
      }
    });
  }, [pushToast]);

  // ── TTS ───────────────────────────────────────────────────────────────────
  const handleTtsStart = useCallback(() => setOrbState('SPEAKING'), [setOrbState]);
  const handleTtsEnd   = useCallback(() => setOrbState('IDLE'),     [setOrbState]);
  const handleTtsError = useCallback(
    (err: string) => {
      setOrbState('IDLE');
      pushToast({ message: `TTS error: ${err}`, level: 'error' });
    },
    [setOrbState, pushToast],
  );

  const tts = useTtsPipeline({ onStart: handleTtsStart, onEnd: handleTtsEnd, onError: handleTtsError });

  // Accumulate assistant text from live SSE parts — avoids stale closure on messages state
  const lastSpokenIdRef = useRef<string | null>(null);
  useSSE((event) => {
    // Track latest assistant message text as parts arrive
    if (event.type === 'message.part.updated') {
      const part = event.properties.part;
      if (part.type === 'text' && (part as { text?: string }).text) {
        const existing = latestAssistantTextRef.current;
        const msgId = (part as { messageID?: string }).messageID ?? '';
        const chunk = (part as { text: string }).text;
        if (existing?.msgId === msgId) {
          // Same message — append (parts may update incrementally)
          latestAssistantTextRef.current = { msgId, text: chunk };
        } else {
          // New message
          latestAssistantTextRef.current = { msgId, text: chunk };
        }
      }
      // step-finish with reason=stop = reliable end-of-turn signal in OpenCode 1.17.5
      if (part.type === 'step-finish' && (part as { reason?: string }).reason === 'stop') {
        if (!ttsEnabled) {
          console.log('[VoiceController] TTS skipped — disabled in settings');
          return;
        }
        const latest = latestAssistantTextRef.current;
        if (!latest || latest.msgId === lastSpokenIdRef.current) return;
        lastSpokenIdRef.current = latest.msgId;
        const text = sanitizeForSpeech(latest.text);
        console.log('[VoiceController] TTS firing on step-finish stop, text:', text.slice(0, 80));
        if (text.trim()) tts.play(text).catch((e) => console.error('[VoiceController] TTS play error:', e));
      }
    }

    // session.idle is also emitted — use it as a fallback trigger
    if (event.type === 'session.idle') {
      if (!ttsEnabled) return;
      const latest = latestAssistantTextRef.current;
      if (!latest || latest.msgId === lastSpokenIdRef.current) return;
      lastSpokenIdRef.current = latest.msgId;
      const text = sanitizeForSpeech(latest.text);
      console.log('[VoiceController] TTS firing on session.idle, text:', text.slice(0, 80));
      if (text.trim()) tts.play(text).catch((e) => console.error('[VoiceController] TTS play error:', e));
    }
  });

  // Interrupt TTS when a new user turn starts
  useEffect(() => { if (isBusy) tts.stop(); }, [isBusy, tts]);

  // ── STT ───────────────────────────────────────────────────────────────────
  const transcriptBufferRef = useRef('');

  const handleTranscript = useCallback((chunk: string) => {
    transcriptBufferRef.current += chunk;
  }, []);

  const handlePttStart = useCallback(() => {
    transcriptBufferRef.current = '';
    setOrbState('LISTENING');
    tts.stop(); // interrupt any ongoing TTS
  }, [setOrbState, tts]);

  const handlePttStop = useCallback(() => {
    const text = transcriptBufferRef.current.trim();
    transcriptBufferRef.current = '';
    if (text && activeSessionID) {
      sendMessage(text).catch(() => {});
      setOrbState('THINKING');
    } else {
      setOrbState('IDLE');
    }
  }, [activeSessionID, sendMessage, setOrbState]);

  const handleSttError = useCallback(
    (err: string) => {
      setOrbState('IDLE');
      pushToast({ message: `STT error: ${err}`, level: 'error' });
    },
    [setOrbState, pushToast],
  );

  // THE one and only useSttBridge call in the entire app.
  // Result published to SttProvider → InputBar reads via useSttContext().
  const stt = useSttBridge({
    mode: sttMode,
    onTranscript: handleTranscript,
    onStart: handlePttStart,
    onStop: handlePttStop,
    onError: handleSttError,
  });

  return <SttProvider value={stt}>{children}</SttProvider>;
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

/** Strip markdown for speech — mirrors TtsPipeline.sanitizeForSpeech */
function sanitizeForSpeech(text: string): string {
  return text
    .replace(/```[\s\S]*?```/g, '')
    .replace(/`[^`]+`/g, '')
    .replace(/^#{1,6}\s+/gm, '')
    .replace(/[*_]{1,3}([^*_]+)[*_]{1,3}/g, '$1')
    .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
    .replace(/https?:\/\/\S+/g, '')
    .replace(/\s{2,}/g, ' ')
    .trim();
}
