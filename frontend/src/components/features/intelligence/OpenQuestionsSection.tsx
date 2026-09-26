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
    <div className="bg-white rounded-2xl border border-slate-200/90 p-4 shadow-sm flex flex-col justify-between h-full">
      <div>
        {/* Header */}
        <div className="flex items-center justify-between gap-2 pb-3 border-b border-slate-100">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-pink-100 flex items-center justify-center">
              <HelpCircle className="w-3.5 h-3.5 text-pink-500" />
            </div>
            <h3 className="text-xs font-bold text-slate-900 tracking-tight">
              Open Questions
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

        {/* Questions List */}
        <div className="divide-y divide-slate-100 mt-2">
          {questions.map((item, idx) => (
            <div key={idx} className="py-3 first:pt-1 last:pb-1 flex items-start gap-2.5">
              <span className="text-xs font-bold text-slate-900 mt-0.5 shrink-0">
                {idx + 1}.
              </span>
              <div className="flex-1 min-w-0">
                <p className="text-xs font-medium text-slate-800 leading-snug">
                  {item.question}
                </p>
                <p className="text-[11px] text-slate-400 font-normal mt-1.5">
                  Raised by: {item.author || "Alex"} • {item.timestamp || "12:15"}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
