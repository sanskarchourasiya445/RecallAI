"use client";

import React, { useState, useRef, useEffect } from "react";
import { Sparkles, Send, Bot, Loader2 } from "lucide-react";
import { UIMessage } from "@/types/chat";
import { sendChatMessage } from "@/lib/api/chat";

interface AIChatProps {
  sessionId?: string;
  initialMessages?: UIMessage[];
  onActionTriggered?: (actionId: string) => void;
}

const DEFAULT_MESSAGES: UIMessage[] = [
  {
    id: "msg-1",
    sender: "user",
    content: "What are the main action items from this meeting?",
    timestamp: "10:24 AM",
  },
  {
    id: "msg-2",
    sender: "ai",
    content: `Here are the main action items identified from this meeting:

1. Prepare and distribute complete PostgreSQL migration plan (Rahul) – Due Apr 30, 2025
2. Create content marketing plan (Priya) – Due May 5, 2025
3. Finalize engineering resources (David) – Due May 10, 2025
4. Share customer feedback summary (Sarah) – Due May 8, 2025`,
    timestamp: "10:25 AM",
  },
  {
    id: "msg-3",
    sender: "user",
    content: "Show me what the team decided about the AI feature?",
    timestamp: "10:26 AM",
  },
  {
    id: "msg-4",
    sender: "ai",
    content:
      "The team decided to prioritize the AI-powered search feature for Q2 release. This was confirmed during the meeting at 12:34, with Rahul leading the initiative.",
    timestamp: "10:26 AM",
    citations: [
      {
        evidence_id: "E1",
        time_range: "00:00:00 - 00:00:25",
        chunk_index: 0,
        source: "transcript",
      },
    ],
  },
];

export function AIChat({
  sessionId = "demo_backend_migration",
  initialMessages = DEFAULT_MESSAGES,
  onActionTriggered,
}: AIChatProps) {
  const [messages, setMessages] = useState<UIMessage[]>(initialMessages);
  const [inputVal, setInputVal] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  const handleSend = async () => {
    const text = inputVal.trim();
    if (!text || isLoading) return;

    setErrorMsg(null);
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

    try {
      const response = await sendChatMessage({
        session_id: sessionId,
        message: text,
        top_k: 4,
      });

      const aiTime = new Date().toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
      });

      const aiMessage: UIMessage = {
        id: `ai-${Date.now()}`,
        sender: "ai",
        content: response.answer,
        timestamp: aiTime,
        citations: response.citations,
        evidence: response.evidence,
        intent: response.intent,
        requiresConfirmation: response.requires_confirmation,
        pendingActionId: response.pending_action_id,
      };

      setMessages((prev) => [...prev, aiMessage]);

      if (response.requires_confirmation && response.pending_action_id && onActionTriggered) {
        onActionTriggered(response.pending_action_id);
      }
    } catch (err: unknown) {
      const aiTime = new Date().toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
      });

      const errText = err instanceof Error ? err.message : "Backend unavailable";
      setErrorMsg(errText);

      // Add informative message
      const fallbackMsg: UIMessage = {
        id: `ai-${Date.now()}`,
        sender: "ai",
        content: `I could not reach the live RAG backend (${errText}). If the meeting is still indexing or server is starting up, please try again shortly.`,
        timestamp: aiTime,
      };

      setMessages((prev) => [...prev, fallbackMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-2xl border border-slate-200/80 shadow-card flex flex-col flex-[6] min-h-[320px] max-h-[65%] overflow-hidden">
      {/* Compact Header */}
      <div className="shrink-0 px-3.5 py-2.5 border-b border-slate-100 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-lg bg-indigo-50 flex items-center justify-center shrink-0">
            <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
          </div>
          <div>
            <h3 className="text-[14px] sm:text-[15px] font-bold text-slate-900 leading-tight">
              AI Chat
            </h3>
            <p className="text-[11px] text-slate-400 font-normal">
              Ask questions about this meeting
            </p>
          </div>
        </div>
      </div>

      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto p-3 space-y-3">
        {messages.map((msg) => {
          const isUser = msg.sender === "user";

          if (isUser) {
            return (
              <div key={msg.id} className="flex flex-col items-end">
                <div className="max-w-[85%] rounded-2xl rounded-tr-xs bg-[#EEF2FF] border border-indigo-100 px-3 py-2 text-xs text-slate-800 shadow-2xs leading-relaxed">
                  {msg.content}
                </div>
                <span className="text-[10px] text-slate-400 mt-1 mr-1">
                  {msg.timestamp}
                </span>
              </div>
            );
          }

          return (
            <div key={msg.id} className="flex items-start gap-2">
              {/* AI Avatar */}
              <div className="w-5 h-5 rounded-full bg-gradient-to-tr from-indigo-600 to-purple-600 flex items-center justify-center shrink-0 mt-0.5 shadow-2xs">
                <Bot className="w-3 h-3 text-white" />
              </div>

              <div className="flex-1 min-w-0">
                {/* AI Response Card */}
                <div className="rounded-2xl rounded-tl-xs bg-slate-50 border border-slate-200/70 p-2.5 text-xs text-slate-700 leading-relaxed shadow-2xs whitespace-pre-line">
                  {msg.content}

                  {/* Grounded Citations if present */}
                  {msg.citations && msg.citations.length > 0 && (
                    <div className="mt-2 pt-1.5 border-t border-slate-200/60 flex flex-wrap gap-1">
                      <span className="text-[10px] text-slate-400 font-medium">
                        Citations:
                      </span>
                      {msg.citations.map((c, i) => (
                        <span
                          key={i}
                          className="px-1.5 py-0.2 rounded bg-indigo-50 border border-indigo-200 text-indigo-700 text-[10px] font-semibold"
                        >
                          [{c.evidence_id}] {c.time_range}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
                <span className="text-[10px] text-slate-400 mt-0.5 ml-1 inline-block">
                  {msg.timestamp}
                </span>
              </div>
            </div>
          );
        })}

        {/* Loading Spinner */}
        {isLoading && (
          <div className="flex items-center gap-1.5 text-xs text-slate-400 pl-7">
            <Loader2 className="w-3.5 h-3.5 animate-spin text-indigo-500" />
            <span>Searching meeting memory & transcript...</span>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Fixed Chat Input Bar at Bottom */}
      <div className="shrink-0 p-2.5 border-t border-slate-100 bg-white rounded-b-2xl">
        {errorMsg && (
          <div className="mb-2 px-2.5 py-1 rounded-lg bg-rose-50 border border-rose-100 text-[11px] text-rose-600 flex items-center justify-between">
            <span className="truncate">{errorMsg}</span>
            <button
              onClick={() => setErrorMsg(null)}
              className="text-rose-500 hover:text-rose-700 ml-1 text-xs"
            >
              dismiss
            </button>
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
            type="text"
            value={inputVal}
            onChange={(e) => setInputVal(e.target.value)}
            placeholder="Ask anything about this meeting..."
            disabled={isLoading}
            className="w-full h-8 pl-3 pr-9 rounded-xl bg-slate-50 hover:bg-slate-100/70 focus:bg-white text-xs text-slate-800 placeholder:text-slate-400 border border-slate-200 focus:border-indigo-500 focus:outline-none transition-all"
          />
          <button
            type="submit"
            disabled={!inputVal.trim() || isLoading}
            aria-label="Send message"
            className="absolute right-1 w-6 h-6 rounded-lg bg-indigo-600 hover:bg-indigo-700 disabled:opacity-40 text-white flex items-center justify-center transition-all shadow-xs"
          >
            <Send className="w-3 h-3" />
          </button>
        </form>
      </div>
    </div>
  );
}
