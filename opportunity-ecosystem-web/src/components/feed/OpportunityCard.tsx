"use client";

import React, { useState } from "react";
import { RecommendationItem } from "@/lib/api";
import {
  Sparkles,
  ShieldCheck,
  ShieldAlert,
  Calendar,
  MapPin,
  Building2,
  Bookmark,
  ExternalLink,
  ChevronRight,
  Check,
} from "lucide-react";

interface OpportunityCardProps {
  opportunity: RecommendationItem;
  onViewDetails: (opportunity: RecommendationItem) => void;
}

export function OpportunityCard({ opportunity, onViewDetails }: OpportunityCardProps) {
  const [isBookmarked, setIsBookmarked] = useState(false);

  // Match % score calculation — use the actual value, no fake fallback inflation
  const matchPct = Math.round(
    opportunity.match_relevance_pct ??
      (opportunity.similarity != null ? opportunity.similarity * 100 : 0)
  );

  // Trust score: 0 - 100 (0 = not yet rated, not inflated)
  const trustScore = opportunity.trust_score ?? 0;

  // Match Badge styling
  const getMatchBadgeStyle = (pct: number) => {
    if (pct >= 85) {
      return "bg-emerald-500/15 border-emerald-500/40 text-emerald-300 shadow-sm shadow-emerald-500/20";
    }
    if (pct >= 70) {
      return "bg-indigo-500/15 border-indigo-500/40 text-indigo-300 shadow-sm shadow-indigo-500/20";
    }
    return "bg-amber-500/15 border-amber-500/40 text-amber-300 shadow-sm shadow-amber-500/20";
  };

  // Trust Score Badge styling
  const getTrustBadgeStyle = (score: number) => {
    if (score >= 80) {
      return "bg-cyan-500/10 border-cyan-500/30 text-cyan-300";
    }
    if (score >= 60) {
      return "bg-blue-500/10 border-blue-500/30 text-blue-300";
    }
    return "bg-zinc-800 border-zinc-700 text-zinc-400";
  };

  return (
    <div className="group rounded-2xl border border-zinc-800/80 bg-zinc-900/50 hover:bg-zinc-900/80 backdrop-blur-xl p-6 transition-all duration-300 hover:border-indigo-500/40 hover:shadow-xl hover:shadow-indigo-500/5 flex flex-col justify-between">
      <div>
        {/* Top Header: Category/Domain + Match % + Trust Score */}
        <div className="flex flex-wrap items-center justify-between gap-2.5 mb-4">
          <div className="flex flex-wrap items-center gap-2">
            {opportunity.domain && (
              <span className="px-2.5 py-1 rounded-lg text-xs font-semibold bg-indigo-500/10 border border-indigo-500/20 text-indigo-300">
                {opportunity.domain}
              </span>
            )}
            {opportunity.type && (
              <span className="px-2.5 py-1 rounded-lg text-xs font-medium bg-zinc-800/80 text-zinc-300 border border-zinc-700/60">
                {opportunity.type}
              </span>
            )}
          </div>

          <div className="flex items-center gap-2">
            {/* Match % Badge */}
            <div
              className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold border transition ${getMatchBadgeStyle(
                matchPct
              )}`}
            >
              <Sparkles className="h-3.5 w-3.5" />
              <span>{matchPct}% Match</span>
            </div>

            {/* Trust Score Badge */}
            <div
              className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium border ${getTrustBadgeStyle(
                trustScore
              )}`}
              title={`Trust Score verified from source: ${trustScore}/100`}
            >
              {trustScore >= 70 ? (
                <ShieldCheck className="h-3.5 w-3.5 text-cyan-400" />
              ) : (
                <ShieldAlert className="h-3.5 w-3.5 text-amber-400" />
              )}
              <span>{trustScore} Trust</span>
            </div>

            {/* Bookmark button */}
            <button
              type="button"
              onClick={() => setIsBookmarked(!isBookmarked)}
              className={`p-1.5 rounded-lg border transition ${
                isBookmarked
                  ? "bg-indigo-500/20 border-indigo-500/40 text-indigo-300"
                  : "bg-zinc-950/60 border-zinc-800 text-zinc-500 hover:text-zinc-200"
              }`}
              title={isBookmarked ? "Saved to bookmarks" : "Save opportunity"}
            >
              <Bookmark className={`h-3.5 w-3.5 ${isBookmarked ? "fill-current" : ""}`} />
            </button>
          </div>
        </div>

        {/* Title */}
        <h3
          onClick={() => onViewDetails(opportunity)}
          className="text-lg font-bold text-white group-hover:text-indigo-300 transition cursor-pointer mb-2 leading-snug"
        >
          {opportunity.title}
        </h3>

        {/* Organizer & Location */}
        <div className="flex flex-wrap items-center gap-y-1 gap-x-4 text-xs text-zinc-400 mb-3">
          {opportunity.organizer && (
            <div className="flex items-center gap-1.5 text-zinc-300">
              <Building2 className="h-3.5 w-3.5 text-zinc-500" />
              <span>{opportunity.organizer}</span>
            </div>
          )}
          {opportunity.location && (
            <div className="flex items-center gap-1.5">
              <MapPin className="h-3.5 w-3.5 text-zinc-500" />
              <span>{opportunity.location}</span>
            </div>
          )}
          {opportunity.deadline && (
            <div className="flex items-center gap-1.5 text-amber-400/90 font-medium">
              <Calendar className="h-3.5 w-3.5" />
              <span>Deadline: {opportunity.deadline}</span>
            </div>
          )}
        </div>

        {/* Description Snippet */}
        <p className="text-xs text-zinc-400 leading-relaxed line-clamp-3 mb-4">
          {opportunity.description}
        </p>

        {/* Match Rationale / Explanation */}
        {opportunity.reason && (
          <div className="p-3 rounded-xl bg-indigo-950/20 border border-indigo-500/15 text-[11px] text-zinc-300 mb-4 flex items-start gap-2">
            <Sparkles className="h-3.5 w-3.5 text-indigo-400 shrink-0 mt-0.5" />
            <div className="leading-tight">
              <span className="font-semibold text-indigo-300">Why it matched: </span>
              {opportunity.reason}
            </div>
          </div>
        )}
      </div>

      {/* Card Footer: Action Buttons */}
      <div className="pt-4 border-t border-zinc-800/80 flex items-center justify-between gap-3">
        <span className="text-[11px] text-zinc-500">
          {opportunity.is_fallback ? "Browse mode · Profile match unavailable" : "Grounded pgvector Match"}
        </span>

        <button
          type="button"
          onClick={() => onViewDetails(opportunity)}
          className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-zinc-800 hover:bg-zinc-700 text-xs font-semibold text-white transition group-hover:bg-indigo-600 group-hover:shadow-md group-hover:shadow-indigo-500/20 cursor-pointer"
        >
          <span>View Details</span>
          <ChevronRight className="h-3.5 w-3.5 transition group-hover:translate-x-0.5" />
        </button>
      </div>
    </div>
  );
}
