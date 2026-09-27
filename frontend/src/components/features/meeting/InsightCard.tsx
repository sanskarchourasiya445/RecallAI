"use client";

import React from "react";
import {
  FileText,
  CheckCircle2,
  Zap,
  HelpCircle,
  ChevronRight,
} from "lucide-react";

interface InsightCardsGridProps {
  summaryCount?: string;
  decisionsCount?: number;
  actionItemsCount?: number;
  openQuestionsCount?: number;
  isLoading?: boolean;
  onSelectCard?: (type: string) => void;
}

export function InsightCardsGrid({
  summaryCount = "Key points & insights",
  decisionsCount = 4,
  actionItemsCount = 3,
  openQuestionsCount = 2,
  isLoading = false,
  onSelectCard,
}: InsightCardsGridProps) {
  const cards = [
    {
      id: "summary",
      title: "Summary",
      subtitle: summaryCount,
      icon: FileText,
      bg: "bg-[#F8F9FE]",
      border: "border-[#E5EAFA]",
      iconBg: "bg-indigo-600 text-white",
      arrowColor: "text-indigo-400 group-hover:text-indigo-600",
    },
    {
      id: "decisions",
      title: "Decisions",
      subtitle: `${decisionsCount} key decisions`,
      icon: CheckCircle2,
      bg: "bg-[#F3FAF6]",
      border: "border-[#DEF1E7]",
      iconBg: "bg-emerald-600 text-white",
      arrowColor: "text-emerald-400 group-hover:text-emerald-600",
    },
    {
      id: "action_items",
      title: "Action Items",
      subtitle: `${actionItemsCount} open tasks`,
      icon: Zap,
      bg: "bg-[#FEF9F2]",
      border: "border-[#FBEED9]",
      iconBg: "bg-amber-500 text-white",
      arrowColor: "text-amber-400 group-hover:text-amber-600",
    },
    {
      id: "open_questions",
      title: "Open Questions",
      subtitle: `${openQuestionsCount} questions`,
      icon: HelpCircle,
      bg: "bg-[#FCF5F7]",
      border: "border-[#F9E2E8]",
      iconBg: "bg-pink-500 text-white",
      arrowColor: "text-pink-400 group-hover:text-pink-600",
    },
  ];

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 animate-pulse">
        {[1, 2, 3, 4].map((i) => (
          <div
            key={i}
            className="h-[92px] sm:h-[96px] rounded-xl border border-slate-200 bg-white px-3.5 py-3 flex items-center justify-between"
          >
            <div className="flex items-center gap-3 w-full">
              <div className="w-8 h-8 rounded-lg bg-slate-200 shrink-0" />
              <div className="space-y-1.5 flex-1">
                <div className="h-4 bg-slate-200 rounded w-1/2" />
                <div className="h-3 bg-slate-100 rounded w-3/4" />
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
      {cards.map((card) => {
        const Icon = card.icon;
        return (
          <div
            key={card.id}
            onClick={() => onSelectCard && onSelectCard(card.id)}
            className={`group h-[92px] sm:h-[96px] rounded-xl border ${card.border} ${card.bg} px-3.5 py-3 flex items-center justify-between cursor-pointer transition-all duration-150 shadow-card hover:shadow-card-hover hover:-translate-y-0.5`}
          >
            <div className="flex items-center gap-3 min-w-0 flex-1">
              <div
                className={`w-8 h-8 rounded-lg ${card.iconBg} flex items-center justify-center shadow-2xs shrink-0`}
              >
                <Icon className="w-4 h-4" />
              </div>
              <div className="leading-tight min-w-0 flex-1">
                <h4 className="text-[14px] sm:text-[15px] font-semibold text-slate-900 tracking-tight whitespace-nowrap">
                  {card.title}
                </h4>
                <p className="text-[12px] text-slate-500 mt-1 font-normal leading-snug line-clamp-2 break-words">
                  {card.subtitle}
                </p>
              </div>
            </div>
            <ChevronRight
              className={`w-3.5 h-3.5 ${card.arrowColor} transition-transform group-hover:translate-x-0.5 shrink-0 ml-1.5`}
            />
          </div>
        );
      })}
    </div>
  );
}
