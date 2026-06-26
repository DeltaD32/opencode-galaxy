// Real-time todo panel — tracks todo.updated SSE events for the active session.
import type { Todo } from "../types/opencode";
import { useTodos } from "../hooks/useTodos";

interface Props {
  sessionID: string | null;
}

const STATUS_CONFIG = {
  pending:     { label: "Pending",     dot: "bg-bmw-grey/40",   text: "text-bmw-grey" },
  in_progress: { label: "In progress", dot: "bg-bmw-yellow animate-pulse-slow", text: "text-bmw-yellow" },
  completed:   { label: "Done",        dot: "bg-bmw-green",     text: "text-bmw-green/70" },
  cancelled:   { label: "Cancelled",   dot: "bg-bmw-red/40",    text: "text-bmw-grey/40" },
} as const;

const PRIORITY_BADGE = {
  high:   "text-bmw-red/80 bg-bmw-red/10",
  medium: "text-bmw-yellow/80 bg-bmw-yellow/10",
  low:    "text-bmw-grey/60 bg-surface-overlay",
} as const;

function TodoItem({ todo }: { todo: Todo }) {
  const cfg = STATUS_CONFIG[todo.status];
  const isCompleted = todo.status === "completed";
  const isCancelled = todo.status === "cancelled";

  return (
    <div
      className={`flex items-start gap-3 px-3 py-2.5 rounded-lg transition-colors ${
        isCompleted ? "opacity-60" : isCancelled ? "opacity-40" : "hover:bg-surface-overlay/50"
      }`}
      data-testid="todo-item"
      data-status={todo.status}
    >
      {/* Status dot */}
      <div className="mt-1.5 flex-shrink-0">
        <span className={`block w-2 h-2 rounded-full ${cfg.dot}`} />
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <p className={`text-xs leading-relaxed ${
          isCompleted || isCancelled ? "line-through text-bmw-grey/50" : "text-white/85"
        }`}>
          {todo.content}
        </p>
      </div>

      {/* Priority badge */}
      <span className={`text-[9px] font-semibold uppercase tracking-wider px-1.5 py-0.5 rounded flex-shrink-0 ${PRIORITY_BADGE[todo.priority]}`}>
        {todo.priority}
      </span>
    </div>
  );
}

export function TodoPanel({ sessionID }: Props) {
  const { todos, hasTodos, pendingCount, inProgressCount, completedCount } = useTodos(sessionID);

  if (!hasTodos) {
    return (
      <div
        className="flex flex-col items-center justify-center py-8 text-bmw-grey/40"
        data-testid="todo-empty"
      >
        <svg className="w-7 h-7 mb-2 opacity-50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
            d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
        </svg>
        <p className="text-xs">No tasks yet</p>
      </div>
    );
  }

  const groups: Array<{ status: Todo["status"]; items: Todo[] }> = (
    [
      { status: "in_progress" as const, items: todos.filter((t) => t.status === "in_progress") },
      { status: "pending"     as const, items: todos.filter((t) => t.status === "pending") },
      { status: "completed"   as const, items: todos.filter((t) => t.status === "completed") },
      { status: "cancelled"   as const, items: todos.filter((t) => t.status === "cancelled") },
    ] as const
  ).filter((g) => g.items.length > 0);

  return (
    <div className="flex flex-col" data-testid="todo-panel">
      {/* Header stats */}
      <div className="flex items-center gap-3 px-3 py-2 border-b border-surface-border text-[10px]">
        {inProgressCount > 0 && (
          <span className="text-bmw-yellow">{inProgressCount} active</span>
        )}
        {pendingCount > 0 && (
          <span className="text-bmw-grey/60">{pendingCount} pending</span>
        )}
        {completedCount > 0 && (
          <span className="text-bmw-green/70">{completedCount} done</span>
        )}
      </div>

      {/* Groups */}
      <div className="py-1 overflow-y-auto max-h-80">
        {groups.map(({ status, items }) => {
          const cfg = STATUS_CONFIG[status];
          return (
            <div key={status}>
              <p className="px-3 pt-2 pb-1 text-[9px] font-semibold uppercase tracking-wider text-bmw-grey/40">
                {cfg.label}
              </p>
              {items.map((todo) => (
                <TodoItem key={todo.id} todo={todo} />
              ))}
            </div>
          );
        })}
      </div>
    </div>
  );
}
