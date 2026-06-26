// Blocking permission dialog — surfaces permission.v2.asked events.
// Shown as a modal overlay; blocks interaction until Allow or Deny is clicked.
import type { PendingPermission } from "../hooks/usePermissions";

interface Props {
  permission: PendingPermission;
  onAllow: () => void;
  onDeny: () => void;
}

const ACTION_LABELS: Record<string, { label: string; icon: string; color: string }> = {
  write:    { label: "Write file",       icon: "✏️", color: "text-bmw-yellow" },
  read:     { label: "Read file",        icon: "📖", color: "text-bmw-blue-light" },
  delete:   { label: "Delete file",      icon: "🗑️", color: "text-bmw-red" },
  execute:  { label: "Execute command",  icon: "⚡", color: "text-bmw-orange" },
  network:  { label: "Network request",  icon: "🌐", color: "text-bmw-blue" },
  doom_loop:{ label: "Run recursive loop", icon: "🔄", color: "text-bmw-orange" },
  external_directory: { label: "Access external path", icon: "📁", color: "text-bmw-yellow" },
};

export function PermissionDialog({ permission, onAllow, onDeny }: Props) {
  const info = ACTION_LABELS[permission.action] ?? {
    label: permission.action,
    icon: "🔒",
    color: "text-bmw-grey",
  };

  return (
    // Modal backdrop
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="permission-title"
      className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in"
      data-testid="permission-dialog"
    >
      <div className="w-full max-w-md rounded-2xl border border-surface-border bg-surface-raised shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center gap-3 px-5 py-4 border-b border-surface-border">
          <div className="w-9 h-9 rounded-xl bg-bmw-blue/10 border border-bmw-blue/20 flex items-center justify-center text-lg flex-shrink-0">
            {info.icon}
          </div>
          <div className="min-w-0">
            <h2 id="permission-title" className="text-sm font-semibold text-white">
              Permission required
            </h2>
            <p className={`text-xs mt-0.5 ${info.color}`}>{info.label}</p>
          </div>
        </div>

        {/* Body */}
        <div className="px-5 py-4 space-y-3">
          {permission.path && (
            <div className="rounded-lg bg-surface-overlay border border-surface-border px-3 py-2.5">
              <p className="text-[10px] font-semibold uppercase tracking-wider text-bmw-grey/50 mb-1">Path</p>
              <p className="text-xs text-white/80 font-mono break-all">{permission.path}</p>
            </div>
          )}
          {permission.description && (
            <div className="rounded-lg bg-surface-overlay border border-surface-border px-3 py-2.5">
              <p className="text-[10px] font-semibold uppercase tracking-wider text-bmw-grey/50 mb-1">Description</p>
              <p className="text-xs text-white/80">{permission.description}</p>
            </div>
          )}
          {!permission.path && !permission.description && (
            <p className="text-xs text-bmw-grey">
              The agent is requesting permission for: <span className="text-white font-mono">{permission.action}</span>
            </p>
          )}
        </div>

        {/* Actions */}
        <div className="flex gap-2.5 px-5 pb-5">
          <button
            onClick={onDeny}
            aria-label="Deny permission"
            className="flex-1 px-4 py-2.5 rounded-xl border border-surface-border bg-surface-overlay text-sm font-medium text-bmw-grey hover:bg-surface-overlay/70 hover:text-white transition-colors"
          >
            Deny
          </button>
          <button
            onClick={onAllow}
            aria-label="Allow permission"
            className="flex-1 px-4 py-2.5 rounded-xl bg-bmw-blue hover:bg-bmw-blue-dark text-sm font-medium text-white transition-colors"
          >
            Allow
          </button>
        </div>
      </div>
    </div>
  );
}
