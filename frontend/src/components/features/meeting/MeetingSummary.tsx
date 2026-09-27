"use client";

import React from "react";
import { Sparkles, ArrowRight } from "lucide-react";

interface MeetingSummaryProps {
  summary?: string;
  keyHighlights?: string[];
  onViewFullSummary?: () => void;
}

export function MeetingSummary({
  summary = "The team discussed the product roadmap for Q2, focusing on the new AI features, user experience improvements, and go-to-market strategy. Key topics included the timeline for the feature launch, resource allocation, and customer feedback from the beta program.",
  keyHighlights = [
    "AI-powered search feature will be prioritized for Q2 release",
    "UX improvements based on beta feedback",
    "Go-to-market strategy to include content marketing and partnerships",
    "Need to finalize engineering resources for the next phase",
  ],
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

        {/* Summary Paragraph */}
        <p className="text-[13px] sm:text-[14px] text-slate-600 leading-relaxed font-normal">
          {summary}
        </p>

        {/* Key Highlights Subheading */}
        <div className="mt-3.5">
          <h4 className="text-[14px] font-semibold text-slate-900 mb-2">Key Highlights</h4>
          <ul className="space-y-1.5">
            {keyHighlights.map((highlight, idx) => (
              <li key={idx} className="flex items-start gap-2.5 text-[13px] text-slate-600 leading-snug">
                {/* Purple dot bullet indicator */}
                <span className="w-1.5 h-1.5 rounded-full bg-indigo-500 mt-1.5 shrink-0" />
                <span>{highlight}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
