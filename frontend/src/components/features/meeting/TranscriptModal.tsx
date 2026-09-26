"use client";

import React, { useState } from "react";
import { X, Search, Copy, Check } from "lucide-react";

interface TranscriptModalProps {
  isOpen: boolean;
  onClose: () => void;
  transcript: string;
  title?: string;
}

export function TranscriptModal({
  isOpen,
  onClose,
  transcript,
  title = "Meeting Transcript",
}: TranscriptModalProps) {
  const [search, setSearch] = useState("");
  const [copied, setCopied] = useState(false);

  if (!isOpen) return null;

  const handleCopy = () => {
    navigator.clipboard.writeText(transcript);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const lines = transcript
    .split("\n\n")
    .filter((block) => block.toLowerCase().includes(search.toLowerCase()));

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/50 backdrop-blur-xs animate-in fade-in duration-200">
      <div className="bg-white rounded-3xl border border-slate-200 shadow-2xl max-w-2xl w-full max-h-[85vh] flex flex-col overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold text-slate-900">{title}</h3>
            <p className="text-xs text-slate-400">Verbatim timestamped transcript</p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleCopy}
              className="p-1.5 rounded-lg border border-slate-200 hover:bg-slate-50 text-slate-600 text-xs flex items-center gap-1"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copied ? "Copied" : "Copy"}</span>
            </button>
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Filter bar */}
        <div className="p-3 bg-slate-50 border-b border-slate-100 flex items-center gap-2">
          <Search className="w-4 h-4 text-slate-400 ml-2" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search keywords or speakers in transcript..."
            className="w-full bg-transparent text-xs text-slate-800 placeholder:text-slate-400 focus:outline-none"
          />
        </div>

        {/* Transcript Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {lines.map((block, idx) => (
            <div key={idx} className="p-3 rounded-xl bg-slate-50 border border-slate-100 text-xs text-slate-700 font-mono leading-relaxed whitespace-pre-wrap">
              {block}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
