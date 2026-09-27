"use client";

import { useState, useEffect, useCallback } from "react";
import {
  MeetingDetailResponse,
  DecisionItem,
  ActionItem,
  OpenQuestionItem,
} from "@/types/meeting";
import {
  getMeeting,
  getMeetingSummary,
  getMeetingDecisions,
  getMeetingActions,
  getMeetingOpenQuestions,
  loadDemoMeeting,
} from "@/lib/api/meetings";

export const DEMO_SESSION_ID = "demo_backend_migration";

export interface UseMeetingReturn {
  meeting: MeetingDetailResponse | null;
  decisions: DecisionItem[];
  actionItems: ActionItem[];
  openQuestions: OpenQuestionItem[];
  isLoading: boolean;
  isError: boolean;
  errorMessage: string | null;
  isOfflineFallback: boolean;
  refetch: () => Promise<void>;
  toggleAction: (index: number) => void;
}

const FALLBACK_TRANSCRIPT = `00:00:00 - 00:00:25
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

const FALLBACK_MEETING: MeetingDetailResponse = {
  session_id: DEMO_SESSION_ID,
  title: "Backend Platform Migration & Cloud Infrastructure Sync",
  transcript: FALLBACK_TRANSCRIPT,
  summary:
    "The team discussed the product roadmap for Q2, focusing on the new AI features, user experience improvements, and go-to-market strategy. Key topics included the timeline for the feature launch, resource allocation, and customer feedback from the beta program.",
  status: "completed",
  is_demo: true,
};

const FALLBACK_DECISIONS: DecisionItem[] = [
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
];

const FALLBACK_ACTIONS: ActionItem[] = [
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
];

const FALLBACK_QUESTIONS: OpenQuestionItem[] = [
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
];

export function useMeeting(sessionId: string = DEMO_SESSION_ID): UseMeetingReturn {
  const [meeting, setMeeting] = useState<MeetingDetailResponse | null>(null);
  const [decisions, setDecisions] = useState<DecisionItem[]>([]);
  const [actionItems, setActionItems] = useState<ActionItem[]>([]);
  const [openQuestions, setOpenQuestions] = useState<OpenQuestionItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isError, setIsError] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isOfflineFallback, setIsOfflineFallback] = useState(false);

  const fetchMeetingData = useCallback(async () => {
    setIsLoading(true);
    setIsError(false);
    setErrorMessage(null);
    setIsOfflineFallback(false);

    const targetId = sessionId.trim() || DEMO_SESSION_ID;

    try {
      // 1. Fetch meeting details
      let detail: MeetingDetailResponse;
      if (targetId === DEMO_SESSION_ID) {
        detail = await loadDemoMeeting();
      } else {
        detail = await getMeeting(targetId);
      }

      setMeeting(detail);

      // 2. Fetch parallel intelligence resources
      const [sumRes, decRes, actRes, qRes] = await Promise.allSettled([
        getMeetingSummary(targetId),
        getMeetingDecisions(targetId),
        getMeetingActions(targetId),
        getMeetingOpenQuestions(targetId),
      ]);

      if (sumRes.status === "fulfilled" && sumRes.value.summary) {
        setMeeting((prev) =>
          prev ? { ...prev, summary: sumRes.value.summary } : prev
        );
      }

      if (decRes.status === "fulfilled" && decRes.value.key_decisions) {
        setDecisions(decRes.value.key_decisions);
      } else {
        setDecisions([]);
      }

      if (actRes.status === "fulfilled" && actRes.value.action_items) {
        setActionItems(actRes.value.action_items);
      } else {
        setActionItems([]);
      }

      if (qRes.status === "fulfilled" && qRes.value.open_questions) {
        setOpenQuestions(qRes.value.open_questions);
      } else {
        setOpenQuestions([]);
      }
    } catch (err: unknown) {
      // If the target is the demo meeting and backend is unreachable, serve offline fixture
      if (targetId === DEMO_SESSION_ID) {
        setIsOfflineFallback(true);
        setMeeting(FALLBACK_MEETING);
        setDecisions(FALLBACK_DECISIONS);
        setActionItems(FALLBACK_ACTIONS);
        setOpenQuestions(FALLBACK_QUESTIONS);
      } else {
        setIsError(true);
        setErrorMessage(
          err instanceof Error
            ? err.message
            : `Failed to load meeting session '${targetId}'`
        );
      }
    } finally {
      setIsLoading(false);
    }
  }, [sessionId]);

  useEffect(() => {
    fetchMeetingData();
  }, [fetchMeetingData]);

  const toggleAction = useCallback((index: number) => {
    setActionItems((prev) =>
      prev.map((item, i) => {
        if (i !== index) return item;
        const isDone = item.status === "Done";
        return {
          ...item,
          status: isDone ? "Open" : "Done",
        };
      })
    );
  }, []);

  return {
    meeting,
    decisions,
    actionItems,
    openQuestions,
    isLoading,
    isError,
    errorMessage,
    isOfflineFallback,
    refetch: fetchMeetingData,
    toggleAction,
  };
}
