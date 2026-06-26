/**
 * settingsStore.ts — Persistent JARVIS user preferences (localStorage).
 *
 * Covers:
 *   - ttsEnabled: whether TTS speaks agent responses aloud
 *   - sttModel: which whisper model the sidecar should load
 *     (stored here; VoiceController reads it on sidecar health-probe)
 *
 * NOTE: Changing sttModel requires restarting the sidecar — the frontend
 * shows a reminder banner when the selected model differs from the running one.
 */

import { create } from 'zustand';

export type WhisperModel =
  | 'mlx-community/whisper-small-mlx'
  | 'mlx-community/distil-whisper-large-v3';

interface SettingsState {
  /** Speak JARVIS responses aloud via TTS pipeline. Default: true. */
  ttsEnabled: boolean;
  /** Whisper model to use in sidecar. Default: small (recommended for PTT). */
  sttModel: WhisperModel;

  setTtsEnabled: (v: boolean) => void;
  setSttModel: (m: WhisperModel) => void;
}

// ── Persist to localStorage ────────────────────────────────────────────────────

function load<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(`jarvis.settings.${key}`);
    if (raw == null) return fallback;
    return JSON.parse(raw) as T;
  } catch {
    return fallback;
  }
}

function save<T>(key: string, value: T): void {
  try {
    localStorage.setItem(`jarvis.settings.${key}`, JSON.stringify(value));
  } catch {
    // storage may be unavailable in some contexts — ignore
  }
}

// ── Store ──────────────────────────────────────────────────────────────────────

export const useSettingsStore = create<SettingsState>((set) => ({
  ttsEnabled: load<boolean>('ttsEnabled', true),
  sttModel:   load<WhisperModel>('sttModel', 'mlx-community/whisper-small-mlx'),

  setTtsEnabled: (v) => {
    save('ttsEnabled', v);
    set({ ttsEnabled: v });
  },
  setSttModel: (m) => {
    save('sttModel', m);
    set({ sttModel: m });
  },
}));
