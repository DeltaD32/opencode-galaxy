// Message + streaming hook.
// Loads historical messages for a session, then assembles live streaming
// output from SSE delta events. Tracks per-turn cost from step-finish parts.

import { useState, useEffect, useCallback, useRef } from "react";
import type { Message, Part, StepFinishPart, TextPart, MessageInfo } from "../types/opencode";
import { listMessages, sendPromptAsync } from "../lib/opencode-client";
import { useSSE } from "./useSSE";

interface StreamingState {
  messageID: string | null;
  text: string;
}

interface UseMessagesReturn {
  messages: Message[];
  streaming: StreamingState;
  isBusy: boolean;
  lastTurnCost: number | null;
  sendMessage: (text: string, agent?: string) => Promise<void>;
  isLoading: boolean;
  error: string | null;
}

export function useMessages(sessionID: string | null): UseMessagesReturn {
  const [messages, setMessages] = useState<Message[]>([]);
  const [streaming, setStreaming] = useState<StreamingState>({ messageID: null, text: "" });
  const [isBusy, setIsBusy] = useState(false);
  const [lastTurnCost, setLastTurnCost] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Track parts for the current streaming message (by partID → accumulated text)
  const streamingPartsRef = useRef<Map<string, string>>(new Map());

  // Load history when session changes
  useEffect(() => {
    if (!sessionID) {
      setMessages([]);
      setStreaming({ messageID: null, text: "" });
      setIsBusy(false);
      return;
    }

    setIsLoading(true);
    setMessages([]);
    setStreaming({ messageID: null, text: "" });
    streamingPartsRef.current.clear();

    listMessages(sessionID)
      .then(setMessages)
      .catch((e: unknown) => setError(String(e)))
      .finally(() => setIsLoading(false));
  }, [sessionID]);

  // SSE event handler — scoped to this session
  useSSE((event) => {
    switch (event.type) {
      case "session.status": {
        setIsBusy(event.properties.status.type === "busy");
        break;
      }

      case "session.idle": {
        // OpenCode 1.17.5 does NOT emit session.idle; kept for forward-compat.
        setIsBusy(false);
        setStreaming({ messageID: null, text: "" });
        streamingPartsRef.current.clear();
        break;
      }

      case "message.updated": {
        // SSE carries `info` (metadata only, no parts) — merge into existing message
        const info = event.properties.info as MessageInfo;
        setMessages((prev) => {
          const idx = prev.findIndex((m) => m.id === info.id);
          if (idx >= 0) {
            // Merge updated info into existing message, preserving accumulated parts
            const updated = [...prev];
            updated[idx] = { ...updated[idx], ...info };
            return updated;
          }
          // New message from SSE — create with empty parts (parts arrive via message.part.updated)
          return [...prev, { ...info, parts: [] }];
        });
        break;
      }

      case "message.part.delta": {
        const { messageID, partID, delta } = event.properties;
        // Accumulate delta into our ref
        const current = streamingPartsRef.current.get(partID) ?? "";
        streamingPartsRef.current.set(partID, current + delta);

        // Find the latest text partID to display
        // We show the last text part's accumulated content
        let latestText = "";
        streamingPartsRef.current.forEach((text) => {
          latestText = text; // last one wins — fine for single text part
        });

        setStreaming({ messageID, text: latestText });
        break;
      }

      case "message.part.updated": {
        const part = event.properties.part;

        // Capture step-finish cost AND use it as the completion signal.
        // OpenCode 1.17.5 never emits session.idle — the step-finish part
        // with reason="stop" is the reliable end-of-turn indicator.
        if (part.type === "step-finish") {
          const sfPart = part as StepFinishPart;
          setLastTurnCost(sfPart.cost);
          if (sfPart.reason === "stop") {
            setIsBusy(false);
            setStreaming({ messageID: null, text: "" });
            streamingPartsRef.current.clear();
          }
        }

        // When a text part arrives with content, update the message list
        if (part.type === "text" && (part as TextPart).text) {
          setMessages((prev) => {
            const msgIdx = prev.findIndex((m) => m.id === part.messageID);
            if (msgIdx < 0) return prev;

            const msg = prev[msgIdx];
            const partIdx = msg.parts.findIndex((p) => p.id === part.id);
            const updatedParts: Part[] =
              partIdx >= 0
                ? msg.parts.map((p, i) => (i === partIdx ? part : p))
                : [...msg.parts, part];

            const updatedMessages = [...prev];
            updatedMessages[msgIdx] = { ...msg, parts: updatedParts };
            return updatedMessages;
          });
        }
        break;
      }
    }
  }, sessionID ?? undefined);

  const sendMessage = useCallback(
    async (text: string, agent?: string): Promise<void> => {
      if (!sessionID || isBusy) return;
      streamingPartsRef.current.clear();
      setStreaming({ messageID: null, text: "" });
      await sendPromptAsync(sessionID, [{ type: "text", text }], agent);
      // isBusy will be set true by the session.status SSE event
    },
    [sessionID, isBusy],
  );

  return {
    messages,
    streaming,
    isBusy,
    lastTurnCost,
    sendMessage,
    isLoading,
    error,
  };
}
