// Renders live streaming text with a blinking cursor.
// Used as an overlay while the assistant is generating.

import ReactMarkdown from "react-markdown";

interface Props {
  text: string;
  isStreaming: boolean;
}

export function StreamingText({ text, isStreaming }: Props) {
  if (!text && !isStreaming) return null;

  return (
    <div className="relative">
      <div className="prose prose-invert prose-sm max-w-none text-white/90">
        <ReactMarkdown>{text}</ReactMarkdown>
      </div>
      {isStreaming && (
        <span
          className="inline-block w-2 h-4 bg-bmw-blue ml-0.5 align-text-bottom animate-pulse-slow"
          aria-hidden="true"
        />
      )}
    </div>
  );
}
