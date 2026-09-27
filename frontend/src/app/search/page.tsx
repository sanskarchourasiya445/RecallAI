"use client";

import React, { useState, useEffect, useRef, Suspense, useCallback } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { AppShell } from "@/components/layouts/AppShell";
import { searchWorkspace } from "@/lib/api/search";
import {
  sendWorkspaceChatStream,
  getWorkspaceMemory,
} from "@/lib/api/workspace";
import { listMeetings } from "@/lib/api/meetings";
import { SearchResultItem } from "@/types/search";
import {
  WorkspaceCitationItem,
  WorkspaceMemoryResponse,
} from "@/types/workspace";
import { MeetingListItem } from "@/types/meeting";
import {
  Search,
  Sparkles,
  Bot,
  User,
  ArrowRight,
  Clock,
  Calendar,
  CheckCircle2,
  HelpCircle,
  FileText,
  Loader2,
  ExternalLink,
  ChevronRight,
  Send,
  Database,
  AlertCircle,
} from "lucide-react";

type SearchCategory = "all" | "transcript" | "decision" | "action_item" | "dilemma";

interface WorkspaceChatMessage {
  id: string;
  sender: "user" | "assistant";
  text: string;
  citations?: WorkspaceCitationItem[];
  sources?: Array<{ session_id: string; title: string; source: string }>;
  isStreaming?: boolean;
}

function GlobalSearchContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const initialQuery = searchParams?.get("q") || "";

  const [query, setQuery] = useState(initialQuery);
  const [selectedMeetingId, setSelectedMeetingId] = useState<string>("all");
  const [selectedCategory, setSelectedCategory] = useState<SearchCategory>("all");
  const [results, setResults] = useState<SearchResultItem[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [meetings, setMeetings] = useState<MeetingListItem[]>([]);

  // Workspace memory state
  const [memory, setMemory] = useState<WorkspaceMemoryResponse | null>(null);
  const [activeTab, setActiveTab] = useState<"search" | "assistant" | "memory">("search");

  // Cross-meeting Assistant Chat State
  const [chatMessages, setChatMessages] = useState<WorkspaceChatMessage[]>([]);
  const [assistantInput, setAssistantInput] = useState("");
  const [isStreamingAssistant, setIsStreamingAssistant] = useState(false);
  const chatScrollRef = useRef<HTMLDivElement>(null);

  const executeSearch = useCallback(async (searchTerm: string, meetingFilter?: string) => {
    if (!searchTerm.trim()) return;
    setIsSearching(true);
    setHasSearched(true);
    setErrorMessage(null);

    try {
      const sid = meetingFilter && meetingFilter !== "all" ? meetingFilter : undefined;
      const res = await searchWorkspace({
        query: searchTerm.trim(),
        limit: 25,
        session_id: sid,
      });
      setResults(res.results || []);
    } catch (err: unknown) {
      console.error("Search failed:", err);
      const msg = err instanceof Error ? err.message : "Failed to execute search. Please check your connection and try again.";
      setErrorMessage(msg);
      setResults([]);
    } finally {
      setIsSearching(false);
    }
  }, []);

  // Load meeting list and workspace memory on mount
  useEffect(() => {
    async function loadInitialData() {
      try {
        const [meetingList, memData] = await Promise.all([
          listMeetings().catch(() => []),
          getWorkspaceMemory().catch(() => null),
        ]);
        setMeetings(meetingList);
        if (memData) setMemory(memData);
      } catch (e) {
        console.error("Failed to load meetings or workspace memory:", e);
      }
    }
    loadInitialData();
  }, []);

  // Execute initial search if ?q= parameter is present in URL
  useEffect(() => {
    if (initialQuery.trim()) {
      executeSearch(initialQuery.trim(), selectedMeetingId);
    }
  }, [initialQuery, selectedMeetingId, executeSearch]);

  const handleSearchSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (query.trim()) {
      executeSearch(query.trim(), selectedMeetingId);
    }
  };

  const filteredResults = results.filter((item) => {
    if (selectedCategory === "all") return true;
    if (selectedCategory === "transcript") return item.match_type === "transcript";
    if (selectedCategory === "decision") return item.match_type === "decision";
    if (selectedCategory === "action_item") return item.match_type === "action_item";
    if (selectedCategory === "dilemma") return item.match_type === "dilemma";
    return true;
  });

  const navigateToEvidence = (sessionId: string, startSeconds: number, evidenceId?: string) => {
    const params = new URLSearchParams();
    if (startSeconds !== undefined) params.set("t", String(Math.floor(startSeconds)));
    if (evidenceId) params.set("ev", evidenceId);
    router.push(`/meetings/${sessionId}?${params.toString()}`);
  };

  // Cross-Meeting Assistant Q&A
  const handleSendAssistant = async (questionText?: string) => {
    const textToSend = (questionText || assistantInput).trim();
    if (!textToSend || isStreamingAssistant) return;

    setAssistantInput("");
    setActiveTab("assistant");

    const userMsgId = `user-${Date.now()}`;
    const assistantMsgId = `assistant-${Date.now()}`;

    const newMessages: WorkspaceChatMessage[] = [
      ...chatMessages,
      { id: userMsgId, sender: "user", text: textToSend },
      { id: assistantMsgId, sender: "assistant", text: "", citations: [], isStreaming: true },
    ];
    setChatMessages(newMessages);
    setIsStreamingAssistant(true);

    try {
      await sendWorkspaceChatStream(
        { message: textToSend, top_k: 6 },
        {
          onMetadata: (meta) => {
            setChatMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantMsgId
                  ? {
                      ...msg,
                      citations: meta.citations || [],
                      sources: meta.sources || [],
                    }
                  : msg
              )
            );
          },
          onToken: (delta) => {
            setChatMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantMsgId
                  ? { ...msg, text: msg.text + delta }
                  : msg
              )
            );
          },
          onDone: (full) => {
            setChatMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantMsgId
                  ? {
                      ...msg,
                      text: full.answer,
                      citations: full.citations || [],
                      sources: full.sources || [],
                      isStreaming: false,
                    }
                  : msg
              )
            );
            setIsStreamingAssistant(false);
          },
          onError: (err) => {
            setChatMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantMsgId
                  ? {
                      ...msg,
                      text: `Cross-meeting search failed: ${err.message}`,
                      isStreaming: false,
                    }
                  : msg
              )
            );
            setIsStreamingAssistant(false);
          },
        }
      );
    } catch (err: unknown) {
      setChatMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMsgId
            ? {
                ...msg,
                text: `Assistant error: ${err instanceof Error ? err.message : String(err)}`,
                isStreaming: false,
              }
            : msg
        )
      );
      setIsStreamingAssistant(false);
    }
  };

  const getMatchTypeBadge = (matchType: string) => {
    switch (matchType) {
      case "decision":
        return {
          label: "Confirmed Decision",
          bg: "bg-emerald-50 text-emerald-700 border-emerald-200",
          icon: CheckCircle2,
        };
      case "action_item":
        return {
          label: "Action Item",
          bg: "bg-blue-50 text-blue-700 border-blue-200",
          icon: Clock,
        };
      case "dilemma":
        return {
          label: "Open Dilemma",
          bg: "bg-amber-50 text-amber-700 border-amber-200",
          icon: HelpCircle,
        };
      default:
        return {
          label: "Transcript Passage",
          bg: "bg-slate-100 text-slate-700 border-slate-200",
          icon: FileText,
        };
    }
  };

  // Render assistant citations as interactive pills
  const renderCitationsPills = (citations?: WorkspaceCitationItem[]) => {
    if (!citations || citations.length === 0) return null;
    return (
      <div className="mt-3 pt-2.5 border-t border-slate-200/80 flex flex-wrap gap-1.5 items-center">
        <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider mr-1">
          Grounded Sources:
        </span>
        {citations.map((c, i) => (
          <button
            key={i}
            onClick={() => navigateToEvidence(c.session_id, c.start_seconds, c.evidence_id)}
            className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-medium rounded-md bg-indigo-50 text-indigo-700 hover:bg-indigo-100 border border-indigo-200/80 transition-colors shadow-2xs group"
          >
            <span>{c.citation_label}</span>
            <ExternalLink className="w-3 h-3 text-indigo-400 group-hover:text-indigo-600" />
          </button>
        ))}
      </div>
    );
  };

  return (
    <AppShell
      currentNav="search"
      onNewMeetingClick={() => router.push("/meetings")}
      onSearch={(q) => {
        setQuery(q);
        executeSearch(q, selectedMeetingId);
      }}
      rightPanel={
        <div className="p-4 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-2">
              <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
              Workspace Intelligence
            </h3>
          </div>

          {/* Quick Memory Stats */}
          {memory && (
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-100">
                <div className="text-[11px] text-slate-500 font-medium">Meetings</div>
                <div className="text-base font-bold text-slate-900">
                  {memory.overview.total_meetings}
                </div>
              </div>
              <div className="p-2.5 rounded-lg bg-emerald-50/60 border border-emerald-100">
                <div className="text-[11px] text-emerald-700 font-medium">Decisions</div>
                <div className="text-base font-bold text-emerald-800">
                  {memory.overview.total_decisions}
                </div>
              </div>
              <div className="p-2.5 rounded-lg bg-blue-50/60 border border-blue-100">
                <div className="text-[11px] text-blue-700 font-medium">Action Items</div>
                <div className="text-base font-bold text-blue-800">
                  {memory.overview.total_action_items}
                </div>
              </div>
              <div className="p-2.5 rounded-lg bg-amber-50/60 border border-amber-100">
                <div className="text-[11px] text-amber-700 font-medium">Open Dilemmas</div>
                <div className="text-base font-bold text-amber-800">
                  {memory.overview.total_open_questions}
                </div>
              </div>
            </div>
          )}

          {/* Tracked Topics */}
          {memory && memory.overview.tracked_topics.length > 0 && (
            <div className="space-y-1.5 pt-2 border-t border-slate-100">
              <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
                Workspace Topics
              </div>
              <div className="flex flex-wrap gap-1">
                {memory.overview.tracked_topics.map((t, idx) => (
                  <button
                    key={idx}
                    onClick={() => {
                      setQuery(t);
                      executeSearch(t, selectedMeetingId);
                      setActiveTab("search");
                    }}
                    className="px-2 py-0.5 text-[11px] rounded-md bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200/80 transition-colors"
                  >
                    #{t}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Key Team People */}
          {memory && memory.overview.tracked_people.length > 0 && (
            <div className="space-y-1.5 pt-2 border-t border-slate-100">
              <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
                Active Participants
              </div>
              <div className="flex flex-wrap gap-1">
                {memory.overview.tracked_people.map((p, idx) => (
                  <button
                    key={idx}
                    onClick={() => {
                      setQuery(p);
                      executeSearch(p, selectedMeetingId);
                      setActiveTab("search");
                    }}
                    className="px-2 py-0.5 text-[11px] rounded-md bg-indigo-50 hover:bg-indigo-100 text-indigo-700 border border-indigo-200/60 transition-colors flex items-center gap-1"
                  >
                    <User className="w-2.5 h-2.5" />
                    {p}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      }
    >
      <div className="p-4 md:p-6 max-w-5xl mx-auto space-y-6">
        {/* Main Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-xl md:text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
              <Search className="w-6 h-6 text-indigo-600" />
              Global Workspace Search & Intelligence
            </h1>
            <p className="text-xs md:text-sm text-slate-500 mt-1">
              Search transcripts, verified decisions, action items, and dilemmas across all meetings in your workspace.
            </p>
          </div>

          {/* Navigation Pill Switcher */}
          <div className="flex items-center p-1 bg-slate-100 rounded-xl border border-slate-200 self-start shrink-0">
            <button
              onClick={() => setActiveTab("search")}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                activeTab === "search"
                  ? "bg-white text-indigo-600 shadow-2xs"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              Unified Search
            </button>
            <button
              onClick={() => setActiveTab("assistant")}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5 ${
                activeTab === "assistant"
                  ? "bg-white text-indigo-600 shadow-2xs"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              <Bot className="w-3.5 h-3.5" />
              Cross-Meeting AI
            </button>
            <button
              onClick={() => setActiveTab("memory")}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5 ${
                activeTab === "memory"
                  ? "bg-white text-indigo-600 shadow-2xs"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              <Database className="w-3.5 h-3.5" />
              Workspace Memory
            </button>
          </div>
        </div>

        {/* TAB 1: UNIFIED SEARCH */}
        {activeTab === "search" && (
          <div className="space-y-5">
            {/* Search Input Box */}
            <form onSubmit={handleSearchSubmit} className="space-y-3">
              <div className="relative">
                <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                <input
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Search across all meetings (e.g. 'PostgreSQL database migration', 'Rahul', 'AWS deployment region')..."
                  className="w-full h-12 pl-12 pr-28 rounded-xl bg-white text-sm text-slate-800 placeholder:text-slate-400 border border-slate-200 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 shadow-xs transition-all"
                />
                <button
                  type="submit"
                  disabled={isSearching || !query.trim()}
                  className="absolute right-2 top-1/2 -translate-y-1/2 px-4 py-2 rounded-lg bg-indigo-600 text-white text-xs font-semibold hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed shadow-2xs transition-colors flex items-center gap-1.5"
                >
                  {isSearching ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : "Search"}
                </button>
              </div>

              {/* Filters Bar */}
              <div className="flex flex-wrap items-center justify-between gap-3 text-xs">
                {/* Category Pills */}
                <div className="flex flex-wrap items-center gap-1.5">
                  <span className="text-slate-400 font-medium mr-1">Filter:</span>
                  {[
                    { id: "all", label: "All Matches" },
                    { id: "transcript", label: "Transcripts" },
                    { id: "decision", label: "Decisions" },
                    { id: "action_item", label: "Action Items" },
                    { id: "dilemma", label: "Open Dilemmas" },
                  ].map((cat) => (
                    <button
                      type="button"
                      key={cat.id}
                      onClick={() => setSelectedCategory(cat.id as SearchCategory)}
                      className={`px-2.5 py-1 rounded-lg font-medium transition-colors border ${
                        selectedCategory === cat.id
                          ? "bg-indigo-50 text-indigo-700 border-indigo-200 font-semibold"
                          : "bg-white text-slate-600 border-slate-200 hover:bg-slate-50"
                      }`}
                    >
                      {cat.label}
                    </button>
                  ))}
                </div>

                {/* Meeting Scope Selector */}
                <div className="flex items-center gap-2">
                  <span className="text-slate-400 font-medium">Scope:</span>
                  <select
                    value={selectedMeetingId}
                    onChange={(e) => {
                      setSelectedMeetingId(e.target.value);
                      if (query.trim()) executeSearch(query.trim(), e.target.value);
                    }}
                    className="h-8 px-2.5 rounded-lg bg-white border border-slate-200 text-slate-700 text-xs font-medium focus:outline-none focus:border-indigo-500 shadow-2xs"
                  >
                    <option value="all">All Workspace Meetings ({meetings.length})</option>
                    {meetings.map((m) => (
                      <option key={m.session_id} value={m.session_id}>
                        {m.title}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </form>

            {/* Quick Suggestion Chips (when no search yet) */}
            {!hasSearched && (
              <div className="p-6 rounded-2xl bg-white border border-slate-200/80 shadow-2xs space-y-4">
                <div className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                  Popular Cross-Meeting Search Queries
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                  {[
                    "PostgreSQL database migration dependencies",
                    "AWS deployment region and data residency",
                    "Frontend dashboard analytics queries",
                    "Client session token validation dilemma",
                    "Sprint architecture review commitments",
                  ].map((chip, idx) => (
                    <button
                      key={idx}
                      onClick={() => {
                        setQuery(chip);
                        executeSearch(chip, selectedMeetingId);
                      }}
                      className="text-left p-3 rounded-xl bg-slate-50 hover:bg-indigo-50/60 border border-slate-200/70 hover:border-indigo-200 transition-all text-xs font-medium text-slate-700 hover:text-indigo-900 flex items-center justify-between group"
                    >
                      <span className="truncate">{chip}</span>
                      <ArrowRight className="w-3.5 h-3.5 text-slate-400 group-hover:text-indigo-600 shrink-0 ml-2 transition-transform group-hover:translate-x-0.5" />
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Error Banner */}
            {errorMessage && (
              <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 flex items-center justify-between gap-3 text-xs shadow-2xs">
                <div className="flex items-center gap-2.5 min-w-0">
                  <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
                  <span className="font-medium">{errorMessage}</span>
                </div>
                <button
                  type="button"
                  onClick={() => executeSearch(query, selectedMeetingId)}
                  className="px-3 py-1 bg-white hover:bg-rose-100 text-rose-700 font-semibold rounded-lg border border-rose-300 transition-colors shrink-0"
                >
                  Retry
                </button>
              </div>
            )}

            {/* Search Results Display */}
            {hasSearched && (
              <div className="space-y-3">
                <div className="flex items-center justify-between text-xs text-slate-500 px-1">
                  <span>
                    Found <strong className="text-slate-800">{filteredResults.length}</strong> result{filteredResults.length === 1 ? "" : "s"} for &quot;{query}&quot;
                  </span>
                  {isSearching && (
                    <span className="flex items-center gap-1.5 text-indigo-600 font-medium">
                      <Loader2 className="w-3.5 h-3.5 animate-spin" /> Searching...
                    </span>
                  )}
                </div>

                {filteredResults.length === 0 && !isSearching ? (
                  <div className="p-8 text-center bg-white rounded-2xl border border-slate-200/80 space-y-2">
                    <AlertCircle className="w-8 h-8 text-slate-400 mx-auto" />
                    <div className="text-sm font-semibold text-slate-800">
                      No matching discussions or intelligence found
                    </div>
                    <p className="text-xs text-slate-500 max-w-md mx-auto">
                      No verified transcripts or decisions matched &quot;{query}&quot; in the selected meeting scope. Try broader search terms.
                    </p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {filteredResults.map((item, idx) => {
                      const badgeInfo = getMatchTypeBadge(item.match_type);
                      const BadgeIcon = badgeInfo.icon;

                      return (
                        <div
                          key={idx}
                          className="p-4 rounded-xl bg-white border border-slate-200/80 hover:border-indigo-300 transition-all shadow-2xs space-y-2.5 group"
                        >
                          {/* Card Header: Meeting Title, Match Type, Timestamp */}
                          <div className="flex flex-wrap items-center justify-between gap-2">
                            <div className="flex flex-wrap items-center gap-2">
                              <span className="text-xs font-bold text-slate-900 flex items-center gap-1.5">
                                <Calendar className="w-3.5 h-3.5 text-indigo-600 shrink-0" />
                                {item.meeting_title}
                              </span>

                              <span
                                className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-semibold border ${badgeInfo.bg}`}
                              >
                                <BadgeIcon className="w-3 h-3" />
                                {badgeInfo.label}
                              </span>

                              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-medium bg-slate-100 text-slate-600 border border-slate-200">
                                <Clock className="w-3 h-3 text-slate-400" />
                                {item.timestamp}
                              </span>
                            </div>

                            <div className="flex items-center gap-2">
                              {/* Relevance Score Pill */}
                              <span className="text-[11px] font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-md border border-emerald-200">
                                {Math.round(item.relevance_score * 100)}% Match
                              </span>

                              {/* Evidence ID Badge */}
                              <span className="text-[11px] font-bold text-indigo-700 bg-indigo-50 px-1.5 py-0.5 rounded border border-indigo-200">
                                {item.evidence_id}
                              </span>
                            </div>
                          </div>

                          {/* Snippet Text */}
                          <div className="text-xs text-slate-700 leading-relaxed bg-slate-50/60 p-3 rounded-lg border border-slate-100 font-mono text-[11.5px] whitespace-pre-line">
                            {item.snippet}
                          </div>

                          {/* Action Footer */}
                          <div className="flex items-center justify-between pt-1">
                            <span className="text-[11px] text-slate-400">
                              Session ID: <code className="text-slate-600">{item.session_id}</code>
                            </span>

                            <button
                              onClick={() =>
                                navigateToEvidence(
                                  item.session_id,
                                  item.start_seconds,
                                  item.evidence_id
                                )
                              }
                              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold text-indigo-600 hover:text-indigo-800 hover:bg-indigo-50 transition-colors"
                            >
                              <span>Open in Meeting Workspace</span>
                              <ChevronRight className="w-3.5 h-3.5" />
                            </button>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* TAB 2: CROSS-MEETING AI ASSISTANT */}
        {activeTab === "assistant" && (
          <div className="space-y-4">
            <div className="p-4 rounded-xl bg-gradient-to-r from-indigo-50/70 to-blue-50/50 border border-indigo-100 flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                  <Bot className="w-4 h-4 text-indigo-600" />
                  RecallAI Multi-Meeting Intelligence Assistant
                </h3>
                <p className="text-xs text-slate-600 mt-0.5">
                  Ask questions that synthesize discussions, commitments, and dilemmas across all loaded meetings with grounded citations.
                </p>
              </div>
            </div>

            {/* Conversation Flow */}
            <div
              ref={chatScrollRef}
              className="min-h-[320px] max-h-[500px] overflow-y-auto space-y-4 p-4 rounded-2xl bg-white border border-slate-200/80 shadow-2xs"
            >
              {chatMessages.length === 0 ? (
                <div className="py-12 text-center space-y-4">
                  <Bot className="w-10 h-10 text-indigo-400 mx-auto" />
                  <div className="text-sm font-semibold text-slate-800">
                    Ask anything across your workspace
                  </div>
                  <p className="text-xs text-slate-500 max-w-md mx-auto">
                    Try asking questions that span multiple conversations to uncover cross-meeting decisions and dependencies:
                  </p>
                  <div className="flex flex-col gap-2 max-w-lg mx-auto text-left">
                    {[
                      "What decisions were made about PostgreSQL and database architecture across all meetings?",
                      "What open dilemmas exist regarding AWS deployment and data residency?",
                      "What action items are assigned to Rahul across all meetings?",
                    ].map((prompt, idx) => (
                      <button
                        key={idx}
                        onClick={() => handleSendAssistant(prompt)}
                        className="p-2.5 rounded-lg bg-slate-50 hover:bg-indigo-50/70 border border-slate-200 text-xs font-medium text-slate-700 hover:text-indigo-900 transition-colors flex items-center justify-between group"
                      >
                        <span className="truncate">{prompt}</span>
                        <ArrowRight className="w-3.5 h-3.5 text-slate-400 group-hover:text-indigo-600 shrink-0 ml-2" />
                      </button>
                    ))}
                  </div>
                </div>
              ) : (
                chatMessages.map((msg) => (
                  <div
                    key={msg.id}
                    className={`flex gap-3 ${
                      msg.sender === "user" ? "justify-end" : "justify-start"
                    }`}
                  >
                    {msg.sender === "assistant" && (
                      <div className="w-7 h-7 rounded-lg bg-indigo-600 text-white flex items-center justify-center shrink-0 text-xs shadow-2xs">
                        <Bot className="w-4 h-4" />
                      </div>
                    )}

                    <div
                      className={`max-w-[85%] rounded-2xl p-4 text-xs leading-relaxed ${
                        msg.sender === "user"
                          ? "bg-indigo-600 text-white shadow-2xs"
                          : "bg-slate-50 border border-slate-200/80 text-slate-800"
                      }`}
                    >
                      <div className="whitespace-pre-line font-sans">
                        {msg.text || (
                          <span className="flex items-center gap-1.5 text-slate-400">
                            <Loader2 className="w-3.5 h-3.5 animate-spin" />
                            Synthesizing cross-meeting evidence...
                          </span>
                        )}
                      </div>

                      {/* Structured Grounded Citations */}
                      {msg.sender === "assistant" && renderCitationsPills(msg.citations)}
                    </div>

                    {msg.sender === "user" && (
                      <div className="w-7 h-7 rounded-lg bg-slate-200 text-slate-700 flex items-center justify-center shrink-0 text-xs">
                        <User className="w-4 h-4" />
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>

            {/* Assistant Input Bar */}
            <div className="relative">
              <input
                type="text"
                value={assistantInput}
                onChange={(e) => setAssistantInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSendAssistant()}
                placeholder="Ask cross-meeting question (e.g. 'What did Rahul commit to across both meetings?')..."
                className="w-full h-11 pl-4 pr-12 rounded-xl bg-white text-xs text-slate-800 placeholder:text-slate-400 border border-slate-200 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 shadow-xs"
              />
              <button
                onClick={() => handleSendAssistant()}
                disabled={isStreamingAssistant || !assistantInput.trim()}
                className="absolute right-1.5 top-1/2 -translate-y-1/2 w-8 h-8 rounded-lg bg-indigo-600 text-white flex items-center justify-center hover:bg-indigo-700 disabled:opacity-40 disabled:cursor-not-allowed shadow-2xs transition-colors"
              >
                {isStreamingAssistant ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Send className="w-3.5 h-3.5" />
                )}
              </button>
            </div>
          </div>
        )}

        {/* TAB 3: WORKSPACE MEMORY EXPLORER */}
        {activeTab === "memory" && memory && (
          <div className="space-y-6">
            {/* Confirmed Decisions Section */}
            <div className="p-5 rounded-2xl bg-white border border-slate-200/80 shadow-2xs space-y-3">
              <div className="flex items-center justify-between pb-2 border-b border-slate-100">
                <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  Confirmed Workspace Decisions ({memory.decisions.length})
                </h3>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {memory.decisions.map((d, idx) => (
                  <div
                    key={idx}
                    className="p-3.5 rounded-xl bg-slate-50/80 border border-slate-200/70 hover:border-emerald-300 transition-colors space-y-1.5"
                  >
                    <div className="flex items-center justify-between text-[11px] text-slate-500">
                      <span className="font-semibold text-slate-800 truncate max-w-[200px]">
                        {d.meeting_title}
                      </span>
                      <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800">
                        {d.status}
                      </span>
                    </div>
                    <div className="text-xs font-medium text-slate-800 leading-snug">
                      {d.decision}
                    </div>
                    {d.rationale && (
                      <div className="text-[11px] text-slate-500 italic">
                        Why: {d.rationale}
                      </div>
                    )}
                    <button
                      onClick={() => navigateToEvidence(d.session_id, 0)}
                      className="text-[11px] text-indigo-600 hover:text-indigo-800 font-semibold flex items-center gap-1 pt-1"
                    >
                      View in Meeting <ChevronRight className="w-3 h-3" />
                    </button>
                  </div>
                ))}
              </div>
            </div>

            {/* Action Items Section */}
            <div className="p-5 rounded-2xl bg-white border border-slate-200/80 shadow-2xs space-y-3">
              <div className="flex items-center justify-between pb-2 border-b border-slate-100">
                <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
                  <Clock className="w-4 h-4 text-blue-600" />
                  Assigned Action Items ({memory.action_items.length})
                </h3>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {memory.action_items.map((a, idx) => (
                  <div
                    key={idx}
                    className="p-3.5 rounded-xl bg-slate-50/80 border border-slate-200/70 hover:border-blue-300 transition-colors space-y-1.5"
                  >
                    <div className="flex items-center justify-between text-[11px] text-slate-500">
                      <span className="font-semibold text-slate-800 truncate max-w-[200px]">
                        {a.meeting_title}
                      </span>
                      <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-blue-100 text-blue-800">
                        Owner: {a.owner || "Unassigned"}
                      </span>
                    </div>
                    <div className="text-xs font-medium text-slate-800 leading-snug">
                      {a.task}
                    </div>
                    {a.deadline && (
                      <div className="text-[11px] text-slate-500">
                        Due: <strong className="text-slate-700">{a.deadline}</strong>
                      </div>
                    )}
                    <button
                      onClick={() => navigateToEvidence(a.session_id, 0)}
                      className="text-[11px] text-indigo-600 hover:text-indigo-800 font-semibold flex items-center gap-1 pt-1"
                    >
                      View in Meeting <ChevronRight className="w-3 h-3" />
                    </button>
                  </div>
                ))}
              </div>
            </div>

            {/* Open Dilemmas Section */}
            <div className="p-5 rounded-2xl bg-white border border-slate-200/80 shadow-2xs space-y-3">
              <div className="flex items-center justify-between pb-2 border-b border-slate-100">
                <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
                  <HelpCircle className="w-4 h-4 text-amber-600" />
                  Open Dilemmas Requiring Resolution ({memory.open_questions.length})
                </h3>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {memory.open_questions.map((q, idx) => (
                  <div
                    key={idx}
                    className="p-3.5 rounded-xl bg-amber-50/30 border border-amber-200/60 hover:border-amber-300 transition-colors space-y-1.5"
                  >
                    <div className="flex items-center justify-between text-[11px] text-amber-900">
                      <span className="font-semibold truncate max-w-[200px]">
                        {q.meeting_title}
                      </span>
                      <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-800">
                        Pending
                      </span>
                    </div>
                    <div className="text-xs font-medium text-slate-800 leading-snug">
                      {q.question}
                    </div>
                    {q.context && (
                      <div className="text-[11px] text-slate-500">
                        Context: {q.context}
                      </div>
                    )}
                    <button
                      onClick={() => navigateToEvidence(q.session_id, 0)}
                      className="text-[11px] text-indigo-600 hover:text-indigo-800 font-semibold flex items-center gap-1 pt-1"
                    >
                      View in Meeting <ChevronRight className="w-3 h-3" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}

export default function GlobalSearchPage() {
  return (
    <Suspense
      fallback={
        <div className="flex h-screen items-center justify-center bg-[#F6F8FC] text-slate-500 text-xs">
          Loading Global Workspace Search...
        </div>
      }
    >
      <GlobalSearchContent />
    </Suspense>
  );
}
