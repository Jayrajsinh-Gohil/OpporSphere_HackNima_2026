"use client";

import React from "react";
import { TeamMatchItem } from "@/lib/api";
import {
  Sparkles,
  Star,
  Users,
  Send,
  CheckCircle2,
  GraduationCap,
  Briefcase,
  Check,
} from "lucide-react";

interface TeammateCandidateCardProps {
  candidate: TeamMatchItem;
  isInvited?: boolean;
  onInvite: (candidate: TeamMatchItem) => void;
}

export function TeammateCandidateCard({
  candidate,
  isInvited = false,
  onInvite,
}: TeammateCandidateCardProps) {
  // Initials for avatar
  const initials = candidate.name
    ? candidate.name
        .split(" ")
        .map((n) => n[0])
        .slice(0, 2)
        .join("")
        .toUpperCase()
    : "ST";

  const matchPct = Math.round(candidate.match_percentage || candidate.match_score * 100);

  return (
    <div className="group rounded-2xl border border-zinc-800/80 bg-zinc-900/50 hover:bg-zinc-900/80 backdrop-blur-xl p-6 transition-all duration-300 hover:border-indigo-500/40 hover:shadow-xl hover:shadow-indigo-500/5 flex flex-col justify-between">
      <div className="space-y-4">
        {/* Card Header: Avatar, Name, Compatibility % */}
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="h-12 w-12 rounded-2xl bg-gradient-to-tr from-indigo-500/30 to-purple-500/30 border border-indigo-500/30 flex items-center justify-center font-bold text-base text-indigo-300 shadow-md">
              {initials}
            </div>
            <div>
              <h3 className="font-bold text-white text-base leading-snug group-hover:text-indigo-300 transition">
                {candidate.name}
              </h3>
              {candidate.department && (
                <div className="flex items-center gap-1.5 text-xs text-zinc-400 mt-0.5">
                  <GraduationCap className="h-3.5 w-3.5 text-zinc-500 shrink-0" />
                  <span className="truncate max-w-[160px] sm:max-w-[200px]">
                    {candidate.department}
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* Compatibility Score Badge */}
          <div
            className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold border shrink-0 ${
              matchPct >= 85
                ? "bg-emerald-500/15 border-emerald-500/40 text-emerald-300 shadow-sm shadow-emerald-500/20"
                : matchPct >= 70
                ? "bg-indigo-500/15 border-indigo-500/40 text-indigo-300 shadow-sm shadow-indigo-500/20"
                : "bg-amber-500/15 border-amber-500/40 text-amber-300"
            }`}
          >
            <Sparkles className="h-3 w-3" />
            <span>{matchPct}% Match</span>
          </div>
        </div>

        {/* Roles & Synergy Bar */}
        <div className="flex flex-wrap items-center gap-2 pt-1">
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium bg-zinc-800/80 text-zinc-200 border border-zinc-700/60">
            <Briefcase className="h-3 w-3 text-zinc-400" />
            <span>{candidate.preferred_role}</span>
          </span>

          {candidate.is_complementary && (
            <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-semibold bg-purple-500/15 border border-purple-500/30 text-purple-300">
              <Star className="h-3 w-3 fill-purple-400 text-purple-400" />
              <span>Complementary Role</span>
            </span>
          )}
        </div>

        {/* Shared Skills */}
        {candidate.shared_skills && candidate.shared_skills.length > 0 && (
          <div className="space-y-1.5 text-xs">
            <div className="text-[11px] font-medium text-indigo-300 flex items-center gap-1">
              <Check className="h-3 w-3 text-indigo-400" />
              <span>Shared Competencies ({candidate.shared_skills.length}):</span>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {candidate.shared_skills.map((skill) => (
                <span
                  key={skill}
                  className="px-2 py-0.5 rounded-md bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-[11px]"
                >
                  {skill}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Complementary Skills */}
        {candidate.complementary_skills && candidate.complementary_skills.length > 0 && (
          <div className="space-y-1.5 text-xs">
            <div className="text-[11px] font-medium text-purple-300 flex items-center gap-1">
              <Sparkles className="h-3 w-3 text-purple-400" />
              <span>Brings New Skills:</span>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {candidate.complementary_skills.slice(0, 4).map((skill) => (
                <span
                  key={skill}
                  className="px-2 py-0.5 rounded-md bg-purple-500/10 border border-purple-500/20 text-purple-300 text-[11px]"
                >
                  +{skill}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Recommendation Rationale */}
        {candidate.recommendation_reason && (
          <div className="p-3 rounded-xl bg-zinc-950/70 border border-zinc-800 text-[11px] text-zinc-400 leading-relaxed">
            <span className="font-semibold text-zinc-300">Synergy Reason: </span>
            {candidate.recommendation_reason}
          </div>
        )}
      </div>

      {/* Card Footer: Action Button */}
      <div className="pt-5 mt-4 border-t border-zinc-800/80 flex items-center justify-between">
        <span className="text-[11px] text-zinc-500">
          Cosine Similarity + Role Bonus
        </span>

        {isInvited ? (
          <span className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-emerald-500/15 border border-emerald-500/30 text-emerald-300 text-xs font-semibold">
            <CheckCircle2 className="h-3.5 w-3.5" />
            <span>Invite Sent</span>
          </span>
        ) : (
          <button
            type="button"
            onClick={() => onInvite(candidate)}
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-xs font-semibold text-white shadow-md shadow-indigo-500/20 transition cursor-pointer"
          >
            <Send className="h-3.5 w-3.5" />
            <span>Invite Teammate</span>
          </button>
        )}
      </div>
    </div>
  );
}
