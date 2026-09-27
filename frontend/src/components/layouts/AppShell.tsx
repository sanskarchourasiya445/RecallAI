"use client";

import React, { useState, useMemo } from "react";
import { usePathname, useRouter } from "next/navigation";
import { Sidebar } from "./Sidebar";
import { TopBar } from "./TopBar";
import { X, Sparkles } from "lucide-react";

interface AppShellProps {
  children: React.ReactNode;
  rightPanel: React.ReactNode;
  onNewMeetingClick: () => void;
  onSearch?: (query: string) => void;
  currentNav?: string;
}

export function AppShell({
  children,
  rightPanel,
  onNewMeetingClick,
  onSearch,
  currentNav,
}: AppShellProps) {
  const pathname = usePathname();
  const router = useRouter();

  const activeNav = useMemo(() => {
    if (currentNav) return currentNav;
    if (!pathname || pathname === "/") return "meetings";
    if (pathname.startsWith("/meetings")) return "meetings";
    if (pathname.startsWith("/actions")) return "actions";
    if (pathname.startsWith("/settings")) return "settings";
    return "meetings";
  }, [pathname, currentNav]);

  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);
  const [isMobileAIOpen, setIsMobileAIOpen] = useState(false);

  const handleNavSelect = (navId: string) => {
    if (navId === "dashboard") {
      router.push("/");
    } else if (navId === "meetings") {
      router.push("/meetings");
    } else if (navId === "actions") {
      router.push("/actions");
    } else if (navId === "settings") {
      router.push("/settings");
    } else if (navId === "chat") {
      setIsMobileAIOpen(true);
    }
  };

  return (
    <div className="flex min-h-screen bg-[#F6F8FC] text-slate-800 antialiased font-sans">
      {/* 1. LEFT COLLAPSIBLE / SLIDING SIDEBAR (240-245px expanded, 68-72px collapsed) */}
      <Sidebar
        activeNav={activeNav}
        setActiveNav={handleNavSelect}
        isCollapsed={isSidebarCollapsed}
        onToggleCollapse={() => setIsSidebarCollapsed((prev) => !prev)}
        isMobileOpen={isMobileSidebarOpen}
        onCloseMobile={() => setIsMobileSidebarOpen(false)}
        pendingActionsCount={3}
        onNewMeetingClick={onNewMeetingClick}
      />

      {/* 2. CENTRAL WORKSPACE + TOP BAR (flexible width, reclaims space when sidebar collapses) */}
      <div className="flex-1 min-w-0 flex flex-col transition-all duration-200">
        {/* Top Header Bar with Global Search, User Profile, and Mobile Triggers */}
        <TopBar
          onSearch={onSearch}
          pendingNotificationsCount={1}
          onOpenMobileMenu={() => setIsMobileSidebarOpen(true)}
          onToggleMobileAI={() => setIsMobileAIOpen((prev) => !prev)}
        />

        {/* Main Content Area */}
        <main className="flex-1 p-4 md:p-5 overflow-y-auto space-y-4">
          {children}
        </main>
      </div>

      {/* 3. RIGHT AI PANEL (~360–370px wide, pinned full-height workspace) */}
      <aside className="w-[360px] xl:w-[370px] shrink-0 border-l border-slate-200/80 bg-white/40 p-3 h-screen sticky top-0 overflow-hidden hidden xl:flex flex-col gap-2.5">
        {rightPanel}
      </aside>

      {/* 4. TABLET & MOBILE AI PANEL DRAWER (< xl screens) */}
      {isMobileAIOpen && (
        <>
          <div
            onClick={() => setIsMobileAIOpen(false)}
            className="fixed inset-0 z-40 bg-slate-950/60 backdrop-blur-xs xl:hidden animate-in fade-in duration-200"
          />
          <div className="fixed top-0 right-0 bottom-0 z-50 w-full max-w-[380px] bg-[#F6F8FC] border-l border-slate-200 p-3.5 flex flex-col gap-3 shadow-2xl xl:hidden animate-in slide-in-from-right duration-200">
            <div className="flex items-center justify-between pb-1 border-b border-slate-200/80">
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-indigo-600" />
                <span className="text-xs font-bold text-slate-900">RecallAI Intelligence Panel</span>
              </div>
              <button
                onClick={() => setIsMobileAIOpen(false)}
                className="p-1 rounded-lg text-slate-500 hover:text-slate-800 hover:bg-slate-200/60"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            <div className="flex-1 overflow-hidden flex flex-col gap-3">
              {rightPanel}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
