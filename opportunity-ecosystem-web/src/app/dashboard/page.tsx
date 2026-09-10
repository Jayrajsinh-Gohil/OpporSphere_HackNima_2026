"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import {
  Layers,
  LogOut,
  User,
  Shield,
  Key,
  Users,
  Search,
  Bot,
  ArrowRight,
  Sparkles,
  CheckCircle,
} from "lucide-react";
import { api } from "@/lib/api";

function DashboardContent() {
  const { user, session, signOut } = useAuth();
  const router = useRouter();
  const [profileSummary, setProfileSummary] = useState<string | null>(null);

  useEffect(() => {
    // Attempt fetching student profile from backend using the Bearer token
    if (session) {
      api.student
        .getProfile()
        .then((res) => {
          const profile = res?.data;
          if (profile?.full_name || profile?.name) {
            setProfileSummary(`${profile.full_name || profile.name} (${profile.department || "Student"})`);
          }
        })
        .catch(() => {
          // Backend might not have this test student record yet
          setProfileSummary(user?.user_metadata?.full_name || user?.email || "Student");
        });
    }
  }, [session, user]);

  const handleSignOut = async () => {
    await signOut();
    router.push("/login");
  };

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 flex flex-col">
      {/* Header */}
      <header className="sticky top-0 z-50 backdrop-blur-xl bg-zinc-950/70 border-b border-zinc-800/80 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <Link href="/" className="flex items-center gap-3 group">
            <div className="h-9 w-9 rounded-xl bg-gradient-to-tr from-indigo-500 to-purple-500 flex items-center justify-center shadow-md shadow-indigo-500/20">
              <Layers className="h-5 w-5 text-white" />
            </div>
            <span className="font-bold text-lg text-white">OpporSphere</span>
          </Link>

          <div className="flex items-center gap-4">
            <div className="hidden sm:flex items-center gap-2 px-3 py-1 rounded-lg bg-zinc-900 border border-zinc-800 text-xs text-zinc-300">
              <User className="h-3.5 w-3.5 text-indigo-400" />
              <span>{user?.email}</span>
            </div>

            <button
              onClick={handleSignOut}
              className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-zinc-900 hover:bg-rose-500/10 hover:border-rose-500/30 hover:text-rose-400 border border-zinc-800 text-xs font-medium text-zinc-300 transition cursor-pointer"
            >
              <LogOut className="h-3.5 w-3.5" />
              <span>Sign Out</span>
            </button>
          </div>
        </div>
      </header>

      {/* Main Dashboard Body */}
      <main className="flex-1 max-w-7xl mx-auto w-full px-6 py-10 space-y-8">
        {/* Welcome Banner */}
        <div className="relative rounded-3xl overflow-hidden border border-zinc-800 bg-gradient-to-br from-indigo-950/30 via-zinc-900 to-zinc-950 p-8 flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
          <div className="max-w-2xl space-y-3">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <CheckCircle className="h-3.5 w-3.5" />
              <span>Session Authenticated & Active</span>
            </div>
            <h1 className="text-3xl font-bold text-white tracking-tight">
              Hello, {profileSummary || user?.email?.split("@")[0] || "Explorer"}!
            </h1>
            <p className="text-sm text-zinc-400">
              Welcome to OpporSphere. Explore smart recommendations, connect with hackathon teammates, and get answers from your AI copilot.
            </p>
          </div>

          <Link
            href="/profile/setup"
            className="inline-flex items-center gap-2 px-5 py-3 rounded-2xl bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 text-white font-semibold text-xs shadow-lg shadow-indigo-500/25 hover:opacity-95 transition shrink-0 cursor-pointer"
          >
            <Sparkles className="h-4 w-4" />
            <span>AI Profile Setup & Match Wizard</span>
            <ArrowRight className="h-4 w-4" />
          </Link>
        </div>

        {/* Student Hub Status Card */}
        <div className="rounded-2xl border border-zinc-800/80 bg-zinc-900/40 p-6">
          <div className="flex items-center gap-2 mb-4">
            <Shield className="h-5 w-5 text-indigo-400" />
            <h2 className="font-semibold text-white text-base">Your Student Profile & Match Hub</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 rounded-xl bg-zinc-950 border border-zinc-800">
              <div className="text-xs text-zinc-500 mb-1">Account Status</div>
              <div className="text-xs font-semibold text-emerald-400 flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-full bg-emerald-400" />
                <span>Verified Active Student</span>
              </div>
            </div>

            <div className="p-4 rounded-xl bg-zinc-950 border border-zinc-800">
              <div className="text-xs text-zinc-500 mb-1">Department / Program</div>
              <div className="text-xs font-medium text-zinc-200 truncate">
                {profileSummary ? "Profile Configured" : "Setup In Progress"}
              </div>
            </div>

            <div className="p-4 rounded-xl bg-zinc-950 border border-zinc-800">
              <div className="flex items-center justify-between text-xs text-zinc-500 mb-1">
                <span>AI Recommendation Engine</span>
                <Sparkles className="h-3 w-3 text-indigo-400" />
              </div>
              <div className="text-xs font-medium text-indigo-300">
                Active & Ready
              </div>
            </div>
          </div>
        </div>

        {/* Feature Quick Launch Cards */}
        <div>
          <h2 className="text-lg font-semibold text-white mb-4">Explore AI Modules</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            <Link
              href="/feed"
              className="group rounded-2xl border border-zinc-800 bg-zinc-900/30 p-6 hover:border-indigo-500/40 hover:bg-zinc-900/60 transition block"
            >
              <div className="h-10 w-10 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center mb-4 group-hover:scale-110 transition">
                <Sparkles className="h-5 w-5" />
              </div>
              <h3 className="font-semibold text-white mb-1">Opportunity Feed</h3>
              <p className="text-xs text-zinc-400 mb-4">
                Personalized opportunity feed ranked by AI similarity and trust scores.
              </p>
              <div className="inline-flex items-center gap-1.5 text-xs font-medium text-indigo-400 group-hover:text-indigo-300 transition">
                <span>Explore Matches</span>
                <ArrowRight className="h-3.5 w-3.5" />
              </div>
            </Link>

            <Link
              href="/team-finder"
              className="group rounded-2xl border border-zinc-800 bg-zinc-900/30 p-6 hover:border-indigo-500/40 hover:bg-zinc-900/60 transition block"
            >
              <div className="h-10 w-10 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center mb-4 group-hover:scale-110 transition">
                <Users className="h-5 w-5" />
              </div>
              <h3 className="font-semibold text-white mb-1">AI Team Finder</h3>
              <p className="text-xs text-zinc-400 mb-4">
                Discover matched teammates for upcoming hackathons with role complementarity.
              </p>
              <div className="inline-flex items-center gap-1.5 text-xs font-medium text-indigo-400 group-hover:text-indigo-300 transition">
                <span>Find Teammates</span>
                <ArrowRight className="h-3.5 w-3.5" />
              </div>
            </Link>

            <Link
              href="/discovery"
              className="group rounded-2xl border border-zinc-800 bg-zinc-900/30 p-6 hover:border-purple-500/40 hover:bg-zinc-900/60 transition block"
            >
              <div className="h-10 w-10 rounded-xl bg-purple-500/10 border border-purple-500/20 text-purple-400 flex items-center justify-center mb-4 group-hover:scale-110 transition">
                <Search className="h-5 w-5" />
              </div>
              <h3 className="font-semibold text-white mb-1">Smart Discovery</h3>
              <p className="text-xs text-zinc-400 mb-4">
                Natural-language opportunity search using spaCy NER and pgvector matching.
              </p>
              <div className="inline-flex items-center gap-1.5 text-xs font-medium text-purple-400 group-hover:text-purple-300 transition">
                <span>Search Opportunities</span>
                <ArrowRight className="h-3.5 w-3.5" />
              </div>
            </Link>

            <div className="group rounded-2xl border border-zinc-800 bg-zinc-900/30 p-6 hover:border-pink-500/40 transition">
              <div className="h-10 w-10 rounded-xl bg-pink-500/10 border border-pink-500/20 text-pink-400 flex items-center justify-center mb-4">
                <Bot className="h-5 w-5" />
              </div>
              <h3 className="font-semibold text-white mb-1">Student Copilot</h3>
              <p className="text-xs text-zinc-400 mb-4">
                Grounded conversational assistant answering queries from real event records.
              </p>
              <div className="inline-flex items-center gap-1.5 text-xs font-medium text-pink-400 group-hover:text-pink-300 transition">
                <span>Open Copilot</span>
                <ArrowRight className="h-3.5 w-3.5" />
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

export default function DashboardPage() {
  return (
    <ProtectedRoute>
      <DashboardContent />
    </ProtectedRoute>
  );
}
