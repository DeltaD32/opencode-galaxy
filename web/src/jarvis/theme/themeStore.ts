import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export type JarvisTheme =
  | 'observatory'
  | 'cel-shade'
  | 'blueprint'
  | 'synthwave'
  | 'forge'
  | 'black-ice'
  | 'chrome';

export const JARVIS_THEMES: { id: JarvisTheme; label: string }[] = [
  { id: 'observatory', label: 'Observatory' },
  { id: 'cel-shade',   label: 'Cel-Shade' },
  { id: 'blueprint',   label: 'Blueprint' },
  { id: 'synthwave',   label: 'Synthwave' },
  { id: 'forge',       label: 'Forge' },
  { id: 'black-ice',   label: 'Black Ice' },
  { id: 'chrome',      label: 'Chrome' },
];

interface ThemeState {
  theme: JarvisTheme;
  blinking: boolean;
  setTheme: (theme: JarvisTheme) => void;
}

export const useThemeStore = create<ThemeState>()(
  persist(
    (set, get) => ({
      theme: 'observatory',
      blinking: false,

      setTheme: (newTheme: JarvisTheme) => {
        if (get().theme === newTheme) return;

        // Blink transition: overlay fades in (150ms), variables swap, overlay fades out (300ms)
        set({ blinking: true });

        setTimeout(() => {
          // Swap the data-jarvis-theme attribute on <html>
          document.documentElement.setAttribute('data-jarvis-theme', newTheme);
          set({ theme: newTheme });

          setTimeout(() => {
            set({ blinking: false });
          }, 300);
        }, 150);
      },
    }),
    {
      name: 'jarvis-theme',
      partialize: (state) => ({ theme: state.theme }),
      onRehydrateStorage: () => (state) => {
        // Apply persisted theme immediately on load
        if (state?.theme) {
          document.documentElement.setAttribute('data-jarvis-theme', state.theme);
        }
      },
    }
  )
);

/** Call once on app boot to set the initial theme attribute. */
export function initTheme(): void {
  const stored = localStorage.getItem('jarvis-theme');
  let theme: JarvisTheme = 'observatory';
  if (stored) {
    try {
      const parsed = JSON.parse(stored);
      if (parsed?.state?.theme) theme = parsed.state.theme;
    } catch { /* ignore */ }
  }
  document.documentElement.setAttribute('data-jarvis-theme', theme);
}
