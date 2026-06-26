/**
 * SttBridge.ts — privacy-aware STT mode switcher.
 *
 * Modes:
 *   'none'       — no STT backend available; PTT is cleanly disabled.
 *                  Set when mlx-whisper probe fails. NEVER falls back to
 *                  webspeech — it requires Google's cloud endpoint which is
 *                  blocked on BMW network (results in 'network' error).
 *   'mlxwhisper' — MediaRecorder + WebSocket to localhost:5001/ws/transcribe.
 *                  Privacy default: audio never leaves the machine.
 *   'webspeech'  — Web Speech API (Chrome/Safari only). Streams audio to
 *                  Google. Blocked on BMW corporate network. Kept for local
 *                  development use only — not exposed as a user-facing option.
 *
 * Architecture note:
 *   useSttBridge is called ONCE in VoiceController and published via SttContext.
 *   InputBar and any other consumer read from SttContext — never call this hook
 *   themselves. Two concurrent recognition instances kill each other in ~500 ms.
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import { useVoice } from '../../hooks/useVoice';

// ─── Types ────────────────────────────────────────────────────────────────────

export type SttMode = 'none' | 'mlxwhisper' | 'webspeech';

export interface SttBridgeOptions {
  mode: SttMode;
  onTranscript: (text: string) => void;
  onStart?: () => void;
  onStop?: () => void;
  onError?: (err: string) => void;
}

export interface SttBridgeResult {
  isListening: boolean;
  start: () => void;
  stop: () => void;
  supported: boolean;
  mode: SttMode;
  /** Accumulating transcript text while listening — cleared on stop. Display in UI for confirmation. */
  liveTranscript: string;
  /** True when using webspeech — UI must show privacy warning badge */
  showPrivacyWarning: boolean;
}

// ─── 'none' stub ─────────────────────────────────────────────────────────────

const NONE_RESULT: SttBridgeResult = {
  isListening: false,
  start: () => {},
  stop: () => {},
  supported: false,
  mode: 'none',
  liveTranscript: '',
  showPrivacyWarning: false,
};

// ─── mlx-whisper WebSocket bridge ────────────────────────────────────────────

const MLX_WHISPER_WS = 'ws://localhost:5001/ws/transcribe';

// How long to wait after the last transcript chunk arrives before auto-stopping.
// 1500ms feels natural — long enough not to cut off mid-thought, short enough
// that the user doesn't have to manually release after every utterance.
const SILENCE_TIMEOUT_MS = 1500;

function useMlxWhisperBridge(
  opts: SttBridgeOptions,
): SttBridgeResult {
  const { onTranscript, onStart, onStop, onError } = opts;
  const [isListening, setIsListening] = useState(false);
  const [supported, setSupported] = useState(false);
  const [liveTranscript, setLiveTranscript] = useState('');
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const silenceTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    setSupported(
      typeof navigator !== 'undefined' && !!navigator.mediaDevices?.getUserMedia,
    );
  }, []);

  const clearSilenceTimer = useCallback(() => {
    if (silenceTimerRef.current !== null) {
      clearTimeout(silenceTimerRef.current);
      silenceTimerRef.current = null;
    }
  }, []);

  const stop = useCallback(() => {
    clearSilenceTimer();
    mediaRecorderRef.current?.stop();
    mediaRecorderRef.current = null;
    wsRef.current?.close();
    wsRef.current = null;
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
    setIsListening(false);
    setLiveTranscript('');
    onStop?.();
  }, [onStop, clearSilenceTimer]);

  const resetSilenceTimer = useCallback(() => {
    clearSilenceTimer();
    silenceTimerRef.current = setTimeout(() => {
      // No new transcript for SILENCE_TIMEOUT_MS — treat as end of utterance
      stop();
    }, SILENCE_TIMEOUT_MS);
  }, [clearSilenceTimer, stop]);

  const start = useCallback(() => {
    if (isListening) return;

    let ws: WebSocket;
    try {
      ws = new WebSocket(MLX_WHISPER_WS);
    } catch (err) {
      onError?.(`Cannot connect to mlx-whisper: ${String(err)}`);
      return;
    }
    wsRef.current = ws;

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data as string) as { text?: string; error?: string };
        if (data.error) {
          onError?.(data.error);
          return;
        }
        if (data.text) {
          onTranscript(data.text);
          setLiveTranscript((prev) => (prev ? `${prev} ${data.text}` : data.text!));
          // Got a real transcript chunk — reset the silence countdown
          resetSilenceTimer();
        }
      } catch { /* ignore malformed frames */ }
    };

    ws.onerror = () => {
      onError?.('mlx-whisper WebSocket error — is the sidecar running? (see scripts/whisper-sidecar.py)');
      stop();
    };

    ws.onopen = () => {
      navigator.mediaDevices
        .getUserMedia({ audio: true })
        .then((stream) => {
          streamRef.current = stream;

          const recorder = new MediaRecorder(stream, {
            mimeType: MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
              ? 'audio/webm;codecs=opus'
              : 'audio/webm',
          });

          recorder.ondataavailable = (e) => {
            if (e.data.size > 0 && ws.readyState === WebSocket.OPEN) {
              ws.send(e.data);
            }
          };

          recorder.onstop = () => { stop(); };
          recorder.start(250);
          mediaRecorderRef.current = recorder;
          setIsListening(true);
          // Start the initial silence timer — if no transcript arrives at all,
          // auto-stop after SILENCE_TIMEOUT_MS so the user isn't stuck.
          resetSilenceTimer();
          onStart?.();
        })
        .catch((err) => {
          onError?.(`Microphone access denied: ${String(err)}`);
          ws.close();
        });
    };
  }, [isListening, onTranscript, onStart, onError, stop, resetSilenceTimer]);

  return {
    isListening,
    start,
    stop,
    supported,
    mode: 'mlxwhisper',
    liveTranscript,
    showPrivacyWarning: false,
  };
}

// ─── Main hook ────────────────────────────────────────────────────────────────

export function useSttBridge(options: SttBridgeOptions): SttBridgeResult {
  const { mode, onTranscript, onStart, onStop, onError } = options;

  // ── Web Speech path (local dev only — blocked on BMW network) ────────────────
  const {
    isListening: wsListening,
    isSupported: wsSupported,
    transcript,
    error: wsError,
    startListening,
    stopListening,
  } = useVoice();

  const prevTranscriptRef = useRef('');
  useEffect(() => {
    if (mode !== 'webspeech') return;
    if (!transcript) return;
    const newChunk = transcript.slice(prevTranscriptRef.current.length);
    if (newChunk) onTranscript(newChunk);
    prevTranscriptRef.current = transcript;
  }, [transcript, onTranscript, mode]);

  const prevListeningRef = useRef(false);
  useEffect(() => {
    if (mode !== 'webspeech') return;
    if (prevListeningRef.current && !wsListening) {
      prevTranscriptRef.current = '';
      onStop?.();
    } else if (!prevListeningRef.current && wsListening) {
      onStart?.();
    }
    prevListeningRef.current = wsListening;
  }, [wsListening, onStart, onStop, mode]);

  useEffect(() => {
    if (mode !== 'webspeech' || !wsError) return;
    // Translate cryptic browser error codes into actionable messages
    const msg =
      wsError === 'network'
        ? 'Web Speech blocked (BMW network). Run scripts/whisper-sidecar.py for local STT.'
        : wsError === 'not-allowed'
        ? 'Microphone access denied — allow mic in browser settings.'
        : wsError === 'no-speech'
        ? 'No speech detected.'
        : `Speech recognition error: ${wsError}`;
    onError?.(msg);
  }, [wsError, onError, mode]);

  // ── mlx-whisper path ─────────────────────────────────────────────────────────
  const mlx = useMlxWhisperBridge({ mode, onTranscript, onStart, onStop, onError });

  // ── Unified return ────────────────────────────────────────────────────────────
  if (mode === 'none') return NONE_RESULT;
  if (mode === 'mlxwhisper') return mlx;

  // webspeech
  return {
    isListening: wsListening,
    start: startListening,
    stop: stopListening,
    supported: wsSupported,
    mode: 'webspeech',
    liveTranscript: transcript ?? '',
    showPrivacyWarning: true,
  };
}
