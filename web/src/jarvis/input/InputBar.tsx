import { useState, useCallback, useRef, useEffect, type KeyboardEvent } from 'react';
import { useSttContext } from './SttContext';
import { useSessionContext } from '../session/SessionContext';
import './InputBar.css';

interface Props {
  /** Called when user submits text. */
  onSend: (text: string) => void;
  /** Called when user wants to abort current operation. */
  onAbort?: () => void;
  /** Whether the agent is currently busy. */
  isBusy?: boolean;
  /** Placeholder text. */
  placeholder?: string;
}

export function InputBar({ onSend, onAbort, isBusy = false, placeholder = 'Ask JARVIS…' }: Props) {
  const [text, setText] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const { setOrbState } = useSessionContext();

  // Shared STT bridge — owned by VoiceController, published via SttContext.
  // InputBar reads it from context; never creates its own recognition instance.
  const stt = useSttContext();

  // PTT toggle — click to start/stop
  const handlePttToggle = useCallback(() => {
    if (stt.isListening) {
      stt.stop();
    } else {
      if (!stt.supported) return;
      stt.start();
    }
  }, [stt]);

  // Hold-SPACE = PTT when no text input/textarea/contenteditable is focused
  useEffect(() => {
    const onKeyDown = (e: globalThis.KeyboardEvent) => {
      if (e.code !== 'Space') return;
      const active = document.activeElement as HTMLElement | null;
      const tag = active?.tagName?.toLowerCase();
      if (tag === 'textarea' || tag === 'input' || active?.isContentEditable) return;
      e.preventDefault();
      if (!stt.isListening && stt.supported) {
        stt.start();
      }
    };

    const onKeyUp = (e: globalThis.KeyboardEvent) => {
      if (e.code !== 'Space') return;
      const active = document.activeElement as HTMLElement | null;
      const tag = active?.tagName?.toLowerCase();
      if (tag === 'textarea' || tag === 'input' || active?.isContentEditable) return;
      if (stt.isListening) {
        stt.stop();
      }
    };

    window.addEventListener('keydown', onKeyDown);
    window.addEventListener('keyup', onKeyUp);
    return () => {
      window.removeEventListener('keydown', onKeyDown);
      window.removeEventListener('keyup', onKeyUp);
    };
  }, [stt]);

  // CMD+SHIFT+SPACE — toggle PTT regardless of focus
  useEffect(() => {
    const onKeyDown = (e: globalThis.KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.shiftKey && e.code === 'Space') {
        e.preventDefault();
        handlePttToggle();
      }
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [handlePttToggle]);

  // Sync busy state with orb
  useEffect(() => {
    if (isBusy) {
      setOrbState('THINKING');
    } else if (!stt.isListening) {
      setOrbState('IDLE');
    }
  }, [isBusy, stt.isListening, setOrbState]);

  const handleSend = useCallback(() => {
    const trimmed = text.trim();
    if (!trimmed || isBusy) return;
    onSend(trimmed);
    setText('');
    setOrbState('THINKING');
  }, [text, isBusy, onSend, setOrbState]);

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (isBusy) {
        onAbort?.();
      } else {
        handleSend();
      }
    }
  };

  // Auto-resize textarea to content, capped at max-height
  useEffect(() => {
    const ta = textareaRef.current;
    if (!ta) return;
    ta.style.height = 'auto';
    ta.style.height = `${Math.min(ta.scrollHeight, 120)}px`;
  }, [text]);

  return (
    <div className="jarvis-input-bar">
      {/* Text input */}
      <textarea
        ref={textareaRef}
        className="jarvis-input-field"
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={isBusy ? 'JARVIS is working… (Enter to abort)' : placeholder}
        rows={1}
        aria-label="Message input"
      />

      {/* PTT mic button */}
      <button
        className={`jarvis-ptt-button${stt.isListening ? ' active' : ''}${stt.mode === 'none' ? ' disabled-voice' : ''}`}
        onClick={handlePttToggle}
        aria-label={stt.isListening ? 'Stop listening' : 'Push to talk'}
        title={
          stt.mode === 'none'
            ? 'Voice unavailable — run: python scripts/whisper-sidecar.py'
            : stt.supported
            ? stt.isListening
              ? 'Stop (Space)'
              : `Talk (Space / ⌘⇧Space) [${stt.mode}]`
            : 'Voice not supported in this browser'
        }
        disabled={!stt.supported}
      >
        {/* Privacy warning badge — only shown while actively listening */}
        {stt.showPrivacyWarning && stt.isListening && (
          <span className="jarvis-stt-privacy-badge" title="Audio is sent to Google">
            ⚠ Google
          </span>
        )}

        {/* Mic icon */}
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8}>
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M12 1a3 3 0 00-3 3v8a3 3 0 006 0V4a3 3 0 00-3-3z"
          />
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M19 10v2a7 7 0 01-14 0v-2M12 19v4M8 23h8"
          />
        </svg>
      </button>

      {/* Send / Abort button */}
      <button
        className="jarvis-send-button"
        onClick={isBusy ? () => onAbort?.() : handleSend}
        disabled={!isBusy && !text.trim()}
        aria-label={isBusy ? 'Abort' : 'Send'}
        title={isBusy ? 'Abort (Enter)' : 'Send (Enter)'}
      >
        {isBusy ? (
          /* Stop icon */
          <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
            <rect x="6" y="6" width="12" height="12" rx="2" />
          </svg>
        ) : (
          /* Send icon */
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M22 2L11 13M22 2L15 22l-4-9-9-4 20-7z" />
          </svg>
        )}
      </button>

      <p className="jarvis-input-hint">
        Enter to send · Shift+Enter new line · Space (no focus) = PTT
      </p>
    </div>
  );
}
