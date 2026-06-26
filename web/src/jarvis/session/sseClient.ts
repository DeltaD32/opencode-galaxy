/**
 * sseClient.ts — thin re-export of the existing useSSE hook.
 *
 * In Phase 2+ this becomes a proper client with reconnection logic
 * and event typing. For Phase 1 it just wraps useSSE so all JARVIS
 * components import from a stable location.
 */
export { useSSE, useSSEStatus, subscribeSSE } from '../../hooks/useSSE';

// Re-export the SSEEvent type for consumers that need it
export type { SSEEvent } from '../../types/opencode';
