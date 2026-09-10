import { describe, it, expect, vi, beforeEach } from "vitest";
import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { InviteTeammateModal } from "@/components/team-finder/InviteTeammateModal";
import { TeamMatchItem, api } from "@/lib/api";

// Mock the API client
vi.mock("@/lib/api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api")>();
  return {
    ...actual,
    api: {
      ...actual.api,
      teamFinder: {
        invite: vi.fn(),
      },
    },
  };
});

describe("InviteTeammateModal Component", () => {
  const mockCandidate: TeamMatchItem = {
    student_id: "stu-101",
    name: "Alex Rivera",
    department: "Human-Computer Interaction",
    preferred_role: "UI/UX Designer",
    skills: ["Figma", "Design Systems", "Prototyping"],
    interests: ["Design Systems", "Accessibility"],
    shared_skills: ["Prototyping"],
    complementary_skills: ["Figma", "Design Systems"],
    similarity_score: 0.76,
    role_bonus: 0.15,
    match_score: 0.91,
    match_percentage: 91,
    is_complementary: true,
    recommendation_reason: "Provides complementary design leadership to accompany engineering.",
  };

  const eventId = "evt-hack-2026";
  const eventTitle = "Global GenAI Hackathon 2026";

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("returns null when candidate is null", () => {
    const { container } = render(
      <InviteTeammateModal
        candidate={null}
        eventId={eventId}
        eventTitle={eventTitle}
        onClose={vi.fn()}
        onSuccess={vi.fn()}
      />
    );
    expect(container.firstChild).toBeNull();
  });

  it("renders modal with AI drafted message tailored to candidate", () => {
    render(
      <InviteTeammateModal
        candidate={mockCandidate}
        eventId={eventId}
        eventTitle={eventTitle}
        currentStudentName="Dev Lead"
        onClose={vi.fn()}
        onSuccess={vi.fn()}
      />
    );

    expect(screen.getByText("Invite Alex Rivera")).toBeInTheDocument();
    expect(screen.getByText(eventTitle)).toBeInTheDocument();
    expect(screen.getByText("91% Match")).toBeInTheDocument();

    const textarea = screen.getByRole("textbox") as HTMLTextAreaElement;
    expect(textarea.value).toContain("Alex Rivera");
    expect(textarea.value).toContain("Global GenAI Hackathon 2026");
    expect(textarea.value).toContain("UI/UX Designer");
  });

  it("allows user to customize message and change role", () => {
    render(
      <InviteTeammateModal
        candidate={mockCandidate}
        eventId={eventId}
        eventTitle={eventTitle}
        onClose={vi.fn()}
        onSuccess={vi.fn()}
      />
    );

    const textarea = screen.getByRole("textbox") as HTMLTextAreaElement;
    fireEvent.change(textarea, { target: { value: "Let's build a prize-winning project together!" } });
    expect(textarea.value).toBe("Let's build a prize-winning project together!");

    const roleSelect = screen.getByLabelText(/team role offered/i) as HTMLSelectElement;
    fireEvent.change(roleSelect, { target: { value: "co-leader" } });
    expect(roleSelect.value).toBe("co-leader");
  });

  it("submits invitation via API and renders success confirmation", async () => {
    const mockSuccessResponse = {
      data: {
        invite_id: "inv-999",
        team_id: "team-777",
        team_name: "Lead's Team",
        event_id: eventId,
        inviter_id: "me",
        inviter_name: "Dev Lead",
        invited_student_id: mockCandidate.student_id,
        invited_student_name: mockCandidate.name,
        role: "co-leader",
        status: "pending",
        message: "Let's build a prize-winning project together!",
        created_at: new Date().toISOString(),
      },
    };

    vi.mocked(api.teamFinder.invite).mockResolvedValue(mockSuccessResponse as any);

    const handleSuccess = vi.fn();
    const handleClose = vi.fn();

    render(
      <InviteTeammateModal
        candidate={mockCandidate}
        eventId={eventId}
        eventTitle={eventTitle}
        currentStudentName="Dev Lead"
        onClose={handleClose}
        onSuccess={handleSuccess}
      />
    );

    const roleSelect = screen.getByLabelText(/team role offered/i);
    fireEvent.change(roleSelect, { target: { value: "co-leader" } });

    const submitBtn = screen.getByRole("button", { name: /send invitation/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(api.teamFinder.invite).toHaveBeenCalledWith({
        event_id: eventId,
        invited_student_id: mockCandidate.student_id,
        role: "co-leader",
        custom_message: expect.stringContaining("Alex Rivera"),
      });
    });

    await waitFor(() => {
      expect(screen.getByText("Invitation Dispatched!")).toBeInTheDocument();
      expect(handleSuccess).toHaveBeenCalledWith(mockCandidate.student_id);
    });

    const doneButton = screen.getByRole("button", { name: /done/i });
    fireEvent.click(doneButton);
    expect(handleClose).toHaveBeenCalled();
  });

  it("handles API error gracefully and displays error banner", async () => {
    vi.mocked(api.teamFinder.invite).mockRejectedValue(new Error("Student already has a pending invitation"));

    render(
      <InviteTeammateModal
        candidate={mockCandidate}
        eventId={eventId}
        eventTitle={eventTitle}
        onClose={vi.fn()}
        onSuccess={vi.fn()}
      />
    );

    const submitBtn = screen.getByRole("button", { name: /send invitation/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText("Student already has a pending invitation")).toBeInTheDocument();
    });
  });
});
