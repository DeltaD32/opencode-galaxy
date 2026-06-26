import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

// Global styles
import "./styles/index.css";

// JARVIS theme tokens (must load before any theme CSS so :root defaults are set)
import "./jarvis/theme/jarvisThemeTokens.css";

// Theme variants (loaded all at once; `data-jarvis-theme` attr on <html> activates the right one)
import "./jarvis/theme/themes/observatory.css";
import "./jarvis/theme/themes/cel-shade.css";
import "./jarvis/theme/themes/blueprint.css";
import "./jarvis/theme/themes/synthwave.css";
import "./jarvis/theme/themes/forge.css";
import "./jarvis/theme/themes/black-ice.css";
import "./jarvis/theme/themes/chrome.css";

// JARVIS shell
import { JarvisShell } from "./jarvis/JarvisShell";
import { SessionProvider } from "./jarvis/session/SessionContext";
import { initTheme } from "./jarvis/theme/themeStore";
import { ensureAudioUnlocked } from "./jarvis/voice/audioUnlock";

// Apply stored theme immediately before first paint to prevent flash
initTheme();

// Register one-shot listener: unlocks browser autoplay on first user gesture.
// Must be called before any TTS play() attempt.
ensureAudioUnlocked();

const root = document.getElementById("root");
if (!root) throw new Error("Root element #root not found");

createRoot(root).render(
  <StrictMode>
    <SessionProvider>
      <JarvisShell />
    </SessionProvider>
  </StrictMode>,
);
