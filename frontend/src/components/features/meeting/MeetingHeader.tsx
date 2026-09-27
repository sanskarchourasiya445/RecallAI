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
  Mic,
} from "lucide-react";

interface MeetingHeaderProps {
  title?: string;
  duration?: string;
  participantsCount?: number;
  dateStr?: string;
  status?: string;
  isLoading?: boolean;
  onShare?: () => void;
  onDownload?: () => void;
  onVoiceClick?: () => void;
}

export function MeetingHeader({
  title = "Product Strategy Meeting",
  duration = "42 min",
  participantsCount = 12,
  dateStr = "Apr 28, 2025 • 10:00 AM",
  status = "Completed",
  isLoading = false,
  onShare,
  onDownload,
  onVoiceClick,
}: MeetingHeaderProps) {
  if (isLoading) {
    return (
      <div className="relative overflow-hidden rounded-2xl border border-slate-200/80 bg-white px-5 py-4 shadow-card min-h-[112px] flex items-center animate-pulse">
        <div className="w-full flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-3.5 flex-1">
            <div className="w-10 h-10 rounded-xl bg-slate-200 shrink-0" />
            <div className="space-y-2 flex-1 max-w-lg">
              <div className="h-6 bg-slate-200 rounded w-3/4" />
              <div className="h-3.5 bg-slate-100 rounded w-1/2" />
            </div>
          </div>
          <div className="flex items-center gap-2">
            <div className="h-7 w-20 bg-slate-100 rounded-lg" />
            <div className="h-7 w-20 bg-slate-100 rounded-lg" />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="relative overflow-hidden rounded-2xl border border-slate-200/80 bg-gradient-to-r from-white via-indigo-50/20 to-blue-50/40 px-5 py-4 shadow-card min-h-[112px] flex items-center">
      {/* Abstract subtle flowing wave graphics on right background */}
      <div className="absolute right-0 top-0 bottom-0 w-2/5 pointer-events-none opacity-25">
        <svg
          viewBox="0 0 400 160"
          className="w-full h-full object-cover"
          preserveAspectRatio="none"
        >
          <defs>
            <linearGradient id="waveGradRefined" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#818cf8" stopOpacity="0.25" />
              <stop offset="100%" stopColor="#38bdf8" stopOpacity="0.3" />
            </linearGradient>
          </defs>
          <path
            d="M 60,0 C 180,90 240,10 400,60 L 400,160 L 0,160 Z"
            fill="url(#waveGradRefined)"
          />
        </svg>
      </div>

      <div className="relative z-10 w-full flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        {/* Left: Meeting Icon + Title + Metadata */}
        <div className="flex items-start sm:items-center gap-3.5 min-w-0 flex-1">
          {/* Rounded square calendar icon container */}
          <div className="w-10 h-10 rounded-xl bg-indigo-50 border border-indigo-100 flex items-center justify-center shrink-0 shadow-2xs mt-0.5 sm:mt-0">
            <Calendar className="w-5 h-5 text-indigo-600" />
          </div>

          <div className="min-w-0 flex-1">
            <h1 className="text-xl sm:text-[22px] lg:text-[24px] font-bold text-slate-900 tracking-tight leading-snug line-clamp-2 break-words">
              {title}
            </h1>

            {/* Metadata row */}
            <div className="flex flex-wrap items-center gap-3.5 mt-1 text-[12px] sm:text-[13px] text-slate-500 font-normal">
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

        {/* Right: Completed Status Badge + Buttons */}
        <div className="flex sm:flex-col sm:items-end justify-between items-center gap-2 shrink-0">
          {/* Status Badge */}
          <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-emerald-50 border border-emerald-200/70 text-emerald-700 text-[11px] font-semibold capitalize">
            <CheckCircle2 className="w-3 h-3 text-emerald-600" />
            <span>{status}</span>
          </div>

          {/* Action Buttons: Voice, Share, Download, More */}
          <div className="flex items-center gap-1.5">
            {onVoiceClick && (
              <button
                onClick={onVoiceClick}
                className="inline-flex items-center gap-1.5 h-7 px-2.5 rounded-lg bg-indigo-50 hover:bg-indigo-100 border border-indigo-200 text-indigo-700 text-xs font-semibold shadow-2xs transition-all active:scale-95"
                title="Start voice interaction"
              >
                <Mic className="w-3 h-3 text-indigo-600" />
                <span>Voice</span>
              </button>
            )}
            <button
              onClick={onShare}
              className="inline-flex items-center gap-1.5 h-7 px-2.5 rounded-lg bg-white hover:bg-slate-50 border border-slate-200 text-slate-700 text-xs font-medium shadow-2xs transition-all active:scale-95"
            >
              <Share2 className="w-3 h-3 text-slate-500" />
              <span>Share</span>
            </button>
            <button
              onClick={onDownload}
              className="inline-flex items-center gap-1.5 h-7 px-2.5 rounded-lg bg-white hover:bg-slate-50 border border-slate-200 text-slate-700 text-xs font-medium shadow-2xs transition-all active:scale-95"
            >
              <Download className="w-3 h-3 text-slate-500" />
              <span>Download</span>
            </button>
            <button
              aria-label="More options"
              className="h-7 w-7 rounded-lg bg-white hover:bg-slate-50 border border-slate-200 text-slate-600 flex items-center justify-center shadow-2xs transition-all active:scale-95"
            >
              <MoreHorizontal className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
