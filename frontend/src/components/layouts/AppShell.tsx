"use client";

import React, { useState } from "react";
import { Sidebar } from "./Sidebar";
import { TopBar } from "./TopBar";

interface AppShellProps {
  children: React.ReactNode;
  rightPanel: React.ReactNode;
  onNewMeetingClick: () => void;
  onSearch?: (query: string) => void;
}

export function AppShell({
  children,
  rightPanel,
  onNewMeetingClick,
  onSearch,
}: AppShellProps) {
  const [activeNav, setActiveNav] = useState("dashboard");

  return (
    <div className="flex min-h-screen bg-[#F6F8FC] text-slate-800 antialiased font-sans">
      {/* 1. LEFT FIXED SIDEBAR (~235px wide, deep navy) */}
      <Sidebar
        activeNav={activeNav}
        setActiveNav={setActiveNav}
        pendingActionsCount={3}
        onNewMeetingClick={onNewMeetingClick}
      />

      {/* 2. CENTRAL WORKSPACE + TOP BAR */}
      <div className="flex-1 min-w-0 flex flex-col">
        {/* Top Header Bar with Global Search & User Profile */}
        <TopBar onSearch={onSearch} pendingNotificationsCount={1} />

        {/* Main Content Area */}
        <main className="flex-1 p-4 overflow-y-auto space-y-3">
          {children}
        </main>
      </div>

      {/* 3. RIGHT AI PANEL (~365px wide, contextual AI workspace) */}
      <aside className="w-[365px] shrink-0 border-l border-slate-200/80 bg-white/40 p-3.5 overflow-y-auto space-y-3.5 hidden xl:block">
        {rightPanel}
      </aside>
    </div>
  );
}
