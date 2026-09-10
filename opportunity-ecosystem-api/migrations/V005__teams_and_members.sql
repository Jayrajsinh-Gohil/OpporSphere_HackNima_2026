-- =============================================================================
-- V005 — Teams & Team Members
-- Teams are formed for a specific event; members have roles within the team.
-- =============================================================================

-- ─────────────────────────────────────────────────────────────────────────────
-- TEAMS
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.teams (
    id              UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- The event this team is participating in
    event_id        UUID        NOT NULL
                        REFERENCES public.events (id)
                        ON DELETE CASCADE,

    -- Display name for the team
    name            TEXT        NOT NULL CHECK (char_length(name) BETWEEN 2 AND 100),

    -- Student who created / owns the team
    created_by      UUID        NOT NULL
                        REFERENCES public.students (id)
                        ON DELETE RESTRICT,

    -- Allow others to join (false = invite only)
    is_open         BOOLEAN     NOT NULL DEFAULT TRUE,

    -- Metadata
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- A student can only create one team per event
    CONSTRAINT uq_teams_event_creator UNIQUE (event_id, created_by)
);

COMMENT ON TABLE  public.teams IS 'Teams formed for a specific event instance.';

CREATE INDEX IF NOT EXISTS idx_teams_event_id
    ON public.teams (event_id);

CREATE INDEX IF NOT EXISTS idx_teams_created_by
    ON public.teams (created_by);

CREATE TRIGGER trg_teams_updated_at
    BEFORE UPDATE ON public.teams
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();


-- ─────────────────────────────────────────────────────────────────────────────
-- TEAM MEMBERS
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TYPE team_member_role AS ENUM (
    'leader',
    'member',
    'observer'
);

CREATE TABLE IF NOT EXISTS public.team_members (
    id          UUID                PRIMARY KEY DEFAULT uuid_generate_v4(),

    team_id     UUID                NOT NULL
                    REFERENCES public.teams (id)
                    ON DELETE CASCADE,

    student_id  UUID                NOT NULL
                    REFERENCES public.students (id)
                    ON DELETE CASCADE,

    role        team_member_role    NOT NULL DEFAULT 'member',

    joined_at   TIMESTAMPTZ         NOT NULL DEFAULT NOW(),

    -- A student may only appear once per team
    CONSTRAINT uq_team_members_team_student UNIQUE (team_id, student_id)
);

COMMENT ON TABLE  public.team_members IS 'Junction table: which students belong to which team and in what role.';

CREATE INDEX IF NOT EXISTS idx_team_members_team_id
    ON public.team_members (team_id);

CREATE INDEX IF NOT EXISTS idx_team_members_student_id
    ON public.team_members (student_id);
