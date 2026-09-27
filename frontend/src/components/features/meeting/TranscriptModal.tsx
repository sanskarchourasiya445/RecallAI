"use client";

import React, { useState, useMemo, useEffect, useRef } from "react";
import {
  X,
  Search,
  Copy,
  Check,
  Download,
  Filter,
  Clock,
  Sparkles,
} from "lucide-react";

interface TranscriptEntry {
  id: string;
  timeRange: string;
  speaker: string;
  text: string;
  evidenceId?: string;
}

interface TranscriptModalProps {
  isOpen: boolean;
  onClose: () => void;
  transcript: string;
  title?: string;
  targetTimestamp?: string | null;
  targetEvidenceId?: string | null;
}

const SPEAKER_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  alex: { bg: "bg-blue-50", text: "text-blue-700", border: "border-blue-200" },
  sarah: { bg: "bg-purple-50", text: "text-purple-700", border: "border-purple-200" },
  rahul: { bg: "bg-emerald-50", text: "text-emerald-700", border: "border-emerald-200" },
  david: { bg: "bg-amber-50", text: "text-amber-700", border: "border-amber-200" },
  priya: { bg: "bg-pink-50", text: "text-pink-700", border: "border-pink-200" },
  michael: { bg: "bg-cyan-50", text: "text-cyan-700", border: "border-cyan-200" },
};

function getSpeakerStyle(name: string) {
  const key = name.toLowerCase().trim();
  return (
    SPEAKER_COLORS[key] || {
      bg: "bg-indigo-50",
      text: "text-indigo-700",
      border: "border-indigo-200",
    }
  );
}

export function TranscriptModal({
  isOpen,
  onClose,
  transcript,
  title = "Meeting Transcript",
  targetTimestamp,
  targetEvidenceId,
}: TranscriptModalProps) {
  const [search, setSearch] = useState("");
  const [selectedSpeaker, setSelectedSpeaker] = useState<string>("all");
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [copiedAll, setCopiedAll] = useState(false);
  const entryRefs = useRef<Record<string, HTMLDivElement | null>>({});

  // Parse raw transcript text into structured transcript entries
  const parsedEntries = useMemo<TranscriptEntry[]>(() => {
    if (!transcript) return [];

    const blocks = transcript.split(/\n\s*\n/).filter((b) => b.trim().length > 0);
    const result: TranscriptEntry[] = [];

    blocks.forEach((block, idx) => {
      const lines = block.trim().split("\n");
      let timeRange = "";
      let speaker = "Speaker";
      let text = block;

      // Format: line 1 = "00:00:00 - 00:00:25", line 2 = "Alex: Good morning..."
      if (lines.length >= 2 && lines[0].includes(":") && (lines[0].includes("-") || lines[0].includes("-->"))) {
        timeRange = lines[0].trim();
        const secondLine = lines.slice(1).join("\n");
        const match = secondLine.match(/^([^:]+):\s*([\s\S]*)/);
        if (match) {
          speaker = match[1].trim();
          text = match[2].trim();
        } else {
          text = secondLine;
        }
      } else {
        // Line format: "Alex: Good morning..."
        const match = block.match(/^([^:]+):\s*([\s\S]*)/);
        if (match) {
          speaker = match[1].trim();
          text = match[2].trim();
        }
      }

      result.push({
        id: `tr-${idx}`,
        timeRange: timeRange || `00:0${idx}:00 - 00:0${idx + 1}:00`,
        speaker,
        text,
        evidenceId: `E${idx + 1}`,
      });
    });

    return result;
  }, [transcript]);

  // Extract unique speakers list
  const uniqueSpeakers = useMemo(() => {
    const set = new Set<string>();
    parsedEntries.forEach((e) => {
      if (e.speaker && e.speaker !== "Speaker") set.add(e.speaker);
    });
    return Array.from(set);
  }, [parsedEntries]);

  // Filter entries by search and selected speaker
  const filteredEntries = useMemo(() => {
    return parsedEntries.filter((item) => {
      const matchSearch =
        !search.trim() ||
        item.text.toLowerCase().includes(search.toLowerCase()) ||
        item.speaker.toLowerCase().includes(search.toLowerCase()) ||
        item.timeRange.toLowerCase().includes(search.toLowerCase());

      const matchSpeaker =
        selectedSpeaker === "all" ||
        item.speaker.toLowerCase() === selectedSpeaker.toLowerCase();

      return matchSearch && matchSpeaker;
    });
  }, [parsedEntries, search, selectedSpeaker]);

  // Scroll to target timestamp or evidence if requested
  useEffect(() => {
    if (isOpen && (targetTimestamp || targetEvidenceId)) {
      const matched = parsedEntries.find(
        (e) =>
          (targetTimestamp && (e.timeRange.includes(targetTimestamp) || targetTimestamp.includes(e.timeRange))) ||
          (targetEvidenceId && e.evidenceId === targetEvidenceId)
      );

      if (matched && entryRefs.current[matched.id]) {
        setTimeout(() => {
          entryRefs.current[matched.id]?.scrollIntoView({
            behavior: "smooth",
            block: "center",
          });
        }, 150);
      }
    }
  }, [isOpen, targetTimestamp, targetEvidenceId, parsedEntries]);

  if (!isOpen) return null;

  const handleCopyAll = () => {
    navigator.clipboard.writeText(transcript);
    setCopiedAll(true);
    setTimeout(() => setCopiedAll(false), 2000);
  };

  const handleCopyLine = (entry: TranscriptEntry) => {
    navigator.clipboard.writeText(`[${entry.timeRange}] ${entry.speaker}: ${entry.text}`);
    setCopiedId(entry.id);
    setTimeout(() => setCopiedId(null), 1500);
  };

  const handleDownloadTxt = () => {
    const blob = new Blob([transcript], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `transcript-${Date.now()}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Helper to render text with highlighted search keyword
  const renderHighlightedText = (text: string, query: string) => {
    if (!query.trim()) return text;
    const parts = text.split(new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")})`, "gi"));
    return (
      <>
        {parts.map((part, i) =>
          part.toLowerCase() === query.toLowerCase() ? (
            <mark key={i} className="bg-amber-200 text-amber-950 font-semibold px-0.5 rounded">
              {part}
            </mark>
          ) : (
            part
          )
        )}
      </>
    );
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-slate-950/60 backdrop-blur-xs animate-in fade-in duration-200">
      <div className="bg-white rounded-3xl border border-slate-200 shadow-2xl max-w-3xl w-full max-h-[88vh] flex flex-col overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600">
              <Sparkles className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-900 leading-tight">
                {title}
              </h3>
              <p className="text-xs text-slate-400 font-normal">
                Verbatim timestamped dialogue with speaker separation & search
              </p>
            </div>
          </div>

          <div className="flex items-center gap-1.5">
            <button
              onClick={handleCopyAll}
              title="Copy entire transcript"
              className="h-8 px-2.5 rounded-lg border border-slate-200 hover:bg-slate-50 text-slate-700 text-xs font-semibold flex items-center gap-1.5 transition-all"
            >
              {copiedAll ? (
                <>
                  <Check className="w-3.5 h-3.5 text-emerald-600" />
                  <span className="text-emerald-700">Copied</span>
                </>
              ) : (
                <>
                  <Copy className="w-3.5 h-3.5 text-slate-400" />
                  <span>Copy</span>
                </>
              )}
            </button>

            <button
              onClick={handleDownloadTxt}
              title="Download transcript as TXT"
              className="h-8 px-2.5 rounded-lg border border-slate-200 hover:bg-slate-50 text-slate-700 text-xs font-semibold flex items-center gap-1.5 transition-all"
            >
              <Download className="w-3.5 h-3.5 text-slate-400" />
              <span>Download</span>
            </button>

            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors ml-1"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Filter and Search Toolbar */}
        <div className="p-3 bg-slate-50/80 border-b border-slate-100 flex flex-wrap items-center justify-between gap-3 shrink-0">
          {/* Search box */}
          <div className="relative flex-1 min-w-[200px]">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search transcript by keyword, phrase, or timestamp..."
              className="w-full h-8 pl-8 pr-3 rounded-xl border border-slate-200 bg-white text-xs text-slate-800 placeholder:text-slate-400 focus:outline-none focus:border-indigo-500"
            />
          </div>

          {/* Speaker filter selector */}
          <div className="flex items-center gap-1.5 shrink-0">
            <Filter className="w-3 h-3 text-slate-400" />
            <select
              value={selectedSpeaker}
              onChange={(e) => setSelectedSpeaker(e.target.value)}
              className="h-8 px-2.5 rounded-xl border border-slate-200 bg-white text-xs text-slate-700 font-semibold focus:outline-none focus:border-indigo-500"
            >
              <option value="all">All Speakers ({parsedEntries.length})</option>
              {uniqueSpeakers.map((spk) => (
                <option key={spk} value={spk}>
                  {spk}
                </option>
              ))}
            </select>
          </div>

          {search && (
            <span className="text-[11px] text-slate-500 font-medium">
              {filteredEntries.length} match{filteredEntries.length === 1 ? "" : "es"}
            </span>
          )}
        </div>

        {/* Transcript Dialogue List */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-3.5">
          {filteredEntries.length === 0 ? (
            <div className="py-12 text-center text-slate-400 space-y-2">
              <Search className="w-8 h-8 mx-auto text-slate-300 stroke-1" />
              <p className="text-xs font-semibold text-slate-600">No dialogue matched your filter</p>
              <p className="text-[11px] text-slate-400">
                Try searching with different keywords or switch speaker filter back to &quot;All Speakers&quot;.
              </p>
            </div>
          ) : (
            filteredEntries.map((item) => {
              const spkStyle = getSpeakerStyle(item.speaker);
              const isTarget =
                (targetTimestamp && (item.timeRange.includes(targetTimestamp) || targetTimestamp.includes(item.timeRange))) ||
                (targetEvidenceId && item.evidenceId === targetEvidenceId);

              return (
                <div
                  key={item.id}
                  ref={(el) => {
                    entryRefs.current[item.id] = el;
                  }}
                  className={`p-3.5 rounded-2xl border transition-all ${
                    isTarget
                      ? "bg-indigo-50/60 border-indigo-300 shadow-md ring-2 ring-indigo-200"
                      : "bg-white hover:bg-slate-50/60 border-slate-200/80 shadow-2xs"
                  }`}
                >
                  {/* Top line: Speaker Pill + Timestamp + Actions */}
                  <div className="flex items-center justify-between gap-2 mb-2">
                    <div className="flex items-center gap-2 min-w-0">
                      {/* Speaker Badge */}
                      <span
                        className={`px-2.5 py-0.5 rounded-lg border text-[11px] font-bold shrink-0 ${spkStyle.bg} ${spkStyle.text} ${spkStyle.border}`}
                      >
                        {item.speaker}
                      </span>

                      {/* Timestamp button */}
                      <span
                        onClick={() => handleCopyLine(item)}
                        title="Click to copy line"
                        className="inline-flex items-center gap-1 text-[11px] font-mono text-slate-400 hover:text-indigo-600 cursor-pointer"
                      >
                        <Clock className="w-3 h-3" />
                        <span>{item.timeRange}</span>
                      </span>

                      {/* Evidence citation pill */}
                      {item.evidenceId && (
                        <span className="px-1.5 py-0.2 rounded bg-slate-100 text-slate-500 text-[10px] font-mono font-semibold">
                          [{item.evidenceId}]
                        </span>
                      )}
                    </div>

                    <button
                      onClick={() => handleCopyLine(item)}
                      title="Copy dialogue snippet"
                      className="text-[11px] text-slate-400 hover:text-indigo-600 flex items-center gap-1 font-medium transition-colors"
                    >
                      {copiedId === item.id ? (
                        <span className="text-emerald-600 flex items-center gap-0.5">
                          <Check className="w-3 h-3" /> Copied
                        </span>
                      ) : (
                        <span className="flex items-center gap-0.5">
                          <Copy className="w-3 h-3" /> Copy
                        </span>
                      )}
                    </button>
                  </div>

                  {/* Dialogue Content */}
                  <p className="text-[13px] text-slate-700 leading-relaxed font-normal whitespace-pre-line pl-1">
                    {renderHighlightedText(item.text, search)}
                  </p>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}
