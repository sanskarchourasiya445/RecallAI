"use client";

import React from "react";
import { CheckCircle2, ArrowRight } from "lucide-react";
import { DecisionItem } from "@/types/meeting";

interface DecisionsSectionProps {
  decisions?: DecisionItem[];
  onViewAll?: () => void;
}

export function DecisionsSection({
  decisions = [
    {
      decision: "AI search feature will be prioritized for Q2 release.",
      timestamp: "12:34",
      author: "Rahul",
      status: "Confirmed",
    },
    {
      decision: "Marketing budget will be increased by 20% for Q2.",
      timestamp: "18:22",
      author: "Priya",
      status: "Confirmed",
    },
    {
      decision: "Engineering team will use the new architecture for the AI module.",
      timestamp: "26:17",
      author: "David",
      status: "Confirmed",
    },
  ],
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
          </div>
          <button
            onClick={onViewAll}
            className="inline-flex items-center gap-1 text-xs font-semibold text-indigo-600 hover:text-indigo-700 transition-colors"
          >
            <span>View all</span>
            <ArrowRight className="w-3 h-3" />
          </button>
        </div>

        {/* Decisions List */}
        <div className="divide-y divide-slate-100">
          {decisions.map((item, idx) => (
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
      </div>
    </div>
  );
}
