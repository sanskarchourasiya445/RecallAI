"use client";

import React, { useState } from "react";
import { Zap, ArrowRight, Check } from "lucide-react";
import { ActionItem } from "@/types/meeting";

interface ActionItemsSectionProps {
  actionItems?: ActionItem[];
  isLoading?: boolean;
  onViewAll?: () => void;
  onToggleItem?: (idx: number) => void;
}

export function ActionItemsSection({
  actionItems = [],
  isLoading = false,
  onViewAll,
  onToggleItem,
}: ActionItemsSectionProps) {
  const [checkedState, setCheckedState] = useState<Record<number, boolean>>({});

  const handleToggle = (idx: number) => {
    setCheckedState((prev) => ({
      ...prev,
      [idx]: !prev[idx],
    }));
    if (onToggleItem) onToggleItem(idx);
  };

  return (
    <div className="bg-white rounded-2xl border border-slate-200/80 p-3.5 shadow-card flex flex-col min-h-[190px]">
      <div>
        {/* Header */}
        <div className="flex items-center justify-between gap-2 pb-2 border-b border-slate-100">
          <div className="flex items-center gap-2">
            <Zap className="w-4 h-4 text-amber-500 fill-amber-500 shrink-0" />
            <h3 className="text-[15px] sm:text-[16px] font-bold text-slate-900 tracking-tight">
              Action Items
            </h3>
            {actionItems.length > 0 && (
              <span className="px-1.5 py-0.2 rounded-full bg-amber-50 text-amber-700 text-[10px] font-bold">
                {actionItems.length}
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
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="py-2.5 flex items-start gap-2.5">
                <div className="w-3.5 h-3.5 rounded bg-slate-200 shrink-0 mt-0.5" />
                <div className="flex-1 space-y-1.5">
                  <div className="h-3.5 bg-slate-200 rounded w-4/5" />
                  <div className="h-2.5 bg-slate-100 rounded w-1/3" />
                </div>
              </div>
            ))}
          </div>
        ) : actionItems.length === 0 ? (
          /* Empty State */
          <div className="py-8 text-center text-slate-400">
            <Zap className="w-6 h-6 mx-auto mb-1.5 text-slate-300 stroke-1" />
            <p className="text-xs font-semibold text-slate-600">No action items detected</p>
            <p className="text-[11px] text-slate-400 mt-0.5">
              All tasks completed or none explicitly assigned.
            </p>
          </div>
        ) : (
          /* Action Items List */
          <div className="divide-y divide-slate-100">
            {actionItems.slice(0, 4).map((item, idx) => {
              const isChecked = checkedState[idx] || item.status === "Done";
              const isHigh = item.priority === "High";

              return (
                <div key={idx} className="py-2 first:pt-1.5 last:pb-0.5 flex items-start gap-2.5">
                  {/* Custom Checkbox */}
                  <button
                    onClick={() => handleToggle(idx)}
                    aria-label={`Toggle task ${item.task}`}
                    className={`w-3.5 h-3.5 rounded mt-0.5 flex items-center justify-center border transition-all shrink-0 ${
                      isChecked
                        ? "bg-amber-500 border-amber-500 text-white"
                        : "border-slate-300 hover:border-amber-400 bg-white"
                    }`}
                  >
                    {isChecked && <Check className="w-2.5 h-2.5 stroke-[3]" />}
                  </button>

                  <div className="flex-1 min-w-0">
                    <p
                      className={`text-[13px] font-medium leading-snug line-clamp-2 break-words ${
                        isChecked ? "line-through text-slate-400" : "text-slate-800"
                      }`}
                    >
                      {item.task}
                    </p>
                    <div className="flex items-center justify-between gap-2 mt-0.5">
                      <span className="text-[12px] text-slate-400 font-normal truncate">
                        Due: {item.deadline || "TBD"} · {item.owner || "Unassigned"}
                      </span>
                      <span
                        className={`px-1.5 py-0.2 rounded-full text-[10px] font-semibold border shrink-0 ${
                          isHigh
                            ? "bg-rose-50 border-rose-200/70 text-rose-600"
                            : "bg-amber-50 border-amber-200/70 text-amber-700"
                        }`}
                      >
                        {item.priority || "Medium"}
                      </span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
