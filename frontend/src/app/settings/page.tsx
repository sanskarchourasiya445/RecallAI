"use client";

import React, { useState, useEffect } from "react";
import { AppShell } from "@/components/layouts/AppShell";
import { AIChat } from "@/components/features/chat/AIChat";
import { QuickActions } from "@/components/features/actions/QuickActions";
import { NewMeetingModal } from "@/components/features/meeting/NewMeetingModal";
import {
  Settings,
  Server,
  Cpu,
  Shield,
  Database,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
} from "lucide-react";
import { apiClient } from "@/lib/api/client";

interface HealthData {
  status: string;
  version: string;
  app: string;
  environment: string;
}

export default function SettingsPage() {
  const [isNewMeetingOpen, setIsNewMeetingOpen] = useState(false);
  const [health, setHealth] = useState<HealthData | null>(null);
  const [isLoadingHealth, setIsLoadingHealth] = useState(true);

  const checkHealth = async () => {
    setIsLoadingHealth(true);
    try {
      const data = await apiClient<HealthData>("/api/v1/health");
      setHealth(data);
    } catch {
      setHealth({
        status: "offline",
        version: "2.1.0",
        app: "RecallAI Platform",
        environment: "local",
      });
    } finally {
      setIsLoadingHealth(false);
    }
  };

  useEffect(() => {
    checkHealth();
  }, []);

  return (
    <AppShell
      currentNav="settings"
      onNewMeetingClick={() => setIsNewMeetingOpen(true)}
      rightPanel={
        <>
          <AIChat sessionId="demo_backend_migration" />
          <QuickActions sessionId="demo_backend_migration" pendingCount={3} />
        </>
      }
    >
      <div className="space-y-4">
        {/* Header */}
        <div className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-card flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-slate-100 flex items-center justify-center text-slate-700 shadow-2xs">
              <Settings className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-slate-900 tracking-tight">
                System & Integration Settings
              </h1>
              <p className="text-xs text-slate-400 font-normal">
                RecallAI backend connection, AI model routing, and pipeline configuration
              </p>
            </div>
          </div>

          <button
            onClick={checkHealth}
            className="h-9 px-3 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 flex items-center gap-1.5 text-xs font-semibold text-slate-600 shadow-2xs transition-all active:scale-95"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Check Backend</span>
          </button>
        </div>

        {/* Configuration Sections */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Backend Connectivity Status */}
          <div className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-card space-y-3">
            <div className="flex items-center gap-2 text-sm font-bold text-slate-900">
              <Server className="w-4 h-4 text-indigo-600" />
              <span>FastAPI Backend Status</span>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200/70 space-y-2 text-xs">
              <div className="flex items-center justify-between">
                <span className="text-slate-500">API Endpoint</span>
                <span className="font-mono font-semibold text-slate-800">{process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-500">Service Status</span>
                {isLoadingHealth ? (
                  <span className="text-slate-400">Pinging...</span>
                ) : health?.status === "ok" || health?.status === "healthy" ? (
                  <span className="inline-flex items-center gap-1 text-emerald-600 font-bold">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    Online (v{health?.version || "2.1.0"})
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 text-amber-600 font-bold">
                    <AlertCircle className="w-3.5 h-3.5" />
                    Offline (Fallback Enabled)
                  </span>
                )}
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-500">Environment</span>
                <span className="font-semibold text-slate-700 capitalize">
                  {health?.environment || "Development"}
                </span>
              </div>
            </div>
          </div>

          {/* AI Models & Intelligence Architecture */}
          <div className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-card space-y-3">
            <div className="flex items-center gap-2 text-sm font-bold text-slate-900">
              <Cpu className="w-4 h-4 text-purple-600" />
              <span>AI Models & Intelligence Engines</span>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200/70 space-y-2 text-xs">
              <div className="flex items-center justify-between">
                <span className="text-slate-500">Transcription (STT)</span>
                <span className="font-semibold text-slate-800">Whisper / Sarvam AI</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-500">Reasoning & Extraction</span>
                <span className="font-semibold text-slate-800">Gemini 2.5 Flash / Groq</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-500">Vector Knowledge Base</span>
                <span className="font-semibold text-slate-800">ChromaDB (HNSW Cosine)</span>
              </div>
            </div>
          </div>

          {/* Human-in-the-Loop Confirmation Policy */}
          <div className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-card space-y-3">
            <div className="flex items-center gap-2 text-sm font-bold text-slate-900">
              <Shield className="w-4 h-4 text-emerald-600" />
              <span>Safety & Confirmation Policies</span>
            </div>

            <p className="text-xs text-slate-600 leading-relaxed">
              RecallAI enforces strict safety gates for consequential actions. High-risk operations such as sending emails or scheduling external meetings cannot execute without explicit confirmation.
            </p>
          </div>

          {/* Session Storage */}
          <div className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-card space-y-3">
            <div className="flex items-center gap-2 text-sm font-bold text-slate-900">
              <Database className="w-4 h-4 text-blue-600" />
              <span>Session Storage</span>
            </div>

            <p className="text-xs text-slate-600 leading-relaxed">
              Sessions are managed through thread-safe in-memory stores with preloaded demo fixtures. Vector embeddings persist across requests within the local ChromaDB index.
            </p>
          </div>
        </div>
      </div>

      <NewMeetingModal
        isOpen={isNewMeetingOpen}
        onClose={() => setIsNewMeetingOpen(false)}
      />
    </AppShell>
  );
}
