/**
 * PanelLayer.tsx — Slide-in side panel host for Phase J3.
 *
 * Renders a right-side drawer that slides in over the shell content.
 * The panel is identified by its ID; the content is passed as children.
 * Clicking the backdrop or pressing Escape closes the panel.
 */

import { useEffect, type ReactNode } from 'react';
import { usePanelStore } from './panelStore';
import './PanelLayer.css';

interface PanelLayerProps {
  id: string;
  title: string;
  children: ReactNode;
  /** Width of the panel (default: 440px) */
  width?: number;
}

export function PanelLayer({ id, title, children, width = 440 }: PanelLayerProps) {
  const { openPanel, closePanel } = usePanelStore();
  const isOpen = openPanel === id;

  // Close on Escape key
  useEffect(() => {
    if (!isOpen) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') closePanel();
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [isOpen, closePanel]);

  return (
    <>
      {/* Backdrop — semi-transparent, closes panel on click */}
      <div
        className={`jarvis-panel-backdrop ${isOpen ? 'open' : ''}`}
        aria-hidden="true"
        onClick={closePanel}
      />

      {/* Drawer */}
      <aside
        className={`jarvis-panel-drawer ${isOpen ? 'open' : ''}`}
        style={{ width }}
        role="dialog"
        aria-modal="true"
        aria-label={title}
        aria-hidden={!isOpen}
      >
        {/* Header */}
        <div className="jarvis-panel-header">
          <span className="jarvis-panel-title">{title}</span>
          <button
            className="jarvis-icon-btn jarvis-panel-close"
            onClick={closePanel}
            aria-label={`Close ${title}`}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none"
              stroke="currentColor" strokeWidth={2} strokeLinecap="round">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="jarvis-panel-content">
          {children}
        </div>
      </aside>
    </>
  );
}
