"use client";

import { useState, useEffect, useCallback, useMemo } from "react";
import { MeetingListItem } from "@/types/meeting";
import { listMeetings } from "@/lib/api/meetings";

export type MeetingSortOption = "newest" | "oldest" | "title" | "actions" | "decisions";
export type MeetingSourceFilter = "all" | "youtube" | "upload";

export interface UseMeetingsListReturn {
  meetings: MeetingListItem[];
  filteredMeetings: MeetingListItem[];
  searchQuery: string;
  setSearchQuery: (query: string) => void;
  sortBy: MeetingSortOption;
  setSortBy: (sort: MeetingSortOption) => void;
  filterSource: MeetingSourceFilter;
  setFilterSource: (filter: MeetingSourceFilter) => void;
  isLoading: boolean;
  isError: boolean;
  errorMessage: string | null;
  refetch: () => Promise<void>;
}

export function useMeetingsList(): UseMeetingsListReturn {
  const [meetings, setMeetings] = useState<MeetingListItem[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [sortBy, setSortBy] = useState<MeetingSortOption>("newest");
  const [filterSource, setFilterSource] = useState<MeetingSourceFilter>("all");
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
          decisions_count: 4,
          actions_count: 3,
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
    let result = [...meetings];

    // Filter by search query
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      result = result.filter(
        (m) =>
          m.title.toLowerCase().includes(query) ||
          (m.source && m.source.toLowerCase().includes(query)) ||
          (m.summary_preview && m.summary_preview.toLowerCase().includes(query))
      );
    }

    // Filter by source type
    if (filterSource !== "all") {
      result = result.filter((m) => {
        const type = m.source_type?.toLowerCase() || (m.source?.toLowerCase().includes("youtube") ? "youtube" : "upload");
        return type === filterSource;
      });
    }

    // Sort
    result.sort((a, b) => {
      if (sortBy === "title") {
        return a.title.localeCompare(b.title);
      }
      if (sortBy === "actions") {
        return (b.actions_count || 0) - (a.actions_count || 0);
      }
      if (sortBy === "decisions") {
        return (b.decisions_count || 0) - (a.decisions_count || 0);
      }
      if (sortBy === "oldest") {
        return (a.created_at || "").localeCompare(b.created_at || "");
      }
      // default newest
      return (b.created_at || "").localeCompare(a.created_at || "");
    });

    return result;
  }, [meetings, searchQuery, filterSource, sortBy]);

  return {
    meetings,
    filteredMeetings,
    searchQuery,
    setSearchQuery,
    sortBy,
    setSortBy,
    filterSource,
    setFilterSource,
    isLoading,
    isError,
    errorMessage,
    refetch: fetchMeetings,
  };
}
