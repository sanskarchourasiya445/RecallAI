"use client";

import React, { useState, useRef, useEffect, useMemo, useCallback } from "react";
import {
  Sparkles,
  Send,
  Bot,
  Loader2,
  ArrowUpRight,
  Copy,
  Check,
  RotateCcw,
  AlertCircle,
  CheckCircle2,
  XCircle,
  Trash2,
  Clock,
  Users,
} from "lucide-react";
import { UIMessage, CitationItem } from "@/types/chat";
import { DecisionItem, ActionItem, OpenQuestionItem } from "@/types/meeting";
import {
  sendChatMessage,
  sendChatMessageStream,
  getChatHistory,
  clearChatHistory,
} from "@/lib/api/chat";
import { confirmAction, rejectAction } from "@/lib/api/actions";

interface AIChatProps {
  sessionId?: string;
  meetingTitle?: string;
  meetingDuration?: string;
  meetingParticipantsCount?: number;
  decisions?: DecisionItem[];
  actionItems?: ActionItem[];
  openQuestions?: OpenQuestionItem[];
  initialMessages?: UIMessage[];
  onActionTriggered?: (actionId: string) => void;
  onNavigateToTranscript?: (timestamp: string, evidenceId?: string) => void;
}

function formatCitationLabel(evidenceId: string, timeRange: string): string {
  if (!timeRange || timeRange === "Not specified") return `[${evidenceId}]`;
  const startPart = timeRange.split(/[-–]/)[0]?.trim();
  if (!startPart) return `[${evidenceId}]`;
  const cleaned =
    startPart.startsWith("00:") && startPart.length > 5
      ? startPart.slice(3)
      : startPart;
  return `[${evidenceId} · ${cleaned}]`;
}

export function AIChat({
  sessionId = "demo_backend_migration",
  meetingTitle = "Product & Architecture Sync",
  meetingDuration,
  meetingParticipantsCount,
  decisions = [],
  actionItems = [],
  openQuestions = [],
  initialMessages,
  onActionTriggered,
  onNavigateToTranscript,
}: AIChatProps) {
  const [messages, setMessages] = useState<UIMessage[]>(initialMessages || []);
  const [inputVal, setInputVal] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [actionProcessingId, setActionProcessingId] = useState<string | null>(null);
  const [lastUserMessage, setLastUserMessage] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  // Auto-scroll on new messages or streaming chunk updates
  const scrollToBottom = useCallback((smooth = true) => {
    messagesEndRef.current?.scrollIntoView({
      behavior: smooth ? "smooth" : "auto",
    });
  }, []);

  useEffect(() => {
    scrollToBottom(true);
  }, [messages, isLoading, isStreaming, scrollToBottom]);

  // Load chat history from backend on session mount
  useEffect(() => {
    let isCancelled = false;

    async function loadHistory() {
      if (initialMessages && initialMessages.length > 0) return;

      try {
        const hist = await getChatHistory(sessionId);
        if (isCancelled) return;

        if (hist.turns && hist.turns.length > 0) {
          const loaded: UIMessage[] = [];
          hist.turns.forEach((t) => {
            const timeStr = t.timestamp
              ? new Date(t.timestamp).toLocaleTimeString([], {
                  hour: "2-digit",
                  minute: "2-digit",
                })
              : "Previous";

            loaded.push({
              id: `usr-hist-${t.turn_id}`,
              sender: "user",
              content: t.user_message,
              timestamp: timeStr,
            });

            loaded.push({
              id: `ai-hist-${t.turn_id}`,
              sender: "ai",
              content: t.assistant_message,
              timestamp: timeStr,
              citations: t.evidence_ids?.map((id, idx) => ({
                evidence_id: id,
                time_range: "Not specified",
                chunk_index: idx,
                source: "meeting_transcript",
              })),
            });
          });
          setMessages(loaded);
        }
      } catch {
        // If history endpoint returns 404 (session not yet loaded in memory), keep empty
      }
    }

    loadHistory();

    return () => {
      isCancelled = true;
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, [sessionId, initialMessages]);

  // Compute dynamic suggested prompts based on actual meeting intelligence
  const suggestedPrompts = useMemo(() => {
    const list: string[] = [];

    // Decisions-driven prompt
    if (decisions && decisions.length > 0) {
      const firstDec = decisions[0];
      const decTitle = firstDec.decision || "";
      if (decTitle.toLowerCase().includes("postgres")) {
        list.push("What was decided about PostgreSQL migration?");
      } else if (decTitle.length > 5 && decTitle.length < 50) {
        list.push(`What did the team decide regarding ${decTitle}?`);
      } else {
        list.push("What were the main decisions made in this meeting?");
      }
    } else {
      list.push("What were the main decisions made?");
    }

    // Action items-driven prompt
    if (actionItems && actionItems.length > 0) {
      const firstAct = actionItems[0];
      if (firstAct.owner) {
        list.push(`What action items were assigned to ${firstAct.owner}?`);
      } else {
        list.push("What action items were assigned and to whom?");
      }
    } else {
      list.push("What action items were assigned?");
    }

    // Open questions-driven prompt
    if (openQuestions && openQuestions.length > 0) {
      list.push("What questions or dilemmas remain unresolved?");
    } else {
      list.push("Summarize the most important discussion points.");
    }

    return list.slice(0, 3);
  }, [decisions, actionItems, openQuestions]);

  // Copy response content
  const handleCopy = (content: string, id: string) => {
    if (typeof window !== "undefined") {
      navigator.clipboard.writeText(content);
      setCopiedId(id);
      setTimeout(() => setCopiedId(null), 2000);
    }
  };

  // Reset/Clear history for current session
  const handleClearHistory = async () => {
    if (window.confirm("Clear conversation history for this meeting?")) {
      try {
        await clearChatHistory(sessionId);
        setMessages([]);
      } catch (e) {
        console.error("Failed to clear history:", e);
      }
    }
  };

  // Handle action confirmation directly inside chat
  const handleConfirmAction = async (actionId: string, messageId: string) => {
    setActionProcessingId(actionId);
    try {
      const result = await confirmAction(actionId, sessionId);
      setMessages((prev) =>
        prev.map((msg) => {
          if (msg.id === messageId) {
            return {
              ...msg,
              requiresConfirmation: false,
              actionStatus: "confirmed",
              actionResult: result.message || "Action confirmed and executed successfully.",
            };
          }
          return msg;
        })
      );
      if (onActionTriggered) onActionTriggered(actionId);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Confirmation failed";
      setErrorMsg(msg);
    } finally {
      setActionProcessingId(null);
    }
  };

  // Handle action rejection directly inside chat
  const handleRejectAction = async (actionId: string, messageId: string) => {
    setActionProcessingId(actionId);
    try {
      await rejectAction(actionId, sessionId, "Declined in chat interface");
      setMessages((prev) =>
        prev.map((msg) => {
          if (msg.id === messageId) {
            return {
              ...msg,
              requiresConfirmation: false,
              actionStatus: "rejected",
              actionResult: "Action was declined and cancelled.",
            };
          }
          return msg;
        })
      );
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Rejection failed";
      setErrorMsg(msg);
    } finally {
      setActionProcessingId(null);
    }
  };

  // Send query with progressive streaming fallback
  const handleSend = async (overrideText?: string) => {
    const text = (overrideText || inputVal).trim();
    if (!text || isLoading || isStreaming) return;

    setErrorMsg(null);
    setLastUserMessage(text);
    const userTime = new Date().toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    });

    const userMessage: UIMessage = {
      id: `usr-${Date.now()}`,
      sender: "user",
      content: text,
      timestamp: userTime,
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputVal("");
    setIsLoading(true);

    const aiMessageId = `ai-${Date.now()}`;
    const initialAiMessage: UIMessage = {
      id: aiMessageId,
      sender: "ai",
      content: "",
      timestamp: userTime,
      isStreaming: true,
      citations: [],
      evidence: [],
    };

    // Pre-insert streaming AI message placeholder
    setMessages((prev) => [...prev, initialAiMessage]);

    // Setup abort controller
    const controller = new AbortController();
    abortControllerRef.current = controller;

    try {
      setIsStreaming(true);
      setIsLoading(false);

      await sendChatMessageStream(
        {
          session_id: sessionId,
          message: text,
          top_k: 4,
        },
        {
          onMetadata: (meta) => {
            setMessages((prev) =>
              prev.map((msg) => {
                if (msg.id === aiMessageId) {
                  return {
                    ...msg,
                    citations: meta.citations || [],
                    evidence: meta.evidence || [],
                    intent: meta.intent,
                    requiresConfirmation: meta.requires_confirmation,
                    pendingActionId: meta.pending_action_id,
                  };
                }
                return msg;
              })
            );
          },
          onToken: (delta) => {
            setMessages((prev) =>
              prev.map((msg) => {
                if (msg.id === aiMessageId) {
                  return {
                    ...msg,
                    content: msg.content + delta,
                  };
                }
                return msg;
              })
            );
          },
          onDone: (doneData) => {
            const aiTime = new Date().toLocaleTimeString([], {
              hour: "2-digit",
              minute: "2-digit",
            });

            setMessages((prev) =>
              prev.map((msg) => {
                if (msg.id === aiMessageId) {
                  return {
                    ...msg,
                    content: doneData.answer || msg.content,
                    timestamp: aiTime,
                    isStreaming: false,
                    citations: doneData.citations || msg.citations,
                    evidence: doneData.evidence || msg.evidence,
                    intent: doneData.intent,
                    requiresConfirmation: doneData.requires_confirmation,
                    pendingActionId: doneData.pending_action_id,
                  };
                }
                return msg;
              })
            );

            if (
              doneData.requires_confirmation &&
              doneData.pending_action_id &&
              onActionTriggered
            ) {
              onActionTriggered(doneData.pending_action_id);
            }
          },
          onError: (streamErr) => {
            throw streamErr;
          },
        },
        controller.signal
      );
    } catch {
      // Fallback to non-streaming endpoint if streaming fails or disconnects
      try {
        const fallbackRes = await sendChatMessage({
          session_id: sessionId,
          message: text,
          top_k: 4,
        });

        const aiTime = new Date().toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
        });

        setMessages((prev) =>
          prev.map((msg) => {
            if (msg.id === aiMessageId) {
              return {
                ...msg,
                content: fallbackRes.answer,
                timestamp: aiTime,
                isStreaming: false,
                citations: fallbackRes.citations,
                evidence: fallbackRes.evidence,
                intent: fallbackRes.intent,
                requiresConfirmation: fallbackRes.requires_confirmation,
                pendingActionId: fallbackRes.pending_action_id,
              };
            }
            return msg;
          })
        );

        if (
          fallbackRes.requires_confirmation &&
          fallbackRes.pending_action_id &&
          onActionTriggered
        ) {
          onActionTriggered(fallbackRes.pending_action_id);
        }
      } catch (err: unknown) {
        const errText =
          err instanceof Error ? err.message : "Failed to query intelligence service";
        setErrorMsg(errText);

        setMessages((prev) =>
          prev.map((msg) => {
            if (msg.id === aiMessageId) {
              return {
                ...msg,
                content: `Unable to process query: ${errText}. Please check the meeting status and retry.`,
                isStreaming: false,
                error: true,
              };
            }
            return msg;
          })
        );
      }
    } finally {
      setIsLoading(false);
      setIsStreaming(false);
      abortControllerRef.current = null;
    }
  };

  // Retry last failed query
  const handleRetry = () => {
    if (lastUserMessage) {
      handleSend(lastUserMessage);
    }
  };

  return (
    <div className="bg-white rounded-2xl border border-slate-200/80 shadow-card flex flex-col flex-[6] min-h-[360px] max-h-[70%] overflow-hidden">
      {/* Header with Title and Clear History */}
      <div className="shrink-0 px-3.5 py-2.5 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
        <div className="flex items-center gap-2 min-w-0">
          <div className="w-6 h-6 rounded-lg bg-indigo-50 flex items-center justify-center shrink-0">
            <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
          </div>
          <div className="min-w-0">
            <h3 className="text-[13px] sm:text-[14px] font-bold text-slate-900 leading-tight truncate">
              RecallAI Assistant
            </h3>
            <p className="text-[10.5px] text-slate-400 font-normal truncate">
              Grounded multi-turn conversation
            </p>
          </div>
        </div>

        {messages.length > 0 && (
          <button
            type="button"
            onClick={handleClearHistory}
            title="Clear conversation history"
            className="p-1 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        )}
      </div>

      {/* Subtle Active Meeting Context Bar */}
      <div className="shrink-0 px-3.5 py-1.5 bg-slate-100/60 border-b border-slate-200/50 flex items-center justify-between text-[10.5px] text-slate-600">
        <div className="flex items-center gap-1.5 truncate">
          <span className="font-semibold text-indigo-700 uppercase tracking-wider text-[9px] px-1 py-0.5 rounded bg-indigo-50 border border-indigo-100/60">
            Analyzing
          </span>
          <span className="font-medium text-slate-800 truncate" title={meetingTitle}>
            {meetingTitle}
          </span>
        </div>
        <div className="flex items-center gap-2 shrink-0 ml-2 text-slate-400">
          {meetingDuration && (
            <span className="inline-flex items-center gap-0.5">
              <Clock className="w-3 h-3" />
              {meetingDuration}
            </span>
          )}
          {meetingParticipantsCount !== undefined && meetingParticipantsCount > 0 && (
            <span className="inline-flex items-center gap-0.5">
              <Users className="w-3 h-3" />
              {meetingParticipantsCount}
            </span>
          )}
        </div>
      </div>

      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto p-3 space-y-3">
        {/* Empty State with Suggested Questions */}
        {messages.length === 0 && !isLoading && (
          <div className="py-6 px-2 text-center flex flex-col items-center justify-center">
            <div className="w-9 h-9 rounded-2xl bg-indigo-50 border border-indigo-100 flex items-center justify-center mb-2.5 shadow-2xs">
              <Sparkles className="w-4.5 h-4.5 text-indigo-600" />
            </div>
            <h4 className="text-xs font-bold text-slate-800 mb-1">
              Ask RecallAI anything about this meeting
            </h4>
            <p className="text-[11px] text-slate-500 max-w-[260px] leading-relaxed mb-4">
              Answers are grounded in verified transcript passages with navigable timestamp citations.
            </p>

            <div className="w-full space-y-1.5 text-left">
              <p className="text-[10px] uppercase font-bold text-slate-400 tracking-wider px-1">
                Suggested Questions:
              </p>
              {suggestedPrompts.map((prompt, i) => (
                <button
                  key={i}
                  type="button"
                  onClick={() => handleSend(prompt)}
                  className="w-full text-left px-2.5 py-1.5 rounded-xl bg-slate-50 hover:bg-indigo-50/70 border border-slate-200/80 hover:border-indigo-200 text-[11px] text-slate-700 hover:text-indigo-900 transition-all flex items-center justify-between group shadow-2xs"
                >
                  <span className="truncate pr-2 font-medium">{prompt}</span>
                  <ArrowUpRight className="w-3 h-3 text-slate-400 group-hover:text-indigo-600 transition-colors shrink-0" />
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Message Stream */}
        {messages.map((msg) => {
          const isUser = msg.sender === "user";

          if (isUser) {
            return (
              <div key={msg.id} className="flex flex-col items-end">
                <div className="max-w-[85%] rounded-2xl rounded-tr-xs bg-indigo-600 text-white px-3 py-2 text-xs shadow-2xs leading-relaxed font-normal">
                  {msg.content}
                </div>
                <span className="text-[9.5px] text-slate-400 mt-1 mr-1">
                  {msg.timestamp}
                </span>
              </div>
            );
          }

          return (
            <div key={msg.id} className="flex items-start gap-2">
              {/* AI Avatar */}
              <div className="w-6 h-6 rounded-full bg-gradient-to-tr from-indigo-600 to-purple-600 flex items-center justify-center shrink-0 mt-0.5 shadow-2xs">
                <Bot className="w-3.5 h-3.5 text-white" />
              </div>

              <div className="flex-1 min-w-0">
                {/* AI Response Card */}
                <div
                  className={`rounded-2xl rounded-tl-xs p-3 text-xs leading-relaxed shadow-2xs transition-all ${
                    msg.error
                      ? "bg-rose-50/80 border border-rose-200 text-rose-800"
                      : "bg-slate-50 border border-slate-200/80 text-slate-800"
                  }`}
                >
                  {/* Content with progressive streaming cursor */}
                  <div className="whitespace-pre-line">
                    {msg.content || (
                      <span className="text-slate-400 italic">Thinking...</span>
                    )}
                    {msg.isStreaming && (
                      <span className="inline-block w-1.5 h-3.5 ml-1 bg-indigo-600 animate-pulse align-middle" />
                    )}
                  </div>

                  {/* Interactive Grounded Citations (e.g., [E1 · 00:55]) */}
                  {msg.citations && msg.citations.length > 0 && !msg.isStreaming && (
                    <div className="mt-2.5 pt-2 border-t border-slate-200/70">
                      <p className="text-[9.5px] text-slate-400 font-bold mb-1.5 uppercase tracking-wider flex items-center gap-1">
                        <span>Grounded Citations:</span>
                      </p>
                      <div className="flex flex-wrap gap-1.5">
                        {msg.citations.map((c: CitationItem, i: number) => {
                          const label = formatCitationLabel(c.evidence_id, c.time_range);
                          return (
                            <button
                              key={i}
                              type="button"
                              onClick={() =>
                                onNavigateToTranscript?.(c.time_range, c.evidence_id)
                              }
                              title={`Jump to transcript timestamp: ${c.time_range}`}
                              className="inline-flex items-center gap-1 px-2 py-0.5 rounded-lg bg-indigo-50 hover:bg-indigo-100/90 border border-indigo-200/80 text-indigo-700 text-[10px] font-semibold cursor-pointer transition-all active:scale-95 shadow-2xs hover:shadow-xs"
                            >
                              <span>{label}</span>
                              <ArrowUpRight className="w-2.5 h-2.5 opacity-70" />
                            </button>
                          );
                        })}
                      </div>
                    </div>
                  )}

                  {/* Consequential Action Confirmation Gate UI */}
                  {msg.requiresConfirmation && msg.pendingActionId && (
                    <div className="mt-3 p-2.5 rounded-xl bg-amber-50 border border-amber-200 text-amber-900 shadow-2xs">
                      <div className="flex items-center gap-1.5 mb-1.5">
                        <AlertCircle className="w-3.5 h-3.5 text-amber-600 shrink-0" />
                        <span className="text-[11px] font-bold">Action Requires Confirmation</span>
                      </div>
                      <p className="text-[10.5px] text-amber-800 leading-tight mb-2.5">
                        This action has consequential effects. Please confirm or cancel:
                      </p>
                      <div className="flex items-center gap-2">
                        <button
                          type="button"
                          disabled={actionProcessingId === msg.pendingActionId}
                          onClick={() => handleConfirmAction(msg.pendingActionId!, msg.id)}
                          className="px-2.5 py-1 rounded-lg bg-amber-600 hover:bg-amber-700 disabled:opacity-50 text-white text-[10.5px] font-semibold flex items-center gap-1 shadow-2xs transition-all cursor-pointer"
                        >
                          {actionProcessingId === msg.pendingActionId ? (
                            <Loader2 className="w-3 h-3 animate-spin" />
                          ) : (
                            <CheckCircle2 className="w-3 h-3" />
                          )}
                          <span>Confirm</span>
                        </button>
                        <button
                          type="button"
                          disabled={actionProcessingId === msg.pendingActionId}
                          onClick={() => handleRejectAction(msg.pendingActionId!, msg.id)}
                          className="px-2.5 py-1 rounded-lg bg-white hover:bg-slate-100 border border-slate-200 text-slate-700 text-[10.5px] font-semibold flex items-center gap-1 transition-all cursor-pointer"
                        >
                          <XCircle className="w-3 h-3 text-rose-500" />
                          <span>Reject</span>
                        </button>
                      </div>
                    </div>
                  )}

                  {/* Action Completed Status Badge */}
                  {msg.actionStatus && (
                    <div
                      className={`mt-2.5 px-2.5 py-1.5 rounded-lg text-[10.5px] flex items-center gap-1.5 font-medium ${
                        msg.actionStatus === "confirmed"
                          ? "bg-emerald-50 border border-emerald-200 text-emerald-800"
                          : "bg-slate-100 border border-slate-200 text-slate-600"
                      }`}
                    >
                      {msg.actionStatus === "confirmed" ? (
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                      ) : (
                        <XCircle className="w-3.5 h-3.5 text-slate-500" />
                      )}
                      <span>{msg.actionResult}</span>
                    </div>
                  )}
                </div>

                {/* Footer Controls: Timestamp + Copy + Retry */}
                <div className="flex items-center gap-2 mt-1 ml-1 text-[9.5px] text-slate-400">
                  <span>{msg.timestamp}</span>

                  {msg.content && !msg.isStreaming && (
                    <button
                      type="button"
                      onClick={() => handleCopy(msg.content, msg.id)}
                      title="Copy response"
                      className="inline-flex items-center gap-0.5 hover:text-slate-600 transition-colors"
                    >
                      {copiedId === msg.id ? (
                        <>
                          <Check className="w-2.5 h-2.5 text-emerald-600" />
                          <span className="text-emerald-600">Copied</span>
                        </>
                      ) : (
                        <>
                          <Copy className="w-2.5 h-2.5" />
                          <span>Copy</span>
                        </>
                      )}
                    </button>
                  )}

                  {msg.error && (
                    <button
                      type="button"
                      onClick={handleRetry}
                      className="inline-flex items-center gap-1 text-rose-600 hover:text-rose-700 font-semibold transition-colors"
                    >
                      <RotateCcw className="w-2.5 h-2.5" />
                      <span>Retry</span>
                    </button>
                  )}
                </div>
              </div>
            </div>
          );
        })}

        {/* Searching / Retrieval Loader */}
        {isLoading && (
          <div className="flex items-center gap-2 text-xs text-slate-500 pl-8 py-1">
            <Loader2 className="w-3.5 h-3.5 animate-spin text-indigo-600" />
            <span>Searching meeting transcript & memory...</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Suggested Follow-up Prompt Pills (shown when at least 1 turn has occurred) */}
      {messages.length > 0 && !isLoading && !isStreaming && (
        <div className="px-3 py-1.5 bg-slate-50/70 border-t border-slate-100 flex items-center gap-1.5 overflow-x-auto no-scrollbar">
          <span className="text-[10px] text-slate-400 font-semibold uppercase tracking-wider shrink-0">
            Follow-up:
          </span>
          <button
            type="button"
            onClick={() => handleSend("Who is responsible for it?")}
            className="px-2 py-0.5 rounded-full bg-white hover:bg-indigo-50 border border-slate-200/80 text-[10.5px] text-slate-600 hover:text-indigo-700 shrink-0 transition-colors"
          >
            Who is responsible?
          </button>
          <button
            type="button"
            onClick={() => handleSend("What was the deadline decided?")}
            className="px-2 py-0.5 rounded-full bg-white hover:bg-indigo-50 border border-slate-200/80 text-[10.5px] text-slate-600 hover:text-indigo-700 shrink-0 transition-colors"
          >
            What was the deadline?
          </button>
          <button
            type="button"
            onClick={() => handleSend("Was there any disagreement or dilemma?")}
            className="px-2 py-0.5 rounded-full bg-white hover:bg-indigo-50 border border-slate-200/80 text-[10.5px] text-slate-600 hover:text-indigo-700 shrink-0 transition-colors"
          >
            Any disagreement?
          </button>
        </div>
      )}

      {/* Fixed Chat Input Bar at Bottom */}
      <div className="shrink-0 p-2.5 border-t border-slate-100 bg-white rounded-b-2xl">
        {errorMsg && (
          <div className="mb-2 px-2.5 py-1 rounded-lg bg-rose-50 border border-rose-100 text-[11px] text-rose-600 flex items-center justify-between">
            <span className="truncate">{errorMsg}</span>
            <div className="flex items-center gap-1.5 ml-2 shrink-0">
              <button
                type="button"
                onClick={handleRetry}
                className="text-rose-600 underline font-semibold hover:text-rose-800"
              >
                Retry
              </button>
              <button
                type="button"
                onClick={() => setErrorMsg(null)}
                className="text-rose-400 hover:text-rose-600 text-xs"
              >
                ✕
              </button>
            </div>
          </div>
        )}

        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="relative flex items-center"
        >
          <input
            ref={inputRef}
            type="text"
            value={inputVal}
            onChange={(e) => setInputVal(e.target.value)}
            placeholder="Ask a question or follow-up about this meeting..."
            disabled={isLoading || isStreaming}
            className="w-full h-8 pl-3 pr-9 rounded-xl bg-slate-50 hover:bg-slate-100/70 focus:bg-white text-xs text-slate-800 placeholder:text-slate-400 border border-slate-200 focus:border-indigo-500 focus:outline-none transition-all disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={!inputVal.trim() || isLoading || isStreaming}
            aria-label="Send message"
            className="absolute right-1 w-6 h-6 rounded-lg bg-indigo-600 hover:bg-indigo-700 disabled:opacity-40 text-white flex items-center justify-center transition-all shadow-xs cursor-pointer disabled:cursor-not-allowed"
          >
            {isLoading || isStreaming ? (
              <Loader2 className="w-3 h-3 animate-spin" />
            ) : (
              <Send className="w-3 h-3" />
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
