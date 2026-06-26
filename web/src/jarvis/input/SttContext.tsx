/**
 * SttContext.tsx — shares the single SttBridge instance across the tree.
 *
 * VoiceController creates the one useSttBridge call and publishes the result
 * here. InputBar (and any other consumer) reads from this context instead of
 * calling useSttBridge themselves.
 *
 * This prevents two competing Web Speech / MediaRecorder instances from
 * fighting over the microphone and killing each other after ~500 ms.
 */

import { createContext, useContext } from 'react';
import type { SttBridgeResult } from './SttBridge';

// ─── Context ──────────────────────────────────────────────────────────────────

const SttContext = createContext<SttBridgeResult | null>(null);

export const SttProvider = SttContext.Provider;

// ─── Hook ─────────────────────────────────────────────────────────────────────

export function useSttContext(): SttBridgeResult {
  const ctx = useContext(SttContext);
  if (!ctx) {
    throw new Error('useSttContext must be used inside <SttProvider>');
  }
  return ctx;
}
