"use client";

import React from "react";
import { Mic } from "lucide-react";

interface VoiceButtonProps {
  onClick: () => void;
  className?: string;
  label?: string;
  compact?: boolean;
}

/**
 * Reusable voice launch button.
 * Used in MeetingWorkspace header and potentially AppShell toolbar.
 */
export function VoiceButton({ onClick, className = "", label = "Voice", compact = false }: VoiceButtonProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl
        bg-indigo-50 hover:bg-indigo-100 active:bg-indigo-200
        text-indigo-700 border border-indigo-200
        text-xs font-semibold shadow-2xs transition-all
        focus:outline-none focus:ring-2 focus:ring-indigo-500/30
        ${className}`}
      title="Start voice interaction"
      aria-label="Start voice interaction"
    >
      <Mic className="w-3.5 h-3.5 text-indigo-600" />
      {!compact && <span>{label}</span>}
    </button>
  );
}
