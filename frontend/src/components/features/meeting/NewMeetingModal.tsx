"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import {
  X,
  UploadCloud,
  Sparkles,
  Loader2,
  CheckCircle2,
  AlertCircle,
  FileAudio,
} from "lucide-react";
import { ingestYouTube, ingestUpload, processMeeting, loadDemoMeeting } from "@/lib/api/meetings";
import { MeetingDetailResponse } from "@/types/meeting";

function YoutubeIcon(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" {...props}>
      <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z" />
    </svg>
  );
}

type PipelineStep = "idle" | "staging" | "transcribing" | "indexing" | "finalizing" | "completed";

interface NewMeetingModalProps {
  isOpen: boolean;
  onClose: () => void;
  onMeetingLoaded?: (meeting: MeetingDetailResponse) => void;
}

export function NewMeetingModal({
  isOpen,
  onClose,
  onMeetingLoaded,
}: NewMeetingModalProps) {
  const router = useRouter();
  const [tab, setTab] = useState<"demo" | "youtube" | "upload">("demo");
  const [youtubeUrl, setYoutubeUrl] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [language, setLanguage] = useState("english");
  const [isLoading, setIsLoading] = useState(false);
  const [pipelineStep, setPipelineStep] = useState<PipelineStep>("idle");
  const [statusMsg, setStatusMsg] = useState("");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleLoadDemo = async () => {
    setIsLoading(true);
    setErrorMsg(null);
    setPipelineStep("transcribing");
    setStatusMsg("Loading offline demo meeting fixture...");
    try {
      const demo = await loadDemoMeeting();
      setPipelineStep("completed");
      setStatusMsg("Demo meeting loaded successfully!");
      if (onMeetingLoaded) {
        onMeetingLoaded(demo);
      }
      setTimeout(() => {
        onClose();
        router.push(`/meetings/${demo.session_id}`);
      }, 400);
    } catch {
      // Offline fallback
      const mockDemo: MeetingDetailResponse = {
        session_id: "demo_backend_migration",
        title: "Product Strategy Meeting",
        transcript: "Alex: Good morning team...",
        summary:
          "The team discussed the product roadmap for Q2, focusing on the new AI features, user experience improvements, and go-to-market strategy. Key topics included the timeline for the feature launch, resource allocation, and customer feedback from the beta program.",
        status: "completed",
        is_demo: true,
      };
      if (onMeetingLoaded) {
        onMeetingLoaded(mockDemo);
      }
      onClose();
      router.push(`/meetings/${mockDemo.session_id}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleYouTubeSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!youtubeUrl.trim() || isLoading) return;

    setIsLoading(true);
    setErrorMsg(null);
    setPipelineStep("staging");
    setStatusMsg("Staging YouTube media and extracting audio stream via yt-dlp...");

    try {
      // Step 1: Ingest URL
      const ingestRes = await ingestYouTube(youtubeUrl.trim());

      // Step 2: Run pipeline
      setPipelineStep("transcribing");
      setStatusMsg(`Processing session ${ingestRes.session_id}: transcribing speech & extracting intelligence...`);

      const processRes = await processMeeting(ingestRes.session_id, language);

      setPipelineStep("indexing");
      setStatusMsg(`Indexed ${processRes.action_items_count} actions, ${processRes.decisions_count} decisions into ChromaDB...`);

      setPipelineStep("completed");
      setStatusMsg("Pipeline execution complete! Redirecting to meeting workspace...");

      if (onMeetingLoaded) {
        onMeetingLoaded({
          session_id: ingestRes.session_id,
          title: ingestRes.source || "Ingested YouTube Meeting",
          transcript: "",
          summary: "",
          status: "completed",
        });
      }

      setTimeout(() => {
        onClose();
        router.push(`/meetings/${ingestRes.session_id}`);
      }, 600);
    } catch (err: unknown) {
      setErrorMsg(
        err instanceof Error
          ? err.message
          : "Failed to process YouTube URL. Please verify the URL and backend status."
      );
      setPipelineStep("idle");
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileUploadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile || isLoading) return;

    setIsLoading(true);
    setErrorMsg(null);
    setPipelineStep("staging");
    setStatusMsg(`Uploading ${selectedFile.name} (${(selectedFile.size / (1024 * 1024)).toFixed(1)} MB)...`);

    try {
      // Step 1: Upload file
      const ingestRes = await ingestUpload(selectedFile);

      // Step 2: Run pipeline
      setPipelineStep("transcribing");
      setStatusMsg("Transcribing audio segments & generating multi-modal intelligence...");

      const processRes = await processMeeting(ingestRes.session_id, language);

      setPipelineStep("indexing");
      setStatusMsg(`Indexed ${processRes.action_items_count} actions, ${processRes.decisions_count} decisions into ChromaDB...`);

      setPipelineStep("completed");
      setStatusMsg("Workspace ready! Opening meeting...");

      if (onMeetingLoaded) {
        onMeetingLoaded({
          session_id: ingestRes.session_id,
          title: selectedFile.name,
          transcript: "",
          summary: "",
          status: "completed",
        });
      }

      setTimeout(() => {
        onClose();
        router.push(`/meetings/${ingestRes.session_id}`);
      }, 600);
    } catch (err: unknown) {
      setErrorMsg(
        err instanceof Error
          ? err.message
          : "Failed to upload or analyze media file. Please check backend connection."
      );
      setPipelineStep("idle");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/50 backdrop-blur-xs animate-in fade-in duration-200">
      <div className="bg-white rounded-3xl border border-slate-200 shadow-2xl max-w-lg w-full overflow-hidden">
        {/* Modal Header */}
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-indigo-50 flex items-center justify-center">
              <Sparkles className="w-4 h-4 text-indigo-600" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-900 leading-tight">
                Add New Meeting
              </h3>
              <p className="text-xs text-slate-400 font-normal">
                Ingest recordings or load pre-processed offline workspace
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            disabled={isLoading}
            className="p-1 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 disabled:opacity-40"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Tab Selection */}
        <div className="grid grid-cols-3 p-2 bg-slate-50 border-b border-slate-100 text-xs font-semibold text-slate-600">
          <button
            type="button"
            disabled={isLoading}
            onClick={() => setTab("demo")}
            className={`py-2 rounded-xl transition-all ${
              tab === "demo"
                ? "bg-white text-indigo-600 shadow-xs"
                : "hover:text-slate-900 disabled:opacity-50"
            }`}
          >
            🎯 Instant Demo
          </button>
          <button
            type="button"
            disabled={isLoading}
            onClick={() => setTab("youtube")}
            className={`py-2 rounded-xl transition-all ${
              tab === "youtube"
                ? "bg-white text-indigo-600 shadow-xs"
                : "hover:text-slate-900 disabled:opacity-50"
            }`}
          >
            📺 YouTube URL
          </button>
          <button
            type="button"
            disabled={isLoading}
            onClick={() => setTab("upload")}
            className={`py-2 rounded-xl transition-all ${
              tab === "upload"
                ? "bg-white text-indigo-600 shadow-xs"
                : "hover:text-slate-900 disabled:opacity-50"
            }`}
          >
            📁 File Upload
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6">
          {errorMsg && (
            <div className="mb-4 p-3 rounded-xl bg-rose-50 border border-rose-200 text-xs text-rose-700 flex items-start gap-2">
              <AlertCircle className="w-4 h-4 shrink-0 text-rose-600 mt-0.5" />
              <div className="flex-1">
                <p className="font-semibold">Error occurred</p>
                <p className="text-[11px] text-rose-600 mt-0.5">{errorMsg}</p>
              </div>
            </div>
          )}

          {/* Honest Processing Status Banner */}
          {isLoading && (
            <div className="mb-4 p-3.5 rounded-2xl bg-indigo-50/70 border border-indigo-100 space-y-2">
              <div className="flex items-center gap-2 text-xs font-bold text-indigo-950">
                <Loader2 className="w-4 h-4 animate-spin text-indigo-600 shrink-0" />
                <span>
                  {pipelineStep === "staging" && "Staging Source Audio..."}
                  {pipelineStep === "transcribing" && "Transcribing & Extracting Intelligence..."}
                  {pipelineStep === "indexing" && "Indexing Knowledge Embeddings..."}
                  {pipelineStep === "completed" && "Pipeline Finalized!"}
                </span>
              </div>
              <p className="text-[11px] text-slate-600 leading-snug pl-6">
                {statusMsg}
              </p>
            </div>
          )}

          {tab === "demo" && (
            <div className="space-y-4">
              <div className="p-4 rounded-2xl bg-indigo-50/60 border border-indigo-100 space-y-2">
                <h4 className="text-xs font-bold text-indigo-950 flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4 text-indigo-600" />
                  Pre-Parsed & Indexed Offline Demonstration
                </h4>
                <p className="text-xs text-slate-600 leading-relaxed font-normal">
                  Loads the full <strong>Backend Platform Migration & Cloud Infrastructure Sync</strong> fixture with 3 action items, 4 confirmed decisions, 2 open dilemmas, pre-computed vector embeddings, and RAG chat memory. Zero external API keys required!
                </p>
              </div>

              <button
                type="button"
                onClick={handleLoadDemo}
                disabled={isLoading}
                className="w-full py-2.5 rounded-xl bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white text-xs font-bold shadow-md shadow-indigo-500/20 flex items-center justify-center gap-2 active:scale-98 transition-all disabled:opacity-50"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Loading Demo Workspace...</span>
                  </>
                ) : (
                  <span>Load Strategy Meeting Demo</span>
                )}
              </button>
            </div>
          )}

          {tab === "youtube" && (
            <form onSubmit={handleYouTubeSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">
                  YouTube Video or Audio URL
                </label>
                <div className="relative">
                  <YoutubeIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-red-500" />
                  <input
                    type="url"
                    required
                    placeholder="https://www.youtube.com/watch?v=..."
                    value={youtubeUrl}
                    onChange={(e) => setYoutubeUrl(e.target.value)}
                    disabled={isLoading}
                    className="w-full h-10 pl-9 pr-3 rounded-xl border border-slate-200 text-xs text-slate-800 placeholder:text-slate-400 focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">
                  Transcription Language
                </label>
                <select
                  value={language}
                  onChange={(e) => setLanguage(e.target.value)}
                  disabled={isLoading}
                  className="w-full h-9 px-3 rounded-xl border border-slate-200 text-xs text-slate-700 bg-white focus:outline-none focus:border-indigo-500"
                >
                  <option value="english">English (Whisper / Gemini)</option>
                  <option value="hinglish">Hinglish / Hindi (Sarvam STT)</option>
                </select>
              </div>

              <button
                type="submit"
                disabled={isLoading || !youtubeUrl.trim()}
                className="w-full py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold shadow-md transition-all flex items-center justify-center gap-2 disabled:opacity-50"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Processing Media...</span>
                  </>
                ) : (
                  <span>Ingest & Analyze YouTube Video</span>
                )}
              </button>
            </form>
          )}

          {tab === "upload" && (
            <form onSubmit={handleFileUploadSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">
                  Upload Audio or Video File
                </label>
                <div className="border-2 border-dashed border-slate-200 rounded-2xl p-6 text-center hover:border-indigo-400 bg-slate-50/50 cursor-pointer">
                  <input
                    type="file"
                    accept="audio/*,video/*"
                    required
                    onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                    disabled={isLoading}
                    className="hidden"
                    id="file-upload"
                  />
                  <label htmlFor="file-upload" className="cursor-pointer block">
                    {selectedFile ? (
                      <div className="flex flex-col items-center">
                        <FileAudio className="w-8 h-8 text-indigo-600 mb-1" />
                        <p className="text-xs font-bold text-slate-800">
                          {selectedFile.name}
                        </p>
                        <p className="text-[11px] text-slate-500 mt-0.5">
                          {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
                        </p>
                      </div>
                    ) : (
                      <>
                        <UploadCloud className="w-8 h-8 text-indigo-500 mx-auto mb-2" />
                        <p className="text-xs font-semibold text-slate-700">
                          Click to select audio or video file
                        </p>
                        <p className="text-[11px] text-slate-400 mt-1">
                          MP3, WAV, M4A, MP4, WEBM up to 100 MB
                        </p>
                      </>
                    )}
                  </label>
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">
                  Transcription Language
                </label>
                <select
                  value={language}
                  onChange={(e) => setLanguage(e.target.value)}
                  disabled={isLoading}
                  className="w-full h-9 px-3 rounded-xl border border-slate-200 text-xs text-slate-700 bg-white focus:outline-none focus:border-indigo-500"
                >
                  <option value="english">English (Whisper / Gemini)</option>
                  <option value="hinglish">Hinglish / Hindi (Sarvam STT)</option>
                </select>
              </div>

              <button
                type="submit"
                disabled={isLoading || !selectedFile}
                className="w-full py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold shadow-md transition-all flex items-center justify-center gap-2 disabled:opacity-50"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Uploading & Analyzing...</span>
                  </>
                ) : (
                  <span>Upload & Run Intelligence Pipeline</span>
                )}
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
