-- =============================================================================
-- V010 — Team Finder Invitations & Role Preferences
-- Adds invite lifecycle status and drafted message to team_members,
-- plus preferred_role to students for compatibility matching.
-- =============================================================================

-- Add status and invite message to team_members
ALTER TABLE public.team_members
    ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'accepted'
        CHECK (status IN ('pending', 'accepted', 'declined', 'withdrawn')),
    ADD COLUMN IF NOT EXISTS invite_message TEXT,
    ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW();

-- Add preferred_role to students
ALTER TABLE public.students
    ADD COLUMN IF NOT EXISTS preferred_role TEXT;

COMMENT ON COLUMN public.team_members.status IS 'Membership lifecycle: pending (invite) | accepted | declined | withdrawn.';
COMMENT ON COLUMN public.team_members.invite_message IS 'Drafted team invite message generated via Content Generation service.';
COMMENT ON COLUMN public.students.preferred_role IS 'Explicit or default preferred role (e.g. Frontend, Backend, AI/ML Engineer, UI/UX Designer).';

-- Index on team_members status for fast active membership lookups
CREATE INDEX IF NOT EXISTS idx_team_members_status
    ON public.team_members (status);

CREATE INDEX IF NOT EXISTS idx_team_members_team_status
    ON public.team_members (team_id, status);
