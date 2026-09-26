/* eslint-disable @next/next/no-img-element */
"use client";

import React, { useState } from "react";
import { Play, FileText } from "lucide-react";

interface MediaPreviewProps {
  duration?: string;
  thumbnailUrl?: string;
  onViewTranscript?: () => void;
  onPlayClick?: () => void;
}

export function MediaPreview({
  duration = "42:15",
  thumbnailUrl = "https://images.unsplash.com/photo-1577495508048-b635879837f1?auto=format&fit=crop&w=800&q=80",
  onViewTranscript,
  onPlayClick,
}: MediaPreviewProps) {
  const [isPlaying, setIsPlaying] = useState(false);

  return (
    <div className="bg-white rounded-2xl border border-slate-200/80 p-3 shadow-card flex flex-col justify-between h-full">
      {/* Thumbnail area with Play button & Duration badge */}
      <div className="relative w-full aspect-[16/10] rounded-xl overflow-hidden bg-slate-900 group cursor-pointer border border-slate-200/60 shadow-2xs">
        {/* Meeting Image */}
        <img
          src={thumbnailUrl}
          alt="Meeting video preview"
          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300 brightness-95"
        />

        {/* Overlay Dark Tint */}
        <div className="absolute inset-0 bg-slate-950/20 group-hover:bg-slate-950/30 transition-colors" />

        {/* Centered Purple Play Button */}
        <button
          onClick={() => {
            setIsPlaying(!isPlaying);
            if (onPlayClick) onPlayClick();
          }}
          aria-label="Play recording"
          className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-9 h-9 rounded-full bg-gradient-to-tr from-indigo-600 to-purple-600 text-white flex items-center justify-center shadow-md shadow-indigo-600/30 group-hover:scale-110 active:scale-95 transition-all"
        >
          <Play className="w-3.5 h-3.5 fill-white translate-x-0.5" />
        </button>

        {/* Duration badge on bottom right */}
        <div className="absolute bottom-2 right-2 px-1.5 py-0.5 rounded bg-black/75 backdrop-blur-2xs text-[10px] font-semibold text-white tracking-wide">
          {duration}
        </div>
      </div>

      {/* View Transcript Action Underneath */}
      <button
        onClick={onViewTranscript}
        className="w-full mt-2.5 h-7 flex items-center justify-center gap-1.5 text-xs font-semibold text-indigo-600 hover:text-indigo-700 hover:bg-indigo-50/50 rounded-lg transition-colors"
      >
        <FileText className="w-3.5 h-3.5" />
        <span>View Transcript</span>
      </button>
    </div>
  );
}
