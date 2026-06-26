// Session diff viewer — shows file-level patches from GET /session/{id}/diff.
import { useState, useEffect } from "react";
import type { DiffFile } from "../lib/opencode-client";
import { getSessionDiff } from "../lib/opencode-client";

interface Props {
  sessionID: string;
}

function PatchLine({ line }: { line: string }) {
  if (line.startsWith("+++") || line.startsWith("---")) {
    return <span className="text-bmw-grey/60">{line}</span>;
  }
  if (line.startsWith("+")) {
    return <span className="text-bmw-green bg-bmw-green/5 block">{line}</span>;
  }
  if (line.startsWith("-")) {
    return <span className="text-bmw-red bg-bmw-red/5 block">{line}</span>;
  }
  if (line.startsWith("@@")) {
    return <span className="text-bmw-blue-light/70">{line}</span>;
  }
  return <span className="text-white/60">{line}</span>;
}

function FileDiff({ file, defaultOpen = false }: { file: DiffFile; defaultOpen?: boolean }) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <div className="border border-surface-border rounded-xl overflow-hidden mb-3" data-testid="diff-file">
      {/* File header */}
      <button
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center gap-3 px-4 py-3 bg-surface-raised hover:bg-surface-overlay transition-colors text-left"
        aria-expanded={open}
      >
        <svg
          className={`w-3.5 h-3.5 text-bmw-grey/50 flex-shrink-0 transition-transform ${open ? "rotate-90" : ""}`}
          viewBox="0 0 12 12" fill="currentColor"
        >
          <path d="M4 2l4 4-4 4V2z" />
        </svg>
        <span className="font-mono text-xs text-white/90 truncate flex-1">{file.file}</span>
        <div className="flex items-center gap-2 flex-shrink-0 text-[10px]">
          <span className="text-bmw-green">+{file.additions}</span>
          <span className="text-bmw-red">−{file.deletions}</span>
        </div>
      </button>

      {/* Patch */}
      {open && (
        <div className="border-t border-surface-border">
          <pre className="px-4 py-3 text-[11px] font-mono overflow-x-auto leading-relaxed bg-surface/50">
            {file.patch.split("\n").map((line, i) => (
              <PatchLine key={i} line={line} />
            ))}
          </pre>
        </div>
      )}
    </div>
  );
}

export function DiffViewer({ sessionID }: Props) {
  const [diffs, setDiffs] = useState<DiffFile[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!sessionID) return;
    setIsLoading(true);
    setDiffs([]);
    getSessionDiff(sessionID)
      .then(setDiffs)
      .catch((e: unknown) => setError(String(e)))
      .finally(() => setIsLoading(false));
  }, [sessionID]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12 text-bmw-grey/50 text-sm">
        Loading diff…
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center py-12 text-bmw-red/70 text-sm">
        {error}
      </div>
    );
  }

  if (diffs.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-bmw-grey/40" data-testid="diff-empty">
        <svg className="w-8 h-8 mb-2 opacity-50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        <p className="text-sm">No file changes yet</p>
      </div>
    );
  }

  const totalAdditions = diffs.reduce((s, f) => s + f.additions, 0);
  const totalDeletions = diffs.reduce((s, f) => s + f.deletions, 0);

  return (
    <div className="p-4" data-testid="diff-viewer">
      {/* Summary bar */}
      <div className="flex items-center gap-4 mb-4 text-xs text-bmw-grey/60">
        <span>{diffs.length} file{diffs.length !== 1 ? "s" : ""} changed</span>
        <span className="text-bmw-green">+{totalAdditions}</span>
        <span className="text-bmw-red">−{totalDeletions}</span>
      </div>

      {/* Files */}
      {diffs.map((file, i) => (
        <FileDiff key={file.file} file={file} defaultOpen={i === 0 && diffs.length <= 3} />
      ))}
    </div>
  );
}
