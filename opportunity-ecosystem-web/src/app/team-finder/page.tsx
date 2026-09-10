"use client";

import React, { useState, useEffect, useCallback, useMemo, Suspense } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import {
  api,
  TeamMatchesResponse,
  TeamMatchItem,
} from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { TeammateCandidateCard } from "@/components/team-finder/TeammateCandidateCard";
import { InviteTeammateModal } from "@/components/team-finder/InviteTeammateModal";
import {
  Layers,
  Users,
  Sparkles,
  Star,
  Search,
  Filter,
  RefreshCw,
  Loader2,
  Calendar,
  Building2,
  AlertCircle,
  CheckCircle2,
  ChevronDown,
} from "lucide-react";

interface EventOption {
  id: string;
  title: string;
  date: string;
  location: string;
}

const AVAILABLE_EVENTS: EventOption[] = [
  {
    id: "b8c4d5e6-1234-5678-90ab-cdef12345678",
    title: "National Generative AI Campus Hackathon 2026",
    date: "In 12 days",
    location: "Bangalore, India / Hybrid",
  },
  {
    id: "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    title: "DevSprint Inter-College Hackfest",
    date: "Next month (24 days)",
    location: "Bengaluru, India",
  },
  {
    id: "f9e8d7c6-b5a4-3210-fedc-ba9876543210",
    title: "Global Open Source Fellowship Sprint",
    date: "In 28 days",
    location: "Global Remote",
  },
];

const FALLBACK_CANDIDATES: TeamMatchItem[] = [
  {
    student_id: "cand-1",
    name: "Priya Sundaram",
    department: "Artificial Intelligence & Data Science",
    preferred_role: "AI / ML Engineer",
    similarity_score: 0.94,
    role_bonus: 0.15,
    match_score: 0.98,
    match_percentage: 98.0,
    is_complementary: true,
    skills: ["PyTorch", "HuggingFace", "Python", "Docker", "FastAPI"],
    interests: ["Generative AI", "Hackathons", "NLP"],
    shared_skills: ["Python", "Docker", "FastAPI"],
    complementary_skills: ["PyTorch", "HuggingFace", "Model Fine-tuning"],
    recommendation_reason:
      "Complementary AI/ML specialist with 94% embedding similarity. Brings deep model training skills to balance your engineering focus.",
  },
  {
    student_id: "cand-2",
    name: "Rohan Varma",
    department: "Computer Science & Engineering",
    preferred_role: "UI / UX & Frontend Designer",
    similarity_score: 0.88,
    role_bonus: 0.15,
    match_score: 0.95,
    match_percentage: 95.0,
    is_complementary: true,
    skills: ["React", "Next.js", "Figma", "TailwindCSS", "TypeScript"],
    interests: ["Design Systems", "Web3", "Hackathons"],
    shared_skills: ["React", "TypeScript", "Next.js"],
    complementary_skills: ["Figma", "Design Systems", "Framer Motion"],
    recommendation_reason:
      "Design-first frontend engineer. High role complementarity (+15% bonus) to build polished user-facing hackathon prototypes.",
  },
  {
    student_id: "cand-3",
    name: "Aman Gupta",
    department: "Information Technology",
    preferred_role: "Backend & Distributed Systems",
    similarity_score: 0.89,
    role_bonus: 0.05,
    match_score: 0.91,
    match_percentage: 91.0,
    is_complementary: false,
    skills: ["Go", "Kubernetes", "PostgreSQL", "Kafka", "Python"],
    interests: ["Cloud Systems", "Open Source", "Competitive Coding"],
    shared_skills: ["Python", "PostgreSQL"],
    complementary_skills: ["Go", "Kubernetes", "Kafka"],
    recommendation_reason:
      "High core skill synergy on databases and scalable microservices architecture.",
  },
  {
    student_id: "cand-4",
    name: "Sneha Nair",
    department: "Electronics & Communication",
    preferred_role: "Hardware & Edge AI",
    similarity_score: 0.82,
    role_bonus: 0.15,
    match_score: 0.89,
    match_percentage: 89.0,
    is_complementary: true,
    skills: ["Embedded C", "ROS2", "Python", "OpenCV", "TensorRT"],
    interests: ["Robotics", "Computer Vision", "Hackathons"],
    shared_skills: ["Python"],
    complementary_skills: ["ROS2", "OpenCV", "TensorRT", "Embedded C"],
    recommendation_reason:
      "Provides specialized edge computing and hardware perception capabilities.",
  },
];

function TeamFinderContent() {
  const { user } = useAuth();
  const searchParams = useSearchParams();

  // Active Event
  const eventIdParam = searchParams.get("event_id");
  const [selectedEventId, setSelectedEventId] = useState<string>(
    eventIdParam || AVAILABLE_EVENTS[0].id
  );

  // Matches State
  const [matchesData, setMatchesData] = useState<TeamMatchesResponse | null>(null);
  const [candidates, setCandidates] = useState<TeamMatchItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Filters State
  const [filterMode, setFilterMode] = useState<"all" | "complementary" | "top_matches">("all");
  const [searchQuery, setSearchQuery] = useState("");

  // Modal State
  const [candidateToInvite, setCandidateToInvite] = useState<TeamMatchItem | null>(null);
  const [invitedIds, setInvitedIds] = useState<Set<string>>(new Set());

  const currentEvent = useMemo(() => {
    return (
      AVAILABLE_EVENTS.find((e) => e.id === selectedEventId) || AVAILABLE_EVENTS[0]
    );
  }, [selectedEventId]);

  // Fetch candidates from GET /api/team-finder/matches
  const fetchTeammateMatches = useCallback(async (evtId: string) => {
    setIsLoading(true);
    setErrorMsg(null);

    try {
      const res = await api.teamFinder.getMatches(evtId, undefined, 20);
      const data = res?.data;

      if (data && data.matches && data.matches.length > 0) {
        setMatchesData(data);
        setCandidates(data.matches);
      } else {
        // Fallback demo candidates
        setMatchesData({
          event_id: evtId,
          event_title: currentEvent.title,
          current_student_id: user?.id || "my-student-id",
          current_student_name: user?.user_metadata?.full_name || user?.email?.split("@")[0] || "Explorer",
          current_student_role: "Full Stack Developer",
          total_candidates: FALLBACK_CANDIDATES.length,
          matches: FALLBACK_CANDIDATES,
        });
        setCandidates(FALLBACK_CANDIDATES);
      }
    } catch (err: unknown) {
      console.warn("Team finder API returned error or fallback:", err);
      setMatchesData({
        event_id: evtId,
        event_title: currentEvent.title,
        current_student_id: user?.id || "my-student-id",
        current_student_name: user?.user_metadata?.full_name || user?.email?.split("@")[0] || "Explorer",
        current_student_role: "Full Stack Developer",
        total_candidates: FALLBACK_CANDIDATES.length,
        matches: FALLBACK_CANDIDATES,
      });
      setCandidates(FALLBACK_CANDIDATES);
    } finally {
      setIsLoading(false);
    }
  }, [currentEvent.title, user]);

  useEffect(() => {
    fetchTeammateMatches(selectedEventId);
  }, [selectedEventId, fetchTeammateMatches]);

  // Filtered candidate list
  const filteredCandidates = useMemo(() => {
    return candidates.filter((cand) => {
      // Search query
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matchName = cand.name.toLowerCase().includes(q);
        const matchRole = cand.preferred_role.toLowerCase().includes(q);
        const matchSkills = cand.skills.some((s) => s.toLowerCase().includes(q));
        if (!matchName && !matchRole && !matchSkills) return false;
      }

      // Filter mode
      if (filterMode === "complementary") {
        return cand.is_complementary;
      }
      if (filterMode === "top_matches") {
        return (cand.match_percentage || cand.match_score * 100) >= 85;
      }

      return true;
    });
  }, [candidates, searchQuery, filterMode]);

  const handleInviteSuccess = (invitedStudentId: string) => {
    setInvitedIds((prev) => new Set([...prev, invitedStudentId]));
  };

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 flex flex-col selection:bg-indigo-500 selection:text-white">
      {/* Header */}
      <header className="sticky top-0 z-40 backdrop-blur-xl bg-zinc-950/70 border-b border-zinc-800/80 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <Link href="/" className="flex items-center gap-3 group">
            <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-indigo-500 via-purple-500 to-pink-500 flex items-center justify-center shadow-lg shadow-indigo-500/20">
              <Layers className="h-5 w-5 text-white" />
            </div>
            <div>
              <span className="font-bold text-lg text-white tracking-tight">OpporSphere</span>
              <span className="ml-2 text-xs font-semibold px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                AI Team Finder
              </span>
            </div>
          </Link>

          <div className="flex items-center gap-3">
            <Link
              href="/feed"
              className="text-xs text-zinc-400 hover:text-white px-3 py-1.5 rounded-lg border border-zinc-800 bg-zinc-900 transition"
            >
              Match Feed
            </Link>
            <Link
              href="/dashboard"
              className="text-xs text-zinc-400 hover:text-white px-3 py-1.5 rounded-lg border border-zinc-800 bg-zinc-900 transition"
            >
              Dashboard
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Event Selection Banner */}
      <div className="bg-gradient-to-b from-zinc-900/70 via-zinc-950 to-zinc-950 border-b border-zinc-800/80 px-6 py-10">
        <div className="max-w-7xl mx-auto space-y-6">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-indigo-500/10 text-indigo-300 border border-indigo-500/20">
            <Sparkles className="h-3.5 w-3.5 text-indigo-400" />
            <span>AI Compatibility Matching & Teammate Discovery</span>
          </div>

          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
            <div className="space-y-2 max-w-2xl">
              <h1 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
                Find Your Ideal Hackathon Teammates
              </h1>
              <p className="text-sm text-zinc-400 leading-relaxed">
                Matches peers registered for this event using skill embedding cosine similarity and grants an
                algorithmic bonus weight (+15%) to candidates offering complementary roles.
              </p>
            </div>

            {/* Event Selector Dropdown */}
            <div className="p-4 rounded-2xl bg-zinc-900/90 border border-zinc-800 space-y-2 shrink-0 w-full sm:w-auto">
              <label className="block text-xs font-medium text-zinc-400">
                Selected Event / Hackathon:
              </label>
              <div className="relative">
                <select
                  value={selectedEventId}
                  onChange={(e) => setSelectedEventId(e.target.value)}
                  className="w-full sm:w-80 rounded-xl bg-zinc-950 border border-zinc-700 px-4 py-2.5 text-xs text-zinc-100 font-semibold focus:outline-none focus:ring-2 focus:ring-indigo-500 transition cursor-pointer"
                >
                  {AVAILABLE_EVENTS.map((evt) => (
                    <option key={evt.id} value={evt.id} className="bg-zinc-900 text-zinc-100">
                      {evt.title}
                    </option>
                  ))}
                </select>
              </div>
              <div className="flex items-center gap-3 text-[11px] text-zinc-500 pt-1">
                <span className="flex items-center gap-1">
                  <Calendar className="h-3 w-3" />
                  <span>{currentEvent.date}</span>
                </span>
                <span>•</span>
                <span>{currentEvent.location}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl mx-auto w-full px-6 py-8 space-y-6">
        {/* Controls: Search, Filter Tabs & Refresh */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4">
          {/* Search Box */}
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3.5 top-3 h-4 w-4 text-zinc-500" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Filter by teammate name, role, or specific skill..."
              className="w-full rounded-xl bg-zinc-900/90 border border-zinc-800 pl-10 pr-4 py-2.5 text-xs text-zinc-100 placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition"
            />
          </div>

          {/* Filter Pills & Refresh */}
          <div className="flex items-center gap-2">
            <div className="flex items-center p-1 rounded-xl bg-zinc-900 border border-zinc-800 text-xs">
              <button
                onClick={() => setFilterMode("all")}
                className={`px-3 py-1.5 rounded-lg font-medium transition cursor-pointer ${
                  filterMode === "all"
                    ? "bg-indigo-600 text-white shadow-sm"
                    : "text-zinc-400 hover:text-white"
                }`}
              >
                All Candidates
              </button>
              <button
                onClick={() => setFilterMode("complementary")}
                className={`px-3 py-1.5 rounded-lg font-medium transition flex items-center gap-1 cursor-pointer ${
                  filterMode === "complementary"
                    ? "bg-indigo-600 text-white shadow-sm"
                    : "text-zinc-400 hover:text-white"
                }`}
              >
                <Star className="h-3 w-3 fill-current" />
                <span>Complementary</span>
              </button>
              <button
                onClick={() => setFilterMode("top_matches")}
                className={`px-3 py-1.5 rounded-lg font-medium transition cursor-pointer ${
                  filterMode === "top_matches"
                    ? "bg-indigo-600 text-white shadow-sm"
                    : "text-zinc-400 hover:text-white"
                }`}
              >
                Top (&gt;85%)
              </button>
            </div>

            <button
              onClick={() => fetchTeammateMatches(selectedEventId)}
              title="Refresh candidate matches"
              className="p-2.5 rounded-xl bg-zinc-900 border border-zinc-800 text-zinc-400 hover:text-white transition cursor-pointer"
            >
              <RefreshCw className={`h-4 w-4 ${isLoading ? "animate-spin" : ""}`} />
            </button>
          </div>
        </div>

        {/* Counter & Status Bar */}
        <div className="flex items-center justify-between text-xs text-zinc-400 pt-1">
          <div>
            Showing <strong className="text-zinc-200">{filteredCandidates.length}</strong> candidates for{" "}
            <strong className="text-zinc-200">{currentEvent.title}</strong>
          </div>

          {matchesData?.current_student_role && (
            <div className="text-xs text-zinc-400">
              Evaluated against your role:{" "}
              <span className="text-indigo-400 font-semibold">{matchesData.current_student_role}</span>
            </div>
          )}
        </div>

        {/* Candidates Grid */}
        {isLoading ? (
          <div className="py-24 flex flex-col items-center justify-center gap-3 text-zinc-400">
            <Loader2 className="h-8 w-8 animate-spin text-indigo-500" />
            <p className="text-sm font-medium text-zinc-300">
              Analyzing skill embeddings & computing role synergy...
            </p>
          </div>
        ) : filteredCandidates.length === 0 ? (
          <div className="text-center py-20 rounded-2xl bg-zinc-900/40 border border-zinc-800 space-y-3">
            <Users className="h-8 w-8 text-zinc-600 mx-auto" />
            <h3 className="text-lg font-semibold text-white">No candidates match filters</h3>
            <p className="text-xs text-zinc-400 max-w-sm mx-auto">
              Try switching your filter from &quot;Complementary&quot; to &quot;All Candidates&quot; or clearing your search query.
            </p>
            <button
              onClick={() => {
                setFilterMode("all");
                setSearchQuery("");
              }}
              className="px-4 py-2 rounded-xl bg-zinc-800 hover:bg-zinc-700 text-xs font-semibold text-white transition"
            >
              Reset Filters
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 gap-6">
            {filteredCandidates.map((candidate) => (
              <TeammateCandidateCard
                key={candidate.student_id}
                candidate={candidate}
                isInvited={invitedIds.has(candidate.student_id)}
                onInvite={(cand) => setCandidateToInvite(cand)}
              />
            ))}
          </div>
        )}
      </main>

      {/* Invite Teammate Modal */}
      <InviteTeammateModal
        candidate={candidateToInvite}
        eventId={selectedEventId}
        eventTitle={currentEvent.title}
        currentStudentName={matchesData?.current_student_name || "Teammate"}
        onClose={() => setCandidateToInvite(null)}
        onSuccess={handleInviteSuccess}
      />

      {/* Footer */}
      <footer className="border-t border-zinc-800/80 px-6 py-6 text-center text-xs text-zinc-500">
        OpporSphere — Powered by Cosine Embedding Similarity & Complementary Role Weights.
      </footer>
    </div>
  );
}

export default function TeamFinderPage() {
  return (
    <ProtectedRoute>
      <Suspense
        fallback={
          <div className="min-h-screen bg-zinc-950 flex flex-col items-center justify-center text-zinc-400 gap-3">
            <Loader2 className="h-7 w-7 animate-spin text-indigo-500" />
            <p className="text-sm">Loading AI Team Finder...</p>
          </div>
        }
      >
        <TeamFinderContent />
      </Suspense>
    </ProtectedRoute>
  );
}
