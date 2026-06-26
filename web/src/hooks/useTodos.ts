// Real-time todo list — tracks todo.updated SSE events for the active session.
import { useState } from "react";
import type { Todo } from "../types/opencode";
import { useSSE } from "./useSSE";

interface UseTodosReturn {
  todos: Todo[];
  hasTodos: boolean;
  pendingCount: number;
  inProgressCount: number;
  completedCount: number;
}

export function useTodos(sessionID: string | null): UseTodosReturn {
  const [todos, setTodos] = useState<Todo[]>([]);

  useSSE((event) => {
    if (event.type === "todo.updated") {
      if (!sessionID || event.properties.sessionID !== sessionID) return;
      setTodos(event.properties.todos);
    }
  }, sessionID ?? undefined);

  // (session-scoped reset happens naturally via the SSE filter above)

  return {
    todos,
    hasTodos: todos.length > 0,
    pendingCount: todos.filter((t) => t.status === "pending").length,
    inProgressCount: todos.filter((t) => t.status === "in_progress").length,
    completedCount: todos.filter((t) => t.status === "completed").length,
  };
}
