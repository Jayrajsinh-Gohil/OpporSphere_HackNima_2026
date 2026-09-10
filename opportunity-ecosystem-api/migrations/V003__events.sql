-- =============================================================================
-- V003 — Events table
-- One opportunity can spawn multiple "events" (instances / runs).
-- =============================================================================

CREATE TYPE event_status AS ENUM (
    'upcoming',
    'open',
    'closed',
    'cancelled',
    'completed'
);

CREATE TABLE IF NOT EXISTS public.events (
    id                  UUID            PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Parent opportunity
    opportunity_id      UUID            NOT NULL
                            REFERENCES public.opportunities (id)
                            ON DELETE CASCADE,

    -- Lifecycle
    status              event_status    NOT NULL DEFAULT 'upcoming',

    -- Registration
    registration_link   TEXT,

    -- Flexible extra data: start_date, end_date, prizes, judges, etc.
    extra_details       JSONB           NOT NULL DEFAULT '{}',

    -- Metadata
    created_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE  public.events IS 'A specific run / instance of an opportunity (e.g. Hackathon Spring 2025 edition).';
COMMENT ON COLUMN public.events.extra_details IS 'Schema-free bag: start_date, end_date, prizes, judges, max_team_size, etc.';

-- Index on FK for fast reverse lookups
CREATE INDEX IF NOT EXISTS idx_events_opportunity_id
    ON public.events (opportunity_id);

CREATE TRIGGER trg_events_updated_at
    BEFORE UPDATE ON public.events
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
