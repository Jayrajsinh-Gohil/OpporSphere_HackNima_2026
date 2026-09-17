"use client";

import React, { useState, useEffect, useTransition } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import {
  api,
  AdminMetricsResponse,
  AdminOpportunityItem,
  AdminStudentItem,
  AdminSettingItem,
  AdminRosterItem,
  AdminCreateOpportunityInput,
  AdminMeResponse,
} from "@/lib/api";
import {
  Shield,
  ShieldCheck,
  ShieldAlert,
  Layers,
  LayoutDashboard,
  Briefcase,
  Users,
  Settings,
  Search,
  Plus,
  Trash2,
  ExternalLink,
  Sparkles,
  RefreshCw,
  Cpu,
  Database,
  ArrowRight,
  LogOut,
  Calendar,
  MapPin,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  ChevronRight,
  Filter,
  X,
  Lock,
} from "lucide-react";

function GoogleIcon({ className = "h-5 w-5" }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24">
      <path
        fill="#4285F4"
        d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
      />
      <path
        fill="#34A853"
        d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
      />
      <path
        fill="#FBBC05"
        d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
      />
      <path
        fill="#EA4335"
        d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
      />
    </svg>
  );
}

export default function AdminPage() {
  const router = useRouter();
  const { user, loading: authLoading, signInWithGoogle, signOut } = useAuth();

  // Navigation & State
  const [activeTab, setActiveTab] = useState<"overview" | "opportunities" | "students" | "settings">("overview");
  const [isAdmin, setIsAdmin] = useState<boolean | null>(null);
  const [adminProfile, setAdminProfile] = useState<AdminMeResponse | null>(null);
  const [authError, setAuthError] = useState<string | null>(null);
  const [isVerifying, setIsVerifying] = useState(true);

  // Data states
  const [metrics, setMetrics] = useState<AdminMetricsResponse | null>(null);
  const [loadingMetrics, setLoadingMetrics] = useState(false);

  // Opportunities management
  const [oppItems, setOppItems] = useState<AdminOpportunityItem[]>([]);
  const [oppSearch, setOppSearch] = useState("");
  const [oppDomain, setOppDomain] = useState("all");
  const [oppType, setOppType] = useState("all");
  const [oppTotal, setOppTotal] = useState(0);
  const [loadingOpps, setLoadingOpps] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [actionSuccessMsg, setActionSuccessMsg] = useState<string | null>(null);

  // New opportunity form
  const [newOpp, setNewOpp] = useState<AdminCreateOpportunityInput>({
    title: "",
    description: "",
    domain: "technology",
    type: "hackathon",
    location: "Online / Remote",
    organizer: "",
    deadline: "",
    eligibility: "Open to all university students",
    source_url: "",
  });
  const [creatingOpp, setCreatingOpp] = useState(false);

  // Students management
  const [studentItems, setStudentItems] = useState<AdminStudentItem[]>([]);
  const [studentSearch, setStudentSearch] = useState("");
  const [studentTotal, setStudentTotal] = useState(0);
  const [loadingStudents, setLoadingStudents] = useState(false);

  // Settings & Roster
  const [settingsList, setSettingsList] = useState<AdminSettingItem[]>([]);
  const [rosterList, setRosterList] = useState<AdminRosterItem[]>([]);
  const [updatingSetting, setUpdatingSetting] = useState(false);

  // 1. Verify Admin Status
  useEffect(() => {
    if (authLoading) return;

    if (!user) {
      setIsAdmin(false);
      setIsVerifying(false);
      return;
    }

    const checkAdmin = async () => {
      setIsVerifying(true);
      try {
        // 10-second timeout — prevents "Verifying..." from hanging forever if backend is down
        const timeout = new Promise<never>((_, reject) =>
          setTimeout(() => reject(new Error("Backend not reachable (timeout). Ensure the API server is running.")), 10000)
        );
        const res = await Promise.race([api.admin.me(), timeout]);
        if (res?.data?.is_admin) {
          setIsAdmin(true);
          setAdminProfile(res.data);
          loadMetrics();
        } else {
          setIsAdmin(false);
        }
      } catch (err: unknown) {
        setIsAdmin(false);
        const msg = err instanceof Error ? err.message : "Access denied";
        setAuthError(msg);
      } finally {
        setIsVerifying(false);
      }
    };

    checkAdmin();
  }, [user, authLoading]);

  // Load Metrics
  const loadMetrics = async () => {
    setLoadingMetrics(true);
    try {
      const res = await api.admin.getMetrics();
      if (res?.data) {
        setMetrics(res.data);
      }
    } catch (err) {
      console.error("Failed to load metrics:", err);
    } finally {
      setLoadingMetrics(false);
    }
  };

  // Load Opportunities
  const loadOpportunities = async () => {
    setLoadingOpps(true);
    try {
      const res = await api.admin.getOpportunities({
        q: oppSearch || undefined,
        domain: oppDomain !== "all" ? oppDomain : undefined,
        type: oppType !== "all" ? oppType : undefined,
        page_size: 50,
      });
      if (res?.data) {
        setOppItems(res.data.items);
        setOppTotal(res.data.total);
      }
    } catch (err) {
      console.error("Failed to load opportunities:", err);
    } finally {
      setLoadingOpps(false);
    }
  };

  // Load Students
  const loadStudents = async () => {
    setLoadingStudents(true);
    try {
      const res = await api.admin.getStudents({
        q: studentSearch || undefined,
        page_size: 50,
      });
      if (res?.data) {
        setStudentItems(res.data.items);
        setStudentTotal(res.data.total);
      }
    } catch (err) {
      console.error("Failed to load students:", err);
    } finally {
      setLoadingStudents(false);
    }
  };

  // Load Settings & Roster
  const loadSettingsAndRoster = async () => {
    try {
      const [sRes, rRes] = await Promise.all([
        api.admin.getSettings(),
        api.admin.getRoster(),
      ]);
      if (sRes?.data) setSettingsList(sRes.data);
      if (rRes?.data) setRosterList(rRes.data);
    } catch (err) {
      console.error("Failed to load settings/roster:", err);
    }
  };

  // Fetch data on tab change
  useEffect(() => {
    if (!isAdmin) return;
    if (activeTab === "overview") loadMetrics();
    if (activeTab === "opportunities") loadOpportunities();
    if (activeTab === "students") loadStudents();
    if (activeTab === "settings") loadSettingsAndRoster();
  }, [activeTab, isAdmin]);

  // Handle Create Opportunity
  const handleCreateOpportunity = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreatingOpp(true);
    try {
      await api.admin.createOpportunity(newOpp);
      setShowCreateModal(false);
      setActionSuccessMsg(`Opportunity "${newOpp.title}" created successfully!`);
      setTimeout(() => setActionSuccessMsg(null), 5000);
      setNewOpp({
        title: "",
        description: "",
        domain: "technology",
        type: "hackathon",
        location: "Online / Remote",
        organizer: "",
        deadline: "",
        eligibility: "Open to all university students",
        source_url: "",
      });
      loadOpportunities();
      loadMetrics();
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to create opportunity");
    } finally {
      setCreatingOpp(false);
    }
  };

  // Handle Delete Opportunity
  const handleDeleteOpportunity = async (id: string, title: string) => {
    if (!confirm(`Are you sure you want to delete "${title}"?`)) return;
    try {
      await api.admin.deleteOpportunity(id);
      setActionSuccessMsg(`Opportunity deleted successfully.`);
      setTimeout(() => setActionSuccessMsg(null), 4000);
      loadOpportunities();
      loadMetrics();
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to delete opportunity");
    }
  };

  // Toggle LLM Provider
  const handleToggleLLM = async (newProvider: "gemini" | "ollama") => {
    setUpdatingSetting(true);
    try {
      await api.admin.updateSetting("LLM_PROVIDER", newProvider);
      setActionSuccessMsg(`AI Model provider switched to ${newProvider.toUpperCase()}!`);
      setTimeout(() => setActionSuccessMsg(null), 4000);
      loadSettingsAndRoster();
      loadMetrics();
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to update LLM setting");
    } finally {
      setUpdatingSetting(false);
    }
  };

  // ───────────────────────────────────────────────────────────────────────────
  // Loading screen during verification
  // ───────────────────────────────────────────────────────────────────────────
  if (authLoading || isVerifying) {
    return (
      <div className="min-h-screen bg-black flex flex-col items-center justify-center text-zinc-300">
        <div className="relative">
          <div className="h-16 w-16 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center animate-pulse">
            <Shield className="h-8 w-8 text-indigo-400" />
          </div>
          <div className="absolute -inset-1 rounded-2xl bg-indigo-500/20 blur-xl -z-10" />
        </div>
        <p className="mt-4 text-sm font-medium text-zinc-400">Verifying Admin Credentials...</p>
      </div>
    );
  }

  // ───────────────────────────────────────────────────────────────────────────
  // Unauthenticated screen — OAuth Login Gate
  // ───────────────────────────────────────────────────────────────────────────
  if (!user) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center p-4">
        <div className="relative w-full max-w-md">
          <div className="absolute -inset-1 rounded-3xl bg-gradient-to-r from-indigo-500/30 to-purple-500/30 blur-2xl -z-10" />

          <div className="rounded-2xl border border-zinc-800 bg-zinc-950/90 backdrop-blur-xl p-8 shadow-2xl text-center">
            <div className="h-14 w-14 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center mx-auto mb-6 text-indigo-400">
              <Shield className="h-7 w-7" />
            </div>

            <h1 className="text-2xl font-bold text-white mb-2">OpporSphere Admin Portal</h1>
            <p className="text-sm text-zinc-400 mb-8">
              Sign in with an authorized Google administrator account to access platform metrics, opportunity controls, and system configuration.
            </p>

            <button
              onClick={() => signInWithGoogle("/admin")}
              className="w-full flex items-center justify-center gap-3 px-4 py-3 rounded-xl border border-zinc-700 bg-zinc-900 hover:bg-zinc-800 hover:border-zinc-600 text-white font-medium transition cursor-pointer shadow-lg group"
            >
              <GoogleIcon className="h-5 w-5" />
              <span>Sign in with Google (OAuth)</span>
              <ArrowRight className="h-4 w-4 text-zinc-400 group-hover:translate-x-0.5 transition" />
            </button>

            <div className="mt-6 pt-6 border-t border-zinc-900 flex items-center justify-between text-xs text-zinc-500">
              <Link href="/login" className="hover:text-zinc-300 transition">
                Email/Password Login
              </Link>
              <Link href="/dashboard" className="hover:text-zinc-300 transition">
                Back to App
              </Link>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // ───────────────────────────────────────────────────────────────────────────
  // Unauthorized Screen — Logged in, but not an admin
  // ───────────────────────────────────────────────────────────────────────────
  if (user && isAdmin === false) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center p-4">
        <div className="relative w-full max-w-lg">
          <div className="rounded-2xl border border-red-900/40 bg-zinc-950/90 backdrop-blur-xl p-8 shadow-2xl text-center">
            <div className="h-14 w-14 rounded-2xl bg-red-500/10 border border-red-500/20 flex items-center justify-center mx-auto mb-6 text-red-400">
              <ShieldAlert className="h-7 w-7" />
            </div>

            <h1 className="text-2xl font-bold text-white mb-2">Access Denied</h1>
            <p className="text-sm text-zinc-400 mb-4">
              Your account (<span className="text-zinc-200 font-mono font-medium">{user.email}</span>) is not authorized to access the Admin Portal.
            </p>

            {authError && (
              <div className="mb-4 p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-xs text-red-300 font-mono text-left">
                Detail: {authError}
              </div>
            )}

            <div className="p-4 rounded-xl bg-zinc-900/60 border border-zinc-800/80 text-left text-xs text-zinc-400 mb-6 space-y-1.5">
              <div className="font-semibold text-zinc-300 flex items-center gap-1.5">
                <Lock className="h-3.5 w-3.5 text-amber-400" />
                <span>Security Policy</span>
              </div>
              <p>Only email addresses enrolled in the Supabase <code className="text-pink-300">admins</code> table with role <code className="text-pink-300">admin</code> or <code className="text-pink-300">super_admin</code> are permitted.</p>
            </div>

            <div className="flex flex-col sm:flex-row gap-3">
              <button
                onClick={() => {
                  signOut();
                  router.push("/admin");
                }}
                className="flex-1 px-4 py-2.5 rounded-xl border border-zinc-700 bg-zinc-900 hover:bg-zinc-800 text-white text-sm font-medium transition cursor-pointer"
              >
                Switch Account
              </button>
              <Link
                href="/dashboard"
                className="flex-1 px-4 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white text-sm font-medium transition flex items-center justify-center gap-1.5"
              >
                <span>Return to Dashboard</span>
                <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // ───────────────────────────────────────────────────────────────────────────
  // Authorized Admin Workspace
  // ───────────────────────────────────────────────────────────────────────────
  const activeLLM = metrics?.active_llm_provider || "gemini";

  return (
    <div className="min-h-screen bg-black text-zinc-100 flex flex-col">
      {/* Top Admin Navbar */}
      <header className="sticky top-0 z-30 border-b border-zinc-800/80 bg-zinc-950/80 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link href="/dashboard" className="flex items-center gap-2 group">
              <div className="h-9 w-9 rounded-xl bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 flex items-center justify-center text-white font-bold shadow-md shadow-indigo-500/20">
                <Shield className="h-5 w-5" />
              </div>
              <div>
                <span className="font-bold text-white text-lg tracking-tight group-hover:text-indigo-400 transition">
                  OpporSphere
                </span>
                <span className="ml-2 text-xs font-mono font-semibold px-2 py-0.5 rounded-full bg-indigo-500/10 border border-indigo-500/30 text-indigo-400">
                  ADMIN CONSOLE
                </span>
              </div>
            </Link>
          </div>

          <div className="flex items-center gap-3">
            <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-xl bg-zinc-900 border border-zinc-800 text-xs">
              <div className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
              <span className="text-zinc-300 font-mono">{adminProfile?.email}</span>
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-zinc-800 text-indigo-300 uppercase font-semibold">
                {adminProfile?.role}
              </span>
            </div>

            <Link
              href="/dashboard"
              className="px-3 py-1.5 rounded-xl bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-xs font-medium text-zinc-300 hover:text-white transition"
            >
              Exit to App
            </Link>

            <button
              onClick={() => {
                signOut();
                router.push("/login");
              }}
              className="p-2 rounded-xl bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-zinc-400 hover:text-red-400 transition cursor-pointer"
              title="Sign Out"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex gap-2 border-t border-zinc-900 overflow-x-auto">
          <button
            onClick={() => setActiveTab("overview")}
            className={`flex items-center gap-2 py-3 px-3 text-xs font-medium border-b-2 transition whitespace-nowrap cursor-pointer ${
              activeTab === "overview"
                ? "border-indigo-500 text-white"
                : "border-transparent text-zinc-400 hover:text-zinc-200"
            }`}
          >
            <LayoutDashboard className="h-4 w-4" />
            <span>Overview & KPIs</span>
          </button>

          <button
            onClick={() => setActiveTab("opportunities")}
            className={`flex items-center gap-2 py-3 px-3 text-xs font-medium border-b-2 transition whitespace-nowrap cursor-pointer ${
              activeTab === "opportunities"
                ? "border-indigo-500 text-white"
                : "border-transparent text-zinc-400 hover:text-zinc-200"
            }`}
          >
            <Briefcase className="h-4 w-4" />
            <span>Opportunities ({oppTotal || metrics?.total_opportunities || 0})</span>
          </button>

          <button
            onClick={() => setActiveTab("students")}
            className={`flex items-center gap-2 py-3 px-3 text-xs font-medium border-b-2 transition whitespace-nowrap cursor-pointer ${
              activeTab === "students"
                ? "border-indigo-500 text-white"
                : "border-transparent text-zinc-400 hover:text-zinc-200"
            }`}
          >
            <Users className="h-4 w-4" />
            <span>Student Roster ({studentTotal || metrics?.total_students || 0})</span>
          </button>

          <button
            onClick={() => setActiveTab("settings")}
            className={`flex items-center gap-2 py-3 px-3 text-xs font-medium border-b-2 transition whitespace-nowrap cursor-pointer ${
              activeTab === "settings"
                ? "border-indigo-500 text-white"
                : "border-transparent text-zinc-400 hover:text-zinc-200"
            }`}
          >
            <Cpu className="h-4 w-4" />
            <span>AI & System Settings</span>
          </button>
        </div>
      </header>

      {/* Action Notification Toast */}
      {actionSuccessMsg && (
        <div className="bg-emerald-500/10 border-b border-emerald-500/20 px-4 py-2 text-center text-xs text-emerald-400 font-medium animate-fadeIn">
          {actionSuccessMsg}
        </div>
      )}

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* TAB 1: OVERVIEW & KPIS */}
        {activeTab === "overview" && (
          <div className="space-y-8">
            {/* Top KPI Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="p-5 rounded-2xl border border-zinc-800 bg-zinc-900/40 backdrop-blur-sm">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs font-medium text-zinc-400 uppercase tracking-wider">Registered Students</span>
                  <div className="h-8 w-8 rounded-lg bg-blue-500/10 text-blue-400 flex items-center justify-center">
                    <Users className="h-4 w-4" />
                  </div>
                </div>
                <div className="text-3xl font-bold text-white mb-1">
                  {metrics?.total_students ?? "—"}
                </div>
                <div className="text-xs text-zinc-500">Across Computer Science, AI, & Eng</div>
              </div>

              <div className="p-5 rounded-2xl border border-zinc-800 bg-zinc-900/40 backdrop-blur-sm">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs font-medium text-zinc-400 uppercase tracking-wider">Active Opportunities</span>
                  <div className="h-8 w-8 rounded-lg bg-emerald-500/10 text-emerald-400 flex items-center justify-center">
                    <Briefcase className="h-4 w-4" />
                  </div>
                </div>
                <div className="text-3xl font-bold text-white mb-1">
                  {metrics?.active_opportunities ?? "—"}
                </div>
                <div className="text-xs text-zinc-500">
                  Total published: {metrics?.total_opportunities ?? "—"}
                </div>
              </div>

              <div className="p-5 rounded-2xl border border-zinc-800 bg-zinc-900/40 backdrop-blur-sm">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs font-medium text-zinc-400 uppercase tracking-wider">Active LLM Provider</span>
                  <div className="h-8 w-8 rounded-lg bg-purple-500/10 text-purple-400 flex items-center justify-center">
                    <Cpu className="h-4 w-4" />
                  </div>
                </div>
                <div className="text-2xl font-bold text-white mb-1 capitalize flex items-center gap-2">
                  <span>{activeLLM}</span>
                  <span className="h-2 w-2 rounded-full bg-emerald-400" />
                </div>
                <div className="text-xs text-zinc-500">
                  {activeLLM === "gemini" ? "Google Gemini 2.0 Flash" : "Local Ollama Llama3.2"}
                </div>
              </div>

              <div className="p-5 rounded-2xl border border-zinc-800 bg-zinc-900/40 backdrop-blur-sm">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs font-medium text-zinc-400 uppercase tracking-wider">Platform Admins</span>
                  <div className="h-8 w-8 rounded-lg bg-amber-500/10 text-amber-400 flex items-center justify-center">
                    <ShieldCheck className="h-4 w-4" />
                  </div>
                </div>
                <div className="text-3xl font-bold text-white mb-1">
                  {metrics?.total_admins ?? 1}
                </div>
                <div className="text-xs text-zinc-500">Role-based access enforced</div>
              </div>
            </div>

            {/* Distribution Charts & Quick Actions */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Domain Breakdown */}
              <div className="p-6 rounded-2xl border border-zinc-800 bg-zinc-900/30">
                <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
                  <Layers className="h-4 w-4 text-indigo-400" />
                  <span>Opportunities by Domain</span>
                </h3>
                <div className="space-y-3">
                  {metrics?.domain_distribution && Object.keys(metrics.domain_distribution).length > 0 ? (
                    Object.entries(metrics.domain_distribution).map(([dom, count]) => (
                      <div key={dom} className="space-y-1">
                        <div className="flex justify-between text-xs">
                          <span className="text-zinc-300">{dom}</span>
                          <span className="font-mono text-zinc-400">{count}</span>
                        </div>
                        <div className="h-1.5 w-full rounded-full bg-zinc-800 overflow-hidden">
                          <div
                            className="h-full bg-indigo-500 rounded-full"
                            style={{
                              width: `${Math.min(100, (count / (metrics.total_opportunities || 1)) * 100)}%`,
                            }}
                          />
                        </div>
                      </div>
                    ))
                  ) : (
                    <p className="text-xs text-zinc-500">No domain breakdown available.</p>
                  )}
                </div>
              </div>

              {/* Type Breakdown */}
              <div className="p-6 rounded-2xl border border-zinc-800 bg-zinc-900/30">
                <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
                  <Filter className="h-4 w-4 text-purple-400" />
                  <span>Opportunities by Category</span>
                </h3>
                <div className="space-y-3">
                  {metrics?.type_distribution && Object.keys(metrics.type_distribution).length > 0 ? (
                    Object.entries(metrics.type_distribution).map(([typ, count]) => (
                      <div key={typ} className="space-y-1">
                        <div className="flex justify-between text-xs">
                          <span className="text-zinc-300">{typ}</span>
                          <span className="font-mono text-zinc-400">{count}</span>
                        </div>
                        <div className="h-1.5 w-full rounded-full bg-zinc-800 overflow-hidden">
                          <div
                            className="h-full bg-purple-500 rounded-full"
                            style={{
                              width: `${Math.min(100, (count / (metrics.total_opportunities || 1)) * 100)}%`,
                            }}
                          />
                        </div>
                      </div>
                    ))
                  ) : (
                    <p className="text-xs text-zinc-500">No category breakdown available.</p>
                  )}
                </div>
              </div>

              {/* Quick Actions & AI Switcher */}
              <div className="p-6 rounded-2xl border border-zinc-800 bg-zinc-900/30 flex flex-col justify-between">
                <div>
                  <h3 className="text-sm font-semibold text-white mb-2 flex items-center gap-2">
                    <Sparkles className="h-4 w-4 text-pink-400" />
                    <span>Quick Administration</span>
                  </h3>
                  <p className="text-xs text-zinc-400 mb-6">
                    Manage key configurations and content directly without leaving the dashboard.
                  </p>

                  <div className="space-y-3">
                    <button
                      onClick={() => {
                        setActiveTab("opportunities");
                        setShowCreateModal(true);
                      }}
                      className="w-full flex items-center justify-between px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium transition cursor-pointer"
                    >
                      <span className="flex items-center gap-2">
                        <Plus className="h-4 w-4" />
                        <span>Post New Opportunity</span>
                      </span>
                      <ArrowRight className="h-3.5 w-3.5" />
                    </button>

                    <div className="p-3 rounded-xl border border-zinc-800 bg-zinc-950/60">
                      <div className="text-xs font-semibold text-zinc-300 mb-2">Toggle AI Engine</div>
                      <div className="grid grid-cols-2 gap-2">
                        <button
                          disabled={updatingSetting || activeLLM === "gemini"}
                          onClick={() => handleToggleLLM("gemini")}
                          className={`py-1.5 px-2 rounded-lg text-xs font-medium transition cursor-pointer border ${
                            activeLLM === "gemini"
                              ? "bg-purple-600/30 border-purple-500/50 text-purple-200"
                              : "bg-zinc-900 border-zinc-800 text-zinc-400 hover:text-white"
                          }`}
                        >
                          Gemini 2.0
                        </button>
                        <button
                          disabled={updatingSetting || activeLLM === "ollama"}
                          onClick={() => handleToggleLLM("ollama")}
                          className={`py-1.5 px-2 rounded-lg text-xs font-medium transition cursor-pointer border ${
                            activeLLM === "ollama"
                              ? "bg-purple-600/30 border-purple-500/50 text-purple-200"
                              : "bg-zinc-900 border-zinc-800 text-zinc-400 hover:text-white"
                          }`}
                        >
                          Ollama
                        </button>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="pt-4 border-t border-zinc-800/80 text-[11px] text-zinc-500 flex items-center justify-between">
                  <span>Backend API: Operational</span>
                  <span className="text-emerald-400">● 200 OK</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: OPPORTUNITIES MANAGER */}
        {activeTab === "opportunities" && (
          <div className="space-y-6">
            {/* Action Bar */}
            <div className="flex flex-col sm:flex-row gap-4 items-center justify-between">
              <div className="flex flex-1 w-full sm:w-auto gap-3">
                <div className="relative flex-1">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-500" />
                  <input
                    type="text"
                    placeholder="Search by title, company, or city..."
                    value={oppSearch}
                    onChange={(e) => setOppSearch(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && loadOpportunities()}
                    className="w-full pl-9 pr-4 py-2 rounded-xl bg-zinc-900 border border-zinc-800 text-xs text-white placeholder-zinc-500 focus:outline-none focus:border-indigo-500"
                  />
                </div>

                <select
                  value={oppDomain}
                  onChange={(e) => {
                    setOppDomain(e.target.value);
                  }}
                  className="px-3 py-2 rounded-xl bg-zinc-900 border border-zinc-800 text-xs text-zinc-300 focus:outline-none focus:border-indigo-500 cursor-pointer"
                >
                  <option value="all">All Domains</option>
                  <option value="technology">Technology</option>
                  <option value="science">Science</option>
                  <option value="business">Business</option>
                  <option value="arts">Arts</option>
                </select>

                <select
                  value={oppType}
                  onChange={(e) => {
                    setOppType(e.target.value);
                  }}
                  className="px-3 py-2 rounded-xl bg-zinc-900 border border-zinc-800 text-xs text-zinc-300 focus:outline-none focus:border-indigo-500 cursor-pointer"
                >
                  <option value="all">All Types</option>
                  <option value="hackathon">Hackathons</option>
                  <option value="internship">Internships</option>
                  <option value="fellowship">Fellowships</option>
                  <option value="grant">Grants</option>
                  <option value="competition">Competitions</option>
                </select>

                <button
                  onClick={loadOpportunities}
                  className="px-3 py-2 rounded-xl bg-zinc-800 hover:bg-zinc-700 text-xs font-medium text-white transition cursor-pointer"
                  title="Refresh search"
                >
                  <RefreshCw className={`h-4 w-4 ${loadingOpps ? "animate-spin" : ""}`} />
                </button>
              </div>

              <button
                onClick={() => setShowCreateModal(true)}
                className="w-full sm:w-auto flex items-center justify-center gap-2 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-lg shadow-indigo-600/20 transition cursor-pointer"
              >
                <Plus className="h-4 w-4" />
                <span>Create Opportunity</span>
              </button>
            </div>

            {/* Opportunities Table */}
            <div className="rounded-2xl border border-zinc-800 bg-zinc-900/30 overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-zinc-900/80 text-zinc-400 font-semibold border-b border-zinc-800">
                    <tr>
                      <th className="px-4 py-3">Title & Organizer</th>
                      <th className="px-4 py-3">Domain / Type</th>
                      <th className="px-4 py-3">Location</th>
                      <th className="px-4 py-3">Deadline</th>
                      <th className="px-4 py-3">Status</th>
                      <th className="px-4 py-3 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-zinc-800/60 text-zinc-300">
                    {loadingOpps ? (
                      <tr>
                        <td colSpan={6} className="px-4 py-8 text-center text-zinc-500">
                          Loading opportunities...
                        </td>
                      </tr>
                    ) : oppItems.length === 0 ? (
                      <tr>
                        <td colSpan={6} className="px-4 py-8 text-center text-zinc-500">
                          No opportunities match your search criteria.
                        </td>
                      </tr>
                    ) : (
                      oppItems.map((opp) => (
                        <tr key={opp.id} className="hover:bg-zinc-800/30 transition">
                          <td className="px-4 py-3">
                            <div className="font-semibold text-white truncate max-w-xs">{opp.title}</div>
                            <div className="text-[11px] text-zinc-400">{opp.organizer || "Independent"}</div>
                          </td>
                          <td className="px-4 py-3">
                            <span className="inline-block px-2 py-0.5 rounded text-[10px] font-medium bg-indigo-500/10 text-indigo-300 border border-indigo-500/20 mr-1.5 capitalize">
                              {opp.domain}
                            </span>
                            <span className="inline-block px-2 py-0.5 rounded text-[10px] font-medium bg-zinc-800 text-zinc-300 border border-zinc-700 capitalize">
                              {opp.type}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-zinc-400">{opp.location || "Remote"}</td>
                          <td className="px-4 py-3 font-mono text-zinc-400">
                            {opp.deadline ? new Date(opp.deadline).toLocaleDateString() : "Rolling"}
                          </td>
                          <td className="px-4 py-3">
                            {opp.is_active ? (
                              <span className="inline-flex items-center gap-1 text-[11px] text-emerald-400 font-medium">
                                <CheckCircle2 className="h-3 w-3" />
                                <span>Active</span>
                              </span>
                            ) : (
                              <span className="inline-flex items-center gap-1 text-[11px] text-zinc-500 font-medium">
                                <XCircle className="h-3 w-3" />
                                <span>Closed</span>
                              </span>
                            )}
                          </td>
                          <td className="px-4 py-3 text-right">
                            <div className="inline-flex items-center gap-2">
                              {opp.source_url && (
                                <a
                                  href={opp.source_url}
                                  target="_blank"
                                  rel="noreferrer"
                                  className="p-1.5 rounded-lg bg-zinc-800/80 hover:bg-zinc-700 text-zinc-400 hover:text-white transition"
                                  title="Open Source Link"
                                >
                                  <ExternalLink className="h-3.5 w-3.5" />
                                </a>
                              )}
                              <button
                                onClick={() => handleDeleteOpportunity(opp.id, opp.title)}
                                className="p-1.5 rounded-lg bg-red-500/10 hover:bg-red-500/20 border border-red-500/20 text-red-400 transition cursor-pointer"
                                title="Delete Opportunity"
                              >
                                <Trash2 className="h-3.5 w-3.5" />
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* TAB 3: STUDENT DIRECTORY */}
        {activeTab === "students" && (
          <div className="space-y-6">
            {/* Search Bar */}
            <div className="flex gap-3">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-500" />
                <input
                  type="text"
                  placeholder="Search students by name, email, department, skills, or city..."
                  value={studentSearch}
                  onChange={(e) => setStudentSearch(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && loadStudents()}
                  className="w-full pl-9 pr-4 py-2 rounded-xl bg-zinc-900 border border-zinc-800 text-xs text-white placeholder-zinc-500 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <button
                onClick={loadStudents}
                className="px-4 py-2 rounded-xl bg-zinc-800 hover:bg-zinc-700 text-xs font-medium text-white transition flex items-center gap-2 cursor-pointer"
              >
                <RefreshCw className={`h-4 w-4 ${loadingStudents ? "animate-spin" : ""}`} />
                <span>Search</span>
              </button>
            </div>

            {/* Students Table */}
            <div className="rounded-2xl border border-zinc-800 bg-zinc-900/30 overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-zinc-900/80 text-zinc-400 font-semibold border-b border-zinc-800">
                    <tr>
                      <th className="px-4 py-3">Student</th>
                      <th className="px-4 py-3">Department / University</th>
                      <th className="px-4 py-3">Location</th>
                      <th className="px-4 py-3">Primary Skills</th>
                      <th className="px-4 py-3">Joined</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-zinc-800/60 text-zinc-300">
                    {loadingStudents ? (
                      <tr>
                        <td colSpan={5} className="px-4 py-8 text-center text-zinc-500">
                          Loading student records...
                        </td>
                      </tr>
                    ) : studentItems.length === 0 ? (
                      <tr>
                        <td colSpan={5} className="px-4 py-8 text-center text-zinc-500">
                          No students found.
                        </td>
                      </tr>
                    ) : (
                      studentItems.map((st) => (
                        <tr key={st.id} className="hover:bg-zinc-800/30 transition">
                          <td className="px-4 py-3">
                            <div className="font-semibold text-white">{st.name || "Student"}</div>
                            <div className="text-[11px] font-mono text-zinc-400">{st.email}</div>
                          </td>
                          <td className="px-4 py-3 text-zinc-300">{st.department || "Engineering"}</td>
                          <td className="px-4 py-3 text-zinc-400">{st.location || "India"}</td>
                          <td className="px-4 py-3">
                            <div className="flex flex-wrap gap-1 max-w-xs">
                              {st.skills && st.skills.length > 0 ? (
                                st.skills.slice(0, 3).map((sk) => (
                                  <span
                                    key={sk}
                                    className="px-1.5 py-0.5 rounded text-[10px] bg-indigo-500/10 text-indigo-300 border border-indigo-500/20"
                                  >
                                    {sk}
                                  </span>
                                ))
                              ) : (
                                <span className="text-zinc-500">—</span>
                              )}
                              {st.skills && st.skills.length > 3 && (
                                <span className="text-[10px] text-zinc-500">+{st.skills.length - 3}</span>
                              )}
                            </div>
                          </td>
                          <td className="px-4 py-3 font-mono text-zinc-500 text-[11px]">
                            {new Date(st.created_at).toLocaleDateString()}
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* TAB 4: AI & SYSTEM SETTINGS */}
        {activeTab === "settings" && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Live LLM Configuration */}
            <div className="p-6 rounded-2xl border border-zinc-800 bg-zinc-900/30 space-y-6">
              <div>
                <h3 className="text-base font-semibold text-white mb-1 flex items-center gap-2">
                  <Cpu className="h-5 w-5 text-indigo-400" />
                  <span>AI Engine Runtime Configuration</span>
                </h3>
                <p className="text-xs text-zinc-400">
                  Switch the LLM provider live in Supabase. Changes take effect on the very next AI request without restarting the server.
                </p>
              </div>

              <div className="space-y-4">
                <div className="p-4 rounded-xl border border-zinc-800 bg-zinc-950/60 flex items-center justify-between">
                  <div>
                    <div className="font-semibold text-sm text-white">Google Gemini 2.0 Flash</div>
                    <div className="text-xs text-zinc-400">Cloud AI: Fast, high-accuracy semantic embeddings & chat</div>
                  </div>
                  <button
                    disabled={updatingSetting || activeLLM === "gemini"}
                    onClick={() => handleToggleLLM("gemini")}
                    className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition cursor-pointer border ${
                      activeLLM === "gemini"
                        ? "bg-emerald-500/20 border-emerald-500/40 text-emerald-300"
                        : "bg-zinc-800 hover:bg-zinc-700 border-zinc-700 text-zinc-300"
                    }`}
                  >
                    {activeLLM === "gemini" ? "ACTIVE" : "Select Gemini"}
                  </button>
                </div>

                <div className="p-4 rounded-xl border border-zinc-800 bg-zinc-950/60 flex items-center justify-between">
                  <div>
                    <div className="font-semibold text-sm text-white">Local Ollama (Llama 3.2:3b)</div>
                    <div className="text-xs text-zinc-400">On-device privacy: Local inference without cloud cost</div>
                  </div>
                  <button
                    disabled={updatingSetting || activeLLM === "ollama"}
                    onClick={() => handleToggleLLM("ollama")}
                    className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition cursor-pointer border ${
                      activeLLM === "ollama"
                        ? "bg-emerald-500/20 border-emerald-500/40 text-emerald-300"
                        : "bg-zinc-800 hover:bg-zinc-700 border-zinc-700 text-zinc-300"
                    }`}
                  >
                    {activeLLM === "ollama" ? "ACTIVE" : "Select Ollama"}
                  </button>
                </div>
              </div>

              {/* Settings Table */}
              <div className="pt-4 border-t border-zinc-800">
                <h4 className="text-xs font-semibold text-zinc-300 mb-3 flex items-center gap-1.5">
                  <Database className="h-3.5 w-3.5 text-zinc-400" />
                  <span>Database Key-Value Store (`app_settings`)</span>
                </h4>
                <div className="rounded-xl border border-zinc-800 bg-zinc-950/40 overflow-hidden">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-zinc-900/60 text-zinc-400 border-b border-zinc-800">
                      <tr>
                        <th className="px-3 py-2">Key</th>
                        <th className="px-3 py-2">Value</th>
                        <th className="px-3 py-2">Description</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-zinc-800/40 font-mono text-[11px]">
                      {settingsList.map((stg) => (
                        <tr key={stg.key} className="text-zinc-300">
                          <td className="px-3 py-2 text-indigo-400">{stg.key}</td>
                          <td className="px-3 py-2 text-emerald-300 font-bold">{stg.value}</td>
                          <td className="px-3 py-2 text-zinc-500 font-sans">{stg.description}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>

            {/* Platform Administrators Roster */}
            <div className="p-6 rounded-2xl border border-zinc-800 bg-zinc-900/30 space-y-6">
              <div>
                <h3 className="text-base font-semibold text-white mb-1 flex items-center gap-2">
                  <ShieldCheck className="h-5 w-5 text-emerald-400" />
                  <span>Platform Administrators Roster</span>
                </h3>
                <p className="text-xs text-zinc-400">
                  Accounts configured in Supabase with administrative permissions for OpporSphere.
                </p>
              </div>

              <div className="rounded-xl border border-zinc-800 bg-zinc-950/40 overflow-hidden">
                <table className="w-full text-left text-xs">
                  <thead className="bg-zinc-900/60 text-zinc-400 border-b border-zinc-800">
                    <tr>
                      <th className="px-4 py-2.5">Email</th>
                      <th className="px-4 py-2.5">Role</th>
                      <th className="px-4 py-2.5">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-zinc-800/40 text-zinc-300">
                    {rosterList.map((adm) => (
                      <tr key={adm.id}>
                        <td className="px-4 py-3 font-mono text-white">{adm.email}</td>
                        <td className="px-4 py-3">
                          <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-indigo-500/10 text-indigo-300 border border-indigo-500/30 uppercase">
                            {adm.role}
                          </span>
                        </td>
                        <td className="px-4 py-3">
                          <span className="inline-flex items-center gap-1 text-[11px] text-emerald-400 font-medium">
                            <CheckCircle2 className="h-3 w-3" />
                            <span>Active</span>
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="p-4 rounded-xl border border-zinc-800 bg-zinc-900/40 text-xs text-zinc-400 space-y-2">
                <div className="font-semibold text-zinc-300">To Add More Admins:</div>
                <p>
                  Execute an insert statement in your Supabase SQL Editor:
                </p>
                <code className="block p-2 rounded-lg bg-black text-[11px] font-mono text-emerald-400">
                  INSERT INTO admins (email, role) VALUES ('colleague@gmail.com', 'admin');
                </code>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* CREATE OPPORTUNITY MODAL */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="relative w-full max-w-lg rounded-2xl border border-zinc-800 bg-zinc-950 p-6 shadow-2xl">
            <div className="flex items-center justify-between pb-4 border-b border-zinc-800 mb-4">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <Plus className="h-4 w-4 text-indigo-400" />
                <span>Post New Opportunity</span>
              </h3>
              <button
                onClick={() => setShowCreateModal(false)}
                className="p-1 rounded-lg text-zinc-400 hover:text-white transition cursor-pointer"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <form onSubmit={handleCreateOpportunity} className="space-y-4 text-xs">
              <div>
                <label className="block text-zinc-400 font-medium mb-1">Opportunity Title *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Smart India AI Innovation Challenge 2026"
                  value={newOpp.title}
                  onChange={(e) => setNewOpp({ ...newOpp, title: e.target.value })}
                  className="w-full px-3 py-2 rounded-xl bg-zinc-900 border border-zinc-800 text-white placeholder-zinc-500 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-zinc-400 font-medium mb-1">Description *</label>
                <textarea
                  required
                  rows={3}
                  placeholder="Detailed overview of the opportunity, tracks, and requirements..."
                  value={newOpp.description}
                  onChange={(e) => setNewOpp({ ...newOpp, description: e.target.value })}
                  className="w-full px-3 py-2 rounded-xl bg-zinc-900 border border-zinc-800 text-white placeholder-zinc-500 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-zinc-400 font-medium mb-1">Domain *</label>
                  <select
                    value={newOpp.domain}
                    onChange={(e) => setNewOpp({ ...newOpp, domain: e.target.value })}
                    className="w-full px-3 py-2 rounded-xl bg-zinc-900 border border-zinc-800 text-zinc-300 focus:outline-none focus:border-indigo-500"
                  >
                    <option value="technology">Technology</option>
                    <option value="science">Science</option>
                    <option value="business">Business</option>
                    <option value="arts">Arts</option>
                    <option value="other">Other</option>
                  </select>
                </div>

                <div>
                  <label className="block text-zinc-400 font-medium mb-1">Type *</label>
                  <select
                    value={newOpp.type}
                    onChange={(e) => setNewOpp({ ...newOpp, type: e.target.value })}
                    className="w-full px-3 py-2 rounded-xl bg-zinc-900 border border-zinc-800 text-zinc-300 focus:outline-none focus:border-indigo-500"
                  >
                    <option value="hackathon">Hackathon</option>
                    <option value="internship">Internship</option>
                    <option value="fellowship">Fellowship</option>
                    <option value="grant">Grant</option>
                    <option value="competition">Competition</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-zinc-400 font-medium mb-1">Organizer</label>
                  <input
                    type="text"
                    placeholder="e.g. Google Cloud / Microsoft"
                    value={newOpp.organizer}
                    onChange={(e) => setNewOpp({ ...newOpp, organizer: e.target.value })}
                    className="w-full px-3 py-2 rounded-xl bg-zinc-900 border border-zinc-800 text-white placeholder-zinc-500 focus:outline-none focus:border-indigo-500"
                  />
                </div>

                <div>
                  <label className="block text-zinc-400 font-medium mb-1">Location</label>
                  <input
                    type="text"
                    placeholder="e.g. Bengaluru / Online"
                    value={newOpp.location}
                    onChange={(e) => setNewOpp({ ...newOpp, location: e.target.value })}
                    className="w-full px-3 py-2 rounded-xl bg-zinc-900 border border-zinc-800 text-white placeholder-zinc-500 focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-zinc-400 font-medium mb-1">Deadline Date</label>
                  <input
                    type="date"
                    value={newOpp.deadline}
                    onChange={(e) => setNewOpp({ ...newOpp, deadline: e.target.value })}
                    className="w-full px-3 py-2 rounded-xl bg-zinc-900 border border-zinc-800 text-white placeholder-zinc-500 focus:outline-none focus:border-indigo-500"
                  />
                </div>

                <div>
                  <label className="block text-zinc-400 font-medium mb-1">Official Website URL</label>
                  <input
                    type="url"
                    placeholder="https://..."
                    value={newOpp.source_url}
                    onChange={(e) => setNewOpp({ ...newOpp, source_url: e.target.value })}
                    className="w-full px-3 py-2 rounded-xl bg-zinc-900 border border-zinc-800 text-white placeholder-zinc-500 focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>

              <div className="pt-4 border-t border-zinc-800 flex justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 rounded-xl border border-zinc-700 bg-zinc-900 hover:bg-zinc-800 text-zinc-300 font-medium transition cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creatingOpp}
                  className="px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold transition cursor-pointer flex items-center gap-2 shadow-lg shadow-indigo-600/20"
                >
                  {creatingOpp ? (
                    <>
                      <RefreshCw className="h-4 w-4 animate-spin" />
                      <span>Embedding & Saving...</span>
                    </>
                  ) : (
                    <span>Publish Opportunity</span>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
