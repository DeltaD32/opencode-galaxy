import { useEffect, useRef, useState } from 'react';
import { useActivityStore } from './activityStore';
import { useSSE } from '../../hooks/useSSE';
import type { ToolPart } from '../../types/opencode';
import './ActivityModal.css';

/**
 * ActivityModal — shows JARVIS tool-call steps while the agent is working.
 * Floats bottom-right. Auto-dismisses 15s after session goes idle.
 * Hover pauses countdown.
 *
 * SSE wiring notes (opencode 1.17.5):
 *   - Tool steps come from `message.part.updated` where `properties.part` is a
 *     `ToolPart` with shape: { type:"tool", tool, callID, state:{ status, input, output, title } }
 *   - Session idle fires as `session.idle` with `properties: { sessionID }` — no payload needed.
 *   - `session.status` with `status.type === "idle"` is also emitted; we handle both.
 */
export function ActivityModal() {
  const {
    steps,
    visible,
    dismissCountdown,
    addStep,
    updateStep,
    startDismissCountdown,
    setHovered,
    forceClose,
  } = useActivityStore();

  const [mounted, setMounted] = useState(false);
  const [exiting, setExiting] = useState(false);
  const [countdownWidth, setCountdownWidth] = useState(100); // percent 0–100
  const countdownRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Listen to SSE events to populate steps
  useSSE((event) => {
    if (event.type === 'message.part.updated') {
      const { part } = event.properties;

      // Only process tool parts
      if (part.type !== 'tool') return;

      // TypeScript narrowing: part is ToolPart here
      const toolPart = part as ToolPart;
      const { callID, tool, state: toolState } = toolPart;

      const existing = steps.find((s) => s.id === callID);

      if (!existing) {
        addStep({
          id: callID,
          tool: tool ?? 'tool',
          title: toolState?.title ?? tool ?? 'Running…',
          status:
            toolState?.status === 'completed'
              ? 'completed'
              : toolState?.status === 'error'
              ? 'error'
              : toolState?.status === 'pending'
              ? 'pending'
              : 'running',
          input: toolState?.input,
          output: toolState?.output,
          startedAt: Date.now(),
        });
      } else {
        updateStep(callID, {
          status: toolState?.status ?? 'running',
          title: toolState?.title ?? existing.title,
          completedAt:
            toolState?.status === 'completed' ? Date.now() : undefined,
        });
      }
    }

    // session.idle — start auto-dismiss countdown
    if (event.type === 'session.idle') {
      startDismissCountdown();
    }

    // session.status with idle subtype — belt-and-suspenders
    if (
      event.type === 'session.status' &&
      event.properties.status.type === 'idle'
    ) {
      startDismissCountdown();
    }
  });

  // Mount / unmount with entrance + exit animation
  useEffect(() => {
    if (visible) {
      setExiting(false);
      setMounted(true);
    } else if (mounted) {
      setExiting(true);
      const t = setTimeout(() => {
        setMounted(false);
        setExiting(false);
      }, 200);
      return () => clearTimeout(t);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [visible]);

  // Countdown bar — interpolate width from dismissCountdown timestamp
  useEffect(() => {
    if (dismissCountdown === null) {
      setCountdownWidth(100);
      if (countdownRef.current) clearInterval(countdownRef.current);
      return;
    }

    const total = 15_000;
    const updateInterval = 100;

    countdownRef.current = setInterval(() => {
      const remaining = dismissCountdown - Date.now();
      const pct = Math.max(0, (remaining / total) * 100);
      setCountdownWidth(pct);
      if (pct <= 0 && countdownRef.current) {
        clearInterval(countdownRef.current);
      }
    }, updateInterval);

    return () => {
      if (countdownRef.current) clearInterval(countdownRef.current);
    };
  }, [dismissCountdown]);

  if (!mounted) return null;

  return (
    <div
      className={`jarvis-activity-modal ${exiting ? 'jarvis-activity-modal-exit' : 'jarvis-activity-modal-enter'}`}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      role="status"
      aria-label="Agent activity"
    >
      {/* Countdown bar — depletes left-to-right via scaleX */}
      <div
        className="jarvis-activity-countdown"
        style={{ transform: `scaleX(${countdownWidth / 100})` }}
        aria-hidden="true"
      />

      {/* Header */}
      <div className="jarvis-activity-header">
        <span className="jarvis-activity-title">Agent Activity</span>
        <button
          className="jarvis-activity-close"
          onClick={forceClose}
          aria-label="Close activity panel"
        >
          <svg
            width="10"
            height="10"
            viewBox="0 0 10 10"
            fill="none"
            stroke="currentColor"
            strokeWidth={1.5}
          >
            <path strokeLinecap="round" d="M1 1l8 8M9 1L1 9" />
          </svg>
        </button>
      </div>

      {/* Steps list */}
      <div className="jarvis-activity-steps" role="list">
        {steps.length === 0 ? (
          <div className="jarvis-activity-step">
            <div className="jarvis-activity-step-icon" data-status="running" />
            <div className="jarvis-activity-step-content">
              <div className="jarvis-activity-step-tool">Working…</div>
            </div>
          </div>
        ) : (
          steps.map((step) => (
            <div key={step.id} className="jarvis-activity-step" role="listitem">
              <div
                className="jarvis-activity-step-icon"
                data-status={step.status}
              />
              <div className="jarvis-activity-step-content">
                <div className="jarvis-activity-step-tool">{step.tool}</div>
                {step.title && (
                  <div className="jarvis-activity-step-title">{step.title}</div>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
