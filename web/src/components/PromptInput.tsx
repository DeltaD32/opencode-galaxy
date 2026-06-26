import { useState, useRef, useCallback, useEffect } from "react";
import type { SlashCommand } from "../types/opencode";
import { SlashCommandPalette } from "./SlashCommandPalette";
import { VoiceButton } from "./VoiceButton";

interface Props {
  onSend: (text: string) => void;
  onAbort: () => void;
  isBusy: boolean;
  disabled?: boolean;
  placeholder?: string;
}

export function PromptInput({ onSend, onAbort, isBusy, disabled, placeholder }: Props) {
  const [value, setValue] = useState("");
  const [paletteVisible, setPaletteVisible] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Slash command palette — show when value starts with "/"
  const slashQuery = paletteVisible && value.startsWith("/")
    ? value.slice(1)  // text after the slash
    : "";

  const handleSend = useCallback(() => {
    const trimmed = value.trim();
    if (!trimmed || isBusy || disabled) return;
    onSend(trimmed);
    setValue("");
    setPaletteVisible(false);
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  }, [value, isBusy, disabled, onSend]);

  const handleCommandSelect = useCallback((cmd: SlashCommand) => {
    // Replace the "/<query>" in the textarea with the selected command
    const newValue = `/${cmd.name} `;
    setValue(newValue);
    setPaletteVisible(false);
    textareaRef.current?.focus();
  }, []);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
      e.preventDefault();
      handleSend();
    }
    if (e.key === "Escape") {
      if (paletteVisible) {
        setPaletteVisible(false);
      } else if (isBusy) {
        onAbort();
      }
    }
    // Don't propagate arrow keys while palette is open (palette handles them)
    if (paletteVisible && (e.key === "ArrowDown" || e.key === "ArrowUp" || e.key === "Enter" || e.key === "Tab")) {
      e.preventDefault();
    }
  };

  // Auto-resize textarea
  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newVal = e.target.value;
    setValue(newVal);
    // Show palette when line starts with "/"
    if (newVal.startsWith("/") && !isBusy) {
      setPaletteVisible(true);
    } else {
      setPaletteVisible(false);
    }
    const el = e.target;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 200)}px`;
  };

  // Close palette when component loses focus
  useEffect(() => {
    if (!paletteVisible) return;
    function handleClickOutside(e: MouseEvent) {
      if (textareaRef.current && !textareaRef.current.closest("[data-prompt-input]")?.contains(e.target as Node)) {
        setPaletteVisible(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [paletteVisible]);

  return (
    <div className="border-t border-surface-border bg-surface-raised p-4" data-prompt-input>
      {/* Palette sits above the input */}
      <div className="relative">
        <SlashCommandPalette
          query={slashQuery}
          visible={paletteVisible}
          onSelect={handleCommandSelect}
          onClose={() => setPaletteVisible(false)}
        />
      </div>

      <div className={`
        flex items-end gap-3 rounded-xl border px-4 py-3
        bg-surface-overlay transition-colors
        ${disabled ? "opacity-50 border-surface-border" : "border-surface-border focus-within:border-bmw-blue/50"}
      `}>
        {/* Textarea */}
        <textarea
          ref={textareaRef}
          value={value}
          onChange={handleInput}
          onKeyDown={handleKeyDown}
          disabled={disabled || isBusy}
          placeholder={placeholder ?? (isBusy ? "Generating…" : "Message OpenCode… (⌘↵ to send)")}
          rows={1}
          className="
            flex-1 resize-none bg-transparent text-white text-sm
            placeholder-bmw-grey/50 outline-none
            min-h-[1.5rem] max-h-[200px]
          "
          aria-label="Message input"
        />

        {/* Voice input button — left of send/abort */}
        <VoiceButton onTranscript={(text) => setValue((prev) => prev + text)} />

        {/* Send / Abort button */}
        {isBusy ? (
          <button
            onClick={onAbort}
            className="
              flex-shrink-0 w-8 h-8 flex items-center justify-center
              rounded-lg bg-red-600/20 text-red-400
              hover:bg-red-600/40 transition-colors
            "
            title="Abort generation (Esc)"
            aria-label="Abort generation"
          >
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
              <rect x="6" y="6" width="12" height="12" rx="1" />
            </svg>
          </button>
        ) : (
          <button
            onClick={handleSend}
            disabled={!value.trim() || disabled}
            className="
              flex-shrink-0 w-8 h-8 flex items-center justify-center
              rounded-lg transition-colors
              bg-bmw-blue text-white
              hover:bg-bmw-blue-dark
              disabled:opacity-30 disabled:cursor-not-allowed
            "
            title="Send (⌘↵)"
            aria-label="Send message"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 10.5 12 3m0 0 7.5 7.5M12 3v18" />
            </svg>
          </button>
        )}
      </div>

      {/* Hint */}
      <div className="mt-1.5 text-xs text-bmw-grey/40 text-right">
        {isBusy ? "Esc to abort" : paletteVisible ? "↑↓ navigate · Enter select" : "⌘↵ to send · / for commands"}
      </div>
    </div>
  );
}
