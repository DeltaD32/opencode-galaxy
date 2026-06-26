// Agent selector dropdown — shows primary/all-mode agents, emits onSelect.
import { useState, useRef, useEffect } from "react";
import type { Agent } from "../types/opencode";
import { useAgents } from "../hooks/useAgents";

interface Props {
  currentAgent?: string;
  onSelect: (agentName: string) => void;
}

function AgentDot({ color }: { color?: string | null }) {
  return (
    <span
      className="inline-block w-2 h-2 rounded-full flex-shrink-0"
      style={{ backgroundColor: color ?? "#1c69d4" }}
    />
  );
}

export function AgentPicker({ currentAgent, onSelect }: Props) {
  const { primaryAgents, isLoading } = useAgents();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  // Close on outside click
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  const selected = primaryAgents.find((a) => a.name === currentAgent) ?? primaryAgents[0];

  function handleSelect(agent: Agent) {
    onSelect(agent.name);
    setOpen(false);
  }

  if (isLoading) {
    return (
      <div className="h-7 w-28 rounded bg-surface-overlay animate-pulse" />
    );
  }

  return (
    <div ref={ref} className="relative" data-testid="agent-picker">
      <button
        aria-label="Select agent"
        aria-expanded={open}
        aria-haspopup="listbox"
        onClick={() => setOpen((v) => !v)}
        className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-surface-overlay border border-surface-border hover:border-bmw-blue/50 transition-colors text-xs text-white/80 min-w-[7rem] max-w-[14rem]"
      >
        {selected && <AgentDot color={selected.color} />}
        <span className="truncate">{selected?.name ?? "Select agent"}</span>
        <svg className={`w-3 h-3 ml-auto flex-shrink-0 transition-transform ${open ? "rotate-180" : ""}`} viewBox="0 0 12 12" fill="currentColor">
          <path d="M6 8L2 4h8L6 8z" />
        </svg>
      </button>

      {open && (
        <div
          role="listbox"
          aria-label="Agent list"
          className="absolute left-0 top-full mt-1 z-50 min-w-[14rem] max-w-[22rem] rounded-xl border border-surface-border bg-surface-raised shadow-xl overflow-hidden animate-fade-in"
        >
          <div className="py-1 max-h-72 overflow-y-auto">
            {primaryAgents.map((agent) => (
              <button
                key={agent.name}
                role="option"
                aria-selected={agent.name === currentAgent}
                onClick={() => handleSelect(agent)}
                className={`w-full flex items-start gap-2.5 px-3 py-2 text-left hover:bg-surface-overlay transition-colors ${
                  agent.name === currentAgent ? "bg-bmw-blue/10" : ""
                }`}
              >
                <AgentDot color={agent.color} />
                <div className="min-w-0 flex-1">
                  <p className="text-xs font-medium text-white truncate">{agent.name}</p>
                  {agent.description && (
                    <p className="text-xs text-bmw-grey mt-0.5 line-clamp-2">{agent.description}</p>
                  )}
                </div>
                {agent.name === currentAgent && (
                  <svg className="w-3.5 h-3.5 text-bmw-blue flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 12 12">
                    <path d="M10 3L5 9 2 6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" fill="none" />
                  </svg>
                )}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
