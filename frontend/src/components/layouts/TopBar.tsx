"use client";

import React, { useState } from "react";
import { Search, Bell, ChevronDown } from "lucide-react";

interface TopBarProps {
  onSearch?: (query: string) => void;
  pendingNotificationsCount?: number;
}

export function TopBar({ onSearch, pendingNotificationsCount = 1 }: TopBarProps) {
  const [searchVal, setSearchVal] = useState("");

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && onSearch) {
      onSearch(searchVal);
    }
  };

  return (
    <header className="h-14 px-6 flex items-center justify-between gap-4 border-b border-slate-200/80 bg-white/70 backdrop-blur-md sticky top-0 z-20">
      {/* Global Search Bar (approx 550-600px, not full screen) */}
      <div className="relative w-full max-w-[580px]">
        <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
        <input
          type="text"
          value={searchVal}
          onChange={(e) => setSearchVal(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Search meetings, keywords, or ask anything..."
          className="w-full h-9 pl-9 pr-14 rounded-xl bg-slate-50/80 hover:bg-slate-100/70 focus:bg-white text-xs text-slate-800 placeholder:text-slate-400 border border-slate-200 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/10 transition-all shadow-sm"
        />
        <div className="absolute right-2.5 top-1/2 -translate-y-1/2 flex items-center gap-0.5 pointer-events-none">
          <kbd className="px-1.5 py-0.5 text-[10px] font-semibold text-slate-400 bg-white border border-slate-200 rounded shadow-[0_1px_1px_rgba(0,0,0,0.05)]">
            ⌘ K
          </kbd>
        </div>
      </div>

      {/* Top Right User Area */}
      <div className="flex items-center gap-4 shrink-0">
        {/* Notification Bell */}
        <button
          aria-label="Notifications"
          className="relative p-2 rounded-xl text-slate-500 hover:text-slate-700 hover:bg-slate-100 transition-colors"
        >
          <Bell className="w-4 h-4" />
          {pendingNotificationsCount > 0 && (
            <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-blue-600 ring-2 ring-white" />
          )}
        </button>

        {/* User Avatar + Name + Dropdown */}
        <div className="flex items-center gap-2 pl-2 cursor-pointer hover:opacity-90 transition-opacity">
          <div className="w-8 h-8 rounded-full bg-[#101935] text-white font-bold text-xs flex items-center justify-center shadow-sm">
            SC
          </div>
          <span className="text-xs font-semibold text-slate-800 hidden sm:inline-block">
            Sanskar Chourasiya
          </span>
          <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
        </div>
      </div>
    </header>
  );
}
