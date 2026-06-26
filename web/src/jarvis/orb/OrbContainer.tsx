import { useEffect, useMemo } from 'react';
import { Canvas2DOrb } from './Canvas2DOrb';
import { VoxCorona } from './VoxCorona';
import { useSttContext } from '../input/SttContext';
import type { OrbState } from './particleState';
// Note: SVG ring overlay removed — rings are now drawn directly on the Canvas2D
// surface to avoid the CSS-transform / SVG-transform coordinate conflict.

interface Props {
  state: OrbState;
  label?: string;
}

export function OrbContainer({ state, label = 'How can I help?' }: Props) {
  const { liveTranscript } = useSttContext();
  // Stable waveform bar specs — computed once so heights don't jump on re-render
  const waveformBars = useMemo(
    () =>
      Array.from({ length: 20 }, (_, i) => ({
        duration: 0.4 + Math.random() * 0.6,
        delay: i * 0.05,
        height: 30 + Math.random() * 70,
      })),
    [] // empty deps: stable for the lifetime of the component
  );

  // Inject keyframe animations once into document (breathe + waveform only;
  // rings are now drawn on canvas so no ring-spin keyframes needed)
  useEffect(() => {
    const styleId = 'jarvis-orb-keyframes';
    if (document.getElementById(styleId)) return;

    const style = document.createElement('style');
    style.id = styleId;
    style.textContent = `
      @keyframes jarvis-orb-breathe {
        0%, 100% { opacity: 0.82; }
        50%      { opacity: 1; }
      }
      @keyframes jarvis-waveform-bar {
        from { transform: scaleY(0.3); }
        to   { transform: scaleY(1); }
      }
    `;
    document.head.appendChild(style);
  }, []);

  const stateLabel: Record<OrbState, string> = {
    IDLE: label,
    LISTENING: 'listening…',
    THINKING: 'thinking…',
    SPEAKING: 'speaking…',
  };

  return (
    <div className="flex flex-col items-center gap-4">
      {/* The orb itself + Three.js vox corona overlay */}
      <div
        style={{
          position: 'relative',
          width: 320,
          height: 320,
          animation: state === 'IDLE' ? 'jarvis-orb-breathe 4s ease-in-out infinite' : 'none',
        }}
      >
        <Canvas2DOrb state={state} size={320} />
        {/* VoxCorona (Three.js InstancedMesh) — SPEAKING only, per spec */}
        {state === 'SPEAKING' && <VoxCorona state={state} size={320} />}
      </div>

      {/* Waveform placeholder — visible in LISTENING state */}
      {state === 'LISTENING' && (
        <div
          className="flex items-end gap-0.5"
          style={{ height: 20, opacity: 1, transition: 'opacity 200ms ease' }}
          aria-label="Listening waveform"
        >
          {waveformBars.map((bar, i) => (
            <div
              key={i}
              style={{
                width: 3,
                borderRadius: 2,
                backgroundColor: 'var(--jarvis-listen-particle)',
                animation: `jarvis-waveform-bar ${bar.duration}s ease-in-out infinite alternate`,
                animationDelay: `${bar.delay}s`,
                height: `${bar.height}%`,
              }}
            />
          ))}
        </div>
      )}

      {/* Live transcript — shown while LISTENING, fades in as words arrive */}
      <p
        style={{
          minHeight: '1.4em',
          maxWidth: 320,
          textAlign: 'center',
          fontSize: 14,
          fontStyle: 'italic',
          color: 'var(--jarvis-text-accent)',
          opacity: state === 'LISTENING' && liveTranscript ? 1 : 0,
          transition: 'opacity 200ms ease',
          letterSpacing: '0.02em',
          lineHeight: 1.4,
          userSelect: 'none',
          whiteSpace: 'pre-wrap',
          wordBreak: 'break-word',
        }}
        aria-live="polite"
        aria-label="Live speech transcript"
      >
        {liveTranscript || ' '}
      </p>

      {/* Status label */}
      <p
        className="text-sm font-light tracking-widest select-none"
        style={{
          color: state === 'IDLE' ? 'var(--jarvis-text-secondary)' : 'var(--jarvis-text-accent)',
          textTransform: 'uppercase',
          letterSpacing: '0.15em',
          transition: 'color 300ms ease',
        }}
      >
        {stateLabel[state]}
      </p>
    </div>
  );
}
