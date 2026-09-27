"use client";

import React from "react";
import { CheckCircle2, ArrowRight } from "lucide-react";
import { DecisionItem } from "@/types/meeting";

interface DecisionsSectionProps {
  decisions?: DecisionItem[];
  isLoading?: boolean;
  onViewAll?: () => void;
}

export function DecisionsSection({
  decisions = [],
  isLoading = false,
  onViewAll,
}: DecisionsSectionProps) {
  return (
    <div className="bg-white rounded-2xl border border-slate-200/80 p-3.5 shadow-card flex flex-col min-h-[190px]">
      <div>
        {/* Header */}
        <div className="flex items-center justify-between gap-2 pb-2 border-b border-slate-100">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            <h3 className="text-[15px] sm:text-[16px] font-bold text-slate-900 tracking-tight">
              Decisions
            </h3>
            {decisions.length > 0 && (
              <span className="px-1.5 py-0.2 rounded-full bg-emerald-50 text-emerald-700 text-[10px] font-bold">
                {decisions.length}
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
            {[1, 2, 3].map((i) => (
              <div key={i} className="py-2.5 flex items-start gap-2.5">
                <div className="w-4 h-4 rounded-full bg-slate-200 shrink-0 mt-0.5" />
                <div className="flex-1 space-y-1.5">
                  <div className="h-3.5 bg-slate-200 rounded w-5/6" />
                  <div className="h-2.5 bg-slate-100 rounded w-1/2" />
                </div>
              </div>
            ))}
          </div>
        ) : decisions.length === 0 ? (
          /* Empty State */
          <div className="py-8 text-center text-slate-400">
            <CheckCircle2 className="w-6 h-6 mx-auto mb-1.5 text-slate-300 stroke-1" />
            <p className="text-xs font-semibold text-slate-600">No decisions identified</p>
            <p className="text-[11px] text-slate-400 mt-0.5">
              No formal consensus items detected in transcript.
            </p>
          </div>
        ) : (
          /* Decisions List */
          <div className="divide-y divide-slate-100">
            {decisions.slice(0, 4).map((item, idx) => (
              <div key={idx} className="py-2 first:pt-1.5 last:pb-0.5 flex items-start gap-2.5">
                {/* Numbered Green Circle */}
                <div className="w-4 h-4 rounded-full bg-emerald-500 text-white text-[9px] font-bold flex items-center justify-center shrink-0 mt-0.5 shadow-2xs">
                  {idx + 1}
                </div>

                <div className="flex-1 min-w-0">
                  <p className="text-[13px] font-medium text-slate-800 leading-snug line-clamp-2 break-words">
                    {item.decision}
                  </p>
                  <div className="flex items-center justify-between gap-2 mt-0.5">
                    <span className="text-[12px] text-slate-400 font-normal">
                      Based on: {item.timestamp || "12:34"} · {item.author || "Team"}
                    </span>
                    <span className="px-1.5 py-0.2 rounded-full bg-emerald-50 border border-emerald-200/60 text-emerald-700 text-[10px] font-semibold shrink-0">
                      {item.status || "Confirmed"}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
