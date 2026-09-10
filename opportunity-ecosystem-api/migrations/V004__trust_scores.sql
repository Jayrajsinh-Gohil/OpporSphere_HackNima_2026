-- =============================================================================
-- V004 — Trust scores
-- AI-computed quality & duplicate signals per opportunity.
-- =============================================================================

CREATE TABLE IF NOT EXISTS public.trust_scores (
    id              UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Target opportunity
    opportunity_id  UUID        NOT NULL
                        REFERENCES public.opportunities (id)
                        ON DELETE CASCADE,

    -- Scores & flags
    score           SMALLINT    NOT NULL DEFAULT 0
                        CHECK (score BETWEEN 0 AND 100),

    duplicate_flag  BOOLEAN     NOT NULL DEFAULT FALSE,

    -- Flexible quality signals:
    -- e.g. {"spam_likelihood": 0.02, "missing_deadline": true,
    --        "broken_url": false, "endorsements": 3, "flags": ["no_organizer"]}
    quality_flags   JSONB       NOT NULL DEFAULT '{}',

    -- When this score was last computed
    computed_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Prevent multiple score rows for the same opportunity
    CONSTRAINT uq_trust_scores_opportunity UNIQUE (opportunity_id)
);

COMMENT ON TABLE  public.trust_scores IS 'AI-computed trust / quality score for each opportunity.';
COMMENT ON COLUMN public.trust_scores.score IS 'Integer 0-100; higher = more trustworthy.';
COMMENT ON COLUMN public.trust_scores.duplicate_flag IS 'TRUE if this opportunity is likely a duplicate of another.';
COMMENT ON COLUMN public.trust_scores.quality_flags IS 'JSON bag of individual quality signals surfaced to the UI.';

-- Index for fast joins from opportunities
CREATE INDEX IF NOT EXISTS idx_trust_scores_opportunity_id
    ON public.trust_scores (opportunity_id);

-- Partial index: quickly find all flagged duplicates
CREATE INDEX IF NOT EXISTS idx_trust_scores_duplicates
    ON public.trust_scores (opportunity_id)
    WHERE duplicate_flag = TRUE;

-- Partial index: low-trust opportunities  (score < 40)
CREATE INDEX IF NOT EXISTS idx_trust_scores_low_quality
    ON public.trust_scores (score)
    WHERE score < 40;
