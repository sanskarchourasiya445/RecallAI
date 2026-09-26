"use client";

import React, { useState, useEffect } from "react";
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
import { MeetingDetailResponse, ActionItem, DecisionItem, OpenQuestionItem } from "@/types/meeting";
import { getMeetingActions, getMeetingDecisions, getMeetingOpenQuestions, loadDemoMeeting } from "@/lib/api/meetings";

const INITIAL_TRANSCRIPT = `00:00:00 - 00:00:25
Alex: Good morning team. Today we are reviewing our product strategy roadmap for Q2, focusing on the new AI search features, user experience improvements, and go-to-market execution.

00:00:25 - 00:01:40
Sarah: Let's start with our primary database and architecture. The team decided to migrate our primary transactional database to PostgreSQL 16. The write performance and JSON indexing outperformed MySQL by nearly 40%.

00:01:40 - 00:02:45
Rahul: For connection management, we agreed to deploy PgBouncer as a sidecar proxy configured with a pool size of 50 connections per replica to prevent connection starvation during peak traffic.

00:02:45 - 00:03:50
Rahul: I will prepare and distribute the complete PostgreSQL migration plan by Friday at 5 PM (Apr 30, 2025).

00:03:50 - 00:04:45
Priya: On the marketing side, we decided that the marketing budget will be increased by 20% for Q2. I will also create the content marketing plan by May 5, 2025.

00:04:45 - 00:05:40
David: The engineering team will use the new architecture for the AI module. I will finalize engineering resources by May 10, 2025.

00:05:40 - 00:06:20
Sarah: I will share the customer feedback summary by May 8, 2025.

00:06:20 - 00:06:50
Alex: Question: Will we be able to meet the Q2 timeline with current resources? Let's make sure we track that closely.`;

export default function RecallAIDashboard() {
  const [activeTab, setActiveTab] = useState<MeetingTabId>("overview");
  const [isNewMeetingOpen, setIsNewMeetingOpen] = useState(false);
  const [isTranscriptOpen, setIsTranscriptOpen] = useState(false);

  // Active meeting state
  const [meetingData, setMeetingData] = useState<MeetingDetailResponse>({
    session_id: "demo_backend_migration",
    title: "Product Strategy Meeting",
    transcript: INITIAL_TRANSCRIPT,
    summary:
      "The team discussed the product roadmap for Q2, focusing on the new AI features, user experience improvements, and go-to-market strategy. Key topics included the timeline for the feature launch, resource allocation, and customer feedback from the beta program.",
    status: "completed",
    is_demo: true,
  });

  const [decisions, setDecisions] = useState<DecisionItem[]>([
    {
      decision: "AI search feature will be prioritized for Q2 release.",
      timestamp: "12:34",
      author: "Rahul",
      status: "Confirmed",
    },
    {
      decision: "Marketing budget will be increased by 20% for Q2.",
      timestamp: "18:22",
      author: "Priya",
      status: "Confirmed",
    },
    {
      decision: "Engineering team will use the new architecture for the AI module.",
      timestamp: "26:17",
      author: "David",
      status: "Confirmed",
    },
  ]);

  const [actionItems, setActionItems] = useState<ActionItem[]>([
    {
      task: "Prepare and distribute complete Marketing plan",
      owner: "Rahul",
      deadline: "Apr 30, 2025",
      priority: "High",
      status: "Open",
    },
    {
      task: "Create content marketing plan",
      owner: "Priya",
      deadline: "May 5, 2025",
      priority: "High",
      status: "Open",
    },
    {
      task: "Finalize engineering resources",
      owner: "David",
      deadline: "May 10, 2025",
      priority: "Medium",
      status: "Open",
    },
    {
      task: "Share customer feedback summary",
      owner: "Sarah",
      deadline: "May 8, 2025",
      priority: "Medium",
      status: "Open",
    },
  ]);

  const [openQuestions, setOpenQuestions] = useState<OpenQuestionItem[]>([
    {
      question: "Will we be able to meet the Q2 timeline with current resources?",
      author: "Alex",
      timestamp: "12:15",
    },
    {
      question: "What's the expected ROI for the marketing campaign?",
      author: "Priya",
      timestamp: "18:03",
    },
  ]);

  // Attempt background sync with live FastAPI backend on mount
  useEffect(() => {
    async function syncBackendData() {
      try {
        const demo = await loadDemoMeeting();
        if (demo) {
          setMeetingData((prev) => ({
            ...prev,
            session_id: demo.session_id,
            transcript: demo.transcript || prev.transcript,
          }));

          // Fetch structured items
          const [acts, decs, quests] = await Promise.allSettled([
            getMeetingActions(demo.session_id),
            getMeetingDecisions(demo.session_id),
            getMeetingOpenQuestions(demo.session_id),
          ]);

          if (acts.status === "fulfilled" && acts.value.action_items?.length) {
            setActionItems(acts.value.action_items);
          }
          if (decs.status === "fulfilled" && decs.value.key_decisions?.length) {
            setDecisions(decs.value.key_decisions);
          }
          if (quests.status === "fulfilled" && quests.value.open_questions?.length) {
            setOpenQuestions(quests.value.open_questions);
          }
        }
      } catch {
        // Retain pristine pixel-perfect initial reference state if backend is offline
      }
    }
    syncBackendData();
  }, []);

  const handleTabChange = (tab: MeetingTabId) => {
    setActiveTab(tab);
    if (tab === "transcript") {
      setIsTranscriptOpen(true);
    }
  };

  const handleMeetingLoaded = (loaded: MeetingDetailResponse) => {
    setMeetingData(loaded);
  };

  return (
    <AppShell
      onNewMeetingClick={() => setIsNewMeetingOpen(true)}
      onSearch={(q) => console.log("Global search:", q)}
      rightPanel={
        <>
          {/* AI Chat Card */}
          <AIChat sessionId={meetingData.session_id} />

          {/* Quick Actions Card */}
          <QuickActions sessionId={meetingData.session_id} pendingCount={3} />
        </>
      }
    >
      {/* 4. MEETING HEADER */}
      <MeetingHeader
        title={meetingData.title}
        duration="42 min"
        participantsCount={12}
        dateStr="Apr 28, 2025 • 10:00 AM"
        status="Completed"
        onShare={() => alert("Meeting link copied to clipboard!")}
        onDownload={() => alert("Downloading meeting intelligence summary (PDF)...")}
      />

      {/* 5. MEETING TABS */}
      <MeetingTabs activeTab={activeTab} onChangeTab={handleTabChange} />

      {/* 6. FOUR INSIGHT CARDS */}
      <InsightCardsGrid
        summaryCount="Key points & insights"
        decisionsCount={decisions.length || 3}
        actionItemsCount={actionItems.length || 6}
        openQuestionsCount={openQuestions.length || 2}
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
            summary={meetingData.summary}
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
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 items-stretch">
        <DecisionsSection
          decisions={decisions}
          onViewAll={() => setActiveTab("decisions")}
        />
        <ActionItemsSection
          actionItems={actionItems}
          onViewAll={() => setActiveTab("action_items")}
        />
        <OpenQuestionsSection
          questions={openQuestions}
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
        onMeetingLoaded={handleMeetingLoaded}
      />

      <TranscriptModal
        isOpen={isTranscriptOpen}
        onClose={() => {
          setIsTranscriptOpen(false);
          if (activeTab === "transcript") setActiveTab("overview");
        }}
        transcript={meetingData.transcript}
        title={`${meetingData.title} — Transcript`}
      />
    </AppShell>
  );
}
