// SSE hook — connects to the OpenCode /event stream and dispatches
// typed events to subscribers. Auto-reconnects with exponential backoff.
// The hook is a singleton — only one EventSource is kept open regardless
// of how many components call useSSE().

import { useEffect, useCallback, useRef } from "react";
import type { SSEEvent } from "../types/opencode";
import { eventStreamUrl } from "../lib/opencode-client";

type Listener = (event: SSEEvent) => void;

// --- Singleton state outside React ---
let source: EventSource | null = null;
let retryTimeout: ReturnType<typeof setTimeout> | null = null;
let retryDelay = 1000;
const listeners = new Set<Listener>();
let connectionStatus: "connecting" | "connected" | "disconnected" = "disconnected";
const statusListeners = new Set<(s: typeof connectionStatus) => void>();

function notifyStatus(s: typeof connectionStatus) {
  connectionStatus = s;
  statusListeners.forEach((fn) => fn(s));
}

function connect() {
  if (source) return;
  notifyStatus("connecting");

  source = new EventSource(eventStreamUrl());

  source.onopen = () => {
    retryDelay = 1000; // reset backoff on successful connect
    notifyStatus("connected");
  };

  source.onmessage = (e: MessageEvent<string>) => {
    try {
      const event = JSON.parse(e.data) as SSEEvent;
      listeners.forEach((fn) => fn(event));
    } catch {
      // malformed event — ignore
    }
  };

  source.onerror = () => {
    source?.close();
    source = null;
    notifyStatus("disconnected");

    // exponential backoff — cap at 30s
    retryTimeout = setTimeout(() => {
      retryDelay = Math.min(retryDelay * 2, 30_000);
      connect();
    }, retryDelay);
  };
}

function disconnect() {
  if (retryTimeout) clearTimeout(retryTimeout);
  source?.close();
  source = null;
  notifyStatus("disconnected");
}

/** Subscribe to all SSE events. Returns unsubscribe function. */
export function subscribeSSE(listener: Listener): () => void {
  listeners.add(listener);
  if (listeners.size === 1) connect(); // start on first subscriber
  return () => {
    listeners.delete(listener);
    if (listeners.size === 0) disconnect(); // stop when no subscribers
  };
}

/** React hook — subscribe to SSE events filtered by sessionID (or all if omitted). */
export function useSSE(
  handler: (event: SSEEvent) => void,
  sessionID?: string,
) {
  // stable reference so the effect doesn't re-run on every render
  const handlerRef = useRef(handler);
  handlerRef.current = handler;

  useEffect(() => {
    const unsubscribe = subscribeSSE((event) => {
      // If sessionID is provided, only forward events for that session
      if (sessionID) {
        const props = (event as { properties?: { sessionID?: string } }).properties;
        if (props?.sessionID && props.sessionID !== sessionID) return;
      }
      handlerRef.current(event);
    });
    return unsubscribe;
  }, [sessionID]);
}

/** React hook — returns current SSE connection status. */
export function useSSEStatus() {
  const ref = useRef(connectionStatus);

  useEffect(() => {
    const fn = (s: typeof connectionStatus) => { ref.current = s; };
    statusListeners.add(fn);
    return () => { statusListeners.delete(fn); };
  }, []);

  return useCallback(() => ref.current, []);
}
