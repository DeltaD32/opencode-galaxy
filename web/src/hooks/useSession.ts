// Session CRUD hook — list, create, select, delete, title-edit.
// Listens to SSE session.* events to stay in sync without polling.

import { useState, useEffect, useCallback } from "react";
import type { Session } from "../types/opencode";
import {
  listSessions,
  createSession as apiCreate,
  deleteSession as apiDelete,
  updateSessionTitle as apiUpdateTitle,
  abortSession as apiAbort,
} from "../lib/opencode-client";
import { useSSE } from "./useSSE";

interface UseSessionReturn {
  sessions: Session[];
  activeSessionID: string | null;
  setActiveSessionID: (id: string) => void;
  createSession: (title?: string) => Promise<Session>;
  deleteSession: (id: string) => Promise<void>;
  updateTitle: (id: string, title: string) => Promise<void>;
  abortSession: (id: string) => Promise<void>;
  isLoading: boolean;
  error: string | null;
}

export function useSession(): UseSessionReturn {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [activeSessionID, setActiveSessionID] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Initial load
  useEffect(() => {
    setIsLoading(true);
    listSessions()
      .then((data) => {
        // Sort newest first
        const sorted = [...data].sort((a, b) => b.time.updated - a.time.updated);
        setSessions(sorted);
        if (sorted.length > 0 && !activeSessionID) {
          setActiveSessionID(sorted[0].id);
        }
      })
      .catch((e: unknown) => setError(String(e)))
      .finally(() => setIsLoading(false));
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Live sync via SSE
  useSSE((event) => {
    if (event.type === "session.created") {
      setSessions((prev) => [event.properties.info, ...prev]);
    }
    if (event.type === "session.updated") {
      setSessions((prev) =>
        prev.map((s) =>
          s.id === event.properties.sessionID ? event.properties.info : s,
        ),
      );
    }
    if (event.type === "session.deleted") {
      setSessions((prev) => prev.filter((s) => s.id !== event.properties.sessionID));
      if (activeSessionID === event.properties.sessionID) {
        setActiveSessionID(null);
      }
    }
  });

  const createSession = useCallback(async (title?: string): Promise<Session> => {
    const session = await apiCreate(title);
    // SSE session.created will update the list
    setActiveSessionID(session.id);
    return session;
  }, []);

  const deleteSession = useCallback(async (id: string): Promise<void> => {
    // Optimistically remove from state immediately — the OpenCode server does
    // NOT emit a session.deleted SSE event, so we can't wait for SSE to update.
    setSessions((prev) => prev.filter((s) => s.id !== id));
    if (activeSessionID === id) {
      setActiveSessionID(null);
    }
    await apiDelete(id);
  }, [activeSessionID]);

  const updateTitle = useCallback(async (id: string, title: string): Promise<void> => {
    await apiUpdateTitle(id, title);
    // SSE session.updated will reflect the change
  }, []);

  const abortSession = useCallback(async (id: string): Promise<void> => {
    await apiAbort(id);
  }, []);

  return {
    sessions,
    activeSessionID,
    setActiveSessionID,
    createSession,
    deleteSession,
    updateTitle,
    abortSession,
    isLoading,
    error,
  };
}
