"use client";

import React from "react";
import {
  LayoutDashboard,
  Calendar,
  Search,
  Video,
  MessageSquare,
  Zap,
  Settings,
  ChevronLeft,
  ChevronRight,
  Plus,
  X,
} from "lucide-react";

interface SidebarProps {
  activeNav: string;
  setActiveNav: (nav: string) => void;
  isCollapsed: boolean;
  onToggleCollapse: () => void;
  isMobileOpen: boolean;
  onCloseMobile: () => void;
  pendingActionsCount?: number;
  onNewMeetingClick: () => void;
}

export function Sidebar({
  activeNav,
  setActiveNav,
  isCollapsed,
  onToggleCollapse,
  isMobileOpen,
  onCloseMobile,
  pendingActionsCount = 3,
  onNewMeetingClick,
}: SidebarProps) {
  const navItems = [
    { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
    { id: "meetings", label: "Meetings", icon: Calendar },
    { id: "search", label: "Global Search", icon: Search },
    { id: "upload", label: "Upload / YouTube", icon: Video },
    { id: "chat", label: "AI Chat", icon: MessageSquare },
    { id: "actions", label: "Actions", icon: Zap, badge: pendingActionsCount },
    { id: "settings", label: "Settings", icon: Settings },
  ];

  return (
    <>
      {/* Mobile Drawer Backdrop Overlay */}
      {isMobileOpen && (
        <div
          onClick={onCloseMobile}
          className="fixed inset-0 z-40 bg-slate-950/60 backdrop-blur-xs md:hidden animate-in fade-in duration-200"
        />
      )}

      {/* Sidebar Container */}
      <aside
        className={`fixed top-0 bottom-0 left-0 z-50 md:sticky md:top-0 h-screen bg-[#0B1224] text-slate-300 flex flex-col justify-between border-r border-[#172036] select-none transition-all duration-200 ease-in-out shrink-0 ${
          /* Desktop Width */
          isCollapsed ? "md:w-[72px]" : "md:w-[245px]"
        } ${
          /* Mobile Drawer Position */
          isMobileOpen
            ? "translate-x-0 w-[245px] shadow-2xl"
            : "-translate-x-full md:translate-x-0"
        } ${isCollapsed ? "p-2.5" : "p-3.5"}`}
      >
        {/* Top: Brand Header + Navigation */}
        <div className="flex flex-col">
          {/* Header Row: Logo & Collapse / Close Controls */}
          <div
            className={`flex items-center pt-1 pb-4 ${
              isCollapsed ? "flex-col gap-2.5 justify-center items-center" : "justify-between px-1.5"
            }`}
          >
            {/* Logo Mark + Brand Text (if expanded) */}
            <div
              onClick={isCollapsed ? onToggleCollapse : undefined}
              className={`flex items-center gap-2.5 min-w-0 ${isCollapsed ? "cursor-pointer" : ""}`}
              title={isCollapsed ? "Expand sidebar" : undefined}
            >
              <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-indigo-500 to-purple-600 flex items-center justify-center gap-[2.5px] p-1.5 shadow-md shadow-indigo-500/20 shrink-0">
                <span className="w-[2.5px] h-3 bg-cyan-300 rounded-full animate-pulse" />
                <span className="w-[2.5px] h-5 bg-white rounded-full" />
                <span className="w-[2.5px] h-2 bg-indigo-200 rounded-full" />
                <span className="w-[2.5px] h-4 bg-purple-200 rounded-full" />
              </div>

              {!isCollapsed && (
                <div className="min-w-0">
                  <h1 className="text-[15px] font-bold text-white tracking-tight leading-none">
                    RecallAI
                  </h1>
                  <p className="text-[11px] text-slate-400 mt-1 font-normal leading-none truncate">
                    Understand. Remember. Act.
                  </p>
                </div>
              )}
            </div>

            {/* Desktop Collapse / Expand Toggle Button */}
            <button
              onClick={onToggleCollapse}
              title={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
              className="hidden md:flex items-center justify-center w-6 h-6 rounded-md text-slate-400 hover:text-white hover:bg-[#16203a] transition-colors shrink-0"
            >
              {isCollapsed ? (
                <ChevronRight className="w-4 h-4" />
              ) : (
                <ChevronLeft className="w-4 h-4" />
              )}
            </button>

            {/* Mobile Close Button */}
            <button
              onClick={onCloseMobile}
              className="md:hidden p-1 rounded-md text-slate-400 hover:text-white hover:bg-[#16203a]"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Navigation Items */}
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
                    if (isMobileOpen) onCloseMobile();
                  }}
                  title={isCollapsed ? item.label : undefined}
                  className={`relative w-full h-[42px] flex items-center rounded-xl text-xs font-medium transition-all ${
                    isCollapsed
                      ? "justify-center px-0"
                      : "justify-between px-3"
                  } ${
                    isActive
                      ? "bg-indigo-600 text-white shadow-xs font-semibold"
                      : "text-slate-400 hover:text-white hover:bg-[#141c33]"
                  }`}
                >
                  <div
                    className={`flex items-center gap-3 min-w-0 ${
                      isCollapsed ? "justify-center" : ""
                    }`}
                  >
                    <Icon
                      className={`w-4 h-4 shrink-0 ${
                        isActive ? "text-white" : "text-slate-400"
                      }`}
                    />
                    {!isCollapsed && <span className="truncate">{item.label}</span>}
                  </div>

                  {/* Badges */}
                  {item.badge !== undefined && item.badge > 0 && (
                    <>
                      {!isCollapsed ? (
                        <span
                          className={`px-1.5 py-0.2 text-[10px] font-bold rounded-full shrink-0 ${
                            isActive
                              ? "bg-white text-indigo-700"
                              : "bg-[#25284b] text-indigo-300 border border-indigo-500/20"
                          }`}
                        >
                          {item.badge}
                        </span>
                      ) : (
                        <span className="absolute top-1 right-2 w-2 h-2 rounded-full bg-indigo-500 ring-2 ring-[#0B1224]" />
                      )}
                    </>
                  )}
                </button>
              );
            })}
          </nav>
        </div>

        {/* Lower Section: New Meeting Card & Profile */}
        <div className="space-y-3 pt-2">
          {/* New Meeting Card / Collapsed Button */}
          {!isCollapsed ? (
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
          ) : (
            <div className="flex justify-center">
              <button
                onClick={onNewMeetingClick}
                title="New Meeting"
                className="w-10 h-10 rounded-xl bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white flex items-center justify-center shadow-md shadow-indigo-600/30 active:scale-95 transition-all"
              >
                <Plus className="w-4 h-4" />
              </button>
            </div>
          )}

          {/* User Profile Footer */}
          <div
            className={`flex items-center rounded-xl hover:bg-[#141c33] transition-colors cursor-pointer ${
              isCollapsed
                ? "justify-center py-2"
                : "justify-between px-2 py-1.5"
            }`}
          >
            <div className="flex items-center gap-2.5 min-w-0">
              {/* Avatar SC */}
              <div className="w-7 h-7 rounded-full bg-cyan-100 border border-cyan-200 text-cyan-900 font-bold text-xs flex items-center justify-center shrink-0">
                SC
              </div>
              {!isCollapsed && (
                <div className="min-w-0 leading-tight">
                  <p className="text-xs font-semibold text-white truncate">
                    Sanskar Chourasiya
                  </p>
                  <div className="flex items-center gap-1.5 mt-0.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 inline-block" />
                    <span className="text-[10px] text-slate-400 font-normal">
                      Free Plan
                    </span>
                  </div>
                </div>
              )}
            </div>
            {!isCollapsed && (
              <ChevronRight className="w-3.5 h-3.5 text-slate-500 shrink-0" />
            )}
          </div>
        </div>
      </aside>
    </>
  );
}
