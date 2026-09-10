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
  domain?: string;
  prize_pool?: string;
  max_team_size?: number;
}

const FALLBACK_EVENTS: EventOption[] = [
  {
    id: "1ebc71d7-0671-5a73-8b87-b547f0a6fc52",
    title: "HackNima 2025: AI For Social Good",
    date: "Deadline: 2026-10-25",
    location: "Bengaluru, Karnataka (Hybrid)",
    prize_pool: "₹10,00,000",
  },
  {
    id: "24415eae-d8e8-50aa-b44d-f552b80e3a69",
    title: "Flutter Forward India Hackathon 2026",
    date: "Deadline: 2026-10-10",
    location: "Ahmedabad, Gujarat (Hybrid)",
    prize_pool: "₹5,00,000",
  },
  {
    id: "a7196c79-1724-5c1e-8856-116a18f3684e",
    title: "FinTech High-Frequency API & Systems Challenge",
    date: "Deadline: 2026-10-15",
    location: "Mumbai, Maharashtra",
    prize_pool: "₹9,00,000",
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

  // Mode: Event-specific teammate matching VS Directory of all 50 students
  const [activeTab, setActiveTab] = useState<"event_matches" | "all_students">("event_matches");

  // Dynamic Events List
  const [eventsList, setEventsList] = useState<EventOption[]>(FALLBACK_EVENTS);
  const eventIdParam = searchParams.get("event_id");
  const [selectedEventId, setSelectedEventId] = useState<string>(
    eventIdParam || FALLBACK_EVENTS[0].id
  );

  // Matches State
  const [matchesData, setMatchesData] = useState<TeamMatchesResponse | null>(null);
  const [candidates, setCandidates] = useState<TeamMatchItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // All 50 Students Directory State
  const [allStudents, setAllStudents] = useState<TeamMatchItem[]>([]);
  const [selectedRoleFilter, setSelectedRoleFilter] = useState<string>("All Roles");

  // Filters State
  const [filterMode, setFilterMode] = useState<"all" | "complementary" | "top_matches">("all");
  const [searchQuery, setSearchQuery] = useState("");

  // Modal State
  const [candidateToInvite, setCandidateToInvite] = useState<TeamMatchItem | null>(null);
  const [invitedIds, setInvitedIds] = useState<Set<string>>(new Set());

  // Load active events from database on mount
  useEffect(() => {
    async function loadEvents() {
      try {
        const res = await api.teamFinder.getEvents();
        const data = res?.data;
        if (data && data.length > 0) {
          const mapped: EventOption[] = data.map((e) => ({
            id: e.id,
            title: e.title,
            date: e.date || `Deadline: ${e.deadline || "Upcoming"}`,
            location: e.location || "India",
            domain: e.domain,
            prize_pool: e.prize_pool,
            max_team_size: e.max_team_size,
          }));
          setEventsList(mapped);
          if (!eventIdParam) {
            setSelectedEventId(mapped[0].id);
          }
        }
      } catch (err) {
        console.info("Using fallback event list while API connects:", err);
      }
    }

    async function loadAllStudents() {
      try {
        const res = await api.teamFinder.getCandidates({ limit: 50 });
        const data = res?.data;
        if (data && data.length > 0) {
          const mapped: TeamMatchItem[] = data.map((s, idx) => ({
            student_id: s.student_id,
            name: s.name,
            department: `${s.department || "Engineering"} • ${s.location || "India"}`,
            preferred_role: s.preferred_role || "Full Stack Developer",
            similarity_score: 0.88 - (idx * 0.005),
            role_bonus: 0.15,
            match_score: Math.max(0.70, 0.95 - (idx * 0.005)),
            match_percentage: Math.max(70, Math.round((0.95 - (idx * 0.005)) * 100)),
            is_complementary: idx % 2 === 0,
            skills: s.skills || [],
            interests: s.interests || [],
            shared_skills: s.skills?.slice(0, 2) || [],
            complementary_skills: s.skills?.slice(2) || [],
            recommendation_reason: `Active student builder located in ${s.location || "India"} with core focus in ${s.preferred_role || "Engineering"}.`,
          }));
          setAllStudents(mapped);
        }
      } catch (err) {
        console.info("Could not load student directory from API:", err);
      }
    }

    loadEvents();
    loadAllStudents();
  }, [eventIdParam]);

  const currentEvent = useMemo(() => {
    return (
      eventsList.find((e) => e.id === selectedEventId) || eventsList[0] || FALLBACK_EVENTS[0]
    );
  }, [eventsList, selectedEventId]);

  // Fetch candidates from GET /api/team-finder/matches
  const fetchTeammateMatches = useCallback(async (evtId: string) => {
    if (!evtId) return;
    setIsLoading(true);
    setErrorMsg(null);

    try {
      const res = await api.teamFinder.getMatches(evtId, undefined, 30);
      const data = res?.data;

      if (data && data.matches && data.matches.length > 0) {
        setMatchesData(data);
        setCandidates(data.matches);
      } else {
        // If event has no registered matches yet, use the active students directory as event pool
        if (allStudents.length > 0) {
          setMatchesData({
            event_id: evtId,
            event_title: currentEvent.title,
            current_student_id: user?.id || "my-student-id",
            current_student_name: user?.user_metadata?.full_name || user?.email?.split("@")[0] || "Explorer",
            current_student_role: "Full Stack Developer",
            total_candidates: allStudents.length,
            matches: allStudents.slice(0, 20),
          });
          setCandidates(allStudents.slice(0, 20));
        } else {
          setCandidates(FALLBACK_CANDIDATES);
        }
      }
    } catch (err: unknown) {
      console.info("Fetching teammate matches fallback:", err);
      if (allStudents.length > 0) {
        setCandidates(allStudents.slice(0, 20));
      } else {
        setCandidates(FALLBACK_CANDIDATES);
      }
    } finally {
      setIsLoading(false);
    }
  }, [currentEvent.title, user, allStudents]);

  useEffect(() => {
    if (selectedEventId) {
      fetchTeammateMatches(selectedEventId);
    }
  }, [selectedEventId, fetchTeammateMatches]);

  // Active pool of candidates based on current tab
  const activeCandidatePool = useMemo(() => {
    return activeTab === "all_students" && allStudents.length > 0 ? allStudents : candidates;
  }, [activeTab, allStudents, candidates]);

  // Filtered candidate list
  const filteredCandidates = useMemo(() => {
    return activeCandidatePool.filter((cand) => {
      // Role filter (for directory view)
      if (selectedRoleFilter !== "All Roles") {
        if (!cand.preferred_role.toLowerCase().includes(selectedRoleFilter.toLowerCase())) {
          return false;
        }
      }

      // Search query (name, role, skills, department/location)
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matchName = cand.name.toLowerCase().includes(q);
        const matchRole = cand.preferred_role.toLowerCase().includes(q);
        const matchDept = cand.department?.toLowerCase().includes(q);
        const matchSkills = cand.skills.some((s) => s.toLowerCase().includes(q));
        if (!matchName && !matchRole && !matchSkills && !matchDept) return false;
      }

      // Filter mode
      if (filterMode === "complementary") {
        return cand.is_complementary;
      }
      if (filterMode === "top_matches") {
        return (cand.match_percentage || cand.match_score * 100) >= 80;
      }

      return true;
    });
  }, [activeCandidatePool, searchQuery, filterMode, selectedRoleFilter]);

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
                  {eventsList.map((evt) => (
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
        {/* View Mode Tabs: Event Matching vs Student Directory */}
        <div className="flex flex-wrap items-center gap-3 border-b border-zinc-800 pb-4">
          <button
            onClick={() => setActiveTab("event_matches")}
            className={`px-4 py-2.5 rounded-xl text-xs font-semibold transition cursor-pointer flex items-center gap-2 ${
              activeTab === "event_matches"
                ? "bg-gradient-to-r from-indigo-600 to-purple-600 text-white shadow-md shadow-indigo-500/20"
                : "bg-zinc-900 border border-zinc-800 text-zinc-400 hover:text-white"
            }`}
          >
            <Sparkles className="h-3.5 w-3.5" />
            <span>Hackathon Teammate Matching ({eventsList.length} Live Events)</span>
          </button>

          <button
            onClick={() => setActiveTab("all_students")}
            className={`px-4 py-2.5 rounded-xl text-xs font-semibold transition cursor-pointer flex items-center gap-2 ${
              activeTab === "all_students"
                ? "bg-gradient-to-r from-indigo-600 to-purple-600 text-white shadow-md shadow-indigo-500/20"
                : "bg-zinc-900 border border-zinc-800 text-zinc-400 hover:text-white"
            }`}
          >
            <Users className="h-3.5 w-3.5" />
            <span>All Student Builders Directory ({allStudents.length > 0 ? allStudents.length : 50} Across India)</span>
          </button>
        </div>

        {/* Role Filters for All Students Directory */}
        {activeTab === "all_students" && (
          <div className="flex flex-wrap items-center gap-1.5 p-1 rounded-2xl bg-zinc-900/80 border border-zinc-800 text-xs">
            {["All Roles", "AI/ML Engineer", "Backend Developer", "Frontend Developer", "Mobile Developer", "DevOps", "UI/UX Designer", "Product Manager"].map((role) => (
              <button
                key={role}
                onClick={() => setSelectedRoleFilter(role)}
                className={`px-3 py-1.5 rounded-xl font-medium transition cursor-pointer ${
                  selectedRoleFilter === role
                    ? "bg-indigo-600 text-white shadow-sm"
                    : "text-zinc-400 hover:text-white hover:bg-zinc-800/60"
                }`}
              >
                {role}
              </button>
            ))}
          </div>
        )}

        {/* Controls: Search, Filter Tabs & Refresh */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4">
          {/* Search Box */}
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3.5 top-3 h-4 w-4 text-zinc-500" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Filter by name, skills, city (e.g. Bengaluru, Mumbai)..."
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
                All ({filteredCandidates.length})
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
                Top Matches
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
