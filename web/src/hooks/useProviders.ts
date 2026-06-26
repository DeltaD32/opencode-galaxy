// Loads available providers + models from the OpenCode API.
import { useState, useEffect } from "react";
import type { Model } from "../types/opencode";
import { listProviders } from "../lib/opencode-client";

export interface ProviderWithModels {
  id: string;
  name: string;
  models: Model[];
}

interface UseProvidersReturn {
  providers: ProviderWithModels[];
  allModels: (Model & { providerID: string; providerName: string })[];
  defaultModel: { modelID: string; providerID: string } | null;
  isLoading: boolean;
  error: string | null;
}

export function useProviders(): UseProvidersReturn {
  const [providers, setProviders] = useState<ProviderWithModels[]>([]);
  const [defaultModel, setDefaultModel] = useState<{ modelID: string; providerID: string } | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listProviders()
      .then((resp) => {
        const mapped: ProviderWithModels[] = (resp.all ?? []).map((p) => ({
          id: p.id,
          name: p.name,
          models: Object.values(p.models ?? {}),
        }));
        setProviders(mapped);
        setDefaultModel(resp.default ?? null);
      })
      .catch((e: unknown) => setError(String(e)))
      .finally(() => setIsLoading(false));
  }, []);

  const allModels = providers.flatMap((p) =>
    p.models.map((m) => ({ ...m, providerID: p.id, providerName: p.name })),
  );

  return { providers, allModels, defaultModel, isLoading, error };
}
