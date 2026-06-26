/**
 * JarvisShell.tsx — JARVIS Phase 1 root shell.
 *
 * Replaces App.tsx as the entry point. Renders:
 *   - The JARVIS orb (Canvas 2D gyroscope rings + particle field)
 *   - Response/chat area below the orb
 *   - InputBar (text + PTT)
 *   - ActivityModal (tool-call steps, bottom-right)
 *   - Theme blink overlay
 *   - Permission dialog (blocking modal)
 *   - Top bar: mission badge + theme picker + settings stub
 *
 * Galaxy (GalaxyView.tsx) is untouched — it becomes Panel #1 in Phase 3.
 */

import { useCallback, useState } from 'react';
import { OrbContainer } from './orb/OrbContainer';
import { ActivityModal } from './activity/ActivityModal';
import { InputBar } from './input/InputBar';
import { VoiceController } from './voice/VoiceController';
import { ToastLayer } from './voice/ToastLayer';
import { useSessionContext } from './session/SessionContext';
import { useThemeStore, JARVIS_THEMES, type JarvisTheme } from './theme/themeStore';
import { usePanelStore } from './panel/panelStore';
import { GalaxyPanel } from './panel/GalaxyPanel';
import { SettingsPanel } from './panel/SettingsPanel';
import type { AgentStatus } from '../lib/db-reader';
import { ChatThread } from '../components/ChatThread';
import { PermissionDialog } from '../components/PermissionDialog';
import './JarvisShell.css';

// ─── Theme dot colours (hard-coded so they show even without theme CSS) ──────

const THEME_DOT_COLORS: Record<JarvisTheme, string> = {
  'observatory': '#4d8df6',
  'cel-shade':   '#38bdf8',
  'blueprint':   '#36d6e7',
  'synthwave':   '#c44af0',
  'forge':       '#ff6420',
  'black-ice':   '#8ab0d0',
  'chrome':      '#8090a8',
};

// ─── JarvisShell ─────────────────────────────────────────────────────────────

export function JarvisShell() {
  const {
    // Sessions
    activeSessionID,
    createSession,

    // Messages
    messages,
    streaming,
    isBusy,
    lastTurnCost,
    sendMessage,
    abortSession,

    // Permissions
    pendingPermissions,
    replyAllow,
    replyDeny,

    // Mission control
    agentTotal,
    agentBusy,
    agentStatuses,

    // Orb
    orbState,

    // UI selection
    selectedAgent,
  } = useSessionContext();

  const { theme, blinking, setTheme } = useThemeStore();
  const { openPanel, togglePanel } = usePanelStore();

  // ── Send handler — lazy session creation ──────────────────────────────────
  // Do NOT auto-create a session on mount. Sessions are created on first send.
  // This avoids the race where a blank session gets set as activeSessionID
  // before the existing session list finishes loading from the API.
  const handleSend = useCallback(
    async (text: string) => {
      if (!text.trim()) return;
      // If no active session yet, create one now (first message in this window)
      if (!activeSessionID) {
        await createSession();
      }
      await sendMessage(text, selectedAgent);
    },
    [activeSessionID, createSession, sendMessage, selectedAgent],
  );

  const handleAbort = useCallback(() => {
    if (activeSessionID) abortSession(activeSessionID);
  }, [activeSessionID, abortSession]);

  // ── First pending permission ────────────────────────────────────────────────
  const firstPermission = pendingPermissions[0];

  // ── Panel state ─────────────────────────────────────────────────────────────
  const panelOpen = openPanel !== null;

  return (
    // VoiceController wraps the shell so it can publish SttProvider to all children,
    // including InputBar. This ensures only ONE SttBridge instance exists in the tree.
    <VoiceController>
    <div className="jarvis-shell">
      {/* ── Theme blink overlay ───────────────────────────────────────────── */}
      <div
        className={`jarvis-blink-overlay ${
          blinking ? 'fading-in' : 'hidden'
        }`}
        aria-hidden="true"
      />

      {/* ── Top chrome bar ────────────────────────────────────────────────── */}
      <header className="jarvis-topbar" aria-label="JARVIS status bar">
        {/* Mission badge — live agent status from blackboard sections */}
        <div className="jarvis-mission-badge" aria-label="Agent status">
          {agentStatuses.length === 0 ? (
            // Fallback while statuses are loading — show raw SSE count
            <>
              <span className={`jarvis-mission-dot ${agentBusy > 0 ? 'busy' : ''}`} aria-hidden="true" />
              <span style={{ color: 'var(--jarvis-text-secondary)' }}>
                {agentTotal} agent{agentTotal !== 1 ? 's' : ''}
                {agentBusy > 0 && (
                  <span style={{ color: 'var(--jarvis-ptt-active)', marginLeft: 6 }}>· {agentBusy} busy</span>
                )}
              </span>
            </>
          ) : (
            <AgentStatusBadge statuses={agentStatuses} />
          )}
        </div>

        {/* Right: theme picker + settings stub */}
        <div className="jarvis-topbar-actions">
          {/* Theme picker */}
          <div className="jarvis-theme-picker" aria-label="Theme picker" role="group">
            {JARVIS_THEMES.map((t) => (
              <button
                key={t.id}
                className={`jarvis-theme-dot ${theme === t.id ? 'active' : ''}`}
                style={{ background: THEME_DOT_COLORS[t.id] }}
                onClick={() => setTheme(t.id)}
                aria-label={`Switch to ${t.label} theme`}
                aria-pressed={theme === t.id}
                title={t.label}
              />
            ))}
          </div>

          {/* Galaxy panel toggle */}
          <button
            className={`jarvis-icon-btn ${openPanel === 'galaxy' ? 'active' : ''}`}
            aria-label="Agent knowledge graph"
            aria-pressed={openPanel === 'galaxy'}
            title="Agent Knowledge Graph"
            onClick={() => togglePanel('galaxy')}
          >
            {/* Node graph icon */}
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round">
              <circle cx="12" cy="5"  r="2" />
              <circle cx="5"  cy="19" r="2" />
              <circle cx="19" cy="19" r="2" />
              <line x1="12" y1="7"  x2="5"  y2="17" />
              <line x1="12" y1="7"  x2="19" y2="17" />
              <line x1="5"  y1="19" x2="19" y2="19" />
            </svg>
          </button>

          {/* Settings panel toggle */}
          <button
            className={`jarvis-icon-btn ${openPanel === 'settings' ? 'active' : ''}`}
            aria-label="Settings"
            aria-pressed={openPanel === 'settings'}
            title="Settings"
            onClick={() => togglePanel('settings')}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8}>
              <circle cx="12" cy="12" r="3" />
              <path strokeLinecap="round" d="M12 2v2M12 20v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M2 12h2M20 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42" />
            </svg>
          </button>
        </div>
      </header>

      {/* ── Main content ──────────────────────────────────────────────────── */}
      <main
        className={`jarvis-main ${panelOpen ? 'panel-open' : ''}`}
        style={{ paddingTop: 52, paddingBottom: 80 }}
      >
        {/* ── Orb ─────────────────────────────────────────────────────────── */}
        <div className="jarvis-orb-area">
          <OrbContainer state={orbState} />
        </div>

        {/* ── Response / Chat area ─────────────────────────────────────────── */}
        {activeSessionID && messages.length > 0 && (
          <div className="jarvis-chat-wrapper" aria-label="JARVIS response">
            <ChatThread
              messages={messages}
              streamingMessageID={streaming.messageID}
              streamingText={streaming.text}
              isBusy={isBusy}
              lastTurnCost={lastTurnCost}
            />
          </div>
        )}

        {/* ── Empty state hint ─────────────────────────────────────────────── */}
        {(!activeSessionID || messages.length === 0) && orbState === 'IDLE' && (
          <p
            style={{
              marginTop: 8,
              fontSize: 13,
              color: 'var(--jarvis-text-secondary)',
              letterSpacing: '0.05em',
              userSelect: 'none',
            }}
            aria-live="polite"
          >
            Type a message or hold Space to speak
          </p>
        )}
      </main>

      {/* ── Input bar ─────────────────────────────────────────────────────── */}
      <div className="jarvis-input-area">
        <InputBar
          onSend={handleSend}
          onAbort={handleAbort}
          isBusy={isBusy}
        />
      </div>

      {/* ── Activity modal (tool-call steps, bottom-right) ────────────────── */}
      <ActivityModal />

      {/* ── Toast notifications (top-right stack) ─────────────────────────── */}
      <ToastLayer />

      {/* ── Permission dialog (blocking, truly modal) ─────────────────────── */}
      {firstPermission && (
        <div className="jarvis-permission-backdrop" role="dialog" aria-modal="true">
          <PermissionDialog
            permission={firstPermission}
            onAllow={() => replyAllow(firstPermission)}
            onDeny={() => replyDeny(firstPermission)}
          />
        </div>
      )}
      {/* ── Phase J3 Panels ───────────────────────────────────────────────── */}
      <GalaxyPanel />
      <SettingsPanel />
    </div>
    </VoiceController>
  );
}

// ─── AgentStatusBadge ─────────────────────────────────────────────────────────

const BOARD_STATUS_COLOR: Record<string, string> = {
  executing:          'var(--jarvis-ptt-active, #ffb627)',
  deliberating:       '#eab308',
  'awaiting-approval':'#f97316',
  blocked:            '#ef4444',
  done:               '#6b7280',
};

function agentDotColor(s: AgentStatus): string {
  if (s.status === 'idle') return 'var(--jarvis-text-secondary, #4d8df6)';
  return BOARD_STATUS_COLOR[s.blackboardStatus ?? ''] ?? 'var(--jarvis-ptt-active, #ffb627)';
}

function AgentStatusBadge({ statuses }: { statuses: AgentStatus[] }) {
  const [open, setOpen] = useState(false);
  const active = statuses.filter(s => s.status === 'active');
  const idle   = statuses.filter(s => s.status === 'idle');

  return (
    <div style={{ position: 'relative' }}>
      <button
        className="jarvis-agent-status-trigger"
        onClick={() => setOpen(o => !o)}
        aria-haspopup="true"
        aria-expanded={open}
        title="Agent activity — click to expand"
      >
        {/* Active agent dots */}
        {active.slice(0, 6).map(s => (
          <span
            key={s.agent}
            className="jarvis-mission-dot busy"
            style={{ background: agentDotColor(s) }}
            title={`${s.agent}: ${s.taskDescription ?? 'active'}`}
          />
        ))}
        {/* Idle summary dot */}
        {idle.length > 0 && (
          <span className="jarvis-mission-dot" style={{ opacity: 0.4 }} />
        )}
        <span style={{ color: 'var(--jarvis-text-secondary)', marginLeft: 4 }}>
          {active.length > 0
            ? <><span style={{ color: 'var(--jarvis-ptt-active)' }}>{active.length} active</span> · {idle.length} idle</>
            : <>{idle.length} idle</>
          }
        </span>
      </button>

      {/* Popover */}
      {open && (
        <div className="jarvis-agent-popover" role="dialog" aria-label="Agent status detail">
          {statuses.map(s => (
            <div key={s.agent} className="jarvis-agent-row">
              <span
                className="jarvis-agent-dot"
                style={{ background: agentDotColor(s), opacity: s.status === 'idle' ? 0.35 : 1 }}
              />
              <span className="jarvis-agent-name">{s.agent}</span>
              {s.status === 'active' && s.taskDescription && (
                <span className="jarvis-agent-task" title={s.taskDescription}>
                  {s.blackboardStatus && (
                    <span className="jarvis-agent-board-status">{s.blackboardStatus}</span>
                  )}
                  {s.taskDescription.length > 38
                    ? s.taskDescription.slice(0, 37) + '…'
                    : s.taskDescription}
                </span>
              )}
              {s.status === 'idle' && (
                <span className="jarvis-agent-task" style={{ opacity: 0.4 }}>idle</span>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
