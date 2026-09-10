"use client";

import React, { useState } from "react";
import { Search, Sparkles, X, Loader2, ArrowRight } from "lucide-react";

interface SmartSearchBarProps {
  initialQuery?: string;
  onSearch: (query: string) => void;
  isLoading?: boolean;
}

const SAMPLE_PROMPTS = [
  "hackathons in Bangalore next month for CS",
  "remote AI & ML internships this month",
  "open source fellowships for undergraduates",
  "fintech competitions in Mumbai next week",
  "cybersecurity CTF challenges online",
];

export function SmartSearchBar({
  initialQuery = "",
  onSearch,
  isLoading = false,
}: SmartSearchBarProps) {
  const [query, setQuery] = useState(initialQuery);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      onSearch(query.trim());
    }
  };

  const handleSelectPrompt = (prompt: string) => {
    setQuery(prompt);
    onSearch(prompt);
  };

  return (
    <div className="w-full space-y-4">
      {/* Search Input Box */}
      <form onSubmit={handleSubmit} className="relative">
        <div className="relative flex items-center rounded-2xl bg-zinc-900/90 border border-zinc-800 shadow-xl focus-within:border-indigo-500/60 focus-within:ring-2 focus-within:ring-indigo-500/20 transition-all duration-300">
          <div className="pl-4 pr-2 text-zinc-500 flex items-center pointer-events-none">
            <Search className="h-5 w-5 text-indigo-400" />
          </div>

          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Try: 'hackathons in Bangalore next month for CS' or 'remote ML internships'..."
            className="w-full bg-transparent py-4 text-sm text-zinc-100 placeholder-zinc-500 focus:outline-none"
          />

          {query && (
            <button
              type="button"
              onClick={() => setQuery("")}
              className="p-2 text-zinc-500 hover:text-zinc-300 transition mr-1"
            >
              <X className="h-4 w-4" />
            </button>
          )}

          <div className="pr-2">
            <button
              type="submit"
              disabled={isLoading || !query.trim()}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-indigo-500 to-purple-600 font-semibold text-xs text-white shadow-lg shadow-indigo-500/25 hover:from-indigo-600 hover:to-purple-700 transition disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
            >
              {isLoading ? (
                <>
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  <span>Discovering...</span>
                </>
              ) : (
                <>
                  <span>Search</span>
                  <ArrowRight className="h-3.5 w-3.5" />
                </>
              )}
            </button>
          </div>
        </div>
      </form>

      {/* Suggested Natural Language Prompts */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1 text-xs scrollbar-none">
        <span className="text-zinc-500 shrink-0 flex items-center gap-1 font-medium">
          <Sparkles className="h-3 w-3 text-indigo-400" />
          <span>Try asking:</span>
        </span>
        {SAMPLE_PROMPTS.map((prompt) => (
          <button
            key={prompt}
            type="button"
            onClick={() => handleSelectPrompt(prompt)}
            className="px-3 py-1.5 rounded-xl bg-zinc-900/60 hover:bg-zinc-800 border border-zinc-800/80 text-zinc-400 hover:text-indigo-300 whitespace-nowrap transition cursor-pointer text-xs"
          >
            &quot;{prompt}&quot;
          </button>
        ))}
      </div>
    </div>
  );
}
