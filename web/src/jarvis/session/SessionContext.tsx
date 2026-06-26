/**
 * SessionContext.tsx — JARVIS session state provider.
 *
 * Migrates the useMissionControl logic from App.tsx into a proper React
 * context so all JARVIS child components share a single source of truth
 * for session, message, orb, and mission-control state.
 */

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from 'react';
import { useSession } from '../../hooks/useSession';
import { useMessages } from '../../hooks/useMessages';
import { usePermissions } from '../../hooks/usePermissions';
import { useTodos } from '../../hooks/useTodos';
import { useSSE } from '../../hooks/useSSE';
import { listAgents } from '../../lib/opencode-client';
import { fetchAgentStatuses } from '../../lib/db-reader';
import type { AgentStatus } from '../../lib/db-reader';
import type { Session, Message, Agent } from '../../types/opencode';
import type { PendingPermission } from '../../hooks/usePermissions';

// ─── Orb State Machine ───────────────────────────────────────────────────────

export type OrbState = 'IDLE' | 'LISTENING' | 'THINKING' | 'SPEAKING';

// ─── Context Shape ───────────────────────────────────────────────────────────

interface SessionContextValue {
  // Sessions
  sessions: Session[];
  activeSessionID: string | null;
  setActiveSessionID: (id: string) => void;
  createSession: (title?: string) => Promise<Session>;
  deleteSession: (id: string) => Promise<void>;
  updateTitle: (id: string, title: string) => Promise<void>;
  abortSession: (id: string) => Promise<void>;
  isLoading: boolean;
  error: string | null;
  activeSession: Session | undefined;

  // Messages / streaming
  messages: Message[];
  streaming: { messageID: string | null; text: string };
  isBusy: boolean;
  lastTurnCost: number | null;
  sendMessage: (text: string, agent?: string) => Promise<void>;
  messagesLoading: boolean;
  messagesError: string | null;

  // Permissions
  pendingPermissions: PendingPermission[];
  replyAllow: (permission: PendingPermission) => Promise<void>;
  replyDeny: (permission: PendingPermission) => Promise<void>;

  // Todos
  hasTodos: boolean;
  pendingCount: number;
  inProgressCount: number;
  completedCount: number;

  // Mission control
  agents: Agent[];
  agentTotal: number;
  agentBusy: number;
  busyAgentNames: Set<string>;
  agentStatuses: AgentStatus[];

  // Orb state
  orbState: OrbState;
  setOrbState: (state: OrbState) => void;

  // UI selection
  selectedAgent: string | undefined;
  setSelectedAgent: (agent: string | undefined) => void;
  selectedModelID: string | undefined;
  setSelectedModelID: (id: string | undefined) => void;
  selectedProviderID: string | undefined;
  setSelectedProviderID: (id: string | undefined) => void;
}

const SessionContext = createContext<SessionContextValue | null>(null);

// ─── Provider ────────────────────────────────────────────────────────────────

export function SessionProvider({ children }: { children: ReactNode }) {
  // ── Core session hooks ──────────────────────────────────────────────────
  const {
    sessions,
    activeSessionID,
    setActiveSessionID,
    createSession,
    deleteSession,
    updateTitle,
    abortSession,
    isLoading,
    error,
  } = useSession();

  const {
    messages,
    streaming,
    isBusy,
    lastTurnCost,
    sendMessage,
    isLoading: messagesLoading,
    error: messagesError,
  } = useMessages(activeSessionID);

  const { pendingPermissions, replyAllow, replyDeny } = usePermissions(activeSessionID);

  const {
    hasTodos,
    pendingCount,
    inProgressCount,
    completedCount,
  } = useTodos(activeSessionID);

  // ── UI selection ────────────────────────────────────────────────────────
  const [selectedAgent, setSelectedAgent] = useState<string | undefined>(undefined);
  const [selectedModelID, setSelectedModelID] = useState<string | undefined>(undefined);
  const [selectedProviderID, setSelectedProviderID] = useState<string | undefined>(undefined);

  // ── Mission Control (migrated from App.tsx useMissionControl) ───────────
  // Agent registry — keyed by name (not id) per the Agent shape.
  const [agents, setAgents] = useState<Agent[]>([]);
  const sessionAgentMapRef = useRef<Map<string, string>>(new Map());
  const [busySessionIds, setBusySessionIds] = useState<Set<string>>(new Set());
  const [busyAgentNames, setBusyAgentNames] = useState<Set<string>>(new Set());

  useEffect(() => {
    listAgents()
      .then(setAgents)
      .catch(() => {});
  }, []);

  // ── Blackboard agent status polling ──────────────────────────────────────
  // Poll /__db every 3s to derive per-agent activity from the sections table.
  // Only polls while at least one session is busy (or on first mount) to avoid
  // unnecessary DB reads when nothing is happening.
  const [agentStatuses, setAgentStatuses] = useState<AgentStatus[]>([]);
  const agentNamesRef = useRef<string[]>([]);

  useEffect(() => {
    agentNamesRef.current = agents.map(a => a.name);
  }, [agents]);

  useEffect(() => {
    let cancelled = false;
    const poll = () => {
      fetchAgentStatuses(agentNamesRef.current).then(statuses => {
        if (!cancelled) setAgentStatuses(statuses);
      }).catch(() => {});
    };
    poll(); // immediate first fetch
    const id = setInterval(poll, 3000);
    return () => { cancelled = true; clearInterval(id); };
  }, []);

  // Helper: recompute busy agent names from the current set of busy session IDs.
  // Extracted so we don't duplicate logic across event handlers.
  const recomputeBusyNames = useCallback((ids: Set<string>): Set<string> => {
    const names = new Set<string>();
    for (const sid of ids) {
      const agentName = sessionAgentMapRef.current.get(sid);
      if (agentName) names.add(agentName);
    }
    return names;
  }, []);

  useSSE((event) => {
    // Track which agent is running in each session
    if (event.type === 'session.updated') {
      const { sessionID, info } = event.properties as {
        sessionID: string;
        info?: { agent?: string };
      };
      if (info?.agent) {
        sessionAgentMapRef.current.set(sessionID, info.agent);
      }
    }

    if (event.type === 'session.status') {
      const { sessionID, status } = event.properties as {
        sessionID: string;
        status: { type: 'busy' | 'idle' };
      };
      setBusySessionIds((prev) => {
        const next = new Set(prev);
        if (status.type === 'busy') next.add(sessionID);
        else next.delete(sessionID);
        setBusyAgentNames(recomputeBusyNames(next));
        return next;
      });
    }

    if (event.type === 'session.deleted') {
      const { sessionID } = event.properties as { sessionID: string };
      sessionAgentMapRef.current.delete(sessionID);
      setBusySessionIds((prev) => {
        const next = new Set(prev);
        next.delete(sessionID);
        setBusyAgentNames(recomputeBusyNames(next));
        return next;
      });
    }
  });

  // ── Orb State ────────────────────────────────────────────────────────────
  const [orbState, setOrbState] = useState<OrbState>('IDLE');

  // Sync isBusy → orb THINKING / IDLE transitions.
  // Does not override LISTENING or SPEAKING — those are driven by voice UI.
  useEffect(() => {
    if (isBusy) {
      setOrbState((prev) =>
        prev === 'IDLE' || prev === 'LISTENING' ? 'THINKING' : prev,
      );
    } else {
      setOrbState((prev) => (prev === 'THINKING' ? 'IDLE' : prev));
    }
  }, [isBusy]);

  // ── Derived ──────────────────────────────────────────────────────────────
  const activeSession = useMemo(
    () => sessions.find((s) => s.id === activeSessionID) ?? undefined,
    [sessions, activeSessionID],
  );

  const value = useMemo<SessionContextValue>(
    () => ({
      // Sessions
      sessions,
      activeSessionID,
      setActiveSessionID,
      createSession,
      deleteSession,
      updateTitle,
      abortSession,
      isLoading,
      error,
      activeSession,

      // Messages
      messages,
      streaming,
      isBusy,
      lastTurnCost,
      sendMessage,
      messagesLoading,
      messagesError,

      // Permissions
      pendingPermissions,
      replyAllow,
      replyDeny,

      // Todos
      hasTodos,
      pendingCount,
      inProgressCount,
      completedCount,

      // Mission control
      agents,
      agentTotal: agents.length,
      agentBusy: busySessionIds.size,
      busyAgentNames,
      agentStatuses,

      // Orb
      orbState,
      setOrbState,

      // UI selection
      selectedAgent,
      setSelectedAgent,
      selectedModelID,
      setSelectedModelID,
      selectedProviderID,
      setSelectedProviderID,
    }),
    [
      sessions,
      activeSessionID,
      setActiveSessionID,
      createSession,
      deleteSession,
      updateTitle,
      abortSession,
      isLoading,
      error,
      activeSession,
      messages,
      streaming,
      isBusy,
      lastTurnCost,
      sendMessage,
      messagesLoading,
      messagesError,
      pendingPermissions,
      replyAllow,
      replyDeny,
      hasTodos,
      pendingCount,
      inProgressCount,
      completedCount,
      agents,
      busySessionIds,
      busyAgentNames,
      agentStatuses,
      orbState,
      selectedAgent,
      selectedModelID,
      selectedProviderID,
    ],
  );

  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>;
}

// ─── Hook ─────────────────────────────────────────────────────────────────────

export function useSessionContext(): SessionContextValue {
  const ctx = useContext(SessionContext);
  if (!ctx) throw new Error('useSessionContext must be used within <SessionProvider>');
  return ctx;
}
