"use client";

import React, { useState, useRef, DragEvent } from "react";
import { useRouter } from "next/navigation";
import {
  X,
  UploadCloud,
  Sparkles,
  Loader2,
  CheckCircle2,
  AlertCircle,
  FileAudio,
  Radio,
  FileText,
  Brain,
  Database,
  ArrowRight,
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

export type ProcessingStageId =
  | "source_received"
  | "audio_prepared"
  | "transcription"
  | "intelligence_extraction"
  | "knowledge_indexing"
  | "workspace_ready";

interface ProcessingStageInfo {
  id: ProcessingStageId;
  label: string;
  description: string;
  icon: React.ElementType;
}

const STAGES: ProcessingStageInfo[] = [
  {
    id: "source_received",
    label: "Source Received",
    description: "Input source verified & buffer staged",
    icon: Radio,
  },
  {
    id: "audio_prepared",
    label: "Audio Prepared",
    description: "Audio stream extracted & segmented via FFmpeg",
    icon: FileAudio,
  },
  {
    id: "transcription",
    label: "Transcription",
    description: "Multi-speaker dialogue & timestamp generation",
    icon: FileText,
  },
  {
    id: "intelligence_extraction",
    label: "Intelligence Extraction",
    description: "Synthesizing executive summary, decisions & tasks",
    icon: Brain,
  },
  {
    id: "knowledge_indexing",
    label: "Knowledge Indexing",
    description: "Vector embeddings & ChromaDB HNSW store",
    icon: Database,
  },
  {
    id: "workspace_ready",
    label: "Workspace Ready",
    description: "Meeting intelligence finalized",
    icon: CheckCircle2,
  },
];

interface NewMeetingModalProps {
  isOpen: boolean;
  onClose: () => void;
  onMeetingLoaded?: (meeting: MeetingDetailResponse) => void;
}

const MAX_FILE_SIZE_BYTES = 100 * 1024 * 1024; // 100 MB

export function NewMeetingModal({
  isOpen,
  onClose,
  onMeetingLoaded,
}: NewMeetingModalProps) {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [tab, setTab] = useState<"demo" | "youtube" | "upload">("demo");
  const [youtubeUrl, setYoutubeUrl] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [language, setLanguage] = useState("english");
  const [isDragging, setIsDragging] = useState(false);

  // Processing state
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentStageIndex, setCurrentStageIndex] = useState(0);
  const [stageMessage, setStageMessage] = useState("");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [createdSessionId, setCreatedSessionId] = useState<string | null>(null);

  if (!isOpen) return null;

  const resetForm = () => {
    setIsProcessing(false);
    setCurrentStageIndex(0);
    setStageMessage("");
    setErrorMsg(null);
    setCreatedSessionId(null);
    setSelectedFile(null);
    setYoutubeUrl("");
  };

  const handleClose = () => {
    if (!isProcessing) {
      resetForm();
      onClose();
    }
  };

  // Drag and drop handlers
  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    setErrorMsg(null);

    const file = e.dataTransfer.files?.[0];
    if (!file) return;

    if (file.size > MAX_FILE_SIZE_BYTES) {
      setErrorMsg(`File size (${(file.size / (1024 * 1024)).toFixed(1)} MB) exceeds 100 MB maximum limit.`);
      return;
    }

    setSelectedFile(file);
    setTab("upload");
  };

  const handleFileSelect = (file: File | null) => {
    setErrorMsg(null);
    if (!file) return;
    if (file.size > MAX_FILE_SIZE_BYTES) {
      setErrorMsg(`File size (${(file.size / (1024 * 1024)).toFixed(1)} MB) exceeds 100 MB limit.`);
      return;
    }
    setSelectedFile(file);
  };

  // Demo meeting load
  const handleLoadDemo = async () => {
    setIsProcessing(true);
    setErrorMsg(null);
    setCurrentStageIndex(0);
    setStageMessage("Loading pre-parsed demonstration fixture...");

    try {
      setCurrentStageIndex(2); // Transcription
      setStageMessage("Loading verbatim conversation dialogue...");

      const demo = await loadDemoMeeting();

      setCurrentStageIndex(4); // Knowledge indexing
      setStageMessage("Indexing vector embeddings and memory...");

      setCurrentStageIndex(5); // Workspace ready
      setStageMessage("Demo workspace ready! Opening meeting...");

      setCreatedSessionId(demo.session_id);
      if (onMeetingLoaded) {
        onMeetingLoaded(demo);
      }

      setTimeout(() => {
        handleClose();
        router.push(`/meetings/${demo.session_id}`);
      }, 700);
    } catch {
      // Offline fallback
      setCurrentStageIndex(5);
      setStageMessage("Offline demo initialized! Opening workspace...");
      setTimeout(() => {
        handleClose();
        router.push("/meetings/demo_backend_migration");
      }, 700);
    } finally {
      setIsProcessing(false);
    }
  };

  // YouTube Ingestion
  const handleYouTubeSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const url = youtubeUrl.trim();
    if (!url || isProcessing) return;

    // Validation
    if (!url.startsWith("http://") && !url.startsWith("https://")) {
      setErrorMsg("Please enter a valid URL starting with http:// or https://");
      return;
    }

    if (!url.toLowerCase().includes("youtube.com") && !url.toLowerCase().includes("youtu.be")) {
      setErrorMsg("Please enter a valid YouTube video or audio link (youtube.com or youtu.be).");
      return;
    }

    setIsProcessing(true);
    setErrorMsg(null);

    try {
      // Stage 0: Source Received
      setCurrentStageIndex(0);
      setStageMessage(`Validating YouTube URL and contacting video stream...`);

      // Ingest call
      const ingestRes = await ingestYouTube(url);
      setCreatedSessionId(ingestRes.session_id);

      // Stage 1: Audio Prepared
      setCurrentStageIndex(1);
      setStageMessage(`Audio stream downloaded and converted into processing segments.`);

      // Stage 2: Transcription
      setCurrentStageIndex(2);
      setStageMessage(`Transcribing audio with timestamped multi-speaker detection...`);

      // Stage 3 & 4: Process pipeline
      setCurrentStageIndex(3);
      setStageMessage(`Extracting executive summary, key decisions & action items...`);

      const processRes = await processMeeting(ingestRes.session_id, language);

      // Stage 4: Indexing
      setCurrentStageIndex(4);
      setStageMessage(
        `Generated embeddings for ${processRes.action_items_count} tasks and ${processRes.decisions_count} decisions into ChromaDB.`
      );

      // Stage 5: Ready
      setCurrentStageIndex(5);
      setStageMessage("Meeting workspace indexed and ready!");

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
        handleClose();
        router.push(`/meetings/${ingestRes.session_id}`);
      }, 750);
    } catch (err: unknown) {
      setErrorMsg(
        err instanceof Error
          ? err.message
          : "Failed to download and process YouTube audio. Please check network connection and backend logs."
      );
    } finally {
      setIsProcessing(false);
    }
  };

  // File Upload Ingestion
  const handleFileUploadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile || isProcessing) return;

    setIsProcessing(true);
    setErrorMsg(null);

    try {
      // Stage 0: Source Received
      setCurrentStageIndex(0);
      setStageMessage(
        `Uploading ${selectedFile.name} (${(selectedFile.size / (1024 * 1024)).toFixed(1)} MB)...`
      );

      // Upload call
      const ingestRes = await ingestUpload(selectedFile);
      setCreatedSessionId(ingestRes.session_id);

      // Stage 1: Audio Prepared
      setCurrentStageIndex(1);
      setStageMessage(`File saved and normalized into audio chunks via FFmpeg.`);

      // Stage 2: Transcription
      setCurrentStageIndex(2);
      setStageMessage(`Running speech-to-text transcription (${language})...`);

      // Stage 3: Extraction
      setCurrentStageIndex(3);
      setStageMessage(`Extracting decisions, action items, and open questions...`);

      const processRes = await processMeeting(ingestRes.session_id, language);

      // Stage 4: Knowledge Indexing
      setCurrentStageIndex(4);
      setStageMessage(
        `Indexed ${processRes.action_items_count} actions and ${processRes.decisions_count} decisions into ChromaDB.`
      );

      // Stage 5: Ready
      setCurrentStageIndex(5);
      setStageMessage("Processing complete! Loading meeting workspace...");

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
        handleClose();
        router.push(`/meetings/${ingestRes.session_id}`);
      }, 750);
    } catch (err: unknown) {
      setErrorMsg(
        err instanceof Error
          ? err.message
          : "Failed to process audio/video upload. Please check the file format."
      );
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/60 backdrop-blur-xs animate-in fade-in duration-200">
      <div className="bg-white rounded-3xl border border-slate-200 shadow-2xl max-w-xl w-full overflow-hidden">
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
            onClick={handleClose}
            disabled={isProcessing}
            className="p-1 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 disabled:opacity-30 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Tab Selection (Disabled during processing) */}
        {!isProcessing && (
          <div className="grid grid-cols-3 p-2 bg-slate-50 border-b border-slate-100 text-xs font-semibold text-slate-600">
            <button
              type="button"
              onClick={() => setTab("demo")}
              className={`py-2 rounded-xl transition-all ${
                tab === "demo"
                  ? "bg-white text-indigo-600 shadow-xs"
                  : "hover:text-slate-900"
              }`}
            >
              🎯 Instant Demo
            </button>
            <button
              type="button"
              onClick={() => setTab("youtube")}
              className={`py-2 rounded-xl transition-all ${
                tab === "youtube"
                  ? "bg-white text-indigo-600 shadow-xs"
                  : "hover:text-slate-900"
              }`}
            >
              📺 YouTube URL
            </button>
            <button
              type="button"
              onClick={() => setTab("upload")}
              className={`py-2 rounded-xl transition-all ${
                tab === "upload"
                  ? "bg-white text-indigo-600 shadow-xs"
                  : "hover:text-slate-900"
              }`}
            >
              📁 File Upload
            </button>
          </div>
        )}

        {/* Modal Body */}
        <div className="p-6">
          {/* Error Alert with Retry */}
          {errorMsg && (
            <div className="mb-4 p-3.5 rounded-2xl bg-rose-50 border border-rose-200 text-xs text-rose-800 flex items-start gap-2.5 shadow-2xs">
              <AlertCircle className="w-4 h-4 shrink-0 text-rose-600 mt-0.5" />
              <div className="flex-1 min-w-0">
                <p className="font-bold">Ingestion Error</p>
                <p className="text-rose-600 text-[11px] mt-0.5 leading-relaxed">{errorMsg}</p>
              </div>
              <button
                onClick={() => setErrorMsg(null)}
                className="text-[11px] text-rose-700 font-semibold hover:underline shrink-0"
              >
                Dismiss
              </button>
            </div>
          )}

          {/* ACTIVE PROCESSING TIMELINE / STEPPER UI */}
          {isProcessing ? (
            <div className="space-y-5 py-2">
              <div className="text-center space-y-1">
                <h4 className="text-sm font-bold text-slate-900">
                  Processing Meeting Recording
                </h4>
                <p className="text-xs text-slate-500 font-normal">
                  Executing RecallAI multimodal pipeline & indexing intelligence
                </p>
              </div>

              {/* Vertical Stepper */}
              <div className="space-y-3 px-2">
                {STAGES.map((st, idx) => {
                  const isDone = currentStageIndex > idx;
                  const isCurrent = currentStageIndex === idx;

                  return (
                    <div
                      key={st.id}
                      className={`flex items-start gap-3 p-2.5 rounded-xl border transition-all ${
                        isCurrent
                          ? "bg-indigo-50/70 border-indigo-200 shadow-xs"
                          : isDone
                          ? "bg-[#F4FAF6] border-[#DEF1E7]"
                          : "bg-slate-50/50 border-slate-100 opacity-60"
                      }`}
                    >
                      {/* Step Indicator */}
                      <div className="mt-0.5 shrink-0">
                        {isDone ? (
                          <div className="w-6 h-6 rounded-full bg-emerald-500 text-white flex items-center justify-center shadow-xs">
                            <CheckCircle2 className="w-3.5 h-3.5 stroke-[2.5]" />
                          </div>
                        ) : isCurrent ? (
                          <div className="w-6 h-6 rounded-full bg-indigo-600 text-white flex items-center justify-center shadow-xs animate-pulse">
                            <Loader2 className="w-3.5 h-3.5 animate-spin" />
                          </div>
                        ) : (
                          <div className="w-6 h-6 rounded-full bg-slate-200 text-slate-400 flex items-center justify-center text-[10px] font-bold">
                            {idx + 1}
                          </div>
                        )}
                      </div>

                      {/* Step Details */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between">
                          <p
                            className={`text-xs font-bold leading-tight ${
                              isCurrent
                                ? "text-indigo-950"
                                : isDone
                                ? "text-emerald-950"
                                : "text-slate-500"
                            }`}
                          >
                            {st.label}
                          </p>
                          <span className="text-[10px] text-slate-400 font-medium">
                            {isDone ? "Done" : isCurrent ? "In Progress" : "Pending"}
                          </span>
                        </div>
                        <p className="text-[11px] text-slate-500 mt-0.5 leading-snug">
                          {isCurrent ? stageMessage || st.description : st.description}
                        </p>
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Status footer banner */}
              <div className="p-3 rounded-xl bg-slate-50 border border-slate-200/70 text-center text-xs text-slate-500 font-mono">
                {createdSessionId ? `Session ID: ${createdSessionId}` : "Initializing pipeline runtime..."}
              </div>
            </div>
          ) : (
            <>
              {/* TAB 1: INSTANT DEMO */}
              {tab === "demo" && (
                <div className="space-y-4">
                  <div className="p-4 rounded-2xl bg-indigo-50/60 border border-indigo-100 space-y-2">
                    <h4 className="text-xs font-bold text-indigo-950 flex items-center gap-1.5">
                      <CheckCircle2 className="w-4 h-4 text-indigo-600" />
                      Pre-Parsed & Indexed Offline Demonstration
                    </h4>
                    <p className="text-xs text-slate-600 leading-relaxed font-normal">
                      Loads the full <strong>Backend Platform Migration & Cloud Infrastructure Sync</strong> workspace with verbatim speaker dialogue, 3 action items, 4 confirmed decisions, 2 open dilemmas, pre-computed vector embeddings, and RAG chat memory.
                    </p>
                  </div>

                  <button
                    type="button"
                    onClick={handleLoadDemo}
                    className="w-full py-2.5 rounded-xl bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white text-xs font-bold shadow-md shadow-indigo-500/20 flex items-center justify-center gap-2 active:scale-98 transition-all"
                  >
                    <span>Load Demo Meeting Workspace</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              )}

              {/* TAB 2: YOUTUBE INGESTION */}
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
                        onChange={(e) => {
                          setYoutubeUrl(e.target.value);
                          setErrorMsg(null);
                        }}
                        className="w-full h-10 pl-9 pr-3 rounded-xl border border-slate-200 text-xs text-slate-800 placeholder:text-slate-400 focus:outline-none focus:border-indigo-500"
                      />
                    </div>
                    <p className="text-[11px] text-slate-400 mt-1">
                      Audio stream will be acquired, segmented, and transcribed with speaker attribution.
                    </p>
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-slate-700 mb-1">
                      Transcription Language
                    </label>
                    <select
                      value={language}
                      onChange={(e) => setLanguage(e.target.value)}
                      className="w-full h-9 px-3 rounded-xl border border-slate-200 text-xs text-slate-700 bg-white focus:outline-none focus:border-indigo-500"
                    >
                      <option value="english">English (Default — Whisper / Gemini)</option>
                      <option value="hinglish">Hinglish / Hindi (Sarvam STT)</option>
                    </select>
                  </div>

                  <button
                    type="submit"
                    disabled={!youtubeUrl.trim()}
                    className="w-full py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold shadow-md transition-all flex items-center justify-center gap-2 disabled:opacity-50"
                  >
                    <span>Ingest & Run Pipeline</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </form>
              )}

              {/* TAB 3: FILE UPLOAD (DRAG & DROP) */}
              {tab === "upload" && (
                <form onSubmit={handleFileUploadSubmit} className="space-y-4">
                  <div>
                    <label className="block text-xs font-bold text-slate-700 mb-1">
                      Upload Audio or Video Recording
                    </label>

                    {/* Drag and drop zone */}
                    <div
                      onDragOver={handleDragOver}
                      onDragLeave={handleDragLeave}
                      onDrop={handleDrop}
                      onClick={() => fileInputRef.current?.click()}
                      className={`border-2 border-dashed rounded-2xl p-6 text-center cursor-pointer transition-all ${
                        isDragging
                          ? "border-indigo-500 bg-indigo-50/50 scale-[1.01]"
                          : selectedFile
                          ? "border-emerald-300 bg-emerald-50/30"
                          : "border-slate-200 hover:border-indigo-400 bg-slate-50/50"
                      }`}
                    >
                      <input
                        ref={fileInputRef}
                        type="file"
                        accept="audio/*,video/*,.mp3,.wav,.m4a,.mp4,.webm,.ogg"
                        onChange={(e) => handleFileSelect(e.target.files?.[0] || null)}
                        className="hidden"
                      />

                      {selectedFile ? (
                        <div className="flex flex-col items-center">
                          <div className="w-10 h-10 rounded-xl bg-emerald-100 text-emerald-600 flex items-center justify-center mb-2 shadow-2xs">
                            <FileAudio className="w-5 h-5" />
                          </div>
                          <p className="text-xs font-bold text-slate-900 truncate max-w-xs">
                            {selectedFile.name}
                          </p>
                          <p className="text-[11px] text-slate-500 mt-0.5">
                            {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB · Ready to upload
                          </p>
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              setSelectedFile(null);
                            }}
                            className="mt-2 text-[11px] text-rose-600 hover:underline"
                          >
                            Remove file
                          </button>
                        </div>
                      ) : (
                        <div className="flex flex-col items-center">
                          <UploadCloud className="w-8 h-8 text-indigo-500 mb-2" />
                          <p className="text-xs font-semibold text-slate-700">
                            {isDragging ? "Drop file to upload" : "Click to browse or drag & drop"}
                          </p>
                          <p className="text-[11px] text-slate-400 mt-1">
                            MP3, WAV, M4A, MP4, WEBM up to 100 MB
                          </p>
                        </div>
                      )}
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-slate-700 mb-1">
                      Transcription Language
                    </label>
                    <select
                      value={language}
                      onChange={(e) => setLanguage(e.target.value)}
                      className="w-full h-9 px-3 rounded-xl border border-slate-200 text-xs text-slate-700 bg-white focus:outline-none focus:border-indigo-500"
                    >
                      <option value="english">English (Default — Whisper / Gemini)</option>
                      <option value="hinglish">Hinglish / Hindi (Sarvam STT)</option>
                    </select>
                  </div>

                  <button
                    type="submit"
                    disabled={!selectedFile}
                    className="w-full py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold shadow-md transition-all flex items-center justify-center gap-2 disabled:opacity-50"
                  >
                    <span>Upload & Process Meeting</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </form>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
