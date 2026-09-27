"use client";

import React, { useState } from "react";
import { AppShell } from "@/components/layouts/AppShell";
import { MeetingHeader } from "@/components/features/meeting/MeetingHeader";
import { MeetingTabs, MeetingTabId } from "@/components/features/meeting/MeetingTabs";
import { InsightCardsGrid } from "@/components/features/meeting/InsightCard";
import { MeetingSummary } from "@/components/features/meeting/MeetingSummary";
import { MediaPreview } from "@/components/features/meeting/MediaPreview";
import { DecisionsSection } from "@/components/features/intelligence/DecisionsSection";
import { ActionItemsSection } from "@/components/features/intelligence/ActionItemsSection";
import { OpenQuestionsSection } from "@/components/features/intelligence/OpenQuestionsSection";
import { SourcesSection } from "@/components/features/intelligence/SourcesSection";
import { AIChat } from "@/components/features/chat/AIChat";
import { QuickActions } from "@/components/features/actions/QuickActions";
import { NewMeetingModal } from "@/components/features/meeting/NewMeetingModal";
import { TranscriptModal } from "@/components/features/meeting/TranscriptModal";
import { useMeeting, DEMO_SESSION_ID } from "@/lib/hooks/useMeeting";
import { AlertCircle, RefreshCw, WifiOff } from "lucide-react";

interface MeetingWorkspaceProps {
  sessionId?: string;
  initialTab?: MeetingTabId;
}

export function MeetingWorkspace({
  sessionId = DEMO_SESSION_ID,
  initialTab = "overview",
}: MeetingWorkspaceProps) {
  const [activeTab, setActiveTab] = useState<MeetingTabId>(initialTab);
  const [isNewMeetingOpen, setIsNewMeetingOpen] = useState(false);
  const [isTranscriptOpen, setIsTranscriptOpen] = useState(false);

  const {
    meeting,
    decisions,
    actionItems,
    openQuestions,
    isLoading,
    isError,
    errorMessage,
    isOfflineFallback,
    refetch,
    toggleAction,
  } = useMeeting(sessionId);

  const handleTabChange = (tab: MeetingTabId) => {
    setActiveTab(tab);
    if (tab === "transcript") {
      setIsTranscriptOpen(true);
    }
  };

  const handleDownload = () => {
    if (!meeting) return;
    const blob = new Blob(
      [
        `RECALLAI INTELLIGENCE REPORT\n`,
        `============================\n`,
        `Title: ${meeting.title}\n`,
        `Session ID: ${meeting.session_id}\n\n`,
        `SUMMARY\n-------\n${meeting.summary}\n\n`,
        `KEY DECISIONS (${decisions.length})\n------------------\n`,
        ...decisions.map((d, i) => `${i + 1}. ${d.decision} [${d.timestamp || ""}]\n`),
        `\nACTION ITEMS (${actionItems.length})\n----------------\n`,
        ...actionItems.map(
          (a, i) => `${i + 1}. [${a.status}] ${a.task} (Owner: ${a.owner || "TBD"}, Due: ${a.deadline || "TBD"})\n`
        ),
        `\nOPEN QUESTIONS (${openQuestions.length})\n-------------------\n`,
        ...openQuestions.map((q, i) => `${i + 1}. ${q.question} (By: ${q.author || "Team"})\n`),
      ],
      { type: "text/plain;charset=utf-8" }
    );
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `recallai-${meeting.session_id}-report.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleShare = () => {
    if (typeof window !== "undefined") {
      navigator.clipboard.writeText(window.location.href);
      alert("Meeting workspace link copied to clipboard!");
    }
  };

  return (
    <AppShell
      currentNav="meetings"
      onNewMeetingClick={() => setIsNewMeetingOpen(true)}
      onSearch={(q) => console.log("Global search:", q)}
      rightPanel={
        <>
          {/* AI Chat Card */}
          <AIChat sessionId={meeting?.session_id || sessionId} />

          {/* Quick Actions Card */}
          <QuickActions
            sessionId={meeting?.session_id || sessionId}
            pendingCount={3}
          />
        </>
      }
    >
      {/* Offline Fallback Notice */}
      {isOfflineFallback && (
        <div className="p-3 rounded-2xl bg-amber-50/80 border border-amber-200 text-xs text-amber-800 flex items-center justify-between gap-3 shadow-2xs">
          <div className="flex items-center gap-2 min-w-0">
            <WifiOff className="w-4 h-4 text-amber-600 shrink-0" />
            <span className="truncate">
              Serving offline demo meeting fixture. Backend server is currently starting or unreachable.
            </span>
          </div>
          <button
            onClick={() => refetch()}
            className="px-2.5 py-1 rounded-lg bg-white border border-amber-300 text-amber-900 font-semibold hover:bg-amber-100 flex items-center gap-1.5 shrink-0"
          >
            <RefreshCw className="w-3 h-3" />
            <span>Reconnect</span>
          </button>
        </div>
      )}

      {/* Error Banner with Retry */}
      {isError && (
        <div className="p-4 rounded-2xl bg-rose-50 border border-rose-200 text-xs text-rose-800 flex items-center justify-between gap-3">
          <div className="flex items-center gap-2.5 min-w-0">
            <AlertCircle className="w-5 h-5 text-rose-600 shrink-0" />
            <div>
              <p className="font-bold">Failed to load meeting intelligence</p>
              <p className="text-rose-600 text-[11px] mt-0.5">{errorMessage}</p>
            </div>
          </div>
          <button
            onClick={() => refetch()}
            className="px-3 py-1.5 rounded-xl bg-rose-600 hover:bg-rose-700 text-white font-bold flex items-center gap-1.5 shrink-0 shadow-xs"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Try Again</span>
          </button>
        </div>
      )}

      {/* 4. MEETING HEADER */}
      <MeetingHeader
        title={meeting?.title || "Product Strategy Meeting"}
        duration="42 min"
        participantsCount={12}
        dateStr="Apr 28, 2025 • 10:00 AM"
        status={meeting?.status || "Completed"}
        isLoading={isLoading}
        onShare={handleShare}
        onDownload={handleDownload}
      />

      {/* 5. MEETING TABS */}
      <MeetingTabs activeTab={activeTab} onChangeTab={handleTabChange} />

      {/* 6. FOUR INSIGHT CARDS */}
      <InsightCardsGrid
        summaryCount="Key points & insights"
        decisionsCount={decisions.length}
        actionItemsCount={actionItems.length}
        openQuestionsCount={openQuestions.length}
        isLoading={isLoading}
        onSelectCard={(id) => {
          if (id === "summary") setActiveTab("summary");
          if (id === "decisions") setActiveTab("decisions");
          if (id === "action_items") setActiveTab("action_items");
          if (id === "open_questions") setActiveTab("open_questions");
        }}
      />

      {/* 7. MAIN SUMMARY + VIDEO AREA (approx 70% Summary / 30% Video) */}
      <div className="grid grid-cols-1 lg:grid-cols-10 gap-3 items-stretch">
        <div className="lg:col-span-7">
          <MeetingSummary
            summary={meeting?.summary || ""}
            isLoading={isLoading}
            onViewFullSummary={() => setActiveTab("summary")}
          />
        </div>
        <div className="lg:col-span-3">
          <MediaPreview
            duration="42:15"
            onViewTranscript={() => setIsTranscriptOpen(true)}
          />
        </div>
      </div>

      {/* 8. LOWER THREE-COLUMN INTELLIGENCE SECTION (Decisions, Action Items, Open Questions) */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 items-start">
        <DecisionsSection
          decisions={decisions}
          isLoading={isLoading}
          onViewAll={() => setActiveTab("decisions")}
        />
        <ActionItemsSection
          actionItems={actionItems}
          isLoading={isLoading}
          onToggleItem={toggleAction}
          onViewAll={() => setActiveTab("action_items")}
        />
        <OpenQuestionsSection
          questions={openQuestions}
          isLoading={isLoading}
          onViewAll={() => setActiveTab("open_questions")}
        />
      </div>

      {/* 9. SOURCES & EVIDENCE */}
      <SourcesSection
        onViewAll={() => setActiveTab("sources")}
        onOpenSource={(src) => {
          if (src.type === "transcript") setIsTranscriptOpen(true);
        }}
      />

      {/* Modals */}
      <NewMeetingModal
        isOpen={isNewMeetingOpen}
        onClose={() => setIsNewMeetingOpen(false)}
        onMeetingLoaded={() => {
          refetch();
        }}
      />

      <TranscriptModal
        isOpen={isTranscriptOpen}
        onClose={() => {
          setIsTranscriptOpen(false);
          if (activeTab === "transcript") setActiveTab("overview");
        }}
        transcript={meeting?.transcript || ""}
        title={`${meeting?.title || "Meeting"} — Transcript`}
      />
    </AppShell>
  );
}
