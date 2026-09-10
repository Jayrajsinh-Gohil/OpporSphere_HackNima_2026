-- =============================================================================
-- V006 — Applications
-- Tracks a student's application lifecycle for any opportunity.
-- =============================================================================

CREATE TYPE application_status AS ENUM (
    'draft',
    'submitted',
    'under_review',
    'shortlisted',
    'accepted',
    'rejected',
    'withdrawn'
);

CREATE TABLE IF NOT EXISTS public.applications (
    id              UUID                PRIMARY KEY DEFAULT uuid_generate_v4(),

    student_id      UUID                NOT NULL
                        REFERENCES public.students (id)
                        ON DELETE CASCADE,

    opportunity_id  UUID                NOT NULL
                        REFERENCES public.opportunities (id)
                        ON DELETE CASCADE,

    status          application_status  NOT NULL DEFAULT 'draft',

    -- Notes / cover letter text (optional; full doc stored externally)
    notes           TEXT,

    applied_at      TIMESTAMPTZ         NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ         NOT NULL DEFAULT NOW(),

    -- One application per student per opportunity
    CONSTRAINT uq_applications_student_opportunity UNIQUE (student_id, opportunity_id)
);

COMMENT ON TABLE  public.applications IS 'A student''s application to a specific opportunity.';
COMMENT ON COLUMN public.applications.status IS 'Lifecycle: draft → submitted → under_review → shortlisted → accepted/rejected.';

-- Indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_applications_student_id
    ON public.applications (student_id);

CREATE INDEX IF NOT EXISTS idx_applications_opportunity_id
    ON public.applications (opportunity_id);

CREATE INDEX IF NOT EXISTS idx_applications_status
    ON public.applications (status);

-- Fast lookup of all submitted (non-draft) applications
CREATE INDEX IF NOT EXISTS idx_applications_submitted
    ON public.applications (student_id, applied_at DESC)
    WHERE status != 'draft';

CREATE TRIGGER trg_applications_updated_at
    BEFORE UPDATE ON public.applications
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
