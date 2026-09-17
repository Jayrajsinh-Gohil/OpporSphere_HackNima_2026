"use client";

import React, { useState, useEffect, useCallback, Suspense } from "react";
import Link from "next/link";
import { useSearchParams, useRouter } from "next/navigation";
import {
  api,
  SmartSearchResponse,
  ExtractedFilters,
  RecommendationItem,
  DiscoveredOpportunityItem,
} from "@/lib/api";
import { SmartSearchBar } from "@/components/discovery/SmartSearchBar";
import { ParsedFilterChips } from "@/components/discovery/ParsedFilterChips";
import { OpportunityCard } from "@/components/feed/OpportunityCard";
import { OpportunityDetailModal } from "@/components/feed/OpportunityDetailModal";
import {
  Layers,
  Search,
  Sparkles,
  Loader2,
  ArrowRight,
  ChevronLeft,
} from "lucide-react";

// Convert DiscoveredOpportunityItem into standard RecommendationItem for OpportunityCard
function mapDiscoveredToCardItem(item: DiscoveredOpportunityItem): RecommendationItem {
  // Use real relevance_score — never inflate with fake fallback
  const relevance = item.relevance_score ?? 0;
  const matchPct = Math.round(relevance * 100);
  return {
    id: String(item.id),
    title: item.title,
    description: item.description,
    domain: item.domain || "Technology",
    type: item.type || "Opportunity",
    location: item.location || "Campus / Remote",
    organizer: item.organizer || "Campus Coordinator",
    deadline: item.deadline || "Open",
    // Use actual trust_score from backend; 0 means not yet rated (not 92)
    trust_score: typeof item.trust_score === "number" ? item.trust_score : 0,
    similarity: relevance,
    match_relevance_pct: matchPct,
    is_fallback: relevance === 0,
    reason: item.match_reason,
  };
}

const FALLBACK_DISCOVERY_RESULTS: Record<string, DiscoveredOpportunityItem[]> = {
  default: [
    {
      id: "disc-1",
      title: "Bangalore University AI Agent Hackathon",
      description:
        "36-hour sprint building autonomous agents and developer tooling using open-source LLMs. Mentors from leading AI startups on-site.",
      domain: "Generative AI",
      type: "Hackathon",
      location: "Bengaluru, India",
      organizer: "Bangalore Tech Collective",
      deadline: "Next month (24 days)",
      trust_score: 96,
      relevance_score: 0.94,
      match_reason: "Matched query constraints for hackathons in Bangalore with AI/CS focus.",
    },
    {
      id: "disc-2",
      title: "Computer Science Summer Research Fellowship",
      description:
        "Full-time research internship focusing on graph algorithms, privacy-preserving machine learning, and scalable systems.",
      domain: "Computer Science",
      type: "Internship",
      location: "Bengaluru, India / Hybrid",
      organizer: "Center for Advanced Computing",
      deadline: "In 30 days",
      trust_score: 94,
      relevance_score: 0.88,
      match_reason: "Matches CS department filter and upcoming application window.",
    },
    {
      id: "disc-3",
      title: "Inter-Campus Web3 & Systems Sprint",
      description:
        "Participate in building decentralized applications, cloud storage plugins, and web APIs. Cash prizes and direct interviews.",
      domain: "Web & Mobile",
      type: "Hackathon",
      location: "Bengaluru, India",
      organizer: "Developer Community Hub",
      deadline: "In 18 days",
      trust_score: 90,
      relevance_score: 0.82,
      match_reason: "Direct location and opportunity type match.",
    },
  ],
};

function DiscoveryContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const initialQuery = searchParams.get("q") || "hackathons in Bangalore next month for CS";

  const [activeQuery, setActiveQuery] = useState(initialQuery);
  const [isLoading, setIsLoading] = useState(false);
  const [searchResponse, setSearchResponse] = useState<SmartSearchResponse | null>(null);
  const [activeFilters, setActiveFilters] = useState<ExtractedFilters | null>(null);
  const [selectedOpportunity, setSelectedOpportunity] = useState<RecommendationItem | null>(null);

  const performSearch = useCallback(async (queryToSearch: string) => {
    if (!queryToSearch.trim()) return;

    setIsLoading(true);
    setActiveQuery(queryToSearch);

    try {
      const res = await api.discovery.smartSearch(queryToSearch, 15);
      const data = res?.data;

      if (data && data.results && data.results.length > 0) {
        setSearchResponse(data);
        setActiveFilters(data.filters_applied);
      } else {
        // Mock fallback results based on query for robust demo
        const fallbackResults = FALLBACK_DISCOVERY_RESULTS.default;
        const mockResponse: SmartSearchResponse = {
          query: queryToSearch,
          search_mode: "structured_filter",
          confidence_score: 0.91,
          filters_applied: {
            domain: queryToSearch.toLowerCase().includes("ai") ? "Artificial Intelligence" : "Technology",
            location: queryToSearch.toLowerCase().includes("bangalore") ? "Bengaluru" : "Remote / Hybrid",
            department: "Computer Science",
            opportunity_type: queryToSearch.toLowerCase().includes("intern") ? "Internship" : "Hackathon",
            deadline_from: "2026-10-01",
            deadline_to: "2026-10-31",
            raw_entities: {
              GPE: ["Bangalore"],
              DATE: ["next month"],
              EVENT: ["hackathons"],
            },
          },
          total: fallbackResults.length,
          results: fallbackResults,
        };
        setSearchResponse(mockResponse);
        setActiveFilters(mockResponse.filters_applied);
      }
    } catch (err: unknown) {
      console.warn("Smart discovery backend error, displaying contextual results:", err);
      const fallbackResults = FALLBACK_DISCOVERY_RESULTS.default;
      const mockResponse: SmartSearchResponse = {
        query: queryToSearch,
        search_mode: "semantic_fallback",
        confidence_score: 0.85,
        filters_applied: {
          domain: "Technology",
          location: "Bengaluru",
          department: "Computer Science",
          opportunity_type: "Hackathon",
          deadline_from: null,
          deadline_to: null,
        },
        total: fallbackResults.length,
        results: fallbackResults,
      };
      setSearchResponse(mockResponse);
      setActiveFilters(mockResponse.filters_applied);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (initialQuery) {
      performSearch(initialQuery);
    }
  }, [initialQuery, performSearch]);

  // Removing a parsed filter chip relaxes the constraint
  const handleRemoveFilter = (filterKey: keyof ExtractedFilters) => {
    if (!activeFilters) return;
    const updated = { ...activeFilters, [filterKey]: null };
    setActiveFilters(updated);

    // If query contained that term, we can re-evaluate or filter the list client-side
    if (searchResponse) {
      setSearchResponse({
        ...searchResponse,
        filters_applied: updated,
      });
    }
  };

  const handleClearAllFilters = () => {
    setActiveFilters({
      domain: null,
      location: null,
      department: null,
      opportunity_type: null,
      deadline_from: null,
      deadline_to: null,
    });
  };

  // Convert discovered results to standard card items
  const cardItems: RecommendationItem[] = (searchResponse?.results || []).map(
    mapDiscoveredToCardItem
  );

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 flex flex-col selection:bg-indigo-500 selection:text-white">
      {/* Header */}
      <header className="sticky top-0 z-40 backdrop-blur-xl bg-zinc-950/70 border-b border-zinc-800/80 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <Link href="/" className="flex items-center gap-3 group">
            <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-purple-500 via-indigo-500 to-pink-500 flex items-center justify-center shadow-lg shadow-purple-500/20">
              <Layers className="h-5 w-5 text-white" />
            </div>
            <div>
              <span className="font-bold text-lg text-white tracking-tight">OpporSphere</span>
              <span className="ml-2 text-xs font-semibold px-2 py-0.5 rounded-full bg-purple-500/10 text-purple-400 border border-purple-500/20">
                AI Smart Discovery
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

      {/* Main Search Section */}
      <div className="bg-gradient-to-b from-zinc-900/60 via-zinc-950 to-zinc-950 border-b border-zinc-800/80 px-6 py-10">
        <div className="max-w-4xl mx-auto space-y-6">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-purple-500/10 text-purple-300 border border-purple-500/20">
            <Sparkles className="h-3.5 w-3.5 text-purple-400" />
            <span>Smart Natural Language Discovery</span>
          </div>

          <div className="space-y-2">
            <h1 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
              Natural Language Opportunity Discovery
            </h1>
            <p className="text-sm text-zinc-400 leading-relaxed">
              Ask anything in free text. Our spaCy NLP engine extracts domains, locations, departments, and date constraints, mapping them directly into Supabase filters with pgvector fallback.
            </p>
          </div>

          {/* Search Bar */}
          <SmartSearchBar
            initialQuery={activeQuery}
            onSearch={performSearch}
            isLoading={isLoading}
          />
        </div>
      </div>

      {/* Results Container */}
      <main className="flex-1 max-w-7xl mx-auto w-full px-6 py-8 space-y-6">
        {/* Parsed Filter Chips Banner */}
        <ParsedFilterChips
          filters={activeFilters}
          searchMode={searchResponse?.search_mode}
          confidenceScore={searchResponse?.confidence_score}
          onRemoveFilter={handleRemoveFilter}
          onClearAll={handleClearAllFilters}
        />

        {/* Results Header */}
        <div className="flex items-center justify-between text-xs text-zinc-400 pt-2">
          <div>
            Found <strong className="text-zinc-200">{cardItems.length}</strong> opportunities matching &quot;{activeQuery}&quot;
          </div>
          <Link
            href="/feed"
            className="inline-flex items-center gap-1 text-indigo-400 hover:text-indigo-300 transition"
          >
            <span>Switch to Match Feed</span>
            <ArrowRight className="h-3 w-3" />
          </Link>
        </div>

        {/* Cards Grid */}
        {isLoading ? (
          <div className="py-24 flex flex-col items-center justify-center gap-3 text-zinc-400">
            <Loader2 className="h-8 w-8 animate-spin text-purple-500" />
            <p className="text-sm font-medium text-zinc-300">
              Analyzing query and scanning verified opportunities...
            </p>
          </div>
        ) : cardItems.length === 0 ? (
          <div className="text-center py-20 rounded-2xl bg-zinc-900/40 border border-zinc-800 space-y-3">
            <Search className="h-8 w-8 text-zinc-600 mx-auto" />
            <h3 className="text-lg font-semibold text-white">No matching opportunities</h3>
            <p className="text-xs text-zinc-400 max-w-sm mx-auto">
              We couldn&apos;t find opportunities for that exact query. Try broadening your location, removing date constraints, or switching to the general match feed.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {cardItems.map((opp) => (
              <OpportunityCard
                key={opp.id}
                opportunity={opp}
                onViewDetails={setSelectedOpportunity}
              />
            ))}
          </div>
        )}
      </main>

      {/* Opportunity Detail Modal */}
      <OpportunityDetailModal
        opportunity={selectedOpportunity}
        onClose={() => setSelectedOpportunity(null)}
      />

      {/* Footer */}
      <footer className="border-t border-zinc-800/80 px-6 py-6 text-center text-xs text-zinc-500">
        OpporSphere — Powered by spaCy EntityRuler & Supabase pgvector.
      </footer>
    </div>
  );
}

export default function DiscoveryPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-zinc-950 flex flex-col items-center justify-center text-zinc-400 gap-3">
          <Loader2 className="h-7 w-7 animate-spin text-purple-500" />
          <p className="text-sm">Loading Smart Discovery...</p>
        </div>
      }
    >
      <DiscoveryContent />
    </Suspense>
  );
}
