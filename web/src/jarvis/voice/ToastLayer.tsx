/**
 * ToastLayer.tsx — floating toast stack for JARVIS.
 *
 * Renders up to 4 toasts top-right, each with:
 *   - Level accent bar (info/success/warning/error)
 *   - Icon
 *   - Message text
 *   - Auto-dismiss progress bar (pauses on hover)
 *   - Manual dismiss button
 *
 * Driven by useToastStore (Zustand). Mount once in JarvisShell.
 */

import { useEffect, useRef, useState } from 'react';
import { useToastStore, type Toast, type ToastLevel } from './toastStore';
import './ToastLayer.css';

// ─── Level icons ─────────────────────────────────────────────────────────────

function ToastIcon({ level }: { level: ToastLevel }) {
  switch (level) {
    case 'success':
      return (
        <svg className="jarvis-toast-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.2} strokeLinecap="round" strokeLinejoin="round">
          <polyline points="20 6 9 17 4 12" />
        </svg>
      );
    case 'warning':
      return (
        <svg className="jarvis-toast-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.2} strokeLinecap="round" strokeLinejoin="round">
          <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
          <line x1="12" y1="9" x2="12" y2="13" />
          <line x1="12" y1="17" x2="12.01" y2="17" />
        </svg>
      );
    case 'error':
      return (
        <svg className="jarvis-toast-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.2} strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="12" r="10" />
          <line x1="12" y1="8" x2="12" y2="12" />
          <line x1="12" y1="16" x2="12.01" y2="16" />
        </svg>
      );
    default:
      return (
        <svg className="jarvis-toast-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.2} strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="12" r="10" />
          <line x1="12" y1="8" x2="12" y2="8.01" />
          <line x1="12" y1="12" x2="12" y2="16" />
        </svg>
      );
  }
}

// ─── Single toast item ────────────────────────────────────────────────────────

function ToastItem({ toast }: { toast: Toast }) {
  const { dismiss, pauseToast, resumeToast, tick } = useToastStore();
  const [leaving, setLeaving] = useState(false);
  const rafRef = useRef<number>(0);
  const lastTickRef = useRef<number>(Date.now());

  // rAF countdown loop — ticks the store every frame while alive
  useEffect(() => {
    function frame() {
      const now = Date.now();
      const elapsed = now - lastTickRef.current;
      lastTickRef.current = now;
      tick(toast.id, elapsed);
      rafRef.current = requestAnimationFrame(frame);
    }
    rafRef.current = requestAnimationFrame(frame);
    return () => cancelAnimationFrame(rafRef.current);
  }, [toast.id, tick]);

  const handleDismiss = () => {
    setLeaving(true);
    setTimeout(() => dismiss(toast.id), 180);
  };

  const progressPct = (toast.remaining / toast.duration) * 100;

  return (
    <div
      className={`jarvis-toast${leaving ? ' leaving' : ''}`}
      data-level={toast.level}
      role="status"
      aria-live="polite"
      onMouseEnter={() => pauseToast(toast.id)}
      onMouseLeave={() => resumeToast(toast.id)}
    >
      <ToastIcon level={toast.level} />
      <span className="jarvis-toast-message">{toast.message}</span>
      <button
        className="jarvis-toast-dismiss"
        onClick={handleDismiss}
        aria-label="Dismiss notification"
        title="Dismiss"
      >
        ×
      </button>
      <div
        className="jarvis-toast-progress"
        style={{ width: `${progressPct}%` }}
        aria-hidden="true"
      />
    </div>
  );
}

// ─── Toast layer ──────────────────────────────────────────────────────────────

export function ToastLayer() {
  const toasts = useToastStore((s) => s.toasts);

  if (toasts.length === 0) return null;

  return (
    <div className="jarvis-toast-layer" aria-label="Notifications" role="region">
      {toasts.map((t) => (
        <ToastItem key={t.id} toast={t} />
      ))}
    </div>
  );
}
