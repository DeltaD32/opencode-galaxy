import React from "react";
import { useVoice } from "../hooks/useVoice";

interface VoiceButtonProps {
  onTranscript: (text: string) => void;
}

const MicIcon: React.FC = () => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    className="w-5 h-5"
    fill="none"
    viewBox="0 0 24 24"
    stroke="currentColor"
  >
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth={2}
      d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-7a3 3 0 01-3-3V5a3 3 0 016 0v6a3 3 0 01-3 3z"
    />
  </svg>
);

const StopIcon: React.FC = () => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    className="w-5 h-5"
    fill="currentColor"
    viewBox="0 0 24 24"
  >
    <rect x="6" y="6" width="12" height="12" rx="2" />
  </svg>
);

export const VoiceButton: React.FC<VoiceButtonProps> = ({ onTranscript }) => {
  const {
    isListening,
    isSupported,
    transcript,
    interimTranscript,
    startListening,
    stopListening,
    error,
  } = useVoice();

  const handleClick = () => {
    if (isListening) {
      stopListening();
      onTranscript(transcript);
    } else {
      startListening();
    }
  };

  const buttonClass = [
    "rounded-full w-10 h-10 flex items-center justify-center transition-all",
    !isSupported
      ? "bg-gray-800 text-gray-600 cursor-not-allowed opacity-50"
      : isListening
      ? "animate-pulse bg-red-500 text-white"
      : "bg-gray-700 hover:bg-gray-600 text-white",
  ].join(" ");

  const titleAttr = !isSupported
    ? "Voice input not supported"
    : error
    ? error
    : undefined;

  return (
    <div className="flex flex-col items-center gap-1">
      <button
        type="button"
        className={buttonClass}
        onClick={handleClick}
        disabled={!isSupported}
        title={titleAttr}
        aria-label={isListening ? "Stop recording" : "Start voice input"}
        aria-pressed={isListening}
      >
        {isListening ? <StopIcon /> : <MicIcon />}
      </button>

      {isListening && (
        <span className="text-xs text-gray-400 max-w-xs truncate">
          {interimTranscript}
        </span>
      )}
    </div>
  );
};

export default VoiceButton;
