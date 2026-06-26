// Expandable tool call card — shows tool name, args, result, and status.
// Handles the real OpenCode 1.17.5 ToolPart shape (type: "tool").
import { useState } from "react";
import type { ToolPart } from "../types/opencode";

interface Props {
  part: ToolPart;
}

function JsonBlock({ value }: { value: unknown }) {
  if (value == null) return null;
  const text = typeof value === "string" ? value : JSON.stringify(value, null, 2);
  return (
    <pre className="text-[11px] text-bmw-grey/80 overflow-x-auto whitespace-pre-wrap break-all leading-relaxed max-h-40 bg-surface-raised/60 rounded px-2.5 py-2 mt-1.5">
      {text}
    </pre>
  );
}

function StatusDot({ status }: { status: ToolPart["state"]["status"] }) {
  if (status === "running" || status === "pending") {
    return <span className="w-2 h-2 rounded-full bg-bmw-yellow animate-pulse-slow flex-shrink-0" />;
  }
  if (status === "error") {
    return <span className="w-2 h-2 rounded-full bg-red-500 flex-shrink-0" />;
  }
  return <span className="w-2 h-2 rounded-full bg-bmw-green flex-shrink-0" />;
}

export function ToolCallCard({ part }: Props) {
  const [expanded, setExpanded] = useState(false);
  const status = part.state?.status ?? "pending";
  const isRunning = status === "running" || status === "pending";
  const isDone = status === "completed";

  // data-state mirrors the old "result"/"call" convention for test selectors
  const dataState = isDone ? "result" : isRunning ? "call" : "error";

  return (
    <div
      className="my-1.5 rounded-lg border border-surface-border bg-surface-raised/50 text-xs overflow-hidden"
      data-testid="tool-call-card"
      data-tool-name={part.tool}
      data-state={dataState}
    >
      {/* Header row */}
      <button
        onClick={() => setExpanded((v) => !v)}
        className="w-full flex items-center gap-2 px-3 py-2 hover:bg-surface-overlay/50 transition-colors text-left"
        aria-expanded={expanded}
        aria-label={`Tool call: ${part.tool}`}
      >
        <StatusDot status={status} />

        <span className="font-mono text-bmw-blue-light font-medium">
          {part.state?.title ?? part.tool}
        </span>

        <span className="ml-auto text-[10px] text-bmw-grey/60 flex-shrink-0">
          {isRunning ? "running…" : isDone ? "done" : "error"}
        </span>

        <svg
          className={`w-3 h-3 text-bmw-grey/50 flex-shrink-0 transition-transform ${expanded ? "rotate-180" : ""}`}
          viewBox="0 0 12 12" fill="currentColor"
        >
          <path d="M6 8L2 4h8L6 8z" />
        </svg>
      </button>

      {/* Expanded body */}
      {expanded && (
        <div className="px-3 pb-2.5 border-t border-surface-border animate-fade-in">
          {part.state?.input != null && (
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-wider text-bmw-grey/50 mt-2 mb-0.5">Input</p>
              <JsonBlock value={part.state.input} />
            </div>
          )}
          {isDone && part.state?.output != null && (
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-wider text-bmw-grey/50 mt-2 mb-0.5">Output</p>
              <JsonBlock value={part.state.output} />
            </div>
          )}
          {status === "error" && part.state?.error != null && (
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-wider text-red-400/80 mt-2 mb-0.5">Error</p>
              <JsonBlock value={part.state.error} />
            </div>
          )}
        </div>
      )}
    </div>
  );
}
