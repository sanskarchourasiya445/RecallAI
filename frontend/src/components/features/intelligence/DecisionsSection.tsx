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
    <div className="bg-white rounded-2xl border border-slate-200/90 p-4 shadow-sm flex flex-col justify-between h-full">
      <div>
        {/* Header */}
        <div className="flex items-center justify-between gap-2 pb-3 border-b border-slate-100">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
            <h3 className="text-xs font-bold text-slate-900 tracking-tight">
              Decisions
            </h3>
          </div>
          <button
            onClick={onViewAll}
            className="inline-flex items-center gap-1 text-[11px] font-semibold text-indigo-600 hover:text-indigo-700 transition-colors"
          >
            <span>View all</span>
            <ArrowRight className="w-3 h-3" />
          </button>
        </div>

        {/* Decisions List */}
        <div className="divide-y divide-slate-100 mt-2">
          {decisions.map((item, idx) => (
            <div key={idx} className="py-2.5 first:pt-1 last:pb-1 flex items-start gap-2.5">
              {/* Numbered Green Circle */}
              <div className="w-5 h-5 rounded-full bg-emerald-500 text-white text-[10px] font-bold flex items-center justify-center shrink-0 mt-0.5 shadow-xs">
                {idx + 1}
              </div>

              <div className="flex-1 min-w-0">
                <p className="text-xs font-medium text-slate-800 leading-snug">
                  {item.decision}
                </p>
                <div className="flex items-center justify-between gap-2 mt-1">
                  <span className="text-[11px] text-slate-400 font-normal">
                    Based on: {item.timestamp || "12:34"} • {item.author || "Team"}
                  </span>
                  <span className="px-2 py-0.5 rounded-full bg-emerald-50 border border-emerald-200/60 text-emerald-700 text-[10px] font-semibold">
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
