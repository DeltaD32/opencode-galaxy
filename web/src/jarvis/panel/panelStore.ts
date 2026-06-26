/**
 * panelStore.ts — Zustand store for the JARVIS slide-in panel system.
 *
 * Panels are identified by string IDs. Only one panel can be open at a time
 * (accordion pattern — toggling one closes any currently open panel).
 *
 * Known panel IDs:
 *   'galaxy'   — GalaxyView (agent knowledge graph)
 *   'settings' — Theme / STT / TTS configuration
 */

import { create } from 'zustand';

interface PanelState {
  /** Currently open panel ID, or null if all panels are closed. */
  openPanel: string | null;

  /** Open a specific panel; close it if it's already open. */
  togglePanel: (id: string) => void;

  /** Force-close whatever panel is open. */
  closePanel: () => void;
}

export const usePanelStore = create<PanelState>((set) => ({
  openPanel: null,

  togglePanel: (id) =>
    set((state) => ({
      openPanel: state.openPanel === id ? null : id,
    })),

  closePanel: () => set({ openPanel: null }),
}));
