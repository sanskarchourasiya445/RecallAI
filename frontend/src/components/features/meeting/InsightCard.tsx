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
  onSelectCard?: (type: string) => void;
}

export function InsightCardsGrid({
  summaryCount = "Key points & insights",
  decisionsCount = 3,
  actionItemsCount = 6,
  openQuestionsCount = 2,
  onSelectCard,
}: InsightCardsGridProps) {
  const cards = [
    {
      id: "summary",
      title: "Summary",
      subtitle: summaryCount,
      icon: FileText,
      bg: "bg-[#f5f6ff]",
      border: "border-indigo-100",
      iconBg: "bg-indigo-500 text-white",
      arrowColor: "text-indigo-400 group-hover:text-indigo-600",
    },
    {
      id: "decisions",
      title: "Decisions",
      subtitle: `${decisionsCount} key decisions`,
      icon: CheckCircle2,
      bg: "bg-[#f0faf5]",
      border: "border-emerald-100",
      iconBg: "bg-emerald-500 text-white",
      arrowColor: "text-emerald-400 group-hover:text-emerald-600",
    },
    {
      id: "action_items",
      title: "Action Items",
      subtitle: `${actionItemsCount} open tasks`,
      icon: Zap,
      bg: "bg-[#fff9f0]",
      border: "border-amber-100",
      iconBg: "bg-amber-500 text-white",
      arrowColor: "text-amber-400 group-hover:text-amber-600",
    },
    {
      id: "open_questions",
      title: "Open Questions",
      subtitle: `${openQuestionsCount} questions`,
      icon: HelpCircle,
      bg: "bg-[#fff5f7]",
      border: "border-pink-100",
      iconBg: "bg-pink-500 text-white",
      arrowColor: "text-pink-400 group-hover:text-pink-600",
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5">
      {cards.map((card) => {
        const Icon = card.icon;
        return (
          <div
            key={card.id}
            onClick={() => onSelectCard && onSelectCard(card.id)}
            className={`group rounded-2xl border ${card.border} ${card.bg} p-3.5 flex items-center justify-between cursor-pointer transition-all duration-150 hover:shadow-sm hover:-translate-y-0.5`}
          >
            <div className="flex items-center gap-3">
              <div
                className={`w-9 h-9 rounded-xl ${card.iconBg} flex items-center justify-center shadow-xs shrink-0`}
              >
                <Icon className="w-4 h-4" />
              </div>
              <div className="leading-tight">
                <h4 className="text-xs font-bold text-slate-900">{card.title}</h4>
                <p className="text-[11px] text-slate-500 mt-0.5 font-medium">
                  {card.subtitle}
                </p>
              </div>
            </div>
            <ChevronRight
              className={`w-4 h-4 ${card.arrowColor} transition-transform group-hover:translate-x-0.5 shrink-0`}
            />
          </div>
        );
      })}
    </div>
  );
}
