import { useEffect, useRef } from "react";
import ReactMarkdown from "react-markdown";
import type { Message, TextPart, ToolPart, StepFinishPart } from "../types/opencode";
import { CostBadge } from "./CostBadge";
import { StreamingText } from "./StreamingText";
import { ToolCallCard } from "./ToolCallCard";

interface Props {
  messages: Message[];
  streamingMessageID: string | null;
  streamingText: string;
  isBusy: boolean;
  lastTurnCost: number | null;
}

// Extract the displayable text from a message's parts
function getMessageText(message: Message): string {
  return message.parts
    .filter((p): p is TextPart => p.type === "text")
    .map((p) => p.text)
    .join("")
    .trim();
}

// Extract tool calls from a message (real API: type === "tool")
function getToolCalls(message: Message): ToolPart[] {
  return message.parts.filter((p): p is ToolPart => p.type === "tool");
}

// Extract step cost from a message
function getStepCost(message: Message): number | null {
  const finish = message.parts.find((p): p is StepFinishPart => p.type === "step-finish");
  return finish?.cost ?? null;
}


function MessageBubble({ message, isStreaming, streamingText }: {
  message: Message;
  isStreaming: boolean;
  streamingText: string;
}) {
  const isUser = message.role === "user";
  const text = getMessageText(message);
  const tools = getToolCalls(message);
  const cost = getStepCost(message);

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-4 animate-fade-in`}>
      {/* Assistant avatar */}
      {!isUser && (
        <div className="w-7 h-7 rounded-full bg-bmw-blue/20 border border-bmw-blue/30 flex items-center justify-center text-xs text-bmw-blue flex-shrink-0 mr-2 mt-0.5">
          AI
        </div>
      )}

      <div className={`flex flex-col max-w-[80%] ${isUser ? "items-end" : "items-start"}`}>
        {/* Bubble */}
        <div className={`
          rounded-2xl px-4 py-3 text-sm leading-relaxed
          ${isUser
            ? "bg-bmw-blue text-white rounded-br-sm"
            : "bg-surface-overlay text-white/90 rounded-bl-sm"
          }
        `}>
          {/* Tool calls */}
          {tools.length > 0 && (
            <div className="mb-2 space-y-1">
              {tools.map((t) => (
                <ToolCallCard key={t.id} part={t} />
              ))}
            </div>
          )}

          {/* Text content */}
          {isStreaming ? (
            <StreamingText text={streamingText} isStreaming={true} />
          ) : text ? (
            <div className="prose prose-invert prose-sm max-w-none">
              <ReactMarkdown>{text}</ReactMarkdown>
            </div>
          ) : null}
        </div>

        {/* Cost badge */}
        {!isUser && cost != null && cost > 0 && (
          <CostBadge cost={cost} className="mt-1 mr-1" prefix="Turn: " />
        )}
      </div>

      {/* User avatar */}
      {isUser && (
        <div className="w-7 h-7 rounded-full bg-surface-overlay border border-surface-border flex items-center justify-center text-xs text-bmw-grey flex-shrink-0 ml-2 mt-0.5">
          You
        </div>
      )}
    </div>
  );
}

export function ChatThread({
  messages,
  streamingMessageID,
  streamingText,
  isBusy,
  lastTurnCost,
}: Props) {
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom on new content
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length, streamingText]);

  if (messages.length === 0 && !isBusy) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center text-bmw-grey/50 select-none">
        <div className="w-12 h-12 rounded-full bg-bmw-blue/10 border border-bmw-blue/20 flex items-center justify-center mb-3">
          <svg className="w-6 h-6 text-bmw-blue/50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
              d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-4 4v-4z" />
          </svg>
        </div>
        <p className="text-sm">Send a message to get started</p>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto px-6 py-4">
      {messages.map((message) => {
        const isStreaming = message.id === streamingMessageID;
        return (
          <MessageBubble
            key={message.id}
            message={message}
            isStreaming={isStreaming}
            streamingText={isStreaming ? streamingText : ""}
          />
        );
      })}

      {/* Typing indicator when busy but no streaming message yet */}
      {isBusy && !streamingMessageID && (
        <div className="flex justify-start mb-4 animate-fade-in">
          <div className="w-7 h-7 rounded-full bg-bmw-blue/20 border border-bmw-blue/30 flex items-center justify-center text-xs text-bmw-blue flex-shrink-0 mr-2 mt-0.5">
            AI
          </div>
          <div className="bg-surface-overlay rounded-2xl rounded-bl-sm px-4 py-3">
            <div className="flex gap-1 items-center h-4">
              <span className="w-1.5 h-1.5 bg-bmw-grey rounded-full animate-bounce [animation-delay:0ms]" />
              <span className="w-1.5 h-1.5 bg-bmw-grey rounded-full animate-bounce [animation-delay:150ms]" />
              <span className="w-1.5 h-1.5 bg-bmw-grey rounded-full animate-bounce [animation-delay:300ms]" />
            </div>
          </div>
        </div>
      )}

      {/* Last turn total cost */}
      {!isBusy && lastTurnCost != null && lastTurnCost > 0 && (
        <div className="flex justify-center mb-2">
          <CostBadge cost={lastTurnCost} prefix="Last turn: " className="text-bmw-grey/40" />
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  );
}
