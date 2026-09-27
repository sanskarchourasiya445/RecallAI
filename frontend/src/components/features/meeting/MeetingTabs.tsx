"use client";

import React from "react";
import {
  Home,
  FileText,
  AlignLeft,
  CheckCircle2,
  CheckSquare,
  HelpCircle,
  Link2,
} from "lucide-react";

export type MeetingTabId =
  | "overview"
  | "transcript"
  | "summary"
  | "decisions"
  | "action_items"
  | "open_questions"
  | "sources";

interface MeetingTabsProps {
  activeTab: MeetingTabId;
  onChangeTab: (tab: MeetingTabId) => void;
}

export function MeetingTabs({ activeTab, onChangeTab }: MeetingTabsProps) {
  const tabs = [
    { id: "overview" as MeetingTabId, label: "Overview", icon: Home },
    { id: "transcript" as MeetingTabId, label: "Transcript", icon: FileText },
    { id: "summary" as MeetingTabId, label: "Summary", icon: AlignLeft },
    { id: "decisions" as MeetingTabId, label: "Decisions", icon: CheckCircle2 },
    { id: "action_items" as MeetingTabId, label: "Action Items", icon: CheckSquare },
    { id: "open_questions" as MeetingTabId, label: "Open Questions", icon: HelpCircle },
    { id: "sources" as MeetingTabId, label: "Sources", icon: Link2 },
  ];

  return (
    <div className="w-full bg-white rounded-xl border border-slate-200/80 p-1 shadow-card">
      <div
        className="w-full gap-1"
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr 1fr 1fr 1.15fr 1.25fr 0.9fr",
        }}
      >
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;

          return (
            <button
              key={tab.id}
              onClick={() => onChangeTab(tab.id)}
              title={tab.label}
              className={`w-full h-8 flex items-center justify-center gap-1 sm:gap-1.5 py-1 px-1.5 sm:px-2 rounded-lg text-[11px] sm:text-xs font-medium transition-all ${
                isActive
                  ? "bg-indigo-600 text-white font-semibold shadow-xs"
                  : "text-slate-600 hover:text-slate-900 hover:bg-slate-50/80"
              }`}
            >
              <Icon
                className={`w-3.5 h-3.5 shrink-0 ${
                  isActive ? "text-white" : "text-slate-400"
                }`}
              />
              <span className="whitespace-nowrap select-none">{tab.label}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
