"use client";

import React, { useState, Suspense } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import {
  Layers,
  Mail,
  Lock,
  User,
  GraduationCap,
  Eye,
  EyeOff,
  ArrowRight,
  AlertCircle,
  CheckCircle2,
  Loader2,
  Sparkles,
} from "lucide-react";

const DEPARTMENTS = [
  "Computer Science & Engineering",
  "Artificial Intelligence & Data Science",
  "Information Technology",
  "Electronics & Communication",
  "Electrical & Electronics",
  "Mechanical Engineering",
  "Biotechnology",
  "Business Administration / Management",
  "Other",
];

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

function SignupForm() {
  const router = useRouter();
  const { signUp, signInWithGoogle } = useAuth();

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [department, setDepartment] = useState(DEPARTMENTS[0]);
  const [showPassword, setShowPassword] = useState(false);

  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isGoogleLoading, setIsGoogleLoading] = useState(false);
  const [showManualForm, setShowManualForm] = useState(false);

  const handleGoogleSignUp = async () => {
    setErrorMsg(null);
    setIsGoogleLoading(true);
    try {
      const { error } = await signInWithGoogle("/dashboard");
      if (error) {
        setErrorMsg(error.message || "Failed to initiate Google sign up.");
        setIsGoogleLoading(false);
      }
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : "Google registration failed.");
      setIsGoogleLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setSuccessMsg(null);

    if (!fullName || !email || !password) {
      setErrorMsg("Please complete all required fields.");
      return;
    }

    if (password.length < 6) {
      setErrorMsg("Password must be at least 6 characters long.");
      return;
    }

    setIsLoading(true);
    try {
      const { user, session, error } = await signUp(email, password, {
        full_name: fullName,
        department,
      });

      if (error) {
        setErrorMsg(error.message);
      } else if (session) {
        router.push("/dashboard");
        router.refresh();
      } else if (user && !session) {
        setSuccessMsg(
          "Account created successfully! Please check your email to verify your account before logging in."
        );
      } else {
        router.push("/dashboard");
      }
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : "Registration failed.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="w-full max-w-lg">
      {/* Brand Header */}
      <div className="text-center mb-8">
        <Link href="/" className="inline-flex items-center gap-2 mb-4 group">
          <div className="h-11 w-11 rounded-xl bg-gradient-to-tr from-indigo-500 via-purple-500 to-pink-500 flex items-center justify-center shadow-lg shadow-indigo-500/25 group-hover:scale-105 transition">
            <Layers className="h-6 w-6 text-white" />
          </div>
          <span className="font-bold text-xl tracking-tight text-white">
            OpporSphere
          </span>
        </Link>
        <h1 className="text-2xl font-bold text-white tracking-tight">Create Student Account</h1>
        <p className="text-sm text-zinc-400 mt-1">
          Join thousands of students matching for hackathons, research, and internships
        </p>
      </div>

      {/* Signup Card */}
      <div className="rounded-2xl border border-zinc-800/80 bg-zinc-900/70 backdrop-blur-xl p-8 shadow-2xl">
        {errorMsg && (
          <div className="mb-6 p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-sm flex items-start gap-3">
            <AlertCircle className="h-5 w-5 shrink-0 mt-0.5" />
            <div className="leading-snug">{errorMsg}</div>
          </div>
        )}

        {/* PRIMARY AUTH ACTION: GOOGLE SIGN-UP */}
        <div className="space-y-4">
          <button
            type="button"
            onClick={handleGoogleSignUp}
            disabled={isGoogleLoading || isLoading}
            className="w-full relative flex items-center justify-center gap-3 px-5 py-3.5 rounded-xl bg-white text-zinc-900 font-semibold text-sm shadow-xl shadow-indigo-500/10 hover:bg-zinc-100 active:scale-[0.99] transition disabled:opacity-60 disabled:cursor-not-allowed cursor-pointer"
          >
            {isGoogleLoading ? (
              <>
                <Loader2 className="h-5 w-5 animate-spin text-zinc-700" />
                <span>Connecting to Google...</span>
              </>
            ) : (
              <>
                <GoogleIcon className="h-5 w-5" />
                <span>Sign up with Google</span>
              </>
            )}
          </button>
          <p className="text-center text-xs text-zinc-500">
            No password required. Instant verified profile via your Google account.
          </p>
        </div>

        {/* Secondary Divider / Toggle */}
        <div className="relative my-6">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-zinc-800" />
          </div>
          <div className="relative flex justify-center text-xs uppercase">
            <button
              type="button"
              onClick={() => setShowManualForm(!showManualForm)}
              className="bg-zinc-900 px-3 text-zinc-500 hover:text-zinc-300 transition flex items-center gap-1.5 cursor-pointer"
            >
              <span>{showManualForm ? "Hide manual registration" : "Or register with email"}</span>
            </button>
          </div>
        </div>

        {/* Success message if confirmation email required */}
        {successMsg && (
          <div className="text-center py-6 space-y-4">
            <div className="h-14 w-14 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center mx-auto">
              <CheckCircle2 className="h-7 w-7" />
            </div>
            <h3 className="text-lg font-semibold text-white">Check Your Inbox</h3>
            <p className="text-sm text-zinc-400 max-w-sm mx-auto">{successMsg}</p>
            <div className="pt-2">
              <Link
                href="/login"
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-zinc-800 hover:bg-zinc-700 text-sm font-medium text-white transition"
              >
                <span>Return to Login</span>
                <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
          </div>
        )}

        {/* MANUAL EMAIL/PASSWORD REGISTRATION */}
        {showManualForm && !successMsg && (
          <form onSubmit={handleSubmit} className="space-y-4 pt-1 animate-in fade-in duration-200">
            {/* Full Name */}
            <div>
              <label className="block text-xs font-medium text-zinc-300 mb-1.5" htmlFor="name">
                Full Name
              </label>
              <div className="relative">
                <User className="absolute left-3.5 top-3 h-4 w-4 text-zinc-500" />
                <input
                  id="name"
                  type="text"
                  required
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="e.g. Alex Sharma"
                  className="w-full rounded-xl bg-zinc-950/70 border border-zinc-800 pl-10 pr-4 py-2.5 text-sm text-zinc-100 placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition"
                />
              </div>
            </div>

            {/* Email Field */}
            <div>
              <label className="block text-xs font-medium text-zinc-300 mb-1.5" htmlFor="email">
                Email Address
              </label>
              <div className="relative">
                <Mail className="absolute left-3.5 top-3 h-4 w-4 text-zinc-500" />
                <input
                  id="email"
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="student@university.edu"
                  className="w-full rounded-xl bg-zinc-950/70 border border-zinc-800 pl-10 pr-4 py-2.5 text-sm text-zinc-100 placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition"
                />
              </div>
            </div>

            {/* Department Selection */}
            <div>
              <label className="block text-xs font-medium text-zinc-300 mb-1.5" htmlFor="dept">
                Department / Program
              </label>
              <div className="relative">
                <GraduationCap className="absolute left-3.5 top-3 h-4 w-4 text-zinc-500" />
                <select
                  id="dept"
                  value={department}
                  onChange={(e) => setDepartment(e.target.value)}
                  className="w-full rounded-xl bg-zinc-950/70 border border-zinc-800 pl-10 pr-4 py-2.5 text-sm text-zinc-100 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition cursor-pointer"
                >
                  {DEPARTMENTS.map((dept) => (
                    <option key={dept} value={dept} className="bg-zinc-900 text-zinc-100">
                      {dept}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Password Field */}
            <div>
              <label className="block text-xs font-medium text-zinc-300 mb-1.5" htmlFor="password">
                Password (minimum 6 characters)
              </label>
              <div className="relative">
                <Lock className="absolute left-3.5 top-3 h-4 w-4 text-zinc-500" />
                <input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  required
                  minLength={6}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full rounded-xl bg-zinc-950/70 border border-zinc-800 pl-10 pr-11 py-2.5 text-sm text-zinc-100 placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-2.5 text-zinc-500 hover:text-zinc-300 p-0.5 transition cursor-pointer"
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isLoading || isGoogleLoading}
              className="w-full mt-3 inline-flex items-center justify-center gap-2 px-5 py-3 rounded-xl bg-zinc-800 hover:bg-zinc-700 font-semibold text-sm text-white transition disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
            >
              {isLoading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span>Creating student account...</span>
                </>
              ) : (
                <>
                  <span>Create Account</span>
                  <ArrowRight className="h-4 w-4" />
                </>
              )}
            </button>
          </form>
        )}
      </div>

      {/* Switch to Login */}
      <div className="text-center mt-6 text-sm text-zinc-400">
        Already have an account?{" "}
        <Link href="/login" className="text-indigo-400 hover:text-indigo-300 font-medium transition">
          Sign in
        </Link>
      </div>
    </div>
  );
}

export default function SignupPage() {
  return (
    <div className="min-h-screen bg-zinc-950 flex flex-col items-center justify-center p-6 relative overflow-hidden">
      {/* Background ambient lighting */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-indigo-600/15 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-1/4 left-1/3 w-80 h-80 bg-purple-600/15 rounded-full blur-3xl pointer-events-none" />

      <Suspense
        fallback={
          <div className="flex items-center gap-2 text-zinc-400">
            <Loader2 className="h-6 w-6 animate-spin text-indigo-500" />
            <span>Loading...</span>
          </div>
        }
      >
        <SignupForm />
      </Suspense>
    </div>
  );
}
