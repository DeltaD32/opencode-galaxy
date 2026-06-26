import { useCallback, useEffect, useRef, useState } from "react";
import { useSession } from "./hooks/useSession";
import { useMessages } from "./hooks/useMessages";
import { usePermissions } from "./hooks/usePermissions";
import { useTodos } from "./hooks/useTodos";
import { useSSE } from "./hooks/useSSE";
import { SessionSidebar } from "./components/SessionSidebar";
import { ChatThread } from "./components/ChatThread";
import { PromptInput } from "./components/PromptInput";
import { CostBadge } from "./components/CostBadge";
import { AgentPicker } from "./components/AgentPicker";
import { ModelPicker } from "./components/ModelPicker";
import { PermissionDialog } from "./components/PermissionDialog";
import { TodoPanel } from "./components/TodoPanel";
import { DiffViewer } from "./components/DiffViewer";
import { CostTracker } from "./components/CostTracker";
import GalaxyView, { type LayerState } from "./components/GalaxyView";
import { listAgents } from "./lib/opencode-client";

// ─── Types ─────────────────────────────────────────────────────────────────────

type RightPanel = "todos" | "diff" | "cost" | null;

// ─── Mission Control badge ──────────────────────────────────────────────────────

/**
 * Tracks agent count from GET /api/agent (distinct configured agents),
 * busy count, and busy agent names from SSE events.
 *
 * session.updated events carry session.info.agent — we use this to build
 * a sessionID → agentName map so galaxy nodes can pulse when their agent
 * is actively processing.
 */
function useMissionControl(): { total: number; busy: number; busyAgentNames: Set<string> } {
  const [agentNames, setAgentNames] = useState<Set<string>>(new Set());
  // sessionID → agentName (populated from session.updated events)
  const sessionAgentMapRef = useRef<Map<string, string>>(new Map());
  // sessionIDs that are currently busy (from session.status events)
  const [busySessionIds, setBusySessionIds] = useState<Set<string>>(new Set());
  // agent names that are currently busy (derived — updated together with busySessionIds)
  const [busyAgentNames, setBusyAgentNames] = useState<Set<string>>(new Set());

  // Load configured agents once on mount
  useEffect(() => {
    listAgents()
      .then((agents) => {
        const names = new Set(agents.map((a) => a.name));
        setAgentNames(names);
      })
      .catch(() => { /* fail silently — badge shows 0 */ });
  }, []);

  useSSE((event) => {
    // Track sessionID → agentName from session.updated
    if (event.type === "session.updated") {
      const { sessionID, info } = event.properties as {
        sessionID: string;
        info?: { agent?: string };
      };
      if (info?.agent) {
        sessionAgentMapRef.current.set(sessionID, info.agent);
      }
    }

    if (event.type === "session.status") {
      const { sessionID, status } = event.properties;
      setBusySessionIds((prev) => {
        const next = new Set(prev);
        if (status.type === "busy") {
          next.add(sessionID);
        } else {
          next.delete(sessionID);
        }
        // Derive busy agent names from updated session set
        const names = new Set<string>();
        for (const sid of next) {
          const agentName = sessionAgentMapRef.current.get(sid);
          if (agentName) names.add(agentName);
        }
        setBusyAgentNames(names);
        return next;
      });
    }

    if (event.type === "session.deleted") {
      const { sessionID } = event.properties;
      sessionAgentMapRef.current.delete(sessionID);
      setBusySessionIds((prev) => {
        const next = new Set(prev);
        next.delete(sessionID);
        // Re-derive busy agent names
        const names = new Set<string>();
        for (const sid of next) {
          const agentName = sessionAgentMapRef.current.get(sid);
          if (agentName) names.add(agentName);
        }
        setBusyAgentNames(names);
        return next;
      });
    }
  });

  return { total: agentNames.size, busy: busySessionIds.size, busyAgentNames };
}

// ─── App ───────────────────────────────────────────────────────────────────────

export function App() {
  // ── Session state ──
  const {
    sessions,
    activeSessionID,
    setActiveSessionID,
    createSession,
    deleteSession,
    abortSession,
    isLoading,
  } = useSession();

  // ── Message / streaming state ──
  const {
    messages,
    streaming,
    isBusy,
    lastTurnCost,
    sendMessage,
  } = useMessages(activeSessionID);

  // ── Permission + todo state ──
  const { pendingPermissions, replyAllow, replyDeny } = usePermissions(activeSessionID);
  const { hasTodos } = useTodos(activeSessionID);

  // ── Local UI state ──
  const [selectedAgent, setSelectedAgent] = useState<string | undefined>(undefined);
  const [selectedModelID, setSelectedModelID] = useState<string | undefined>(undefined);
  const [selectedProviderID, setSelectedProviderID] = useState<string | undefined>(undefined);
  const [rightPanel, setRightPanel] = useState<RightPanel>(null);
  const [sidebarExpanded, setSidebarExpanded] = useState(false);

  // ── Drawer: open when a session is selected, close without deleting ──
  const [drawerOpen, setDrawerOpen] = useState(false);
  const drawerRef = useRef<HTMLDivElement>(null);

  // Open drawer whenever a session becomes active
  useEffect(() => {
    if (activeSessionID) {
      setDrawerOpen(true);
    }
  }, [activeSessionID]);

  // ── Mission Control badge ──
  const { total: agentTotal, busy: agentBusy, busyAgentNames } = useMissionControl();

  // ── Derived ──
  const activeSession = sessions.find((s) => s.id === activeSessionID);

  // ── Handlers ──
  const handleCreate = useCallback(async () => {
    await createSession();
  }, [createSession]);

  const handleSend = useCallback(
    (text: string) => {
      sendMessage(text, selectedAgent);
    },
    [sendMessage, selectedAgent],
  );

  const handleAbort = useCallback(() => {
    if (activeSessionID) abortSession(activeSessionID);
  }, [activeSessionID, abortSession]);

  const togglePanel = (panel: RightPanel) => {
    setRightPanel((prev) => (prev === panel ? null : panel));
  };

  const closeDrawer = () => {
    setDrawerOpen(false);
    // Do NOT clear activeSessionID — session persists, drawer just hides
  };

  // First pending permission (modal is blocking — show one at a time)
  const firstPermission = pendingPermissions[0];

  // ── Galaxy layer toggle state (authoritative — passed to GalaxyView as prop) ──
  const [galaxyLayers, setGalaxyLayers] = useState<LayerState>({
    agents: true,
    skills: true,
    memory: true,
    projects: true,
  });
  const toggleLayer = (layer: keyof LayerState) =>
    setGalaxyLayers((prev) => ({ ...prev, [layer]: !prev[layer] }));

  // ── Galaxy refresh trigger ──
  const [galaxyRefreshTrigger, setGalaxyRefreshTrigger] = useState(0);

  // ── Galaxy node/link count (received from GalaxyView via onCountChange) ──
  const [galaxyCount, setGalaxyCount] = useState<{ nodes: number; links: number } | null>(null);

  return (
    <div className="flex h-screen w-screen bg-surface text-white overflow-hidden font-sans">
      {/* ── Collapsible Session Sidebar ────────────────────────────────────────── */}
      <div
        className={`flex-shrink-0 flex flex-col border-r border-surface-border bg-surface-raised transition-all duration-200 ${
          sidebarExpanded ? "w-60" : "w-12"
        }`}
        aria-label="Session sidebar"
      >
        {/* Collapse toggle at the top */}
        <button
          onClick={() => setSidebarExpanded((v) => !v)}
          aria-label={sidebarExpanded ? "Collapse sidebar" : "Expand sidebar"}
          className="flex items-center justify-center h-10 w-full flex-shrink-0 border-b border-surface-border text-bmw-grey hover:text-white hover:bg-surface-overlay transition-colors"
        >
          {sidebarExpanded ? (
            /* chevron left */
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
            </svg>
          ) : (
            /* chevron right */
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
            </svg>
          )}
        </button>

        {/* Sidebar content — hidden in icon-rail mode */}
        {sidebarExpanded ? (
          <div className="flex-1 min-h-0">
            <SessionSidebar
              sessions={sessions}
              activeSessionID={activeSessionID}
              onSelect={(id) => {
                setActiveSessionID(id);
                setDrawerOpen(true);
              }}
              onCreate={handleCreate}
              onDelete={deleteSession}
              isLoading={isLoading}
            />
          </div>
        ) : (
          /* Icon rail — just a "new session" icon button */
          <div className="flex flex-col items-center gap-2 pt-2">
            <button
              onClick={handleCreate}
              aria-label="New session"
              title="New session"
              className="p-2 rounded-lg text-bmw-grey hover:text-white hover:bg-surface-overlay transition-colors"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
              </svg>
            </button>
            {/* Active session indicator dot */}
            {activeSessionID && (
              <div className="w-1.5 h-1.5 rounded-full bg-bmw-blue" title="Session active" />
            )}
          </div>
        )}
      </div>

      {/* ── Galaxy background + floating UI ───────────────────────────────────── */}
      <div className="relative flex-1 min-w-0">

        {/* Galaxy — always fills this area */}
        <div className="absolute inset-0">
          <GalaxyView
            busyAgentNames={busyAgentNames}
            layers={galaxyLayers}
            refreshTrigger={galaxyRefreshTrigger}
            onCountChange={(nodes, links) => setGalaxyCount({ nodes, links })}
          />
        </div>

        {/* ── Top toolbar (floats over galaxy) ─────────────────────────────────── */}
        <div className="absolute top-0 left-0 right-0 z-20 flex items-center gap-2 px-3 py-2 pointer-events-none">

          {/* Mission Control badge */}
          <div className="pointer-events-auto flex items-center gap-1.5 bg-surface-raised/80 backdrop-blur-sm border border-surface-border rounded-lg px-2.5 py-1 text-xs font-mono">
            <span className="w-1.5 h-1.5 rounded-full bg-bmw-blue flex-shrink-0" />
            <span className="text-white/80">
              {agentTotal} agent{agentTotal !== 1 ? "s" : ""}
              {agentBusy > 0 && (
                <span className="text-bmw-yellow ml-1">· {agentBusy} busy</span>
              )}
            </span>
          </div>

          {/* Spacer */}
          <div className="flex-1" />

          {/* Galaxy layer toggles + Refresh — single authoritative control bar */}
          <div className="pointer-events-auto flex items-center gap-1 bg-surface-raised/80 backdrop-blur-sm border border-surface-border rounded-lg px-2 py-1">
            <span className="text-xs text-white/50 mr-1 select-none">Layers:</span>

            {/* Agents */}
            <button
              aria-label="Toggle agents layer"
              aria-pressed={galaxyLayers.agents}
              onClick={() => toggleLayer("agents")}
              className={`px-2 py-0.5 rounded text-xs font-medium transition-colors ${
                galaxyLayers.agents
                  ? "bg-bmw-blue/30 text-bmw-blue-light"
                  : "text-white/40 hover:text-white/70"
              }`}
            >
              Agents
            </button>

            {/* Skills */}
            <button
              aria-label="Toggle skills layer"
              aria-pressed={galaxyLayers.skills}
              onClick={() => toggleLayer("skills")}
              className={`px-2 py-0.5 rounded text-xs font-medium transition-colors ${
                galaxyLayers.skills
                  ? "bg-green-500/20 text-green-400"
                  : "text-white/40 hover:text-white/70"
              }`}
            >
              Skills
            </button>

            {/* Memory */}
            <button
              aria-label="Toggle memory layer"
              aria-pressed={galaxyLayers.memory}
              onClick={() => toggleLayer("memory")}
              className={`px-2 py-0.5 rounded text-xs font-medium transition-colors ${
                galaxyLayers.memory
                  ? "bg-purple-500/20 text-purple-400"
                  : "text-white/40 hover:text-white/70"
              }`}
            >
              Memory
            </button>

            {/* Projects */}
            <button
              aria-label="Toggle projects layer"
              aria-pressed={galaxyLayers.projects}
              onClick={() => toggleLayer("projects")}
              className={`px-2 py-0.5 rounded text-xs font-medium transition-colors ${
                galaxyLayers.projects
                  ? "bg-orange-500/20 text-orange-400"
                  : "text-white/40 hover:text-white/70"
              }`}
            >
              Projects
            </button>

            {/* Separator */}
            <span className="w-px h-3 bg-white/10 mx-1" />

            {/* Refresh */}
            <button
              aria-label="Refresh galaxy data"
              onClick={() => setGalaxyRefreshTrigger((n) => n + 1)}
              className="px-2 py-0.5 rounded text-xs font-medium text-white/50 hover:text-white transition-colors"
              title="Reload graph data"
            >
              ↺
            </button>
          </div>

          {/* Node count — shown inline next to the layer bar */}
          {galaxyCount && (
            <div className="pointer-events-none text-[10px] text-white/30 tabular-nums select-none">
              {galaxyCount.nodes}n · {galaxyCount.links}l
            </div>
          )}

          {/* Open chat drawer button — only when a session is active and drawer is closed */}
          {activeSessionID && !drawerOpen && (
            <button
              onClick={() => setDrawerOpen(true)}
              aria-label="Open chat"
              className="pointer-events-auto flex items-center gap-1.5 bg-bmw-blue/80 backdrop-blur-sm border border-bmw-blue/50 rounded-lg px-3 py-1 text-xs font-medium text-white hover:bg-bmw-blue transition-colors"
            >
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
              Open Chat
            </button>
          )}
        </div>

        {/* ── Floating right-panel overlays (todos, diff, cost) ─────────────────── */}
        {rightPanel && activeSessionID && (
          <aside
            className="absolute top-12 right-0 bottom-0 z-30 w-72 flex flex-col border-l border-surface-border bg-surface-raised/95 backdrop-blur-md overflow-hidden animate-slide-in"
            aria-label={
              rightPanel === "todos"
                ? "Todo panel"
                : rightPanel === "diff"
                ? "Diff viewer"
                : "Cost tracker"
            }
          >
            {/* Panel header */}
            <div className="flex items-center justify-between px-3 py-2.5 border-b border-surface-border flex-shrink-0">
              <p className="text-xs font-semibold text-white/70 uppercase tracking-wider">
                {rightPanel === "todos"
                  ? "Tasks"
                  : rightPanel === "diff"
                  ? "Changes"
                  : "Cost"}
              </p>
              <button
                onClick={() => setRightPanel(null)}
                aria-label="Close panel"
                className="text-bmw-grey hover:text-white transition-colors"
              >
                <svg className="w-3.5 h-3.5" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" d="M1 1l12 12M13 1L1 13" />
                </svg>
              </button>
            </div>
            {/* Panel content */}
            <div className="flex-1 overflow-y-auto">
              {rightPanel === "todos" && <TodoPanel sessionID={activeSessionID} />}
              {rightPanel === "diff" && <DiffViewer sessionID={activeSessionID} />}
              {rightPanel === "cost" && <CostTracker sessions={sessions} activeSession={activeSession} />}
            </div>
          </aside>
        )}

        {/* ── Chat Drawer (slides in from right) ───────────────────────────────── */}
        {drawerOpen && activeSessionID && (
          <div
            ref={drawerRef}
            className="absolute top-0 right-0 bottom-0 z-40 w-[480px] flex flex-col bg-surface shadow-2xl border-l border-surface-border animate-slide-in"
            aria-label="Chat drawer"
          >
            {/* Drawer header */}
            <header className="flex items-center gap-2 px-3 py-2.5 border-b border-surface-border bg-surface-raised flex-shrink-0 flex-wrap">
              {/* Close drawer button */}
              <button
                onClick={closeDrawer}
                aria-label="Close chat drawer"
                className="flex-shrink-0 p-1.5 rounded-lg text-bmw-grey hover:text-white hover:bg-surface-overlay transition-colors"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
                </svg>
              </button>

              {/* Session title */}
              <div className="flex items-center gap-2 min-w-0 flex-1">
                {activeSession ? (
                  <h1 className="text-sm font-medium text-white truncate">
                    {activeSession.title ?? activeSession.slug ?? "Untitled"}
                  </h1>
                ) : (
                  <h1 className="text-sm font-medium text-bmw-grey">
                    Session
                  </h1>
                )}
              </div>

              {/* Agent + Model pickers */}
              <div className="flex items-center gap-1.5 flex-shrink-0">
                <AgentPicker
                  currentAgent={selectedAgent ?? activeSession?.agent}
                  onSelect={setSelectedAgent}
                />
                <ModelPicker
                  currentModelID={selectedModelID}
                  currentProviderID={selectedProviderID}
                  onSelect={(modelID, providerID) => {
                    setSelectedModelID(modelID);
                    setSelectedProviderID(providerID);
                  }}
                />
              </div>

              {/* Right-panel toggle buttons */}
              <div className="flex items-center gap-1 flex-shrink-0">
                {/* Todo */}
                <button
                  aria-label="Toggle todo panel"
                  aria-pressed={rightPanel === "todos"}
                  onClick={() => togglePanel("todos")}
                  className={`relative p-1.5 rounded-lg transition-colors ${
                    rightPanel === "todos"
                      ? "bg-bmw-blue/20 text-bmw-blue-light"
                      : "text-bmw-grey hover:text-white hover:bg-surface-overlay"
                  }`}
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                  </svg>
                  {hasTodos && (
                    <span className="absolute top-0.5 right-0.5 w-1.5 h-1.5 rounded-full bg-bmw-yellow" />
                  )}
                </button>

                {/* Diff */}
                <button
                  aria-label="Toggle diff viewer"
                  aria-pressed={rightPanel === "diff"}
                  onClick={() => togglePanel("diff")}
                  className={`p-1.5 rounded-lg transition-colors ${
                    rightPanel === "diff"
                      ? "bg-bmw-blue/20 text-bmw-blue-light"
                      : "text-bmw-grey hover:text-white hover:bg-surface-overlay"
                  }`}
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </button>

                {/* Cost */}
                <button
                  aria-label="Toggle cost tracker"
                  aria-pressed={rightPanel === "cost"}
                  onClick={() => togglePanel("cost")}
                  className={`p-1.5 rounded-lg transition-colors ${
                    rightPanel === "cost"
                      ? "bg-bmw-blue/20 text-bmw-blue-light"
                      : "text-bmw-grey hover:text-white hover:bg-surface-overlay"
                  }`}
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </button>
              </div>

              {/* Session cost */}
              {activeSession && activeSession.cost > 0 && (
                <CostBadge
                  cost={activeSession.cost}
                  prefix="Session: "
                  className="text-bmw-grey flex-shrink-0 text-xs"
                />
              )}
            </header>

            {/* Drawer body — chat thread + prompt input */}
            <div className="flex flex-col flex-1 min-h-0">
              <ChatThread
                messages={messages}
                streamingMessageID={streaming.messageID}
                streamingText={streaming.text}
                isBusy={isBusy}
                lastTurnCost={lastTurnCost}
              />
              <PromptInput
                onSend={handleSend}
                onAbort={handleAbort}
                isBusy={isBusy}
              />
            </div>
          </div>
        )}
      </div>

      {/* ── Permission dialog — truly modal, outside all panels ─────────────────── */}
      {firstPermission && (
        <PermissionDialog
          permission={firstPermission}
          onAllow={() => replyAllow(firstPermission)}
          onDeny={() => replyDeny(firstPermission)}
        />
      )}
    </div>
  );
}
