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
    <div className="w-full bg-white rounded-xl border border-slate-200/90 p-1.5 shadow-sm overflow-x-auto">
      <div className="flex items-center gap-1.5 min-w-max">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;

          return (
            <button
              key={tab.id}
              onClick={() => onChangeTab(tab.id)}
              className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                isActive
                  ? "bg-indigo-600 text-white shadow-xs"
                  : "text-slate-600 hover:text-slate-900 hover:bg-slate-50"
              }`}
            >
              <Icon
                className={`w-3.5 h-3.5 ${
                  isActive ? "text-white" : "text-slate-400"
                }`}
              />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
