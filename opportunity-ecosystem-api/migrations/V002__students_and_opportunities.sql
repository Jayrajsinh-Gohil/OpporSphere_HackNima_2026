-- =============================================================================
-- V002 — Core tables: students & opportunities
-- Both include a vector(384) embedding column for pgvector similarity search.
-- =============================================================================

-- ─────────────────────────────────────────────────────────────────────────────
-- ENUM TYPES
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TYPE opportunity_type AS ENUM (
    'hackathon',
    'internship',
    'workshop',
    'competition',
    'fellowship',
    'grant',
    'other'
);

CREATE TYPE opportunity_domain AS ENUM (
    'technology',
    'science',
    'arts',
    'business',
    'social_impact',
    'health',
    'education',
    'environment',
    'other'
);

-- ─────────────────────────────────────────────────────────────────────────────
-- STUDENTS
-- Mirrors Supabase auth.users — linked via id (UUID from auth.users).
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.students (
    id              UUID            PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Identity (id matches auth.users.id when using Supabase Auth)
    name            TEXT            NOT NULL CHECK (char_length(name) BETWEEN 2 AND 120),
    email           CITEXT          NOT NULL UNIQUE,

    -- Profile
    department      TEXT,
    location        TEXT,

    -- Skill / interest arrays  (e.g. {'Python','React','ML'})
    skills          TEXT[]          NOT NULL DEFAULT '{}',
    interests       TEXT[]          NOT NULL DEFAULT '{}',
    career_goals    TEXT,

    -- AI vector — 384-dim matches sentence-transformers/all-MiniLM-L6-v2
    -- and OpenAI text-embedding-3-small (truncated). Adjust to 1536 for
    -- full OpenAI embeddings.
    embedding       vector(384),

    -- Metadata
    is_active       BOOLEAN         NOT NULL DEFAULT TRUE,
    avatar_url      TEXT,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE  public.students IS 'Platform user profiles linked to Supabase Auth identities.';
COMMENT ON COLUMN public.students.embedding IS '384-dim sentence embedding of bio + skills + interests for cosine similarity.';
COMMENT ON COLUMN public.students.skills IS 'Free-text skill tags, e.g. {''Python'',''ML'',''React''}.';

-- Auto-update updated_at on any row change
CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_students_updated_at
    BEFORE UPDATE ON public.students
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- ─────────────────────────────────────────────────────────────────────────────
-- OPPORTUNITIES
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.opportunities (
    id              UUID                PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Core fields
    title           TEXT                NOT NULL CHECK (char_length(title) BETWEEN 5 AND 255),
    description     TEXT                NOT NULL,
    domain          opportunity_domain  NOT NULL DEFAULT 'other',
    type            opportunity_type    NOT NULL DEFAULT 'other',

    -- Details
    eligibility     TEXT,
    deadline        DATE,
    location        TEXT,
    organizer       TEXT,
    source_url      TEXT,

    -- AI vector
    embedding       vector(384),

    -- Status
    is_active       BOOLEAN             NOT NULL DEFAULT TRUE,

    -- Metadata
    created_at      TIMESTAMPTZ         NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ         NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE  public.opportunities IS 'Hackathons, internships, workshops, competitions and other opportunities.';
COMMENT ON COLUMN public.opportunities.embedding IS '384-dim embedding of title + description + eligibility for cosine similarity.';
COMMENT ON COLUMN public.opportunities.type IS 'Opportunity category: hackathon | internship | workshop | competition | fellowship | grant | other.';

CREATE TRIGGER trg_opportunities_updated_at
    BEFORE UPDATE ON public.opportunities
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
