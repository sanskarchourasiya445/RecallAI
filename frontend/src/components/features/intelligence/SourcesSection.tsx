"use client";

import React from "react";
import {
  Link2,
  ArrowRight,
  ExternalLink,
  FileText,
  FileCode,
  FileSpreadsheet,
} from "lucide-react";
import { MeetingSource } from "@/types/meeting";

function YoutubeIcon(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" {...props}>
      <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z" />
    </svg>
  );
}

interface SourcesSectionProps {
  sources?: MeetingSource[];
  onViewAll?: () => void;
  onOpenSource?: (source: MeetingSource) => void;
}

export function SourcesSection({
  sources = [
    {
      id: "1",
      title: "YouTube Video",
      subtitle: "Product Strategy Meeting",
      meta: "42:15",
      type: "youtube",
    },
    {
      id: "2",
      title: "Transcript",
      subtitle: "Full Transcript",
      meta: "12 pages",
      type: "transcript",
    },
    {
      id: "3",
      title: "Document",
      subtitle: "Q2 Roadmap.pdf",
      meta: "PDF · 2.4 MB",
      type: "pdf",
    },
    {
      id: "4",
      title: "Document",
      subtitle: "Customer Feedback.xlsx",
      meta: "XLSX · 1.2 MB",
      type: "spreadsheet",
    },
  ],
  onViewAll,
  onOpenSource,
}: SourcesSectionProps) {
  const getIconConfig = (type: MeetingSource["type"]) => {
    switch (type) {
      case "youtube":
        return {
          icon: YoutubeIcon,
          bg: "bg-red-50 text-red-600 border border-red-100",
        };
      case "transcript":
        return {
          icon: FileText,
          bg: "bg-blue-50 text-blue-600 border border-blue-100",
        };
      case "pdf":
        return {
          icon: FileCode,
          bg: "bg-purple-50 text-purple-600 border border-purple-100",
        };
      case "spreadsheet":
        return {
          icon: FileSpreadsheet,
          bg: "bg-emerald-50 text-emerald-600 border border-emerald-100",
        };
    }
  };

  return (
    <div className="bg-white rounded-2xl border border-slate-200/80 p-3.5 shadow-card">
      {/* Header */}
      <div className="flex items-center justify-between gap-2 pb-2.5 border-b border-slate-100">
        <div className="flex items-center gap-2">
          <Link2 className="w-4 h-4 text-blue-600 shrink-0" />
          <h3 className="text-xs font-bold text-slate-900 tracking-tight">
            Sources & Evidence
          </h3>
        </div>
        <button
          onClick={onViewAll}
          className="inline-flex items-center gap-1 text-[11px] font-semibold text-indigo-600 hover:text-indigo-700 transition-colors"
        >
          <span>View all</span>
          <ArrowRight className="w-3 h-3" />
        </button>
      </div>

      {/* 4 Source Cards Grid without aggressive truncation */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2.5 mt-2.5">
        {sources.map((item) => {
          const config = getIconConfig(item.type);
          const Icon = config.icon;

          return (
            <div
              key={item.id}
              onClick={() => onOpenSource && onOpenSource(item)}
              className="p-3 rounded-xl border border-slate-200/70 hover:border-slate-300 bg-white hover:bg-slate-50/50 cursor-pointer transition-all flex items-start justify-between gap-2.5 group shadow-2xs min-h-[72px]"
            >
              <div className="flex items-start gap-2.5 min-w-0">
                <div
                  className={`w-8 h-8 rounded-lg ${config.bg} flex items-center justify-center shrink-0 shadow-2xs mt-0.5`}
                >
                  <Icon className="w-4 h-4" />
                </div>
                <div className="min-w-0 leading-tight">
                  <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
                    {item.title}
                  </p>
                  <p className="text-xs font-bold text-slate-800 leading-snug mt-0.5 break-words line-clamp-2">
                    {item.subtitle}
                  </p>
                  <p className="text-[11px] text-slate-400 font-normal mt-0.5">
                    {item.meta}
                  </p>
                </div>
              </div>
              <ExternalLink className="w-3.5 h-3.5 text-slate-300 group-hover:text-slate-600 shrink-0 transition-colors mt-0.5" />
            </div>
          );
        })}
      </div>
    </div>
  );
}
