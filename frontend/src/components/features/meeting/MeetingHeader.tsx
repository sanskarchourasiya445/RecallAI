"use client";

import React from "react";
import {
  Calendar,
  Clock,
  Users,
  CheckCircle2,
  Share2,
  Download,
  MoreHorizontal,
} from "lucide-react";

interface MeetingHeaderProps {
  title?: string;
  duration?: string;
  participantsCount?: number;
  dateStr?: string;
  status?: string;
  onShare?: () => void;
  onDownload?: () => void;
}

export function MeetingHeader({
  title = "Product Strategy Meeting",
  duration = "42 min",
  participantsCount = 12,
  dateStr = "Apr 28, 2025 • 10:00 AM",
  status = "Completed",
  onShare,
  onDownload,
}: MeetingHeaderProps) {
  return (
    <div className="relative overflow-hidden rounded-2xl border border-slate-200/90 bg-gradient-to-r from-white via-indigo-50/25 to-blue-100/40 p-5 shadow-sm">
      {/* Abstract subtle flowing wave graphics on right background */}
      <div className="absolute right-0 top-0 bottom-0 w-1/2 pointer-events-none opacity-40">
        <svg
          viewBox="0 0 500 200"
          className="w-full h-full object-cover"
          preserveAspectRatio="none"
        >
          <defs>
            <linearGradient id="waveGrad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#818cf8" stopOpacity="0.2" />
              <stop offset="100%" stopColor="#38bdf8" stopOpacity="0.35" />
            </linearGradient>
          </defs>
          <path
            d="M 100,0 C 220,120 300,10 500,80 L 500,200 L 0,200 Z"
            fill="url(#waveGrad)"
          />
        </svg>
      </div>

      <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-4">
        {/* Left Side: Purple Calendar Icon + Title + Metadata */}
        <div className="flex items-start gap-4">
          {/* Rounded square calendar icon container */}
          <div className="w-12 h-12 rounded-2xl bg-indigo-50 border border-indigo-100/90 flex items-center justify-center shrink-0 shadow-sm shadow-indigo-100">
            <Calendar className="w-6 h-6 text-indigo-600" />
          </div>

          <div>
            <h2 className="text-xl font-bold text-slate-900 tracking-tight">
              {title}
            </h2>

            {/* Metadata row */}
            <div className="flex flex-wrap items-center gap-4 mt-1.5 text-xs text-slate-500 font-medium">
              <div className="flex items-center gap-1.5">
                <Clock className="w-3.5 h-3.5 text-slate-400" />
                <span>{duration}</span>
              </div>
              <div className="flex items-center gap-1.5">
                <Users className="w-3.5 h-3.5 text-slate-400" />
                <span>{participantsCount} participants</span>
              </div>
              <div className="flex items-center gap-1.5">
                <Calendar className="w-3.5 h-3.5 text-slate-400" />
                <span>{dateStr}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right Side: Status Badge + Action Buttons */}
        <div className="flex flex-col sm:items-end gap-2.5">
          {/* Completed Status Badge */}
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-50 border border-emerald-200/80 text-emerald-700 text-xs font-semibold shadow-xs">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
            <span>{status}</span>
          </div>

          {/* Action Buttons: Share, Download, More */}
          <div className="flex items-center gap-2">
            <button
              onClick={onShare}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/90 hover:bg-white border border-slate-200 text-slate-700 text-xs font-medium shadow-xs transition-all hover:border-slate-300 active:scale-95"
            >
              <Share2 className="w-3.5 h-3.5 text-slate-500" />
              <span>Share</span>
            </button>
            <button
              onClick={onDownload}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/90 hover:bg-white border border-slate-200 text-slate-700 text-xs font-medium shadow-xs transition-all hover:border-slate-300 active:scale-95"
            >
              <Download className="w-3.5 h-3.5 text-slate-500" />
              <span>Download</span>
            </button>
            <button
              aria-label="More options"
              className="p-1.5 rounded-lg bg-white/90 hover:bg-white border border-slate-200 text-slate-600 shadow-xs transition-all hover:border-slate-300 active:scale-95"
            >
              <MoreHorizontal className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
