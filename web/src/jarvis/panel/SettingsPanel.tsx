/**
 * SettingsPanel.tsx — Phase J3: Settings drawer (Panel #2).
 *
 * Controls:
 *   - TTS on/off toggle
 *   - STT model selection (whisper-small-mlx vs distil-whisper-large-v3)
 *   - Active theme info (theme switching still via top-bar dots)
 *   - Running sidecar status
 */

import { PanelLayer } from './PanelLayer';
import { useSettingsStore, type WhisperModel } from './settingsStore';
import { useThemeStore, JARVIS_THEMES } from '../theme/themeStore';
import './PanelLayer.css'; // already loaded, import for clarity

const WHISPER_MODELS: { id: WhisperModel; label: string; size: string; note: string }[] = [
  {
    id:    'mlx-community/whisper-small-mlx',
    label: 'whisper-small-mlx',
    size:  '~490 MB',
    note:  'Recommended — fast PTT latency',
  },
  {
    id:    'mlx-community/distil-whisper-large-v3',
    label: 'distil-whisper-large-v3',
    size:  '~750 MB',
    note:  'Higher accuracy, slightly slower',
  },
];

export function SettingsPanel() {
  const { ttsEnabled, setTtsEnabled, sttModel, setSttModel } = useSettingsStore();
  const { theme } = useThemeStore();
  const activeTheme = JARVIS_THEMES.find((t) => t.id === theme);

  return (
    <PanelLayer id="settings" title="Settings" width={360}>

      {/* ── TTS ──────────────────────────────────────────────────── */}
      <div className="jarvis-panel-section">
        <div className="jarvis-panel-section-label">Voice Output (TTS)</div>
        <div className="jarvis-settings-row">
          <div>
            <div className="jarvis-settings-row-label">Speak responses aloud</div>
            <div className="jarvis-settings-row-sub">Uses macOS say or BMW Audio TTS API</div>
          </div>
          <label className="jarvis-toggle" aria-label="Toggle TTS">
            <input
              type="checkbox"
              checked={ttsEnabled}
              onChange={(e) => setTtsEnabled(e.target.checked)}
            />
            <span className="jarvis-toggle-track" />
          </label>
        </div>
      </div>

      {/* ── STT Model ────────────────────────────────────────────── */}
      <div className="jarvis-panel-section">
        <div className="jarvis-panel-section-label">Voice Input (STT) — Whisper Model</div>
        <div
          className="jarvis-settings-row-sub"
          style={{ marginBottom: 10 }}
        >
          Changing model requires restarting the sidecar:
          <br />
          <code style={{ fontSize: 10, color: 'rgba(255,255,255,0.5)' }}>
            python scripts/whisper-sidecar.py --model &lt;id&gt;
          </code>
        </div>
        <div className="jarvis-model-pills">
          {WHISPER_MODELS.map((m) => (
            <button
              key={m.id}
              className={`jarvis-model-pill ${sttModel === m.id ? 'selected' : ''}`}
              onClick={() => setSttModel(m.id)}
              title={`${m.size} — ${m.note}`}
            >
              {m.label}
            </button>
          ))}
        </div>
        {WHISPER_MODELS.map((m) => sttModel === m.id && (
          <div
            key={m.id}
            className="jarvis-settings-row-sub"
            style={{ marginTop: 8 }}
          >
            {m.size} · {m.note}
          </div>
        ))}
      </div>

      {/* ── Theme ────────────────────────────────────────────────── */}
      <div className="jarvis-panel-section">
        <div className="jarvis-panel-section-label">Active Theme</div>
        <div className="jarvis-settings-row-label" style={{ marginBottom: 4 }}>
          {activeTheme?.label ?? theme}
        </div>
        <div className="jarvis-settings-row-sub">
          Switch themes via the colour dots in the top bar.
        </div>
      </div>

      {/* ── Keyboard shortcuts ───────────────────────────────────── */}
      <div className="jarvis-panel-section">
        <div className="jarvis-panel-section-label">Keyboard Shortcuts</div>
        {[
          ['CMD+SHIFT+SPACE', 'Push-to-talk (PTT)'],
          ['Hold SPACE', 'PTT (when no input focused)'],
          ['Escape', 'Close panel'],
        ].map(([key, desc]) => (
          <div key={key} className="jarvis-settings-row" style={{ marginBottom: 6 }}>
            <span className="jarvis-settings-row-sub">{desc}</span>
            <kbd style={{
              fontSize: 10,
              fontFamily: "'SF Mono', monospace",
              padding: '2px 6px',
              borderRadius: 4,
              border: '1px solid rgba(255,255,255,0.15)',
              color: 'rgba(255,255,255,0.5)',
              background: 'rgba(255,255,255,0.05)',
              whiteSpace: 'nowrap',
            }}>
              {key}
            </kbd>
          </div>
        ))}
      </div>

      {/* ── Version ─────────────────────────────────────────────── */}
      <div className="jarvis-panel-section" style={{ opacity: 0.4 }}>
        <div className="jarvis-settings-row-sub">
          JARVIS Phase J3 · OpenCode BMW
        </div>
      </div>
    </PanelLayer>
  );
}
