"use client";

import React, { useState, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Search, Bell, ChevronDown, Menu } from "lucide-react";

interface TopBarProps {
  onSearch?: (query: string) => void;
  pendingNotificationsCount?: number;
  onOpenMobileMenu?: () => void;
  onToggleMobileAI?: () => void;
}

export function TopBar({
  onSearch,
  pendingNotificationsCount = 1,
  onOpenMobileMenu,
  onToggleMobileAI,
}: TopBarProps) {
  const router = useRouter();
  const [searchVal, setSearchVal] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const handleGlobalKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        inputRef.current?.focus();
      }
    };
    window.addEventListener("keydown", handleGlobalKeyDown);
    return () => window.removeEventListener("keydown", handleGlobalKeyDown);
  }, []);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      const trimmed = searchVal.trim();
      if (onSearch) {
        onSearch(trimmed);
      } else if (trimmed) {
        router.push(`/search?q=${encodeURIComponent(trimmed)}`);
      }
    }
  };

  return (
    <header className="h-[54px] px-4 md:px-5 flex items-center justify-between gap-3 border-b border-slate-200/80 bg-white/85 backdrop-blur-md sticky top-0 z-20">
      <div className="flex items-center gap-2 flex-1 max-w-[620px]">
        {/* Mobile Hamburger Menu Toggle */}
        <button
          onClick={onOpenMobileMenu}
          aria-label="Open navigation menu"
          className="md:hidden p-1.5 rounded-lg text-slate-500 hover:text-slate-700 hover:bg-slate-100"
        >
          <Menu className="w-5 h-5" />
        </button>

        {/* Global Search Bar */}
        <div className="relative w-full">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            ref={inputRef}
            type="text"
            value={searchVal}
            onChange={(e) => setSearchVal(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Search meetings, keywords, or ask anything..."
            className="w-full h-8 pl-9 pr-12 rounded-lg bg-slate-50/90 hover:bg-slate-100/70 focus:bg-white text-xs text-slate-800 placeholder:text-slate-400 border border-slate-200 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500/20 transition-all shadow-2xs"
          />
          <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center pointer-events-none">
            <kbd className="px-1.5 py-0.2 text-[10px] font-semibold text-slate-400 bg-white border border-slate-200 rounded shadow-2xs">
              ⌘ K
            </kbd>
          </div>
        </div>
      </div>

      {/* Top Right User Area */}
      <div className="flex items-center gap-2.5 shrink-0">
        {/* Mobile/Tablet AI Assistant Drawer Trigger */}
        <button
          onClick={onToggleMobileAI}
          aria-label="Toggle AI Assistant"
          className="xl:hidden flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-indigo-50 hover:bg-indigo-100/80 border border-indigo-200/70 text-indigo-700 text-xs font-semibold shadow-2xs transition-all active:scale-95"
        >
          <span className="w-2 h-2 rounded-full bg-indigo-500 animate-pulse" />
          <span className="hidden sm:inline">AI Chat</span>
        </button>

        {/* Notification Bell */}
        <button
          aria-label="Notifications"
          className="relative p-1.5 rounded-lg text-slate-500 hover:text-slate-700 hover:bg-slate-100 transition-colors"
        >
          <Bell className="w-4 h-4" />
          {pendingNotificationsCount > 0 && (
            <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 rounded-full bg-blue-600 ring-2 ring-white" />
          )}
        </button>

        {/* User Avatar + Name + Dropdown */}
        <div className="flex items-center gap-2 pl-1 cursor-pointer hover:opacity-90 transition-opacity">
          <div className="w-7 h-7 rounded-full bg-[#0B1224] text-white font-bold text-[11px] flex items-center justify-center shadow-xs">
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
