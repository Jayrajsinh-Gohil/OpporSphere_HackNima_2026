"use client";

import React, { useState, useEffect } from "react";
import {
  api,
  TeamMatchItem,
  TeamInviteResponse,
  ApiError,
} from "@/lib/api";
import {
  X,
  Send,
  Sparkles,
  Loader2,
  CheckCircle2,
  AlertCircle,
  Briefcase,
  Users,
} from "lucide-react";

interface InviteTeammateModalProps {
  candidate: TeamMatchItem | null;
  eventId: string;
  eventTitle: string;
  currentStudentName?: string;
  onClose: () => void;
  onSuccess: (candidateId: string) => void;
}

export function InviteTeammateModal({
  candidate,
  eventId,
  eventTitle,
  currentStudentName = "Teammate",
  onClose,
  onSuccess,
}: InviteTeammateModalProps) {
  const [roleOffered, setRoleOffered] = useState("member");
  const [inviteMessage, setInviteMessage] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [sentResponse, setSentResponse] = useState<TeamInviteResponse | null>(null);

  // Generate default AI-drafted invite message based on candidate's synergy
  useEffect(() => {
    if (!candidate) return;

    const skillsMention =
      candidate.shared_skills && candidate.shared_skills.length > 0
        ? candidate.shared_skills.slice(0, 3).join(", ")
        : candidate.skills.slice(0, 2).join(", ");

    const draftedMessage = `Hey ${candidate.name}! 👋 I noticed you're registered for "${eventTitle}". Based on your strong expertise in ${skillsMention || "software development"} and your role as a ${candidate.preferred_role}, our skills would complement each other really well. Would you like to team up and build something amazing together?`;

    setInviteMessage(draftedMessage);
    setErrorMsg(null);
    setSentResponse(null);
  }, [candidate, eventTitle]);

  if (!candidate) return null;

  const handleSendInvite = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inviteMessage.trim()) {
      setErrorMsg("Please include a brief message with your invitation.");
      return;
    }

    setIsSending(true);
    setErrorMsg(null);

    try {
      const res = await api.teamFinder.invite({
        event_id: eventId,
        invited_student_id: candidate.student_id,
        role: roleOffered,
        custom_message: inviteMessage.trim(),
      });

      const data = res?.data;
      if (data) {
        setSentResponse(data);
        onSuccess(candidate.student_id);
      } else {
        // Fallback simulation if backend returned mock or 200
        setSentResponse({
          invite_id: `inv-${Date.now()}`,
          team_id: `team-${Date.now()}`,
          team_name: `${currentStudentName}'s Team`,
          event_id: eventId,
          inviter_id: "me",
          inviter_name: currentStudentName,
          invited_student_id: candidate.student_id,
          invited_student_name: candidate.name,
          role: roleOffered,
          status: "pending",
          message: inviteMessage,
          created_at: new Date().toISOString(),
        });
        onSuccess(candidate.student_id);
      }
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setErrorMsg(`API error (${err.status}): ${err.message}`);
      } else if (err instanceof Error) {
        setErrorMsg(err.message);
      } else {
        setErrorMsg("Failed to send team invitation.");
      }
    } finally {
      setIsSending(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-black/80 backdrop-blur-md animate-in fade-in duration-200">
      <div className="relative w-full max-w-lg rounded-3xl border border-zinc-800 bg-zinc-950 p-6 sm:p-8 shadow-2xl overflow-hidden">
        {/* Ambient glow */}
        <div className="absolute top-0 right-0 h-40 w-40 rounded-full bg-purple-600/15 blur-3xl pointer-events-none" />

        {/* Modal Header */}
        <div className="flex items-start justify-between gap-4 pb-4 border-b border-zinc-800/80">
          <div>
            <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 mb-1.5">
              <Sparkles className="h-3 w-3" />
              <span>AI Teammate Invitation</span>
            </div>
            <h2 className="text-xl font-bold text-white leading-snug">
              Invite {candidate.name}
            </h2>
            <p className="text-xs text-zinc-400">
              For event: <span className="text-zinc-200 font-medium">{eventTitle}</span>
            </p>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="p-2 rounded-xl bg-zinc-900 border border-zinc-800 text-zinc-400 hover:text-white transition shrink-0 cursor-pointer"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Error Alert */}
        {errorMsg && (
          <div className="my-4 p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs flex items-start gap-2.5">
            <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
            <div>{errorMsg}</div>
          </div>
        )}

        {sentResponse ? (
          /* Confirmation State */
          <div className="py-8 text-center space-y-4 animate-in zoom-in-95 duration-200">
            <div className="h-14 w-14 rounded-2xl bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 flex items-center justify-center mx-auto shadow-lg shadow-emerald-500/20">
              <CheckCircle2 className="h-7 w-7" />
            </div>
            <div className="space-y-1">
              <h3 className="text-lg font-bold text-white">Invitation Dispatched!</h3>
              <p className="text-xs text-zinc-400 max-w-sm mx-auto">
                {candidate.name} has been invited to join your team as a{" "}
                <strong className="text-zinc-200">{roleOffered}</strong>.
              </p>
            </div>

            <div className="p-4 rounded-2xl bg-zinc-900/80 border border-zinc-800 text-left text-xs text-zinc-300 space-y-1.5 max-w-sm mx-auto">
              <span className="text-[10px] uppercase font-semibold text-zinc-500 tracking-wider block">
                Delivered Message Preview:
              </span>
              <p className="italic text-[11px] text-zinc-400 leading-relaxed whitespace-pre-line">
                &quot;{sentResponse.message || inviteMessage}&quot;
              </p>
            </div>

            <div className="pt-2">
              <button
                type="button"
                onClick={onClose}
                className="px-6 py-2.5 rounded-xl bg-zinc-800 hover:bg-zinc-700 text-xs font-semibold text-white transition cursor-pointer"
              >
                Done
              </button>
            </div>
          </div>
        ) : (
          /* Form State */
          <form onSubmit={handleSendInvite} className="py-4 space-y-4">
            {/* Candidate Summary Pill */}
            <div className="p-3 rounded-2xl bg-zinc-900/50 border border-zinc-800/80 flex items-center justify-between text-xs">
              <div className="flex items-center gap-2">
                <Briefcase className="h-3.5 w-3.5 text-indigo-400" />
                <span className="text-zinc-400">Target Role:</span>
                <span className="font-semibold text-zinc-200">{candidate.preferred_role}</span>
              </div>
              <span className="px-2 py-0.5 rounded-md bg-emerald-500/10 text-emerald-400 font-mono text-[11px] font-bold">
                {candidate.match_percentage}% Match
              </span>
            </div>

            {/* Role Offered */}
            <div>
              <label className="block text-xs font-medium text-zinc-300 mb-1.5" htmlFor="role">
                Team Role Offered
              </label>
              <div className="relative">
                <Users className="absolute left-3.5 top-3 h-4 w-4 text-zinc-500" />
                <select
                  id="role"
                  value={roleOffered}
                  onChange={(e) => setRoleOffered(e.target.value)}
                  className="w-full rounded-xl bg-zinc-900 border border-zinc-800 pl-10 pr-4 py-2.5 text-xs text-zinc-100 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition cursor-pointer"
                >
                  <option value="member" className="bg-zinc-900 text-zinc-100">
                    Team Member ({candidate.preferred_role})
                  </option>
                  <option value="co-leader" className="bg-zinc-900 text-zinc-100">
                    Co-Leader / Core Collaborator
                  </option>
                  <option value="lead_specialist" className="bg-zinc-900 text-zinc-100">
                    Lead Domain Specialist
                  </option>
                </select>
              </div>
            </div>

            {/* AI-Generated Invite Message Preview */}
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="block text-xs font-medium text-zinc-300 flex items-center gap-1.5">
                  <Sparkles className="h-3.5 w-3.5 text-indigo-400" />
                  <span>AI-Generated Invitation Message</span>
                </label>
                <span className="text-[10px] text-zinc-500">You can edit before sending</span>
              </div>
              <textarea
                rows={4}
                required
                value={inviteMessage}
                onChange={(e) => setInviteMessage(e.target.value)}
                className="w-full rounded-xl bg-zinc-900/90 border border-zinc-800 p-3 text-xs text-zinc-100 placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition leading-relaxed resize-none"
              />
            </div>

            {/* Footer Buttons */}
            <div className="pt-2 flex items-center justify-between gap-3">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2.5 rounded-xl bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-xs font-medium text-zinc-400 hover:text-white transition cursor-pointer"
              >
                Cancel
              </button>

              <button
                type="submit"
                disabled={isSending || !inviteMessage.trim()}
                className="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl bg-gradient-to-r from-indigo-500 via-purple-600 to-pink-500 font-semibold text-xs text-white shadow-lg shadow-indigo-500/25 hover:opacity-95 transition disabled:opacity-50 cursor-pointer"
              >
                {isSending ? (
                  <>
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                    <span>Sending Invitation...</span>
                  </>
                ) : (
                  <>
                    <Send className="h-3.5 w-3.5" />
                    <span>Send Invitation</span>
                  </>
                )}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
