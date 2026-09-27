"use client";

import React from "react";
import { Sparkles, ArrowRight } from "lucide-react";

interface MeetingSummaryProps {
  summary?: string;
  keyHighlights?: string[];
  isLoading?: boolean;
  onViewFullSummary?: () => void;
}

export function MeetingSummary({
  summary = "",
  keyHighlights = [
    "AI-powered search feature prioritized for Q2 platform launch",
    "Database migration to PostgreSQL 16 with PgBouncer connection pool",
    "Marketing budget increased by 20% to support go-to-market strategy",
    "Engineering allocation finalized for core architecture modules",
  ],
  isLoading = false,
  onViewFullSummary,
}: MeetingSummaryProps) {
  return (
    <div className="bg-white rounded-2xl border border-slate-200/80 p-4 shadow-card flex flex-col justify-between h-full">
      <div>
        {/* Header: AI Sparkle + Title + Right Action */}
        <div className="flex items-center justify-between gap-2 pb-2.5">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-indigo-600" />
            <h3 className="text-[16px] sm:text-[17px] font-bold text-slate-900 tracking-tight">
              Meeting Summary
            </h3>
          </div>
          <button
            onClick={onViewFullSummary}
            className="inline-flex items-center gap-1 text-xs font-semibold text-indigo-600 hover:text-indigo-700 transition-colors"
          >
            <span>View Full Summary</span>
            <ArrowRight className="w-3 h-3" />
          </button>
        </div>

        {/* Loading Skeleton */}
        {isLoading ? (
          <div className="space-y-3 animate-pulse py-2">
            <div className="h-4 bg-slate-200 rounded w-full" />
            <div className="h-4 bg-slate-200 rounded w-11/12" />
            <div className="h-4 bg-slate-200 rounded w-4/5" />
            <div className="mt-4 pt-2 space-y-2">
              <div className="h-3.5 bg-slate-200 rounded w-1/4" />
              <div className="h-3 bg-slate-100 rounded w-3/4" />
              <div className="h-3 bg-slate-100 rounded w-2/3" />
            </div>
          </div>
        ) : (
          <>
            {/* Summary Paragraph */}
            <p className="text-[13px] sm:text-[14px] text-slate-600 leading-relaxed font-normal">
              {summary || "No executive summary available for this session yet."}
            </p>

            {/* Key Highlights Subheading */}
            <div className="mt-3.5">
              <h4 className="text-[14px] font-semibold text-slate-900 mb-2">Key Highlights</h4>
              <ul className="space-y-1.5">
                {keyHighlights.map((highlight, idx) => (
                  <li key={idx} className="flex items-start gap-2.5 text-[13px] text-slate-600 leading-snug">
                    <span className="w-1.5 h-1.5 rounded-full bg-indigo-500 mt-1.5 shrink-0" />
                    <span>{highlight}</span>
                  </li>
                ))}
              </ul>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
