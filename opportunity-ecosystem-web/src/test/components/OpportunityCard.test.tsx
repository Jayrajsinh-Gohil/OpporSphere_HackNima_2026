import { describe, it, expect, vi } from "vitest";
import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { OpportunityCard } from "@/components/feed/OpportunityCard";
import { RecommendationItem } from "@/lib/api";

describe("OpportunityCard Component", () => {
  const mockOpportunity: RecommendationItem = {
    id: "opp-123",
    title: "AI Hackathon for Social Good",
    description: "Build AI applications tackling global challenges in health and climate.",
    type: "hackathon",
    domain: "Artificial Intelligence",
    organizer: "Stanford AI Lab",
    location: "San Francisco, CA",
    deadline: "2026-11-15",
    trust_score: 94,
    match_relevance_pct: 92,
    similarity: 0.92,
    is_fallback: false,
    reason: "Matches your deep learning interest and Python skills.",
  };

  it("renders opportunity details accurately", () => {
    const handleViewDetails = vi.fn();
    render(<OpportunityCard opportunity={mockOpportunity} onViewDetails={handleViewDetails} />);

    expect(screen.getByText("AI Hackathon for Social Good")).toBeInTheDocument();
    expect(screen.getByText("Stanford AI Lab")).toBeInTheDocument();
    expect(screen.getByText("San Francisco, CA")).toBeInTheDocument();
    expect(screen.getByText("Artificial Intelligence")).toBeInTheDocument();
    expect(screen.getByText("hackathon")).toBeInTheDocument();
    expect(screen.getByText("Deadline: 2026-11-15")).toBeInTheDocument();
    expect(screen.getByText(/Matches your deep learning interest/i)).toBeInTheDocument();
  });

  it("displays correct Match % and Trust Score badges", () => {
    const handleViewDetails = vi.fn();
    render(<OpportunityCard opportunity={mockOpportunity} onViewDetails={handleViewDetails} />);

    expect(screen.getByText("92% Match")).toBeInTheDocument();
    expect(screen.getByText("94 Trust")).toBeInTheDocument();
  });

  it("calls onViewDetails when clicking View Details button or title", () => {
    const handleViewDetails = vi.fn();
    render(<OpportunityCard opportunity={mockOpportunity} onViewDetails={handleViewDetails} />);

    const viewButton = screen.getByRole("button", { name: /view details/i });
    fireEvent.click(viewButton);
    expect(handleViewDetails).toHaveBeenCalledTimes(1);
    expect(handleViewDetails).toHaveBeenCalledWith(mockOpportunity);

    const titleEl = screen.getByText("AI Hackathon for Social Good");
    fireEvent.click(titleEl);
    expect(handleViewDetails).toHaveBeenCalledTimes(2);
  });

  it("toggles bookmark state when bookmark button is clicked", () => {
    const handleViewDetails = vi.fn();
    render(<OpportunityCard opportunity={mockOpportunity} onViewDetails={handleViewDetails} />);

    const bookmarkBtn = screen.getByTitle("Save opportunity");
    expect(bookmarkBtn).toBeInTheDocument();

    fireEvent.click(bookmarkBtn);
    expect(screen.getByTitle("Saved to bookmarks")).toBeInTheDocument();

    fireEvent.click(screen.getByTitle("Saved to bookmarks"));
    expect(screen.getByTitle("Save opportunity")).toBeInTheDocument();
  });

  it("handles missing optional attributes gracefully with fallbacks", () => {
    const sparseOpportunity: RecommendationItem = {
      id: "opp-456",
      title: "Open Source Fellowship",
      description: "Contribute to core developer infrastructure.",
      trust_score: 90,
      similarity: 0.85,
      match_relevance_pct: 85,
      is_fallback: false,
    };

    const handleViewDetails = vi.fn();
    render(<OpportunityCard opportunity={sparseOpportunity} onViewDetails={handleViewDetails} />);

    expect(screen.getByText("Open Source Fellowship")).toBeInTheDocument();
    expect(screen.getByText("85% Match")).toBeInTheDocument(); // fallback when similarity not provided
    expect(screen.getByText("90 Trust")).toBeInTheDocument(); // default trust score fallback
    expect(screen.queryByText(/Deadline:/i)).not.toBeInTheDocument();
  });
});
