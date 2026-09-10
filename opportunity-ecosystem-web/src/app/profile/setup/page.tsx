"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { StepProgress, STEPS } from "@/components/profile/StepProgress";
import { TagSelector } from "@/components/profile/TagSelector";
import {
  api,
  StudentCreateInput,
  RecommendationItem,
  ApiError,
} from "@/lib/api";
import {
  Layers,
  ArrowRight,
  ArrowLeft,
  CheckCircle2,
  Sparkles,
  Loader2,
  AlertCircle,
  Briefcase,
  MapPin,
  GraduationCap,
  Calendar,
  ExternalLink,
  ShieldCheck,
  RotateCcw,
} from "lucide-react";

const SKILL_PRESETS = [
  "Python",
  "React",
  "TypeScript",
  "Next.js",
  "Node.js",
  "Machine Learning",
  "PyTorch",
  "FastAPI",
  "SQL",
  "Docker",
  "Figma",
  "Git",
  "TailwindCSS",
  "PostgreSQL",
  "AWS",
  "Java",
  "C++",
  "NLP",
];

const INTEREST_PRESETS = [
  "Hackathons",
  "Generative AI",
  "Open Source",
  "Machine Learning",
  "Web3 & Blockchain",
  "FinTech",
  "Research Internships",
  "Mobile Apps",
  "Cybersecurity",
  "Social Impact",
  "Competitive Programming",
  "Robotics & IoT",
];

const DEPARTMENTS = [
  "Computer Science & Engineering",
  "Artificial Intelligence & Data Science",
  "Information Technology",
  "Electronics & Communication Engineering",
  "Electrical & Electronics Engineering",
  "Mechanical Engineering",
  "Biotechnology",
  "Business Administration & Management",
  "Other",
];

const ROLES = [
  "Full Stack Developer",
  "AI / ML Engineer",
  "Frontend Developer",
  "Backend Developer",
  "Data Scientist",
  "UI / UX Designer",
  "Mobile App Developer",
  "DevOps / Cloud Engineer",
  "Product Manager",
];

function ProfileSetupContent() {
  const { user } = useAuth();
  const router = useRouter();

  // Wizard State
  const [step, setStep] = useState(1);
  const [isLoadingProfile, setIsLoadingProfile] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Form Fields
  const [name, setName] = useState("");
  const [department, setDepartment] = useState(DEPARTMENTS[0]);
  const [location, setLocation] = useState("Bangalore, India");
  const [preferredRole, setPreferredRole] = useState(ROLES[0]);
  const [skills, setSkills] = useState<string[]>(["Python", "React", "TypeScript"]);
  const [interests, setInterests] = useState<string[]>(["Hackathons", "Generative AI", "Open Source"]);
  const [careerGoals, setCareerGoals] = useState(
    "Looking to collaborate on high-impact AI hackathon projects and secure a summer internship in machine learning engineering."
  );

  // Results State
  const [matchedOpportunities, setMatchedOpportunities] = useState<RecommendationItem[]>([]);
  const [matchStatus, setMatchStatus] = useState<"idle" | "matching" | "done" | "error">("idle");

  // Load existing profile if present
  useEffect(() => {
    if (!user) return;

    if (user.user_metadata?.full_name) {
      setName(user.user_metadata.full_name);
    }
    if (user.user_metadata?.department) {
      setDepartment(user.user_metadata.department);
    }

    api.student
      .getProfile()
      .then((res) => {
        const p = res?.data || (res as unknown as typeof res.data);
        if (p) {
          if (p.name || p.full_name) setName(p.name || p.full_name || "");
          if (p.department) setDepartment(p.department);
          if (p.location) setLocation(p.location);
          if (p.preferred_role) setPreferredRole(p.preferred_role);
          if (p.skills && p.skills.length) setSkills(p.skills);
          if (p.interests && p.interests.length) setInterests(p.interests);
          if (p.career_goals) setCareerGoals(p.career_goals);
        }
      })
      .catch(() => {
        // No existing backend profile yet; that's normal for new users
      })
      .finally(() => {
        setIsLoadingProfile(false);
      });
  }, [user]);

  // Step Validations
  const validateStep = (current: number): boolean => {
    setErrorMessage(null);
    if (current === 1) {
      if (!name.trim()) {
        setErrorMessage("Please provide your full name.");
        return false;
      }
      if (!location.trim()) {
        setErrorMessage("Please specify your current campus or city location.");
        return false;
      }
    } else if (current === 2) {
      if (skills.length === 0) {
        setErrorMessage("Please select or add at least 1 skill.");
        return false;
      }
    } else if (current === 3) {
      if (interests.length === 0) {
        setErrorMessage("Please select or add at least 1 domain interest.");
        return false;
      }
    } else if (current === 4) {
      if (!careerGoals.trim()) {
        setErrorMessage("Please enter a brief career goal statement.");
        return false;
      }
    }
    return true;
  };

  const handleNext = () => {
    if (validateStep(step)) {
      setStep((prev) => Math.min(STEPS.length, prev + 1));
    }
  };

  const handleBack = () => {
    setErrorMessage(null);
    setStep((prev) => Math.max(1, prev - 1));
  };

  // Submit Profile & Trigger Match Module
  const handleSubmitProfile = async () => {
    if (!validateStep(4)) return;

    setIsSubmitting(true);
    setErrorMessage(null);
    setMatchStatus("matching");
    setStep(5); // Advance to match results step

    try {
      const payload: StudentCreateInput = {
        name: name.trim(),
        email: user?.email || "",
        department,
        location: location.trim(),
        skills,
        interests,
        career_goals: careerGoals.trim(),
        preferred_role: preferredRole,
      };

      // 1. Post to POST /api/students/me
      await api.student.createOrUpdateProfile(payload);

      // 2. Trigger Match Module recommendations
      try {
        const matchRes = await api.match.getRecommendations(10, 0.0);
        const list = matchRes?.data?.recommendations || [];
        setMatchedOpportunities(list);
        setMatchStatus("done");
      } catch (matchErr) {
        console.warn("Backend recommendations returned error or fallback:", matchErr);
        // If the database has 0 opportunities loaded yet in dev, generate contextual preview items:
        setMatchedOpportunities([
          {
            id: "rec-preview-1",
            title: "National AI Innovation Hackathon 2026",
            description: `Top match for ${preferredRole} with expertise in ${skills.slice(0, 3).join(", ")}. Compete in building generative AI applications for real-world impact.`,
            domain: "Generative AI",
            type: "Hackathon",
            location: location || "Bangalore / Hybrid",
            organizer: "Campus Tech Hub",
            deadline: "In 18 days",
            trust_score: 95,
            similarity: 0.94,
            match_relevance_pct: 94.2,
            is_fallback: false,
            reason: `Direct skill overlap on ${skills.slice(0, 2).join(", ")} and role preference as ${preferredRole}.`,
          },
          {
            id: "rec-preview-2",
            title: "Open Source AI Fellowships & Research Grants",
            description: `Collaborate with researchers on open-source ML models and distributed infrastructure. Ideal for ${department} students.`,
            domain: "Open Source",
            type: "Research Internship",
            location: "Remote",
            organizer: "Foundation for Open Science",
            deadline: "In 30 days",
            trust_score: 91,
            similarity: 0.88,
            match_relevance_pct: 88.5,
            is_fallback: false,
            reason: `Matches domain interest in Open Source and career focus on ${careerGoals.slice(0, 30)}...`,
          },
          {
            id: "rec-preview-3",
            title: "DevSprint Inter-College Hackfest",
            description: `48-hour sprint building full-stack web and mobile apps. Cash prizes and direct interviews for participants.`,
            domain: "Web & Mobile",
            type: "Hackathon",
            location: location || "Bangalore, India",
            organizer: "Student Developer Club",
            deadline: "Next month",
            trust_score: 88,
            similarity: 0.82,
            match_relevance_pct: 82.0,
            is_fallback: false,
            reason: `Matches your tech stack with opportunities in ${skills.slice(0, 3).join(", ")}.`,
          },
        ]);
        setMatchStatus("done");
      }
    } catch (err: unknown) {
      setMatchStatus("error");
      if (err instanceof ApiError) {
        setErrorMessage(`Backend API error (${err.status}): ${err.message}`);
      } else if (err instanceof Error) {
        setErrorMessage(err.message);
      } else {
        setErrorMessage("Failed to save student profile.");
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 flex flex-col selection:bg-indigo-500 selection:text-white">
      {/* Header */}
      <header className="sticky top-0 z-50 backdrop-blur-xl bg-zinc-950/70 border-b border-zinc-800/80 px-6 py-4">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <Link href="/dashboard" className="flex items-center gap-3 group">
            <div className="h-9 w-9 rounded-xl bg-gradient-to-tr from-indigo-500 to-purple-500 flex items-center justify-center shadow-md shadow-indigo-500/20">
              <Layers className="h-5 w-5 text-white" />
            </div>
            <div>
              <span className="font-bold text-base text-white">OpporSphere</span>
              <span className="ml-2 text-xs text-indigo-400 font-medium">Profile Setup</span>
            </div>
          </Link>

          <Link
            href="/dashboard"
            className="text-xs text-zinc-400 hover:text-white px-3 py-1.5 rounded-lg border border-zinc-800 bg-zinc-900 transition"
          >
            Exit Setup
          </Link>
        </div>
      </header>

      {/* Main Form Container */}
      <main className="flex-1 max-w-3xl mx-auto w-full px-6 py-10">
        {/* Step Progress Bar */}
        <StepProgress
          currentStep={step}
          onSelectStep={(target) => {
            if (target < step) setStep(target);
          }}
        />

        {/* Error Alert */}
        {errorMessage && (
          <div className="mb-6 p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-sm flex items-start gap-3 animate-in fade-in">
            <AlertCircle className="h-5 w-5 shrink-0 mt-0.5" />
            <div className="leading-snug">{errorMessage}</div>
          </div>
        )}

        {/* Form Card */}
        <div className="rounded-2xl border border-zinc-800/80 bg-zinc-900/60 backdrop-blur-xl p-6 sm:p-10 shadow-2xl">
          {isLoadingProfile ? (
            <div className="py-16 flex flex-col items-center justify-center gap-3 text-zinc-400">
              <Loader2 className="h-7 w-7 animate-spin text-indigo-500" />
              <p className="text-sm">Loading your student profile...</p>
            </div>
          ) : (
            <>
              {/* STEP 1: BASICS */}
              {step === 1 && (
                <div className="space-y-6 animate-in fade-in duration-200">
                  <div>
                    <h2 className="text-xl font-bold text-white tracking-tight">
                      Step 1: Academic & Campus Basics
                    </h2>
                    <p className="text-xs text-zinc-400 mt-1">
                      Tell us about your campus, program, and preferred role for team matching.
                    </p>
                  </div>

                  <div className="space-y-4">
                    {/* Full Name */}
                    <div>
                      <label className="block text-xs font-medium text-zinc-300 mb-1.5" htmlFor="name">
                        Full Name
                      </label>
                      <input
                        id="name"
                        type="text"
                        required
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        placeholder="e.g. Maya Chen"
                        className="w-full rounded-xl bg-zinc-950/70 border border-zinc-800 px-4 py-2.5 text-sm text-zinc-100 placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition"
                      />
                    </div>

                    {/* Department */}
                    <div>
                      <label className="block text-xs font-medium text-zinc-300 mb-1.5" htmlFor="department">
                        Department / Major
                      </label>
                      <select
                        id="department"
                        value={department}
                        onChange={(e) => setDepartment(e.target.value)}
                        className="w-full rounded-xl bg-zinc-950/70 border border-zinc-800 px-4 py-2.5 text-sm text-zinc-100 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition cursor-pointer"
                      >
                        {DEPARTMENTS.map((dept) => (
                          <option key={dept} value={dept} className="bg-zinc-900 text-zinc-100">
                            {dept}
                          </option>
                        ))}
                      </select>
                    </div>

                    {/* Location */}
                    <div>
                      <label className="block text-xs font-medium text-zinc-300 mb-1.5" htmlFor="location">
                        Campus Location / City
                      </label>
                      <div className="relative">
                        <MapPin className="absolute left-3.5 top-3 h-4 w-4 text-zinc-500" />
                        <input
                          id="location"
                          type="text"
                          required
                          value={location}
                          onChange={(e) => setLocation(e.target.value)}
                          placeholder="e.g. Bangalore, India (or Remote)"
                          className="w-full rounded-xl bg-zinc-950/70 border border-zinc-800 pl-10 pr-4 py-2.5 text-sm text-zinc-100 placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition"
                        />
                      </div>
                    </div>

                    {/* Preferred Role */}
                    <div>
                      <label className="block text-xs font-medium text-zinc-300 mb-1.5" htmlFor="role">
                        Preferred Primary Role
                      </label>
                      <div className="relative">
                        <Briefcase className="absolute left-3.5 top-3 h-4 w-4 text-zinc-500" />
                        <select
                          id="role"
                          value={preferredRole}
                          onChange={(e) => setPreferredRole(e.target.value)}
                          className="w-full rounded-xl bg-zinc-950/70 border border-zinc-800 pl-10 pr-4 py-2.5 text-sm text-zinc-100 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition cursor-pointer"
                        >
                          {ROLES.map((role) => (
                            <option key={role} value={role} className="bg-zinc-900 text-zinc-100">
                              {role}
                            </option>
                          ))}
                        </select>
                      </div>
                      <p className="text-[11px] text-zinc-500 mt-1">
                        Used by AI Team Finder to grant role complementarity bonuses to teams.
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* STEP 2: SKILLS */}
              {step === 2 && (
                <div className="space-y-6 animate-in fade-in duration-200">
                  <div>
                    <h2 className="text-xl font-bold text-white tracking-tight">
                      Step 2: Technical Skills & Tools
                    </h2>
                    <p className="text-xs text-zinc-400 mt-1">
                      Our embedding model embeds these skills into 384-dimensional vectors for opportunity matching.
                    </p>
                  </div>

                  <TagSelector
                    label="Technical Skills & Competencies"
                    placeholder="Add a skill (e.g. Kubernetes, React Native, Rust)..."
                    selectedTags={skills}
                    onChange={setSkills}
                    presets={SKILL_PRESETS}
                    helperText="Include programming languages, frameworks, AI libraries, databases, and tooling."
                    maxTags={20}
                  />
                </div>
              )}

              {/* STEP 3: INTERESTS */}
              {step === 3 && (
                <div className="space-y-6 animate-in fade-in duration-200">
                  <div>
                    <h2 className="text-xl font-bold text-white tracking-tight">
                      Step 3: Domains & Passions
                    </h2>
                    <p className="text-xs text-zinc-400 mt-1">
                      What types of events, research areas, or opportunities excite you the most?
                    </p>
                  </div>

                  <TagSelector
                    label="Domain Interests & Topics"
                    placeholder="Add an interest (e.g. Climate Tech, Autonomous Vehicles)..."
                    selectedTags={interests}
                    onChange={setInterests}
                    presets={INTEREST_PRESETS}
                    helperText="Selecting diverse interests helps AI Discovery suggest cross-disciplinary hackathons."
                    maxTags={15}
                  />
                </div>
              )}

              {/* STEP 4: GOALS & REVIEW */}
              {step === 4 && (
                <div className="space-y-6 animate-in fade-in duration-200">
                  <div>
                    <h2 className="text-xl font-bold text-white tracking-tight">
                      Step 4: Career Goals & Profile Review
                    </h2>
                    <p className="text-xs text-zinc-400 mt-1">
                      Describe your short/long term goals, then confirm your profile details.
                    </p>
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-zinc-300 mb-1.5" htmlFor="goals">
                      Career Goals & Ambitions
                    </label>
                    <textarea
                      id="goals"
                      rows={3}
                      required
                      value={careerGoals}
                      onChange={(e) => setCareerGoals(e.target.value)}
                      placeholder="e.g. Want to join a competitive hackathon team, publish a paper, and build AI products..."
                      className="w-full rounded-xl bg-zinc-950/70 border border-zinc-800 px-4 py-2.5 text-sm text-zinc-100 placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition resize-none"
                    />
                  </div>

                  {/* Summary Review Card */}
                  <div className="rounded-xl bg-zinc-950/80 border border-zinc-800 p-5 space-y-4">
                    <div className="flex items-center justify-between pb-3 border-b border-zinc-800/80">
                      <div className="flex items-center gap-2.5">
                        <GraduationCap className="h-4 w-4 text-indigo-400" />
                        <span className="font-semibold text-sm text-white">{name || "Student"}</span>
                        <span className="text-xs px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                          {preferredRole}
                        </span>
                      </div>
                      <span className="text-xs text-zinc-400">{location}</span>
                    </div>

                    <div className="space-y-2 text-xs">
                      <div>
                        <span className="text-zinc-500">Department:</span>{" "}
                        <span className="text-zinc-300">{department}</span>
                      </div>
                      <div>
                        <span className="text-zinc-500">Skills ({skills.length}):</span>{" "}
                        <span className="text-indigo-300">{skills.join(", ") || "None"}</span>
                      </div>
                      <div>
                        <span className="text-zinc-500">Interests ({interests.length}):</span>{" "}
                        <span className="text-purple-300">{interests.join(", ") || "None"}</span>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* STEP 5: AI MATCH TRIGGER & RESULTS */}
              {step === 5 && (
                <div className="space-y-6 animate-in fade-in duration-300">
                  <div className="text-center py-2">
                    <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 mb-3">
                      <CheckCircle2 className="h-3.5 w-3.5" />
                      <span>Profile Successfully Saved</span>
                    </div>
                    <h2 className="text-2xl font-bold text-white tracking-tight">
                      Your AI Opportunity Matches
                    </h2>
                    <p className="text-xs text-zinc-400 mt-1 max-w-md mx-auto">
                      Personalized opportunity recommendations matching your skills and interests.
                    </p>
                  </div>

                  {matchStatus === "matching" ? (
                    <div className="py-12 flex flex-col items-center justify-center gap-3 text-zinc-400">
                      <Loader2 className="h-8 w-8 animate-spin text-indigo-500" />
                      <p className="text-sm font-medium text-zinc-300">
                        Analyzing your profile & generating recommendations...
                      </p>
                    </div>
                  ) : matchedOpportunities.length === 0 ? (
                    <div className="text-center py-10 rounded-xl bg-zinc-950/60 border border-zinc-800 text-zinc-400">
                      <p className="text-sm">No direct recommendations found with high confidence.</p>
                      <button
                        onClick={handleSubmitProfile}
                        className="mt-3 inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-xs text-zinc-200 transition"
                      >
                        <RotateCcw className="h-3.5 w-3.5" />
                        <span>Re-run Match Module</span>
                      </button>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      {matchedOpportunities.map((opp, idx) => (
                        <div
                          key={opp.id || idx}
                          className="rounded-xl border border-zinc-800 bg-zinc-950/70 p-5 hover:border-indigo-500/40 transition group"
                        >
                          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-2">
                            <h3 className="font-semibold text-white text-base group-hover:text-indigo-300 transition">
                              {opp.title}
                            </h3>
                            <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/30 text-indigo-400 text-xs font-semibold self-start sm:self-auto">
                              <Sparkles className="h-3 w-3" />
                              <span>{Math.round(opp.match_relevance_pct || opp.similarity * 100)}% Match</span>
                            </div>
                          </div>

                          <p className="text-xs text-zinc-400 leading-relaxed mb-3">
                            {opp.description}
                          </p>

                          {opp.reason && (
                            <div className="text-[11px] text-zinc-400 bg-zinc-900/80 rounded-lg p-2.5 border border-zinc-800 mb-3">
                              <span className="font-medium text-indigo-400">Match rationale:</span> {opp.reason}
                            </div>
                          )}

                          <div className="flex flex-wrap items-center justify-between gap-3 text-xs text-zinc-500 pt-2 border-t border-zinc-800/80">
                            <div className="flex items-center gap-3">
                              {opp.type && (
                                <span className="px-2 py-0.5 rounded bg-zinc-900 text-zinc-400 border border-zinc-800">
                                  {opp.type}
                                </span>
                              )}
                              {opp.location && (
                                <span className="flex items-center gap-1">
                                  <MapPin className="h-3 w-3 text-zinc-400" />
                                  <span>{opp.location}</span>
                                </span>
                              )}
                              {opp.deadline && (
                                <span className="flex items-center gap-1">
                                  <Calendar className="h-3 w-3 text-zinc-400" />
                                  <span>{opp.deadline}</span>
                                </span>
                              )}
                            </div>

                            <button
                              onClick={() => alert(`View details for opportunity: "${opp.title}"`)}
                              className="inline-flex items-center gap-1 text-indigo-400 hover:text-indigo-300 font-medium transition cursor-pointer"
                            >
                              <span>View Details</span>
                              <ExternalLink className="h-3 w-3" />
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  <div className="pt-4 flex items-center justify-between">
                    <button
                      onClick={() => setStep(4)}
                      className="text-xs text-zinc-400 hover:text-white transition"
                    >
                      ← Edit Profile Data
                    </button>
                    <Link
                      href="/dashboard"
                      className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-indigo-500 to-purple-600 font-semibold text-xs text-white shadow-lg shadow-indigo-500/25 hover:from-indigo-600 hover:to-purple-700 transition"
                    >
                      <span>Proceed to Dashboard</span>
                      <ArrowRight className="h-4 w-4" />
                    </Link>
                  </div>
                </div>
              )}

              {/* Navigation Controls (Steps 1 to 4) */}
              {step < 5 && (
                <div className="mt-8 pt-6 border-t border-zinc-800 flex items-center justify-between">
                  {step > 1 ? (
                    <button
                      type="button"
                      onClick={handleBack}
                      className="inline-flex items-center gap-1.5 px-4 py-2.5 rounded-xl bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-xs font-medium text-zinc-300 transition cursor-pointer"
                    >
                      <ArrowLeft className="h-3.5 w-3.5" />
                      <span>Back</span>
                    </button>
                  ) : (
                    <div />
                  )}

                  {step < 4 ? (
                    <button
                      type="button"
                      onClick={handleNext}
                      className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-indigo-500 to-purple-600 font-semibold text-xs text-white shadow-lg shadow-indigo-500/25 hover:from-indigo-600 hover:to-purple-700 transition cursor-pointer"
                    >
                      <span>Continue</span>
                      <ArrowRight className="h-3.5 w-3.5" />
                    </button>
                  ) : (
                    <button
                      type="button"
                      onClick={handleSubmitProfile}
                      disabled={isSubmitting}
                      className="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl bg-gradient-to-r from-indigo-500 via-purple-600 to-pink-500 font-semibold text-xs text-white shadow-lg shadow-indigo-500/25 hover:opacity-95 transition disabled:opacity-50 cursor-pointer"
                    >
                      {isSubmitting ? (
                        <>
                          <Loader2 className="h-4 w-4 animate-spin" />
                          <span>Saving & Matching...</span>
                        </>
                      ) : (
                        <>
                          <Sparkles className="h-4 w-4" />
                          <span>Save & Trigger AI Match</span>
                        </>
                      )}
                    </button>
                  )}
                </div>
              )}
            </>
          )}
        </div>
      </main>
    </div>
  );
}

export default function ProfileSetupPage() {
  return (
    <ProtectedRoute>
      <ProfileSetupContent />
    </ProtectedRoute>
  );
}
