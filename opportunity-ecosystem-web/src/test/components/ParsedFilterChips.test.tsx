import { describe, it, expect, vi } from "vitest";
import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { ParsedFilterChips } from "@/components/discovery/ParsedFilterChips";
import { ExtractedFilters } from "@/lib/api";

describe("ParsedFilterChips Component", () => {
  const mockFilters: ExtractedFilters = {
    domain: "Machine Learning",
    location: "San Francisco",
    opportunity_type: "hackathon",
    department: "Computer Science",
    deadline_from: "2026-10-01",
    deadline_to: "2026-10-31",
  };

  it("returns null when filters is null and no searchMode", () => {
    const { container } = render(
      <ParsedFilterChips filters={null} onRemoveFilter={vi.fn()} />
    );
    expect(container.firstChild).toBeNull();
  });

  it("renders extracted filter chips for domain, location, type, and dates", () => {
    const handleRemove = vi.fn();
    render(
      <ParsedFilterChips
        filters={mockFilters}
        searchMode="structured_hybrid"
        confidenceScore={0.92}
        onRemoveFilter={handleRemove}
      />
    );

    expect(screen.getByText("Parsed AI Search Criteria")).toBeInTheDocument();
    expect(screen.getByText(/Location:/i)).toBeInTheDocument();
    expect(screen.getByText("San Francisco")).toBeInTheDocument();
    expect(screen.getByText(/Type:/i)).toBeInTheDocument();
    expect(screen.getByText("hackathon")).toBeInTheDocument();
    expect(screen.getByText(/Dept:/i)).toBeInTheDocument();
    expect(screen.getByText("Computer Science")).toBeInTheDocument();
    expect(screen.getByText(/2026-10-01 → 2026-10-31/i)).toBeInTheDocument();
  });

  it("calls onRemoveFilter when clicking the remove button on a chip", () => {
    const handleRemove = vi.fn();
    render(
      <ParsedFilterChips
        filters={mockFilters}
        onRemoveFilter={handleRemove}
      />
    );

    const removeLocationBtn = screen.getByTitle("Remove location constraint");
    fireEvent.click(removeLocationBtn);

    expect(handleRemove).toHaveBeenCalledWith("location");
  });

  it("calls onClearAll when Clear parsed filters button is clicked", () => {
    const handleClearAll = vi.fn();
    render(
      <ParsedFilterChips
        filters={mockFilters}
        onRemoveFilter={vi.fn()}
        onClearAll={handleClearAll}
      />
    );

    const clearButton = screen.getByRole("button", { name: /clear parsed filters/i });
    fireEvent.click(clearButton);

    expect(handleClearAll).toHaveBeenCalledTimes(1);
  });
});
