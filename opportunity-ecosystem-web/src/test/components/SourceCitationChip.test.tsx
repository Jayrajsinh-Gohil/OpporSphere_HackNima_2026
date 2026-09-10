import { describe, it, expect } from "vitest";
import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { SourceCitationChip } from "@/components/copilot/SourceCitationChip";
import { OpportunitySourceCitation } from "@/lib/api";

describe("SourceCitationChip Component", () => {
  const mockCitation: OpportunitySourceCitation = {
    id: "opp-303",
    title: "Quantum Computing Fellowship",
    similarity: 0.89,
    domain: "Quantum / Physics",
    location: "Boulder, CO",
    deadline: "2026-12-01",
  };

  it("renders index, title, and similarity badge", () => {
    render(<SourceCitationChip citation={mockCitation} index={0} />);

    expect(screen.getByText("[1]")).toBeInTheDocument();
    expect(screen.getByText("Quantum Computing Fellowship")).toBeInTheDocument();
    expect(screen.getByText("89%")).toBeInTheDocument();
  });

  it("reveals rich metadata tooltip on hover and hides on mouse leave", () => {
    render(<SourceCitationChip citation={mockCitation} index={1} />);

    // Initially tooltip is not visible
    expect(screen.queryByText("Source #2")).not.toBeInTheDocument();
    expect(screen.queryByText("Boulder, CO")).not.toBeInTheDocument();

    // Hover over container
    const chipWrapper = screen.getByText("[2]").closest("div")!;
    fireEvent.mouseEnter(chipWrapper);

    // Tooltip should appear
    expect(screen.getByText("Source #2")).toBeInTheDocument();
    expect(screen.getByText("Boulder, CO")).toBeInTheDocument();
    expect(screen.getByText("Deadline: 2026-12-01")).toBeInTheDocument();
    expect(screen.getByText("Grounded in Live DB")).toBeInTheDocument();

    // Mouse leave
    fireEvent.mouseLeave(chipWrapper);
    expect(screen.queryByText("Source #2")).not.toBeInTheDocument();
  });
});
