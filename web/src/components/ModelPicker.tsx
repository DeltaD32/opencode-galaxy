// Model selector — groups models by provider, shows cost/million tokens.
import { useState, useRef, useEffect } from "react";
import { useProviders } from "../hooks/useProviders";

interface Props {
  currentModelID?: string;
  currentProviderID?: string;
  onSelect: (modelID: string, providerID: string) => void;
}

function formatCost(n: number): string {
  if (n === 0) return "free";
  if (n < 1) return `$${n.toFixed(3)}`;
  return `$${n.toFixed(2)}`;
}

export function ModelPicker({ currentModelID, currentProviderID, onSelect }: Props) {
  const { providers, isLoading } = useProviders();
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
        setSearch("");
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  const currentLabel = currentModelID ?? "Select model";

  if (isLoading) {
    return <div className="h-7 w-32 rounded bg-surface-overlay animate-pulse" />;
  }

  const filteredProviders = providers
    .map((p) => ({
      ...p,
      models: p.models.filter(
        (m) =>
          !search ||
          m.id.toLowerCase().includes(search.toLowerCase()) ||
          m.name.toLowerCase().includes(search.toLowerCase()),
      ),
    }))
    .filter((p) => p.models.length > 0);

  return (
    <div ref={ref} className="relative" data-testid="model-picker">
      <button
        aria-label="Select model"
        aria-expanded={open}
        aria-haspopup="listbox"
        onClick={() => setOpen((v) => !v)}
        className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-surface-overlay border border-surface-border hover:border-bmw-blue/50 transition-colors text-xs text-white/80 min-w-[8rem] max-w-[16rem]"
      >
        <svg className="w-3 h-3 flex-shrink-0 text-bmw-grey" fill="none" viewBox="0 0 12 12" stroke="currentColor">
          <circle cx="6" cy="6" r="4.5" strokeWidth="1.2" />
          <path d="M6 3.5v2.5l1.5 1.5" strokeWidth="1.2" strokeLinecap="round" />
        </svg>
        <span className="truncate">{currentLabel}</span>
        <svg className={`w-3 h-3 ml-auto flex-shrink-0 transition-transform ${open ? "rotate-180" : ""}`} viewBox="0 0 12 12" fill="currentColor">
          <path d="M6 8L2 4h8L6 8z" />
        </svg>
      </button>

      {open && (
        <div
          role="listbox"
          aria-label="Model list"
          className="absolute left-0 top-full mt-1 z-50 w-72 rounded-xl border border-surface-border bg-surface-raised shadow-xl overflow-hidden animate-fade-in"
        >
          {/* Search */}
          <div className="px-3 pt-2.5 pb-1.5 border-b border-surface-border">
            <input
              type="text"
              placeholder="Search models…"
              aria-label="Search models"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full bg-surface-overlay rounded-lg px-2.5 py-1.5 text-xs text-white placeholder-bmw-grey/60 outline-none border border-surface-border focus:border-bmw-blue/50 transition-colors"
              autoFocus
            />
          </div>

          <div className="py-1 max-h-80 overflow-y-auto">
            {filteredProviders.map((provider) => (
              <div key={provider.id}>
                <p className="px-3 py-1.5 text-[10px] font-semibold uppercase tracking-wider text-bmw-grey/60">
                  {provider.name}
                </p>
                {provider.models.map((model) => {
                  const isActive = model.id === currentModelID && provider.id === currentProviderID;
                  return (
                    <button
                      key={model.id}
                      role="option"
                      aria-selected={isActive}
                      onClick={() => {
                        onSelect(model.id, provider.id);
                        setOpen(false);
                        setSearch("");
                      }}
                      className={`w-full flex items-center justify-between gap-2 px-3 py-2 hover:bg-surface-overlay transition-colors ${
                        isActive ? "bg-bmw-blue/10" : ""
                      }`}
                    >
                      <span className={`text-xs truncate ${isActive ? "text-bmw-blue-light" : "text-white/80"}`}>
                        {model.id}
                      </span>
                      {model.cost && (
                        <span className="text-[10px] text-bmw-grey/60 flex-shrink-0 whitespace-nowrap">
                          {formatCost(model.cost.input)}/{formatCost(model.cost.output)}
                        </span>
                      )}
                    </button>
                  );
                })}
              </div>
            ))}

            {filteredProviders.length === 0 && (
              <p className="px-3 py-4 text-xs text-bmw-grey/50 text-center">No models match</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
