// Slash command palette — triggered when user types "/" in the prompt input.
// Shown as a floating overlay above the PromptInput area.
import { useState, useEffect, useRef, useCallback } from "react";
import type { SlashCommand } from "../types/opencode";
import { useCommands } from "../hooks/useCommands";

interface Props {
  query: string;              // text after the "/" — used for filtering
  onSelect: (command: SlashCommand) => void;
  onClose: () => void;
  visible: boolean;
}

export function SlashCommandPalette({ query, onSelect, onClose, visible }: Props) {
  const { search, isLoading } = useCommands();
  const [activeIndex, setActiveIndex] = useState(0);
  const listRef = useRef<HTMLDivElement>(null);

  const filtered = search(query);

  // Reset selection when query changes
  useEffect(() => {
    setActiveIndex(0);
  }, [query]);

  // Keyboard navigation
  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (!visible) return;
      switch (e.key) {
        case "ArrowDown":
          e.preventDefault();
          setActiveIndex((i) => Math.min(i + 1, filtered.length - 1));
          break;
        case "ArrowUp":
          e.preventDefault();
          setActiveIndex((i) => Math.max(i - 1, 0));
          break;
        case "Enter":
          e.preventDefault();
          if (filtered[activeIndex]) onSelect(filtered[activeIndex]);
          break;
        case "Escape":
          e.preventDefault();
          onClose();
          break;
        case "Tab":
          e.preventDefault();
          if (filtered[activeIndex]) onSelect(filtered[activeIndex]);
          break;
      }
    },
    [visible, filtered, activeIndex, onSelect, onClose],
  );

  useEffect(() => {
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [handleKeyDown]);

  // Scroll active item into view
  useEffect(() => {
    const el = listRef.current?.children[activeIndex] as HTMLElement | undefined;
    el?.scrollIntoView({ block: "nearest" });
  }, [activeIndex]);

  if (!visible) return null;

  return (
    <div
      role="listbox"
      aria-label="Slash commands"
      className="absolute bottom-full left-0 right-0 mb-1 z-50 rounded-xl border border-surface-border bg-surface-raised shadow-xl overflow-hidden animate-fade-in"
      data-testid="slash-command-palette"
    >
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-surface-border">
        <span className="text-[10px] font-semibold uppercase tracking-wider text-bmw-grey/50">
          Commands {filtered.length > 0 ? `(${filtered.length})` : ""}
        </span>
        <span className="text-[10px] text-bmw-grey/40">↑↓ navigate · Enter select · Esc close</span>
      </div>

      {/* List */}
      <div ref={listRef} className="max-h-56 overflow-y-auto py-1">
        {isLoading && (
          <div className="px-3 py-3 text-xs text-bmw-grey/50">Loading…</div>
        )}
        {!isLoading && filtered.length === 0 && (
          <div className="px-3 py-3 text-xs text-bmw-grey/50">
            No commands match <span className="text-white font-mono">/{query}</span>
          </div>
        )}
        {!isLoading && filtered.map((cmd, i) => (
          <button
            key={cmd.name}
            role="option"
            aria-selected={i === activeIndex}
            onClick={() => onSelect(cmd)}
            onMouseEnter={() => setActiveIndex(i)}
            className={`w-full flex items-start gap-3 px-3 py-2 text-left transition-colors ${
              i === activeIndex ? "bg-bmw-blue/10" : "hover:bg-surface-overlay"
            }`}
          >
            <span className="text-xs font-mono text-bmw-blue-light font-medium flex-shrink-0 mt-0.5">
              /{cmd.name}
            </span>
            {cmd.description && (
              <span className="text-xs text-bmw-grey/70 truncate">{cmd.description}</span>
            )}
          </button>
        ))}
      </div>
    </div>
  );
}
