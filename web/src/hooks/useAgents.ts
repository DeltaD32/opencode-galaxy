// Loads the agent list once and exposes the active agent for a session.
import { useState, useEffect } from "react";
import type { Agent } from "../types/opencode";
import { listAgents } from "../lib/opencode-client";

interface UseAgentsReturn {
  agents: Agent[];
  primaryAgents: Agent[];
  isLoading: boolean;
  error: string | null;
}

export function useAgents(): UseAgentsReturn {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listAgents()
      .then(setAgents)
      .catch((e: unknown) => setError(String(e)))
      .finally(() => setIsLoading(false));
  }, []);

  // Only show non-hidden agents that are mode: primary or mode: all
  const primaryAgents = agents.filter(
    (a) => !a.hidden && (a.mode === "primary" || a.mode === "all"),
  );

  return { agents, primaryAgents, isLoading, error };
}
