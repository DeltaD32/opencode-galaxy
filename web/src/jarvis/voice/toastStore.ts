/**
 * toastStore.ts — Zustand toast queue for JARVIS.
 *
 * Toasts stack top-right, max 4 visible, 6s auto-dismiss, hover-pause.
 * Each toast has a progress bar that depletes over its lifetime.
 *
 * Usage:
 *   const { push } = useToastStore();
 *   push({ message: 'STT active', level: 'info' });
 */

import { create } from 'zustand';

// ─── Types ────────────────────────────────────────────────────────────────────

export type ToastLevel = 'info' | 'success' | 'warning' | 'error';

export interface Toast {
  id: string;
  message: string;
  level: ToastLevel;
  /** ms until auto-dismiss — default 6000 */
  duration: number;
  /** epoch ms when the toast was created (used for progress bar) */
  createdAt: number;
  /** true while user hovers — pauses countdown */
  paused: boolean;
  /** remaining ms when paused — tracks partial consumption */
  remaining: number;
}

interface ToastState {
  toasts: Toast[];
  push: (opts: { message: string; level?: ToastLevel; duration?: number }) => string;
  dismiss: (id: string) => void;
  pauseToast: (id: string) => void;
  resumeToast: (id: string) => void;
  tick: (id: string, elapsed: number) => void;
}

// ─── Store ────────────────────────────────────────────────────────────────────

export const useToastStore = create<ToastState>((set, get) => ({
  toasts: [],

  push({ message, level = 'info', duration = 6000 }) {
    const id = `toast-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
    const toast: Toast = {
      id,
      message,
      level,
      duration,
      createdAt: Date.now(),
      paused: false,
      remaining: duration,
    };
    set((s) => ({
      // Cap at 4 visible — drop oldest if over limit
      toasts: [...s.toasts.slice(-3), toast],
    }));
    return id;
  },

  dismiss(id) {
    set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) }));
  },

  pauseToast(id) {
    set((s) => ({
      toasts: s.toasts.map((t) => (t.id === id ? { ...t, paused: true } : t)),
    }));
  },

  resumeToast(id) {
    set((s) => ({
      toasts: s.toasts.map((t) =>
        t.id === id ? { ...t, paused: false, createdAt: Date.now() } : t,
      ),
    }));
  },

  tick(id, elapsed) {
    const { toasts, dismiss } = get();
    const toast = toasts.find((t) => t.id === id);
    if (!toast || toast.paused) return;
    const next = toast.remaining - elapsed;
    if (next <= 0) {
      dismiss(id);
    } else {
      set((s) => ({
        toasts: s.toasts.map((t) => (t.id === id ? { ...t, remaining: next } : t)),
      }));
    }
  },
}));
