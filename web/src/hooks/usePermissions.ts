// Tracks pending permission.v2.asked SSE events and exposes reply handler.
import { useState, useCallback } from "react";
import { replyPermission } from "../lib/opencode-client";
import { useSSE } from "./useSSE";

export interface PendingPermission {
  id: string;
  sessionID: string;
  action: string;
  path?: string;
  description?: string;
}

interface UsePermissionsReturn {
  pendingPermissions: PendingPermission[];
  replyAllow: (permission: PendingPermission) => Promise<void>;
  replyDeny: (permission: PendingPermission) => Promise<void>;
}

export function usePermissions(sessionID: string | null): UsePermissionsReturn {
  const [pendingPermissions, setPendingPermissions] = useState<PendingPermission[]>([]);

  useSSE((event) => {
    if (event.type === "permission.v2.asked") {
      const p = event.properties;
      // Only track permissions for the active session
      if (!sessionID || p.sessionID !== sessionID) return;
      setPendingPermissions((prev) => {
        if (prev.find((x) => x.id === p.id)) return prev;
        return [...prev, { id: p.id, sessionID: p.sessionID, action: p.action, path: p.path, description: p.description }];
      });
    }
  }, sessionID ?? undefined);

  const removePermission = useCallback((id: string) => {
    setPendingPermissions((prev) => prev.filter((p) => p.id !== id));
  }, []);

  const replyAllow = useCallback(async (permission: PendingPermission) => {
    await replyPermission(permission.sessionID, permission.id, "allow");
    removePermission(permission.id);
  }, [removePermission]);

  const replyDeny = useCallback(async (permission: PendingPermission) => {
    await replyPermission(permission.sessionID, permission.id, "deny");
    removePermission(permission.id);
  }, [removePermission]);

  return { pendingPermissions, replyAllow, replyDeny };
}
