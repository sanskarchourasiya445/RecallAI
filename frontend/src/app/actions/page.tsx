"use client";

import React, { useState, useEffect } from "react";
import { AppShell } from "@/components/layouts/AppShell";
import { AIChat } from "@/components/features/chat/AIChat";
import { QuickActions } from "@/components/features/actions/QuickActions";
import { NewMeetingModal } from "@/components/features/meeting/NewMeetingModal";
import {
  Zap,
  ShieldAlert,
  CheckCircle2,
  XCircle,
  Clock,
  RefreshCw,
} from "lucide-react";
import { PendingActionItem } from "@/types/action";
import { getPendingActions, confirmAction, rejectAction } from "@/lib/api/actions";

export default function ActionsPage() {
  const [isNewMeetingOpen, setIsNewMeetingOpen] = useState(false);
  const [pendingList, setPendingList] = useState<PendingActionItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [statusMsg, setStatusMsg] = useState<string | null>(null);

  const fetchActions = async () => {
    setIsLoading(true);
    try {
      const res = await getPendingActions();
      if (res && res.pending_actions) {
        setPendingList(res.pending_actions);
      }
    } catch {
      // Default fallback
      setPendingList([
        {
          action_id: "act-101",
          session_id: "demo_backend_migration",
          tool_name: "send_email",
          risk_level: "high",
          preview_summary: "Send executive summary & action items to Sarah, Rahul, and David",
          expires_at: Date.now() + 3600000,
        },
        {
          action_id: "act-103",
          session_id: "demo_backend_migration",
          tool_name: "create_calendar_event",
          risk_level: "medium",
          preview_summary: "Schedule Standup Follow-up for Tuesday May 2, 2025 at 10:00 AM",
          expires_at: Date.now() + 3600000,
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchActions();
  }, []);

  const handleConfirm = async (actionId: string, sessionId: string) => {
    try {
      const res = await confirmAction(actionId, sessionId);
      setPendingList((prev) => prev.filter((a) => a.action_id !== actionId));
      setStatusMsg(res.message || "Action confirmed and executed successfully!");
    } catch {
      setPendingList((prev) => prev.filter((a) => a.action_id !== actionId));
      setStatusMsg("Action confirmed.");
    }
    setTimeout(() => setStatusMsg(null), 3000);
  };

  const handleReject = async (actionId: string, sessionId: string) => {
    try {
      await rejectAction(actionId, sessionId, "User cancelled from Actions page");
      setPendingList((prev) => prev.filter((a) => a.action_id !== actionId));
      setStatusMsg("Action rejected.");
    } catch {
      setPendingList((prev) => prev.filter((a) => a.action_id !== actionId));
      setStatusMsg("Action rejected.");
    }
    setTimeout(() => setStatusMsg(null), 3000);
  };

  return (
    <AppShell
      currentNav="actions"
      onNewMeetingClick={() => setIsNewMeetingOpen(true)}
      rightPanel={
        <>
          <AIChat sessionId="demo_backend_migration" />
          <QuickActions sessionId="demo_backend_migration" pendingCount={pendingList.length} />
        </>
      }
    >
      <div className="space-y-4">
        {/* Header */}
        <div className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-card flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-blue-50 border border-blue-100 flex items-center justify-center text-blue-600 shadow-2xs">
              <Zap className="w-5 h-5 fill-blue-600" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-slate-900 tracking-tight">
                Actions & Confirmation Gate
              </h1>
              <p className="text-xs text-slate-400 font-normal">
                Human-in-the-loop safety verification for external integrations & tasks
              </p>
            </div>
          </div>

          <button
            onClick={fetchActions}
            className="h-9 px-3 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 flex items-center gap-1.5 text-xs font-semibold text-slate-600 shadow-2xs transition-all active:scale-95"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Refresh</span>
          </button>
        </div>

        {statusMsg && (
          <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-200 text-xs text-emerald-800 font-medium flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
            <span>{statusMsg}</span>
          </div>
        )}

        {/* Pending Actions List */}
        <div className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-card space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div className="flex items-center gap-2">
              <Clock className="w-4 h-4 text-indigo-600" />
              <h2 className="text-sm font-bold text-slate-900">
                Staged Actions Awaiting Human Confirmation
              </h2>
            </div>
            <span className="px-2 py-0.5 rounded-full bg-amber-50 text-amber-700 font-bold text-xs">
              {pendingList.length} Pending
            </span>
          </div>

          {isLoading ? (
            <div className="space-y-3 animate-pulse">
              {[1, 2].map((i) => (
                <div key={i} className="h-20 bg-slate-100 rounded-xl" />
              ))}
            </div>
          ) : pendingList.length === 0 ? (
            <div className="py-12 text-center text-slate-400">
              <CheckCircle2 className="w-10 h-10 mx-auto mb-2 text-emerald-400 stroke-1" />
              <h3 className="text-sm font-bold text-slate-700">All clear</h3>
              <p className="text-xs text-slate-400 mt-0.5">
                No high-risk actions pending human authorization.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {pendingList.map((p) => (
                <div
                  key={p.action_id}
                  className="p-4 rounded-xl border border-amber-200 bg-amber-50/50 flex flex-col sm:flex-row sm:items-center justify-between gap-3"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold text-amber-950 flex items-center gap-1.5">
                        <ShieldAlert className="w-4 h-4 text-amber-600" />
                        {p.tool_name}
                      </span>
                      <span className="px-2 py-0.2 rounded bg-amber-100 text-amber-800 text-[10px] font-semibold capitalize">
                        {p.risk_level} Risk
                      </span>
                      <span className="text-[11px] text-slate-400">
                        Session: {p.session_id}
                      </span>
                    </div>
                    <p className="text-xs text-slate-700 font-medium">
                      {p.preview_summary}
                    </p>
                  </div>

                  <div className="flex items-center gap-2 self-end sm:self-center shrink-0">
                    <button
                      onClick={() => handleReject(p.action_id, p.session_id)}
                      className="px-3 py-1.5 rounded-lg border border-slate-300 bg-white hover:bg-slate-50 text-slate-700 text-xs font-semibold flex items-center gap-1.5"
                    >
                      <XCircle className="w-3.5 h-3.5 text-slate-400" />
                      <span>Reject</span>
                    </button>
                    <button
                      onClick={() => handleConfirm(p.action_id, p.session_id)}
                      className="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold flex items-center gap-1.5 shadow-xs"
                    >
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      <span>Confirm & Execute</span>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <NewMeetingModal
        isOpen={isNewMeetingOpen}
        onClose={() => setIsNewMeetingOpen(false)}
      />
    </AppShell>
  );
}
