"use client";

import React, { useState } from "react";
import {
  Zap,
  ChevronRight,
  Plus,
  Mail,
  Calendar,
  Layers,
  CheckCircle2,
  XCircle,
  Clock,
  ShieldAlert,
} from "lucide-react";
import { PendingActionItem } from "@/types/action";
import { confirmAction, rejectAction, executeAction } from "@/lib/api/actions";

interface QuickActionsProps {
  sessionId?: string;
  pendingCount?: number;
  onActionCompleted?: (message: string) => void;
}

export function QuickActions({
  sessionId = "demo_backend_migration",
  pendingCount = 3,
  onActionCompleted,
}: QuickActionsProps) {
  const [activeTab, setActiveTab] = useState<"available" | "pending">("available");
  const [pendingList, setPendingList] = useState<PendingActionItem[]>([
    {
      action_id: "act-101",
      session_id: sessionId,
      tool_name: "send_email",
      risk_level: "consequential",
      preview_summary: "Send executive summary & action items to Sarah, Rahul, and David",
      expires_at: Date.now() + 3600000,
    },
    {
      action_id: "act-102",
      session_id: sessionId,
      tool_name: "create_task",
      risk_level: "consequential",
      preview_summary: "Create Jira Ticket: 'Prepare and distribute PostgreSQL migration plan' (Assignee: Rahul)",
      expires_at: Date.now() + 3600000,
    },
    {
      action_id: "act-103",
      session_id: sessionId,
      tool_name: "schedule_calendar_event",
      risk_level: "consequential",
      preview_summary: "Schedule Standup Follow-up for Tuesday May 2, 2025 at 10:00 AM",
      expires_at: Date.now() + 3600000,
    },
  ]);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  const tools = [
    {
      id: "create_task",
      title: "Create Jira Ticket",
      subtitle: "Create a new ticket in Jira",
      icon: Layers,
      bg: "bg-blue-50 text-blue-600 border border-blue-100",
    },
    {
      id: "send_email",
      title: "Send Email",
      subtitle: "Send an email to team members",
      icon: Mail,
      bg: "bg-sky-50 text-sky-600 border border-sky-100",
    },
    {
      id: "schedule_meeting",
      title: "Schedule Meeting",
      subtitle: "Create a calendar event",
      icon: Calendar,
      bg: "bg-purple-50 text-purple-600 border border-purple-100",
    },
  ];

  const handleToolClick = async (toolId: string) => {
    try {
      const res = await executeAction(sessionId, toolId, {
        source_session_id: sessionId,
        title: "Platform Architecture Follow-up",
      });

      if (res.requires_confirmation) {
        setStatusMessage(`Action staged for confirmation: ${res.message}`);
        setActiveTab("pending");
      } else {
        setStatusMessage(`Action executed: ${res.message}`);
        onActionCompleted?.(res.message);
      }
    } catch {
      const msg = `Triggered action: ${toolId} (Simulated execution)`;
      setStatusMessage(msg);
      onActionCompleted?.(msg);
    }

    setTimeout(() => setStatusMessage(null), 3500);
  };

  const handleConfirm = async (actionId: string) => {
    try {
      await confirmAction(actionId, sessionId);
      setPendingList((prev) => prev.filter((a) => a.action_id !== actionId));
      setStatusMessage("Action confirmed and executed successfully!");
      onActionCompleted?.("Action confirmed");
    } catch {
      setPendingList((prev) => prev.filter((a) => a.action_id !== actionId));
      setStatusMessage("Action confirmed (Simulated approval)!");
      onActionCompleted?.("Action confirmed");
    }
    setTimeout(() => setStatusMessage(null), 3000);
  };

  const handleReject = async (actionId: string) => {
    try {
      await rejectAction(actionId, sessionId, "User cancelled from UI");
      setPendingList((prev) => prev.filter((a) => a.action_id !== actionId));
      setStatusMessage("Action rejected.");
      onActionCompleted?.("Action rejected");
    } catch {
      setPendingList((prev) => prev.filter((a) => a.action_id !== actionId));
      setStatusMessage("Action rejected.");
      onActionCompleted?.("Action rejected");
    }
    setTimeout(() => setStatusMessage(null), 3000);
  };

  return (
    <div className="bg-white rounded-2xl border border-slate-200/80 shadow-card p-3.5">
      {/* Header */}
      <div className="flex items-center gap-2 pb-1.5">
        <div className="w-6 h-6 rounded-lg bg-blue-50 flex items-center justify-center shrink-0">
          <Zap className="w-3.5 h-3.5 text-blue-600 fill-blue-600" />
        </div>
        <div>
          <h3 className="text-xs font-bold text-slate-900 leading-tight">
            Quick Actions
          </h3>
          <p className="text-[11px] text-slate-400 font-normal">
            Manage and execute meeting actions
          </p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-3 mt-2 border-b border-slate-100 text-xs">
        <button
          onClick={() => setActiveTab("available")}
          className={`pb-1.5 font-semibold flex items-center gap-1.5 transition-all text-xs ${
            activeTab === "available"
              ? "text-indigo-600 border-b-2 border-indigo-600"
              : "text-slate-400 hover:text-slate-600"
          }`}
        >
          <Plus className="w-3 h-3" />
          <span>Available Tools</span>
        </button>

        <button
          onClick={() => setActiveTab("pending")}
          className={`pb-1.5 font-semibold flex items-center gap-1.5 transition-all text-xs ${
            activeTab === "pending"
              ? "text-indigo-600 border-b-2 border-indigo-600"
              : "text-slate-400 hover:text-slate-600"
          }`}
        >
          <Clock className="w-3 h-3" />
          <span>Pending Actions</span>
          {(pendingList.length > 0 || pendingCount > 0) && (
            <span className="px-1.5 py-0.2 rounded-full bg-indigo-50 text-indigo-600 text-[10px] font-bold">
              {pendingList.length || pendingCount}
            </span>
          )}
        </button>
      </div>

      {/* Feedback banner */}
      {statusMessage && (
        <div className="mt-2 p-1.5 rounded-lg bg-indigo-50 border border-indigo-100 text-[10px] text-indigo-700 font-medium">
          {statusMessage}
        </div>
      )}

      {/* Tab Content: Compact 58-64px rows */}
      <div className="mt-1.5">
        {activeTab === "available" ? (
          <div className="divide-y divide-slate-100">
            {tools.map((tool) => {
              const Icon = tool.icon;
              return (
                <div
                  key={tool.id}
                  onClick={() => handleToolClick(tool.id)}
                  className="h-[56px] flex items-center justify-between group cursor-pointer hover:bg-slate-50/70 rounded-xl px-2 transition-colors"
                >
                  <div className="flex items-center gap-2.5 min-w-0">
                    <div
                      className={`w-7 h-7 rounded-lg ${tool.bg} flex items-center justify-center shrink-0 shadow-2xs`}
                    >
                      <Icon className="w-3.5 h-3.5" />
                    </div>
                    <div className="min-w-0 leading-tight">
                      <p className="text-xs font-bold text-slate-800 truncate">
                        {tool.title}
                      </p>
                      <p className="text-[11px] text-slate-400 truncate mt-0.5">
                        {tool.subtitle}
                      </p>
                    </div>
                  </div>
                  <ChevronRight className="w-3.5 h-3.5 text-slate-300 group-hover:text-slate-600 transition-transform group-hover:translate-x-0.5 shrink-0" />
                </div>
              );
            })}
          </div>
        ) : (
          <div className="space-y-2 mt-2">
            {pendingList.length === 0 ? (
              <p className="text-xs text-slate-400 py-3 text-center">
                No pending consequential actions.
              </p>
            ) : (
              pendingList.map((p) => (
                <div
                  key={p.action_id}
                  className="p-2.5 rounded-xl border border-amber-200/80 bg-amber-50/40 text-xs text-slate-800 space-y-1.5"
                >
                  <div className="flex items-center justify-between gap-1">
                    <div className="flex items-center gap-1.5 font-bold text-amber-900 text-[11px]">
                      <ShieldAlert className="w-3.5 h-3.5 text-amber-600" />
                      <span>{p.tool_name}</span>
                    </div>
                    <span className="text-[10px] text-amber-700 font-semibold px-1.5 py-0.2 bg-amber-100 rounded">
                      {p.risk_level}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-600 leading-snug">
                    {p.preview_summary}
                  </p>
                  <div className="flex items-center justify-end gap-2 pt-1 border-t border-amber-200/50">
                    <button
                      onClick={() => handleReject(p.action_id)}
                      className="px-2 py-0.5 rounded-lg border border-slate-300 hover:bg-slate-100 text-slate-700 text-[10px] font-semibold flex items-center gap-1"
                    >
                      <XCircle className="w-3 h-3 text-slate-400" />
                      <span>Reject</span>
                    </button>
                    <button
                      onClick={() => handleConfirm(p.action_id)}
                      className="px-2 py-0.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-[10px] font-semibold flex items-center gap-1 shadow-xs"
                    >
                      <CheckCircle2 className="w-3 h-3" />
                      <span>Confirm</span>
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        )}
      </div>
    </div>
  );
}
