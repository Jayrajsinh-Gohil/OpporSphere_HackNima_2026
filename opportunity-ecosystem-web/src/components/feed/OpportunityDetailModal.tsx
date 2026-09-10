"use client";

import React, { useEffect } from "react";
import { RecommendationItem } from "@/lib/api";
import {
  X,
  Sparkles,
  ShieldCheck,
  Calendar,
  MapPin,
  Building2,
  ExternalLink,
  Users,
  CheckCircle2,
  Share2,
} from "lucide-react";
import Link from "next/link";

interface OpportunityDetailModalProps {
  opportunity: RecommendationItem | null;
  onClose: () => void;
}

export function OpportunityDetailModal({
  opportunity,
  onClose,
}: OpportunityDetailModalProps) {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  if (!opportunity) return null;

  const matchPct = Math.round(
    opportunity.match_relevance_pct ||
      (opportunity.similarity ? opportunity.similarity * 100 : 85)
  );
  const trustScore = opportunity.trust_score ?? 90;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-black/80 backdrop-blur-md animate-in fade-in duration-200">
      <div className="relative w-full max-w-2xl rounded-3xl border border-zinc-800 bg-zinc-950 p-6 sm:p-8 shadow-2xl overflow-hidden max-h-[90vh] flex flex-col">
        {/* Glow ambient */}
        <div className="absolute top-0 right-0 h-48 w-48 rounded-full bg-indigo-600/15 blur-3xl pointer-events-none" />

        {/* Modal Header */}
        <div className="flex items-start justify-between gap-4 pb-4 border-b border-zinc-800/80">
          <div>
            <div className="flex flex-wrap items-center gap-2 mb-2">
              {opportunity.domain && (
                <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-500/10 border border-indigo-500/20 text-indigo-300">
                  {opportunity.domain}
                </span>
              )}
              {opportunity.type && (
                <span className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-zinc-800 text-zinc-300 border border-zinc-700">
                  {opportunity.type}
                </span>
              )}
            </div>
            <h2 className="text-xl sm:text-2xl font-bold text-white leading-tight">
              {opportunity.title}
            </h2>
          </div>

          <button
            onClick={onClose}
            className="p-2 rounded-xl bg-zinc-900 border border-zinc-800 text-zinc-400 hover:text-white transition shrink-0 cursor-pointer"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Modal Scrollable Body */}
        <div className="flex-1 overflow-y-auto py-6 space-y-6 text-sm text-zinc-300 pr-1">
          {/* Metrics bar: Match % + Trust Score */}
          <div className="grid grid-cols-2 gap-3">
            <div className="p-4 rounded-2xl bg-zinc-900/60 border border-zinc-800/80 flex items-center justify-between">
              <div>
                <span className="text-xs text-zinc-400 block mb-0.5">AI Match Relevance</span>
                <span className="text-xl font-bold text-indigo-400">{matchPct}%</span>
              </div>
              <div className="h-10 w-10 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center">
                <Sparkles className="h-5 w-5" />
              </div>
            </div>

            <div className="p-4 rounded-2xl bg-zinc-900/60 border border-zinc-800/80 flex items-center justify-between">
              <div>
                <span className="text-xs text-zinc-400 block mb-0.5">Verified Trust Score</span>
                <span className="text-xl font-bold text-cyan-400">{trustScore}/100</span>
              </div>
              <div className="h-10 w-10 rounded-xl bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 flex items-center justify-center">
                <ShieldCheck className="h-5 w-5" />
              </div>
            </div>
          </div>

          {/* Logistics */}
          <div className="flex flex-wrap gap-y-2 gap-x-6 text-xs text-zinc-400 p-4 rounded-2xl bg-zinc-900/40 border border-zinc-800/50">
            {opportunity.organizer && (
              <div className="flex items-center gap-2">
                <Building2 className="h-4 w-4 text-zinc-500" />
                <span>Host: <strong className="text-zinc-200">{opportunity.organizer}</strong></span>
              </div>
            )}
            {opportunity.location && (
              <div className="flex items-center gap-2">
                <MapPin className="h-4 w-4 text-zinc-500" />
                <span>Location: <strong className="text-zinc-200">{opportunity.location}</strong></span>
              </div>
            )}
            {opportunity.deadline && (
              <div className="flex items-center gap-2 text-amber-400">
                <Calendar className="h-4 w-4" />
                <span>Deadline: <strong className="text-amber-300">{opportunity.deadline}</strong></span>
              </div>
            )}
          </div>

          {/* Description */}
          <div>
            <h4 className="text-xs font-semibold uppercase tracking-wider text-zinc-400 mb-2">
              Opportunity Overview
            </h4>
            <p className="text-sm text-zinc-300 leading-relaxed whitespace-pre-line">
              {opportunity.description}
            </p>
          </div>

          {/* Rationale */}
          {opportunity.reason && (
            <div className="p-4 rounded-2xl bg-indigo-950/20 border border-indigo-500/20 space-y-1">
              <h4 className="text-xs font-semibold text-indigo-300 flex items-center gap-1.5">
                <Sparkles className="h-3.5 w-3.5 text-indigo-400" />
                <span>Why This Fits Your Profile</span>
              </h4>
              <p className="text-xs text-zinc-300 leading-relaxed">
                {opportunity.reason}
              </p>
            </div>
          )}

          {/* Trust Details */}
          <div className="p-4 rounded-2xl bg-cyan-950/15 border border-cyan-500/20 text-xs text-zinc-300 flex items-start gap-3">
            <ShieldCheck className="h-5 w-5 text-cyan-400 shrink-0 mt-0.5" />
            <div>
              <span className="font-semibold text-cyan-300">Trust & Authenticity Verified</span>
              <p className="text-[11px] text-zinc-400 mt-0.5">
                Organized by verified campus partner with authentic track record, legitimate evaluation rubrics, and direct coordinator oversight.
              </p>
            </div>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="pt-4 border-t border-zinc-800 flex flex-col sm:flex-row items-center justify-between gap-3">
          <Link
            href="/team-finder"
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-xs font-medium text-zinc-200 transition cursor-pointer"
          >
            <Users className="h-4 w-4 text-indigo-400" />
            <span>Find Teammates</span>
          </Link>

          <div className="w-full sm:w-auto flex items-center gap-2">
            <button
              onClick={() => alert(`Copied share link for "${opportunity.title}"`)}
              className="p-2.5 rounded-xl bg-zinc-900 border border-zinc-800 text-zinc-400 hover:text-white transition cursor-pointer"
              title="Share opportunity"
            >
              <Share2 className="h-4 w-4" />
            </button>
            <button
              onClick={() => alert(`Redirecting to registration portal for: "${opportunity.title}"`)}
              className="flex-1 sm:flex-none inline-flex items-center justify-center gap-2 px-6 py-2.5 rounded-xl bg-gradient-to-r from-indigo-500 to-purple-600 font-semibold text-xs text-white shadow-lg shadow-indigo-500/25 hover:from-indigo-600 hover:to-purple-700 transition cursor-pointer"
            >
              <span>Apply / Register Now</span>
              <ExternalLink className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
