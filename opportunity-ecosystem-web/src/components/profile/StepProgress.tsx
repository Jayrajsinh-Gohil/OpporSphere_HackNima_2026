"use client";

import React from "react";
import { Check, User, Wrench, Heart, Target, Sparkles } from "lucide-react";

export interface StepItem {
  number: number;
  title: string;
  shortDesc: string;
  icon: React.ElementType;
}

export const STEPS: StepItem[] = [
  { number: 1, title: "Basics", shortDesc: "Campus & Role", icon: User },
  { number: 2, title: "Skills", shortDesc: "Tech & Tooling", icon: Wrench },
  { number: 3, title: "Interests", shortDesc: "Domains", icon: Heart },
  { number: 4, title: "Career Goals", shortDesc: "Vision & Review", icon: Target },
  { number: 5, title: "AI Matches", shortDesc: "Instant Results", icon: Sparkles },
];

interface StepProgressProps {
  currentStep: number;
  onSelectStep?: (step: number) => void;
}

export function StepProgress({ currentStep, onSelectStep }: StepProgressProps) {
  const progressPct = Math.min(100, Math.round(((currentStep - 1) / (STEPS.length - 1)) * 100));

  return (
    <div className="w-full mb-8">
      {/* Percentage Bar */}
      <div className="flex items-center justify-between text-xs text-zinc-400 mb-2">
        <span>Step {currentStep} of {STEPS.length}</span>
        <span className="font-mono text-indigo-400 font-medium">{progressPct}% Completed</span>
      </div>
      <div className="w-full h-1.5 bg-zinc-800 rounded-full overflow-hidden mb-6">
        <div
          className="h-full bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 rounded-full transition-all duration-500 ease-out"
          style={{ width: `${progressPct}%` }}
        />
      </div>

      {/* Stepper Indicator */}
      <div className="grid grid-cols-5 gap-2 sm:gap-4">
        {STEPS.map((step) => {
          const Icon = step.icon;
          const isCompleted = step.number < currentStep;
          const isCurrent = step.number === currentStep;
          const isClickable = step.number < currentStep && onSelectStep;

          return (
            <button
              key={step.number}
              type="button"
              disabled={!isClickable}
              onClick={() => isClickable && onSelectStep(step.number)}
              className={`flex flex-col items-center text-center group transition ${
                isClickable ? "cursor-pointer" : "cursor-default"
              }`}
            >
              {/* Badge Circle */}
              <div
                className={`h-9 w-9 sm:h-10 sm:w-10 rounded-xl flex items-center justify-center border text-xs font-semibold mb-2 transition-all duration-300 ${
                  isCompleted
                    ? "bg-emerald-500/15 border-emerald-500/40 text-emerald-400 group-hover:scale-105"
                    : isCurrent
                    ? "bg-indigo-600 border-indigo-400 text-white shadow-lg shadow-indigo-500/30 scale-105"
                    : "bg-zinc-900 border-zinc-800 text-zinc-500"
                }`}
              >
                {isCompleted ? <Check className="h-4 w-4 stroke-[3]" /> : <Icon className="h-4 w-4" />}
              </div>

              {/* Title */}
              <span
                className={`text-xs font-medium truncate max-w-full ${
                  isCurrent
                    ? "text-indigo-300"
                    : isCompleted
                    ? "text-zinc-200"
                    : "text-zinc-500"
                }`}
              >
                {step.title}
              </span>
              <span className="hidden sm:block text-[11px] text-zinc-500 truncate max-w-full">
                {step.shortDesc}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
