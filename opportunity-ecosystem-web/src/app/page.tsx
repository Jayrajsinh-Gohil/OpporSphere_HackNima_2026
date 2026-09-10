"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  Sparkles,
  Users,
  Search,
  Bot,
  Layers,
  ArrowRight,
  ShieldCheck,
  CheckCircle2,
  LogIn,
  UserPlus,
  LayoutDashboard,
  Award,
  Zap,
  Compass,
} from "lucide-react";
import { api } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";

export default function Home() {
  const { user, signOut } = useAuth();
  const [apiStatus, setApiStatus] = useState<"checking" | "online" | "offline">("checking");
  const [searchQuery, setSearchQuery] = useState("");

  const checkConnection = async () => {
    setApiStatus("checking");
    try {
      await api.health();
      setApiStatus("online");
    } catch {
      setApiStatus("offline");
    }
  };

  useEffect(() => {
    checkConnection();
  }, []);

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 flex flex-col selection:bg-indigo-500 selection:text-white">
      {/* Top Navigation */}
      <header className="sticky top-0 z-50 backdrop-blur-xl bg-zinc-950/70 border-b border-zinc-800/80 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-indigo-500 via-purple-500 to-pink-500 flex items-center justify-center shadow-lg shadow-indigo-500/20">
              <Layers className="h-5 w-5 text-white" />
            </div>
            <div>
              <span className="font-bold text-lg tracking-tight bg-gradient-to-r from-white via-zinc-200 to-zinc-400 bg-clip-text text-transparent">
                OpporSphere
              </span>
            </div>
          </div>

          <nav className="hidden md:flex items-center gap-6 text-sm text-zinc-400">
            <Link
              href="/discovery"
              className="text-zinc-400 hover:text-white transition flex items-center gap-1.5"
            >
              <Search className="h-4 w-4 text-purple-400" />
              <span>Discover</span>
            </Link>
            <Link
              href="/feed"
              className="text-zinc-400 hover:text-white transition flex items-center gap-1.5"
            >
              <Sparkles className="h-4 w-4 text-indigo-400" />
              <span>Match Feed</span>
            </Link>
            <Link
              href="/team-finder"
              className="text-zinc-400 hover:text-white transition flex items-center gap-1.5"
            >
              <Users className="h-4 w-4 text-pink-400" />
              <span>Team Finder</span>
            </Link>
          </nav>

          <div className="flex items-center gap-3">
            <div
              className={`hidden sm:flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium border ${
                apiStatus === "online"
                  ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                  : apiStatus === "checking"
                  ? "bg-amber-500/10 text-amber-400 border-amber-500/30"
                  : "bg-zinc-800/60 text-zinc-400 border-zinc-700/40"
              }`}
            >
              <span
                className={`h-2 w-2 rounded-full ${
                  apiStatus === "online"
                    ? "bg-emerald-400 animate-pulse"
                    : apiStatus === "checking"
                    ? "bg-amber-400 animate-ping"
                    : "bg-zinc-400"
                }`}
              />
              {apiStatus === "online" ? "Live Services Active" : apiStatus === "checking" ? "Connecting..." : "Live"}
            </div>

            {user ? (
              <div className="flex items-center gap-2">
                <Link
                  href="/dashboard"
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-600/20 border border-indigo-500/30 text-indigo-300 text-xs font-medium hover:bg-indigo-600/30 transition"
                >
                  <LayoutDashboard className="h-3.5 w-3.5" />
                  <span>Dashboard</span>
                </Link>
                <button
                  onClick={() => signOut()}
                  className="text-xs px-2.5 py-1.5 rounded-lg bg-zinc-900 border border-zinc-800 text-zinc-400 hover:text-white transition cursor-pointer"
                >
                  Sign Out
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <Link
                  href="/login"
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-zinc-300 text-xs font-medium transition"
                >
                  <LogIn className="h-3.5 w-3.5" />
                  <span>Sign In</span>
                </Link>
                <Link
                  href="/signup"
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white text-xs font-medium shadow-md shadow-indigo-500/20 transition"
                >
                  <UserPlus className="h-3.5 w-3.5" />
                  <span>Get Started</span>
                </Link>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <main className="flex-1 max-w-7xl mx-auto w-full px-6 py-12 flex flex-col gap-12">
        <div className="relative rounded-3xl overflow-hidden border border-zinc-800/80 bg-gradient-to-b from-zinc-900/80 to-zinc-950 p-8 sm:p-14 shadow-2xl">
          {/* Ambient glowing orbs */}
          <div className="absolute -top-32 -left-32 h-96 w-96 rounded-full bg-indigo-600/20 blur-3xl pointer-events-none" />
          <div className="absolute -bottom-32 -right-32 h-96 w-96 rounded-full bg-purple-600/20 blur-3xl pointer-events-none" />

          <div className="relative z-10 max-w-3xl space-y-6">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-indigo-500/10 text-indigo-300 border border-indigo-500/20">
              <Sparkles className="h-3.5 w-3.5 text-indigo-400" />
              <span>Verified Campus Opportunities & AI Matching</span>
            </div>

            <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight text-white leading-tight">
              Unlock Your Campus Journey with{" "}
              <span className="bg-gradient-to-r from-indigo-400 via-purple-300 to-pink-400 bg-clip-text text-transparent">
                Next-Gen AI Intelligence
              </span>
            </h1>

            <p className="text-lg text-zinc-400 leading-relaxed max-w-2xl">
              Discover high-impact hackathons, internships, and fellowships tailored to your skills.
              Form winning teams with AI compatibility matching and get instant answers with your Student Copilot.
            </p>

            {/* Quick Actions / Search Bar */}
            <div className="flex flex-col sm:flex-row gap-3 pt-4">
              <div className="relative flex-1">
                <Search className="absolute left-4 top-3.5 h-5 w-5 text-zinc-500" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="e.g., 'hackathons in Bangalore next month for CS'..."
                  className="w-full rounded-xl bg-zinc-900/90 border border-zinc-700/70 pl-12 pr-4 py-3 text-sm text-zinc-100 placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition"
                />
              </div>
              <button
                onClick={() => {
                  const targetQuery = searchQuery.trim() || "hackathons in Bangalore next month for CS";
                  window.location.href = `/discovery?q=${encodeURIComponent(targetQuery)}`;
                }}
                className="inline-flex items-center justify-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-indigo-500 to-purple-600 font-semibold text-sm text-white shadow-lg shadow-indigo-500/25 hover:from-indigo-600 hover:to-purple-700 transition cursor-pointer"
              >
                <span>AI Search</span>
                <ArrowRight className="h-4 w-4" />
              </button>
            </div>

            <div className="flex flex-wrap items-center gap-3 pt-2">
              <Link
                href={user ? "/dashboard" : "/signup"}
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-zinc-800 hover:bg-zinc-700 text-sm font-medium text-white transition border border-zinc-700/50"
              >
                <span>{user ? "View Student Dashboard" : "Create Free Account"}</span>
                <ArrowRight className="h-4 w-4" />
              </Link>
              {!user && (
                <Link
                  href="/login"
                  className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-medium text-zinc-300 hover:text-white transition"
                >
                  <span>Already registered? Sign In</span>
                </Link>
              )}
            </div>
          </div>
        </div>

        {/* Feature Grid */}
        <section className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Card 1: Team Finder */}
          <Link
            href="/team-finder"
            className="group rounded-2xl border border-zinc-800 bg-zinc-900/40 p-6 transition hover:border-indigo-500/40 hover:bg-zinc-900/70 block cursor-pointer"
          >
            <div className="h-12 w-12 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center mb-5 group-hover:scale-110 transition-transform">
              <Users className="h-6 w-6" />
            </div>
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-semibold text-lg text-white">AI Team Finder</h3>
              <span className="text-xs px-2.5 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 font-medium">
                Team Synergy
              </span>
            </div>
            <p className="text-sm text-zinc-400 leading-relaxed mb-4">
              Compatibility matching using cosine similarity over skill embeddings, complementary role bonuses, and AI-drafted team invitation messages.
            </p>
            <div className="flex flex-wrap gap-1.5 pt-1">
              <span className="text-[11px] px-2.5 py-1 rounded-md bg-zinc-950 text-zinc-400 border border-zinc-800">
                Complementary Roles
              </span>
              <span className="text-[11px] px-2.5 py-1 rounded-md bg-zinc-950 text-zinc-400 border border-zinc-800">
                Skill Matching
              </span>
            </div>
          </Link>

          {/* Card 2: Smart Discovery */}
          <Link
            href="/discovery"
            className="group rounded-2xl border border-zinc-800 bg-zinc-900/40 p-6 transition hover:border-purple-500/40 hover:bg-zinc-900/70 block cursor-pointer"
          >
            <div className="h-12 w-12 rounded-xl bg-purple-500/10 border border-purple-500/20 text-purple-400 flex items-center justify-center mb-5 group-hover:scale-110 transition-transform">
              <Search className="h-6 w-6" />
            </div>
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-semibold text-lg text-white">Smart Discovery</h3>
              <span className="text-xs px-2.5 py-0.5 rounded-full bg-purple-500/10 text-purple-400 border border-purple-500/20 font-medium">
                Natural Language
              </span>
            </div>
            <p className="text-sm text-zinc-400 leading-relaxed mb-4">
              Extracts domain, location, department, and timeframes using advanced NLP. Seamlessly matches opportunities across nationwide events.
            </p>
            <div className="flex flex-wrap gap-1.5 pt-1">
              <span className="text-[11px] px-2.5 py-1 rounded-md bg-zinc-950 text-zinc-400 border border-zinc-800">
                Semantic Search
              </span>
              <span className="text-[11px] px-2.5 py-1 rounded-md bg-zinc-950 text-zinc-400 border border-zinc-800">
                Location & Deadline
              </span>
            </div>
          </Link>

          {/* Card 3: AI Copilot */}
          <div className="group rounded-2xl border border-zinc-800 bg-zinc-900/40 p-6 transition hover:border-pink-500/40 hover:bg-zinc-900/70">
            <div className="h-12 w-12 rounded-xl bg-pink-500/10 border border-pink-500/20 text-pink-400 flex items-center justify-center mb-5 group-hover:scale-110 transition-transform">
              <Bot className="h-6 w-6" />
            </div>
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-semibold text-lg text-white">Student Copilot</h3>
              <span className="text-xs px-2.5 py-0.5 rounded-full bg-pink-500/10 text-pink-400 border border-pink-500/20 font-medium">
                Verified Answers
              </span>
            </div>
            <p className="text-sm text-zinc-400 leading-relaxed mb-4">
              Grounded conversational assistant answering queries from real event records with source citations and strict anti-hallucination safeguards.
            </p>
            <div className="flex flex-wrap gap-1.5 pt-1">
              <span className="text-[11px] px-2.5 py-1 rounded-md bg-zinc-950 text-zinc-400 border border-zinc-800">
                Event Citations
              </span>
              <span className="text-[11px] px-2.5 py-1 rounded-md bg-zinc-950 text-zinc-400 border border-zinc-800">
                24/7 Guidance
              </span>
            </div>
          </div>
        </section>

        {/* Platform Trust & Impact Highlights */}
        <section className="rounded-2xl border border-zinc-800 bg-zinc-900/30 p-8 sm:p-10">
          <div className="max-w-3xl mb-8">
            <h2 className="text-2xl font-bold text-white tracking-tight">Built for College Innovators</h2>
            <p className="text-sm text-zinc-400 mt-1">
              A curated platform designed to eliminate the noise and connect students with genuine opportunities.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="p-5 rounded-xl bg-zinc-950/60 border border-zinc-800/80 space-y-2">
              <div className="flex items-center gap-2.5 text-indigo-400">
                <ShieldCheck className="h-5 w-5" />
                <span className="text-sm font-semibold text-white">Verified Listings</span>
              </div>
              <p className="text-xs text-zinc-400 leading-relaxed">
                Automated trust scoring and quality verification filter out duplicate or misleading postings.
              </p>
            </div>

            <div className="p-5 rounded-xl bg-zinc-950/60 border border-zinc-800/80 space-y-2">
              <div className="flex items-center gap-2.5 text-purple-400">
                <Zap className="h-5 w-5" />
                <span className="text-sm font-semibold text-white">Personalized Matching</span>
              </div>
              <p className="text-xs text-zinc-400 leading-relaxed">
                Smart vector matching pairs you with opportunities that align with your specific skills and interests.
              </p>
            </div>

            <div className="p-5 rounded-xl bg-zinc-950/60 border border-zinc-800/80 space-y-2">
              <div className="flex items-center gap-2.5 text-pink-400">
                <Award className="h-5 w-5" />
                <span className="text-sm font-semibold text-white">Career Acceleration</span>
              </div>
              <p className="text-xs text-zinc-400 leading-relaxed">
                From hackathon victories to research grants, find the exact milestone that boosts your career.
              </p>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-zinc-800/80 px-6 py-6 text-center text-xs text-zinc-500">
        OpporSphere — Empowering students and professionals to discover, collaborate, and compete.
      </footer>
    </div>
  );
}
