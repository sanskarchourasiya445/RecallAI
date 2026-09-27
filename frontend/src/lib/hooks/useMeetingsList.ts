"use client";

import { useState, useEffect, useCallback, useMemo } from "react";
import { MeetingListItem } from "@/types/meeting";
import { listMeetings } from "@/lib/api/meetings";

export interface UseMeetingsListReturn {
  meetings: MeetingListItem[];
  filteredMeetings: MeetingListItem[];
  searchQuery: string;
  setSearchQuery: (query: string) => void;
  isLoading: boolean;
  isError: boolean;
  errorMessage: string | null;
  refetch: () => Promise<void>;
}

export function useMeetingsList(): UseMeetingsListReturn {
  const [meetings, setMeetings] = useState<MeetingListItem[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isError, setIsError] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const fetchMeetings = useCallback(async () => {
    setIsLoading(true);
    setIsError(false);
    setErrorMessage(null);

    try {
      const items = await listMeetings();
      setMeetings(items);
    } catch (err: unknown) {
      setIsError(true);
      setErrorMessage(
        err instanceof Error ? err.message : "Failed to load meetings list"
      );
      // Fallback with demo meeting if server is starting
      setMeetings([
        {
          session_id: "demo_backend_migration",
          title: "Backend Platform Migration & Cloud Infrastructure Sync",
          status: "completed",
          created_at: "Apr 28, 2025 • 10:00 AM",
          source: "Platform Architecture Meeting",
          source_type: "upload",
          duration: "42 min",
          participants_count: 12,
          summary_preview:
            "The team discussed the product roadmap for Q2, focusing on the new AI features, user experience improvements, and go-to-market strategy...",
          decisions_count: 3,
          actions_count: 4,
          open_questions_count: 2,
          is_demo: true,
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchMeetings();
  }, [fetchMeetings]);

  const filteredMeetings = useMemo(() => {
    if (!searchQuery.trim()) return meetings;
    const query = searchQuery.toLowerCase();
    return meetings.filter(
      (m) =>
        m.title.toLowerCase().includes(query) ||
        (m.source && m.source.toLowerCase().includes(query)) ||
        (m.summary_preview && m.summary_preview.toLowerCase().includes(query))
    );
  }, [meetings, searchQuery]);

  return {
    meetings,
    filteredMeetings,
    searchQuery,
    setSearchQuery,
    isLoading,
    isError,
    errorMessage,
    refetch: fetchMeetings,
  };
}
