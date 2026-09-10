"use client";

import React, { useState } from "react";
import { OpportunitySourceCitation } from "@/lib/api";
import { ExternalLink, Calendar, MapPin, Sparkles } from "lucide-react";
import Link from "next/link";

interface SourceCitationChipProps {
  citation: OpportunitySourceCitation;
  index: number;
  opportunityId?: string;
}

export function SourceCitationChip({
  citation,
  index,
  opportunityId,
}: SourceCitationChipProps) {
  const [showTooltip, setShowTooltip] = useState(false);
  const matchPct = Math.round(citation.similarity * 100);

  return (
    <div
      className="relative inline-block"
      onMouseEnter={() => setShowTooltip(true)}
      onMouseLeave={() => setShowTooltip(false)}
    >
      <Link
        href="/feed"
        className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[11px] font-medium bg-zinc-900/90 hover:bg-indigo-950/60 border border-zinc-800 hover:border-indigo-500/40 text-zinc-300 hover:text-indigo-200 transition cursor-pointer shadow-sm"
      >
        <span className="font-mono text-indigo-400 font-bold">[{index + 1}]</span>
        <span className="truncate max-w-[140px] sm:max-w-[180px]">{citation.title}</span>
        {matchPct > 0 && (
          <span className="text-[10px] text-emerald-400 font-mono">
            {matchPct}%
          </span>
        )}
        <ExternalLink className="h-2.5 w-2.5 text-zinc-500" />
      </Link>

      {/* Floating Hover Tooltip */}
      {showTooltip && (
        <div className="absolute bottom-full left-0 mb-2 z-50 w-64 p-3 rounded-xl bg-zinc-900 border border-zinc-700 shadow-2xl text-xs space-y-2 pointer-events-none animate-in fade-in zoom-in-95 duration-150">
          <div className="flex items-center justify-between gap-1 border-b border-zinc-800 pb-1.5">
            <span className="font-bold text-white truncate">{citation.title}</span>
            <span className="text-[10px] text-indigo-300 font-mono shrink-0">
              Source #{index + 1}
            </span>
          </div>

          <div className="space-y-1 text-[11px] text-zinc-400">
            {citation.domain && (
              <div>
                <span className="text-zinc-500">Domain:</span> {citation.domain}
              </div>
            )}
            {citation.location && (
              <div className="flex items-center gap-1">
                <MapPin className="h-3 w-3 text-zinc-500" />
                <span>{citation.location}</span>
              </div>
            )}
            {citation.deadline && (
              <div className="flex items-center gap-1 text-amber-400/90">
                <Calendar className="h-3 w-3" />
                <span>Deadline: {citation.deadline}</span>
              </div>
            )}
          </div>

          <div className="flex items-center justify-between pt-1 border-t border-zinc-800/80 text-[10px] text-zinc-500">
            <span className="flex items-center gap-1 text-emerald-400">
              <Sparkles className="h-3 w-3" />
              <span>Grounded in Live DB</span>
            </span>
            <span>Click to view in feed</span>
          </div>
        </div>
      )}
    </div>
  );
}
