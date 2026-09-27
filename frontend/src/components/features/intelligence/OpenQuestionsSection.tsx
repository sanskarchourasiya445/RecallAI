"use client";

import React from "react";
import { HelpCircle, ArrowRight } from "lucide-react";
import { OpenQuestionItem } from "@/types/meeting";

interface OpenQuestionsSectionProps {
  questions?: OpenQuestionItem[];
  isLoading?: boolean;
  onViewAll?: () => void;
}

export function OpenQuestionsSection({
  questions = [],
  isLoading = false,
  onViewAll,
}: OpenQuestionsSectionProps) {
  return (
    <div className="bg-white rounded-2xl border border-slate-200/80 p-3.5 shadow-card flex flex-col min-h-[190px]">
      <div>
        {/* Header */}
        <div className="flex items-center justify-between gap-2 pb-2 border-b border-slate-100">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-pink-100 flex items-center justify-center shrink-0">
              <HelpCircle className="w-3.5 h-3.5 text-pink-500" />
            </div>
            <h3 className="text-[15px] sm:text-[16px] font-bold text-slate-900 tracking-tight">
              Open Questions
            </h3>
            {questions.length > 0 && (
              <span className="px-1.5 py-0.2 rounded-full bg-pink-50 text-pink-700 text-[10px] font-bold">
                {questions.length}
              </span>
            )}
          </div>
          <button
            onClick={onViewAll}
            className="inline-flex items-center gap-1 text-xs font-semibold text-indigo-600 hover:text-indigo-700 transition-colors"
          >
            <span>View all</span>
            <ArrowRight className="w-3 h-3" />
          </button>
        </div>

        {/* Loading Skeleton */}
        {isLoading ? (
          <div className="divide-y divide-slate-100 animate-pulse">
            {[1, 2].map((i) => (
              <div key={i} className="py-2.5 flex items-start gap-2">
                <div className="w-3 h-3 bg-slate-200 rounded shrink-0 mt-1" />
                <div className="flex-1 space-y-1.5">
                  <div className="h-3.5 bg-slate-200 rounded w-4/5" />
                  <div className="h-2.5 bg-slate-100 rounded w-2/5" />
                </div>
              </div>
            ))}
          </div>
        ) : questions.length === 0 ? (
          /* Empty State */
          <div className="py-8 text-center text-slate-400">
            <HelpCircle className="w-6 h-6 mx-auto mb-1.5 text-slate-300 stroke-1" />
            <p className="text-xs font-semibold text-slate-600">No open questions</p>
            <p className="text-[11px] text-slate-400 mt-0.5">
              All questions raised were resolved during the discussion.
            </p>
          </div>
        ) : (
          /* Questions List */
          <div className="divide-y divide-slate-100">
            {questions.slice(0, 3).map((item, idx) => (
              <div key={idx} className="py-2 first:pt-1.5 last:pb-0.5 flex items-start gap-2">
                <span className="text-xs font-bold text-slate-900 mt-0.5 shrink-0 w-3">
                  {idx + 1}.
                </span>
                <div className="flex-1 min-w-0">
                  <p className="text-[13px] font-medium text-slate-800 leading-snug line-clamp-2 break-words">
                    {item.question}
                  </p>
                  <p className="text-[12px] text-slate-400 font-normal mt-0.5">
                    Raised by: {item.author || "Alex"} · {item.timestamp || "12:15"}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
