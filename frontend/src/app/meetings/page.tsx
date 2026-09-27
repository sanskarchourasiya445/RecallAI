"use client";

import React, { useState } from "react";
import Link from "next/link";
import { AppShell } from "@/components/layouts/AppShell";
import { AIChat } from "@/components/features/chat/AIChat";
import { QuickActions } from "@/components/features/actions/QuickActions";
import { NewMeetingModal } from "@/components/features/meeting/NewMeetingModal";
import { useMeetingsList, MeetingSortOption } from "@/lib/hooks/useMeetingsList";
import {
  Calendar,
  Clock,
  Users,
  Search,
  Plus,
  CheckCircle2,
  Zap,
  HelpCircle,
  Video,
  FileAudio,
  ArrowRight,
  RefreshCw,
  AlertCircle,
  FileText,
  SlidersHorizontal,
} from "lucide-react";

export default function MeetingsPage() {
  const [isNewMeetingOpen, setIsNewMeetingOpen] = useState(false);
  const {
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
    refetch,
  } = useMeetingsList();

  const totalDecisions = filteredMeetings.reduce((acc, m) => acc + (m.decisions_count || 0), 0);
  const totalActions = filteredMeetings.reduce((acc, m) => acc + (m.actions_count || 0), 0);
  const totalQuestions = filteredMeetings.reduce((acc, m) => acc + (m.open_questions_count || 0), 0);

  return (
    <AppShell
      currentNav="meetings"
      onNewMeetingClick={() => setIsNewMeetingOpen(true)}
      onSearch={setSearchQuery}
      rightPanel={
        <>
          <AIChat sessionId="demo_backend_migration" />
          <QuickActions sessionId="demo_backend_migration" pendingCount={3} />
        </>
      }
    >
      <div className="space-y-4">
        {/* Top Header Card */}
        <div className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-card flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2.5">
              <div className="w-9 h-9 rounded-xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600 shadow-2xs">
                <Calendar className="w-5 h-5" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-slate-900 tracking-tight">
                  Meeting Sessions Directory
                </h1>
                <p className="text-xs text-slate-400 font-normal">
                  Real indexed recordings, decisions, action plans & multi-modal intelligence
                </p>
              </div>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2.5">
            {/* Search Input */}
            <div className="relative w-full sm:w-56">
              <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search meetings, topics..."
                className="w-full h-9 pl-9 pr-3 rounded-xl border border-slate-200 bg-slate-50 focus:bg-white text-xs text-slate-800 placeholder:text-slate-400 focus:outline-none focus:border-indigo-500 transition-all"
              />
            </div>

            {/* Sort Select */}
            <div className="relative flex items-center">
              <SlidersHorizontal className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 pointer-events-none" />
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as MeetingSortOption)}
                className="h-9 pl-8 pr-3 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-xs font-semibold text-slate-700 focus:outline-none focus:border-indigo-500 transition-all"
              >
                <option value="newest">Newest First</option>
                <option value="oldest">Oldest First</option>
                <option value="title">Title (A-Z)</option>
                <option value="actions">Most Action Items</option>
                <option value="decisions">Most Decisions</option>
              </select>
            </div>

            {/* Refresh */}
            <button
              onClick={() => refetch()}
              title="Refresh meetings list"
              className="w-9 h-9 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 flex items-center justify-center text-slate-600 shadow-2xs transition-all active:scale-95 shrink-0"
            >
              <RefreshCw className="w-4 h-4" />
            </button>

            {/* New Meeting Button */}
            <button
              onClick={() => setIsNewMeetingOpen(true)}
              className="h-9 px-3.5 rounded-xl bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white text-xs font-semibold shadow-sm transition-all flex items-center gap-1.5 active:scale-95 shrink-0"
            >
              <Plus className="w-4 h-4" />
              <span>New Meeting</span>
            </button>
          </div>
        </div>

        {/* Source Filters Bar */}
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-1.5 bg-slate-100/80 p-1 rounded-xl text-xs font-semibold">
            <button
              onClick={() => setFilterSource("all")}
              className={`px-3 py-1 rounded-lg transition-all ${
                filterSource === "all"
                  ? "bg-white text-slate-900 shadow-xs"
                  : "text-slate-500 hover:text-slate-900"
              }`}
            >
              All Sources
            </button>
            <button
              onClick={() => setFilterSource("youtube")}
              className={`px-3 py-1 rounded-lg transition-all flex items-center gap-1.5 ${
                filterSource === "youtube"
                  ? "bg-white text-rose-600 shadow-xs"
                  : "text-slate-500 hover:text-slate-900"
              }`}
            >
              <Video className="w-3.5 h-3.5" />
              <span>YouTube</span>
            </button>
            <button
              onClick={() => setFilterSource("upload")}
              className={`px-3 py-1 rounded-lg transition-all flex items-center gap-1.5 ${
                filterSource === "upload"
                  ? "bg-white text-indigo-600 shadow-xs"
                  : "text-slate-500 hover:text-slate-900"
              }`}
            >
              <FileAudio className="w-3.5 h-3.5" />
              <span>Uploads</span>
            </button>
          </div>

          <span className="text-xs text-slate-400 font-normal">
            Showing <strong>{filteredMeetings.length}</strong> meeting{filteredMeetings.length === 1 ? "" : "s"}
          </span>
        </div>

        {/* Quick Stats Metrics Bar */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div className="bg-white rounded-xl border border-slate-200/80 p-3.5 shadow-2xs">
            <p className="text-[11px] font-medium text-slate-400">Total Sessions</p>
            <p className="text-xl font-bold text-slate-900 mt-0.5">
              {filteredMeetings.length} <span className="text-xs font-normal text-slate-400">indexed</span>
            </p>
          </div>
          <div className="bg-white rounded-xl border border-slate-200/80 p-3.5 shadow-2xs">
            <p className="text-[11px] font-medium text-slate-400">Key Decisions</p>
            <p className="text-xl font-bold text-emerald-600 mt-0.5">
              {totalDecisions} <span className="text-xs font-normal text-slate-400">logged</span>
            </p>
          </div>
          <div className="bg-white rounded-xl border border-slate-200/80 p-3.5 shadow-2xs">
            <p className="text-[11px] font-medium text-slate-400">Action Items</p>
            <p className="text-xl font-bold text-amber-500 mt-0.5">
              {totalActions} <span className="text-xs font-normal text-slate-400">tasks</span>
            </p>
          </div>
          <div className="bg-white rounded-xl border border-slate-200/80 p-3.5 shadow-2xs">
            <p className="text-[11px] font-medium text-slate-400">Open Questions</p>
            <p className="text-xl font-bold text-pink-500 mt-0.5">
              {totalQuestions} <span className="text-xs font-normal text-slate-400">unresolved</span>
            </p>
          </div>
        </div>

        {/* Error State */}
        {isError && (
          <div className="p-3.5 rounded-2xl bg-rose-50 border border-rose-200 text-xs text-rose-800 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
              <span>{errorMessage}</span>
            </div>
            <button
              onClick={() => refetch()}
              className="font-bold underline hover:text-rose-900"
            >
              Retry
            </button>
          </div>
        )}

        {/* Meetings Grid / List */}
        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5 animate-pulse">
            {[1, 2, 3, 4].map((i) => (
              <div
                key={i}
                className="bg-white rounded-2xl border border-slate-200/80 p-4 shadow-card space-y-3"
              >
                <div className="flex items-center justify-between">
                  <div className="h-4 bg-slate-200 rounded w-2/3" />
                  <div className="h-4 bg-slate-100 rounded w-16" />
                </div>
                <div className="h-3 bg-slate-100 rounded w-full" />
                <div className="h-3 bg-slate-100 rounded w-4/5" />
                <div className="flex gap-2 pt-2">
                  <div className="h-5 bg-slate-100 rounded-full w-20" />
                  <div className="h-5 bg-slate-100 rounded-full w-20" />
                </div>
              </div>
            ))}
          </div>
        ) : filteredMeetings.length === 0 ? (
          <div className="bg-white rounded-2xl border border-slate-200/80 p-12 text-center shadow-card space-y-3">
            <FileText className="w-10 h-10 mx-auto text-slate-300 stroke-1" />
            <h3 className="text-base font-bold text-slate-800">No meeting sessions found</h3>
            <p className="text-xs text-slate-400 max-w-sm mx-auto">
              {searchQuery
                ? `No meetings match "${searchQuery}". Try another keyword or reset filters.`
                : "No meetings found in this view. Ingest a recording or load the demo workspace!"}
            </p>
            <button
              onClick={() => setIsNewMeetingOpen(true)}
              className="mt-2 inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold shadow-xs"
            >
              <Plus className="w-4 h-4" />
              <span>Add First Meeting</span>
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
            {filteredMeetings.map((m) => {
              const isYoutube = m.source_type === "youtube" || String(m.source).toLowerCase().includes("youtube");

              return (
                <Link
                  key={m.session_id}
                  href={`/meetings/${encodeURIComponent(m.session_id)}`}
                  className="group bg-white rounded-2xl border border-slate-200/80 hover:border-indigo-300 p-4 shadow-card hover:shadow-card-hover transition-all duration-150 flex flex-col justify-between"
                >
                  <div>
                    {/* Top Row: Source Icon + Title + Status */}
                    <div className="flex items-start justify-between gap-2.5">
                      <div className="flex items-start gap-2.5 min-w-0">
                        <div
                          className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 mt-0.5 ${
                            isYoutube
                              ? "bg-rose-50 text-rose-600 border border-rose-100"
                              : "bg-indigo-50 text-indigo-600 border border-indigo-100"
                          }`}
                        >
                          {isYoutube ? (
                            <Video className="w-4 h-4" />
                          ) : (
                            <FileAudio className="w-4 h-4" />
                          )}
                        </div>
                        <div className="min-w-0">
                          <h3 className="text-[14px] sm:text-[15px] font-bold text-slate-900 group-hover:text-indigo-600 transition-colors line-clamp-1">
                            {m.title}
                          </h3>
                          <div className="flex items-center gap-2 mt-0.5 text-[11px] text-slate-400">
                            <span className="flex items-center gap-1">
                              <Clock className="w-3 h-3" />
                              {m.duration || "42 min"}
                            </span>
                            <span>•</span>
                            <span className="flex items-center gap-1">
                              <Users className="w-3 h-3" />
                              {m.participants_count || 12}
                            </span>
                            <span>•</span>
                            <span>{m.created_at || "Apr 28, 2025"}</span>
                          </div>
                        </div>
                      </div>

                      {/* Status Badge */}
                      <span className="px-2 py-0.5 rounded-full bg-emerald-50 border border-emerald-200/60 text-emerald-700 text-[10px] font-semibold capitalize shrink-0">
                        {m.status}
                      </span>
                    </div>

                    {/* Summary Preview */}
                    {m.summary_preview && (
                      <p className="text-xs text-slate-600 line-clamp-2 mt-2.5 leading-relaxed font-normal">
                        {m.summary_preview}
                      </p>
                    )}
                  </div>

                  {/* Bottom Row: Intelligence Pills + Open Arrow */}
                  <div className="mt-3.5 pt-2.5 border-t border-slate-100 flex items-center justify-between">
                    <div className="flex flex-wrap items-center gap-1.5">
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-[#F3FAF6] border border-[#DEF1E7] text-emerald-700 text-[11px] font-semibold">
                        <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                        {m.decisions_count} decisions
                      </span>
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-[#FEF9F2] border border-[#FBEED9] text-amber-700 text-[11px] font-semibold">
                        <Zap className="w-3 h-3 text-amber-500 fill-amber-500" />
                        {m.actions_count} tasks
                      </span>
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-[#FCF5F7] border border-[#F9E2E8] text-pink-700 text-[11px] font-semibold">
                        <HelpCircle className="w-3 h-3 text-pink-500" />
                        {m.open_questions_count} questions
                      </span>
                    </div>

                    <div className="flex items-center text-xs font-semibold text-indigo-600 group-hover:translate-x-0.5 transition-transform">
                      <span>Open Workspace</span>
                      <ArrowRight className="w-3.5 h-3.5 ml-1" />
                    </div>
                  </div>
                </Link>
              );
            })}
          </div>
        )}
      </div>

      <NewMeetingModal
        isOpen={isNewMeetingOpen}
        onClose={() => {
          setIsNewMeetingOpen(false);
          refetch();
        }}
      />
    </AppShell>
  );
}
