import { useState } from "react";
import type { Session } from "../types/opencode";
import { CostBadge } from "./CostBadge";

interface Props {
  sessions: Session[];
  activeSessionID: string | null;
  onSelect: (id: string) => void;
  onCreate: () => void;
  onDelete: (id: string) => void;
  isLoading: boolean;
}

function formatRelativeTime(timestamp: number): string {
  const diff = Date.now() - timestamp;
  const mins = Math.floor(diff / 60_000);
  const hours = Math.floor(diff / 3_600_000);
  const days = Math.floor(diff / 86_400_000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  if (hours < 24) return `${hours}h ago`;
  return `${days}d ago`;
}

export function SessionSidebar({
  sessions,
  activeSessionID,
  onSelect,
  onCreate,
  onDelete,
  isLoading,
}: Props) {
  const [hoveredID, setHoveredID] = useState<string | null>(null);
  const [confirmDeleteID, setConfirmDeleteID] = useState<string | null>(null);

  const handleDelete = (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    if (confirmDeleteID === id) {
      onDelete(id);
      setConfirmDeleteID(null);
    } else {
      setConfirmDeleteID(id);
      setTimeout(() => setConfirmDeleteID(null), 3000);
    }
  };

  return (
    <aside className="flex flex-col w-64 min-w-64 h-full bg-surface-raised border-r border-surface-border">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-surface-border">
        <div className="flex items-center gap-2">
          <div className="w-5 h-5 rounded-full bg-bmw-blue flex items-center justify-center">
            <span className="text-white text-xs font-bold">B</span>
          </div>
          <span className="text-white text-sm font-semibold tracking-wide">OpenCode</span>
        </div>
        <button
          onClick={onCreate}
          className="w-7 h-7 flex items-center justify-center rounded-md text-bmw-grey hover:text-white hover:bg-surface-overlay transition-colors"
          title="New session"
          aria-label="New session"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
          </svg>
        </button>
      </div>

      {/* Session list */}
      <div className="flex-1 overflow-y-auto py-2">
        {isLoading && (
          <div className="px-4 py-8 text-center text-bmw-grey text-sm">
            Loading sessions…
          </div>
        )}
        {!isLoading && sessions.length === 0 && (
          <div className="px-4 py-8 text-center text-bmw-grey text-sm">
            No sessions yet.
            <br />
            <button onClick={onCreate} className="text-bmw-blue hover:underline mt-1">
              Start one
            </button>
          </div>
        )}
        {sessions.map((session) => {
          const isActive = session.id === activeSessionID;
          const isHovered = session.id === hoveredID;
          const isConfirming = session.id === confirmDeleteID;

          return (
            <div
              key={session.id}
              role="button"
              tabIndex={0}
              onClick={() => onSelect(session.id)}
              onKeyDown={(e) => e.key === "Enter" && onSelect(session.id)}
              onMouseEnter={() => setHoveredID(session.id)}
              onMouseLeave={() => setHoveredID(null)}
              className={`
                relative flex flex-col px-4 py-2.5 cursor-pointer select-none
                transition-colors border-l-2
                ${isActive
                  ? "bg-surface-overlay border-bmw-blue text-white"
                  : "border-transparent text-white/70 hover:bg-surface-overlay/50 hover:text-white"
                }
              `}
            >
              {/* Title */}
              <span className="text-sm truncate leading-snug">
                {session.title ?? session.slug ?? "Untitled"}
              </span>

              {/* Meta row */}
              <div className="flex items-center gap-2 mt-0.5">
                <span className="text-xs text-bmw-grey">
                  {formatRelativeTime(session.time.updated)}
                </span>
                {session.cost > 0 && (
                  <CostBadge cost={session.cost} />
                )}
                {session.agent && (
                  <span className="text-xs text-bmw-grey/60 truncate">
                    {session.agent.replace("request-orchestrator", "orchestrator")}
                  </span>
                )}
              </div>

              {/* Delete button — shows on hover */}
              {(isHovered || isConfirming) && (
                <button
                  onClick={(e) => handleDelete(e, session.id)}
                  className={`
                    absolute right-2 top-1/2 -translate-y-1/2
                    w-6 h-6 flex items-center justify-center rounded
                    text-xs transition-colors
                    ${isConfirming
                      ? "bg-red-600 text-white"
                      : "text-bmw-grey hover:text-red-400 hover:bg-surface-border"
                    }
                  `}
                  title={isConfirming ? "Click again to confirm delete" : "Delete session"}
                  aria-label={isConfirming ? "Confirm delete" : "Delete session"}
                >
                  {isConfirming ? "!" : "×"}
                </button>
              )}
            </div>
          );
        })}
      </div>

      {/* Footer — session count */}
      <div className="px-4 py-2 border-t border-surface-border text-xs text-bmw-grey/60">
        {sessions.length} session{sessions.length !== 1 ? "s" : ""}
      </div>
    </aside>
  );
}
