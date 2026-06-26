// Loads slash commands from GET /command.
import { useState, useEffect } from "react";
import type { SlashCommand } from "../types/opencode";
import { listCommands } from "../lib/opencode-client";

interface UseCommandsReturn {
  commands: SlashCommand[];
  isLoading: boolean;
  error: string | null;
  search: (query: string) => SlashCommand[];
}

export function useCommands(): UseCommandsReturn {
  const [commands, setCommands] = useState<SlashCommand[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listCommands()
      .then(setCommands)
      .catch((e: unknown) => setError(String(e)))
      .finally(() => setIsLoading(false));
  }, []);

  const search = (query: string): SlashCommand[] => {
    if (!query) return commands;
    const q = query.toLowerCase();
    return commands.filter(
      (c) =>
        c.name.toLowerCase().includes(q) ||
        (c.description?.toLowerCase().includes(q) ?? false),
    );
  };

  return { commands, isLoading, error, search };
}
