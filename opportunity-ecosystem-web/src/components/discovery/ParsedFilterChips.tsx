"use client";

import React from "react";
import { ExtractedFilters } from "@/lib/api";
import {
  X,
  Sparkles,
  MapPin,
  Calendar,
  GraduationCap,
  Layers,
  Cpu,
  RotateCcw,
} from "lucide-react";

interface ParsedFilterChipsProps {
  filters: ExtractedFilters | null;
  searchMode?: string;
  confidenceScore?: number;
  onRemoveFilter: (filterKey: keyof ExtractedFilters) => void;
  onClearAll?: () => void;
}

export function ParsedFilterChips({
  filters,
  searchMode,
  confidenceScore,
  onRemoveFilter,
  onClearAll,
}: ParsedFilterChipsProps) {
  if (!filters) return null;

  const hasAnyFilter =
    Boolean(filters.domain) ||
    Boolean(filters.location) ||
    Boolean(filters.department) ||
    Boolean(filters.opportunity_type) ||
    Boolean(filters.deadline_from || filters.deadline_to);

  if (!hasAnyFilter && !searchMode) return null;

  const confidencePct = confidenceScore
    ? Math.round(confidenceScore * 100)
    : 85;

  return (
    <div className="p-4 rounded-2xl bg-zinc-900/40 border border-zinc-800/80 space-y-3 animate-in fade-in duration-200">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <Cpu className="h-4 w-4 text-indigo-400" />
          <span className="text-xs font-semibold text-zinc-200">
            Parsed AI Search Criteria
          </span>
          <span className="text-[11px] text-zinc-500">
            (Extracted automatically from your query for transparency)
          </span>
        </div>

        {/* Strategy Indicator Badge */}
        {searchMode && (
          <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-indigo-500/10 border border-indigo-500/20 text-indigo-300">
            <Sparkles className="h-3 w-3" />
            <span>
              {searchMode === "structured_filter"
                ? `spaCy NER Filter (${confidencePct}% conf.)`
                : searchMode === "semantic_fallback"
                ? "pgvector Semantic Fallback"
                : `Strategy: ${searchMode}`}
            </span>
          </div>
        )}
      </div>

      {/* Removable Chips */}
      <div className="flex flex-wrap items-center gap-2 pt-1">
        {filters.domain && (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-xl text-xs font-medium bg-indigo-500/15 border border-indigo-500/30 text-indigo-200">
            <Layers className="h-3 w-3 text-indigo-400" />
            <span>Domain: <strong>{filters.domain}</strong></span>
            <button
              type="button"
              onClick={() => onRemoveFilter("domain")}
              className="hover:text-white p-0.5 rounded transition cursor-pointer"
              title="Remove domain constraint"
            >
              <X className="h-3 w-3" />
            </button>
          </span>
        )}

        {filters.location && (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-xl text-xs font-medium bg-cyan-500/15 border border-cyan-500/30 text-cyan-200">
            <MapPin className="h-3 w-3 text-cyan-400" />
            <span>Location: <strong>{filters.location}</strong></span>
            <button
              type="button"
              onClick={() => onRemoveFilter("location")}
              className="hover:text-white p-0.5 rounded transition cursor-pointer"
              title="Remove location constraint"
            >
              <X className="h-3 w-3" />
            </button>
          </span>
        )}

        {filters.department && (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-xl text-xs font-medium bg-purple-500/15 border border-purple-500/30 text-purple-200">
            <GraduationCap className="h-3 w-3 text-purple-400" />
            <span>Dept: <strong>{filters.department}</strong></span>
            <button
              type="button"
              onClick={() => onRemoveFilter("department")}
              className="hover:text-white p-0.5 rounded transition cursor-pointer"
              title="Remove department constraint"
            >
              <X className="h-3 w-3" />
            </button>
          </span>
        )}

        {filters.opportunity_type && (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-xl text-xs font-medium bg-pink-500/15 border border-pink-500/30 text-pink-200">
            <span>Type: <strong>{filters.opportunity_type}</strong></span>
            <button
              type="button"
              onClick={() => onRemoveFilter("opportunity_type")}
              className="hover:text-white p-0.5 rounded transition cursor-pointer"
              title="Remove type constraint"
            >
              <X className="h-3 w-3" />
            </button>
          </span>
        )}

        {(filters.deadline_from || filters.deadline_to) && (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-xl text-xs font-medium bg-amber-500/15 border border-amber-500/30 text-amber-200">
            <Calendar className="h-3 w-3 text-amber-400" />
            <span>
              Deadline:{" "}
              <strong>
                {filters.deadline_from && filters.deadline_to
                  ? `${filters.deadline_from} → ${filters.deadline_to}`
                  : filters.deadline_to
                  ? `Before ${filters.deadline_to}`
                  : `After ${filters.deadline_from}`}
              </strong>
            </span>
            <button
              type="button"
              onClick={() => {
                onRemoveFilter("deadline_from");
                onRemoveFilter("deadline_to");
              }}
              className="hover:text-white p-0.5 rounded transition cursor-pointer"
              title="Remove date window constraint"
            >
              <X className="h-3 w-3" />
            </button>
          </span>
        )}

        {hasAnyFilter && onClearAll && (
          <button
            type="button"
            onClick={onClearAll}
            className="inline-flex items-center gap-1 px-2.5 py-1 text-xs text-zinc-500 hover:text-zinc-300 transition cursor-pointer"
          >
            <RotateCcw className="h-3 w-3" />
            <span>Clear parsed filters</span>
          </button>
        )}
      </div>
    </div>
  );
}
