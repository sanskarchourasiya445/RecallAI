"use client";

import React from "react";
import { HelpCircle, ArrowRight } from "lucide-react";
import { OpenQuestionItem } from "@/types/meeting";

interface OpenQuestionsSectionProps {
  questions?: OpenQuestionItem[];
  onViewAll?: () => void;
}

export function OpenQuestionsSection({
  questions = [
    {
      question: "Will we be able to meet the Q2 timeline with current resources?",
      author: "Alex",
      timestamp: "12:15",
    },
    {
      question: "What's the expected ROI for the marketing campaign?",
      author: "Priya",
      timestamp: "18:03",
    },
  ],
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
          </div>
          <button
            onClick={onViewAll}
            className="inline-flex items-center gap-1 text-xs font-semibold text-indigo-600 hover:text-indigo-700 transition-colors"
          >
            <span>View all</span>
            <ArrowRight className="w-3 h-3" />
          </button>
        </div>

        {/* Questions List */}
        <div className="divide-y divide-slate-100">
          {questions.map((item, idx) => (
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
      </div>
    </div>
  );
}
