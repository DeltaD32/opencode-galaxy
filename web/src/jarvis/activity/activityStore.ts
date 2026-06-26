import { create } from 'zustand';

export interface ActivityStep {
  id: string;          // callID from SSE
  tool: string;        // tool name e.g. "bash", "read"
  title: string;       // human-readable title
  status: 'pending' | 'running' | 'completed' | 'error';
  input?: unknown;
  output?: string;
  startedAt: number;   // Date.now()
  completedAt?: number;
}

interface ActivityState {
  steps: ActivityStep[];
  visible: boolean;
  dismissCountdown: number | null;  // absolute timestamp of when dismiss fires, or null
  hovered: boolean;

  // Actions
  addStep: (step: ActivityStep) => void;
  updateStep: (id: string, patch: Partial<ActivityStep>) => void;
  clearSteps: () => void;
  show: () => void;
  hide: () => void;
  startDismissCountdown: () => void;
  pauseDismissCountdown: () => void;
  resumeDismissCountdown: () => void;
  setHovered: (hovered: boolean) => void;
  forceClose: () => void;
}

export const useActivityStore = create<ActivityState>((set, get) => {
  let dismissTimer: ReturnType<typeof setTimeout> | null = null;
  let countdownStart: number | null = null;
  let remainingMs = 15000;

  const clearTimer = () => {
    if (dismissTimer) {
      clearTimeout(dismissTimer);
      dismissTimer = null;
    }
  };

  return {
    steps: [],
    visible: false,
    dismissCountdown: null,
    hovered: false,

    addStep: (step) =>
      set((s) => ({
        steps: [...s.steps, step],
        visible: true,
        dismissCountdown: null,
      })),

    updateStep: (id, patch) =>
      set((s) => ({
        steps: s.steps.map((step) =>
          step.id === id ? { ...step, ...patch } : step
        ),
      })),

    clearSteps: () => set({ steps: [] }),

    show: () => set({ visible: true }),

    hide: () => {
      clearTimer();
      set({ visible: false, dismissCountdown: null });
    },

    startDismissCountdown: () => {
      clearTimer();
      remainingMs = 15000;
      countdownStart = Date.now();
      set({ dismissCountdown: Date.now() + remainingMs });
      dismissTimer = setTimeout(() => {
        if (!get().hovered) {
          set({ visible: false, dismissCountdown: null });
        }
      }, remainingMs);
    },

    pauseDismissCountdown: () => {
      if (dismissTimer && countdownStart !== null) {
        const elapsed = Date.now() - countdownStart;
        remainingMs = Math.max(0, remainingMs - elapsed);
        clearTimer();
      }
    },

    resumeDismissCountdown: () => {
      if (remainingMs > 0 && get().dismissCountdown !== null) {
        countdownStart = Date.now();
        set({ dismissCountdown: Date.now() + remainingMs });
        dismissTimer = setTimeout(() => {
          set({ visible: false, dismissCountdown: null });
        }, remainingMs);
      }
    },

    setHovered: (hovered) => {
      const prev = get().hovered;
      set({ hovered });
      if (!prev && hovered) get().pauseDismissCountdown();
      if (prev && !hovered) get().resumeDismissCountdown();
    },

    forceClose: () => {
      clearTimer();
      set({ visible: false, dismissCountdown: null, steps: [] });
    },
  };
});
