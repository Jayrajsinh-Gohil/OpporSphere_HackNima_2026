import { describe, it, expect, vi } from "vitest";
import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { TeammateCandidateCard } from "@/components/team-finder/TeammateCandidateCard";
import { TeamMatchItem } from "@/lib/api";

describe("TeammateCandidateCard Component", () => {
  const mockCandidate: TeamMatchItem = {
    student_id: "stu-101",
    name: "Elena Rostova",
    department: "Computer Science & Engineering",
    preferred_role: "AI / ML Engineer",
    skills: ["Python", "PyTorch", "FastAPI", "PostgreSQL"],
    interests: ["Deep Learning", "Generative AI"],
    shared_skills: ["Python", "FastAPI"],
    complementary_skills: ["PyTorch", "CUDA", "Model Deployment"],
    similarity_score: 0.73,
    role_bonus: 0.15,
    match_score: 0.88,
    match_percentage: 88,
    is_complementary: true,
    recommendation_reason: "Brings strong PyTorch modeling skills to complement your backend infrastructure.",
  };

  it("renders candidate header info, department, and initials", () => {
    const handleInvite = vi.fn();
    render(<TeammateCandidateCard candidate={mockCandidate} onInvite={handleInvite} />);

    expect(screen.getByText("Elena Rostova")).toBeInTheDocument();
    expect(screen.getByText("ER")).toBeInTheDocument(); // Initials avatar
    expect(screen.getByText("Computer Science & Engineering")).toBeInTheDocument();
    expect(screen.getByText("88% Match")).toBeInTheDocument();
  });

  it("renders preferred role and complementary role indicator", () => {
    const handleInvite = vi.fn();
    render(<TeammateCandidateCard candidate={mockCandidate} onInvite={handleInvite} />);

    expect(screen.getByText("AI / ML Engineer")).toBeInTheDocument();
    expect(screen.getByText("Complementary Role")).toBeInTheDocument();
  });

  it("renders shared and complementary skills correctly", () => {
    const handleInvite = vi.fn();
    render(<TeammateCandidateCard candidate={mockCandidate} onInvite={handleInvite} />);

    expect(screen.getByText(/Shared Competencies \(2\):/i)).toBeInTheDocument();
    expect(screen.getByText("Python")).toBeInTheDocument();
    expect(screen.getByText("FastAPI")).toBeInTheDocument();

    expect(screen.getByText(/Brings New Skills:/i)).toBeInTheDocument();
    expect(screen.getByText("+PyTorch")).toBeInTheDocument();
    expect(screen.getByText("+CUDA")).toBeInTheDocument();
  });

  it("renders synergy reason", () => {
    const handleInvite = vi.fn();
    render(<TeammateCandidateCard candidate={mockCandidate} onInvite={handleInvite} />);

    expect(
      screen.getByText(/Brings strong PyTorch modeling skills to complement your backend infrastructure/i)
    ).toBeInTheDocument();
  });

  it("triggers onInvite callback when Invite Teammate button is clicked", () => {
    const handleInvite = vi.fn();
    render(<TeammateCandidateCard candidate={mockCandidate} onInvite={handleInvite} />);

    const inviteButton = screen.getByRole("button", { name: /invite teammate/i });
    fireEvent.click(inviteButton);

    expect(handleInvite).toHaveBeenCalledTimes(1);
    expect(handleInvite).toHaveBeenCalledWith(mockCandidate);
  });

  it("renders 'Invite Sent' badge when isInvited is true", () => {
    const handleInvite = vi.fn();
    render(<TeammateCandidateCard candidate={mockCandidate} isInvited={true} onInvite={handleInvite} />);

    expect(screen.getByText("Invite Sent")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /invite teammate/i })).not.toBeInTheDocument();
  });
});
