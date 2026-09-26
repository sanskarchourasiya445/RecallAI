"use client";

import React from "react";
import {
  LayoutDashboard,
  Calendar,
  Video,
  MessageSquare,
  Zap,
  Settings,
  ChevronRight,
  Plus,
} from "lucide-react";

interface SidebarProps {
  activeNav: string;
  setActiveNav: (nav: string) => void;
  pendingActionsCount?: number;
  onNewMeetingClick: () => void;
}

export function Sidebar({
  activeNav,
  setActiveNav,
  pendingActionsCount = 3,
  onNewMeetingClick,
}: SidebarProps) {
  const navItems = [
    { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
    { id: "meetings", label: "Meetings", icon: Calendar },
    { id: "upload", label: "Upload / YouTube", icon: Video },
    { id: "chat", label: "AI Chat", icon: MessageSquare },
    { id: "actions", label: "Actions", icon: Zap, badge: pendingActionsCount },
    { id: "settings", label: "Settings", icon: Settings },
  ];

  return (
    <aside className="w-[235px] shrink-0 h-screen sticky top-0 bg-[#0B1224] text-slate-300 flex flex-col justify-between p-3.5 border-r border-[#172036] select-none z-30">
      {/* Top Section */}
      <div>
        {/* Brand Logo & Title */}
        <div className="flex items-center gap-3 px-2 pt-1 pb-5">
          {/* Waveform Graphic Mark */}
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-indigo-500 to-purple-600 flex items-center justify-center gap-[3px] p-1.5 shadow-md shadow-indigo-500/20 shrink-0">
            <span className="w-[2.5px] h-3 bg-cyan-300 rounded-full animate-pulse" />
            <span className="w-[2.5px] h-5 bg-white rounded-full" />
            <span className="w-[2.5px] h-2 bg-indigo-200 rounded-full" />
            <span className="w-[2.5px] h-4 bg-purple-200 rounded-full" />
          </div>
          <div className="min-w-0">
            <h1 className="text-[15px] font-bold text-white tracking-tight leading-none">
              RecallAI
            </h1>
            <p className="text-[11px] text-slate-400 mt-1 font-normal leading-none truncate">
              Understand. Remember. Act.
            </p>
          </div>
        </div>

        {/* Navigation Items (height 42-44px) */}
        <nav className="space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeNav === item.id;
            return (
              <button
                key={item.id}
                onClick={() => {
                  if (item.id === "upload") {
                    onNewMeetingClick();
                  } else {
                    setActiveNav(item.id);
                  }
                }}
                className={`w-full h-[42px] flex items-center justify-between px-3 rounded-xl text-xs font-medium transition-all ${
                  isActive
                    ? "bg-indigo-600 text-white shadow-xs font-semibold"
                    : "text-slate-400 hover:text-white hover:bg-[#141c33]"
                }`}
              >
                <div className="flex items-center gap-3">
                  <Icon
                    className={`w-4 h-4 shrink-0 ${
                      isActive ? "text-white" : "text-slate-400"
                    }`}
                  />
                  <span className="truncate">{item.label}</span>
                </div>
                {item.badge !== undefined && item.badge > 0 && (
                  <span
                    className={`px-1.5 py-0.2 text-[10px] font-bold rounded-full ${
                      isActive
                        ? "bg-white text-indigo-700"
                        : "bg-[#25284b] text-indigo-300 border border-indigo-500/20"
                    }`}
                  >
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Lower Section: Promo Card & Profile */}
      <div className="space-y-3 pt-2">
        {/* Compact Promo Card */}
        <div className="relative overflow-hidden rounded-xl bg-gradient-to-b from-[#151c33] via-[#10162a] to-[#0c1020] border border-[#202947] p-3 text-white shadow-sm">
          {/* Subtle Soundwave Backdrop */}
          <div className="flex items-center justify-center gap-1 opacity-70 mb-2 py-0.5">
            <span className="w-0.5 h-2.5 bg-indigo-400 rounded-full" />
            <span className="w-0.5 h-5 bg-purple-400 rounded-full" />
            <span className="w-0.5 h-3 bg-blue-400 rounded-full" />
            <span className="w-0.5 h-6 bg-cyan-300 rounded-full" />
            <span className="w-0.5 h-4 bg-indigo-300 rounded-full" />
            <span className="w-0.5 h-7 bg-purple-500 rounded-full" />
            <span className="w-0.5 h-3.5 bg-blue-300 rounded-full" />
            <span className="w-0.5 h-5 bg-cyan-400 rounded-full" />
            <span className="w-0.5 h-2 bg-indigo-400 rounded-full" />
          </div>

          <h3 className="text-xs font-semibold text-white tracking-tight leading-snug">
            Turn your meetings into action.
          </h3>
          <p className="text-[11px] text-slate-400 mt-1 leading-normal font-normal">
            AI-powered insights, summaries, and action items.
          </p>

          <button
            onClick={onNewMeetingClick}
            className="w-full mt-2.5 h-8 px-2.5 rounded-lg bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white text-xs font-semibold shadow-xs transition-all flex items-center justify-center gap-1.5 active:scale-[0.98]"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>+ New Meeting</span>
          </button>
        </div>

        {/* User Profile Footer */}
        <div className="flex items-center justify-between px-2 py-1.5 rounded-xl hover:bg-[#141c33] transition-colors cursor-pointer">
          <div className="flex items-center gap-2.5 min-w-0">
            {/* Avatar SC */}
            <div className="w-7 h-7 rounded-full bg-cyan-100 border border-cyan-200 text-cyan-900 font-bold text-xs flex items-center justify-center shrink-0">
              SC
            </div>
            <div className="min-w-0 leading-tight">
              <p className="text-xs font-semibold text-white truncate">
                Sanskar Chourasiya
              </p>
              <div className="flex items-center gap-1.5 mt-0.5">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 inline-block" />
                <span className="text-[10px] text-slate-400 font-normal">Free Plan</span>
              </div>
            </div>
          </div>
          <ChevronRight className="w-3.5 h-3.5 text-slate-500 shrink-0" />
        </div>
      </div>
    </aside>
  );
}
