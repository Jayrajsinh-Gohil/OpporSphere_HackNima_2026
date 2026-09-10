-- =============================================================================
-- V009 — Utility views and helper functions
-- =============================================================================

-- ─────────────────────────────────────────────────────────────────────────────
-- VIEW: opportunity_summary
-- Joins opportunity + trust score + event count for the discovery feed.
-- ─────────────────────────────────────────────────────────────────────────────

CREATE OR REPLACE VIEW public.opportunity_summary AS
SELECT
    o.id,
    o.title,
    o.description,
    o.domain,
    o.type,
    o.eligibility,
    o.deadline,
    o.location,
    o.organizer,
    o.source_url,
    o.is_active,
    o.created_at,

    -- Trust
    COALESCE(ts.score, 0)              AS trust_score,
    COALESCE(ts.duplicate_flag, FALSE) AS is_duplicate,
    ts.quality_flags,

    -- Event count
    COUNT(DISTINCT e.id)               AS event_count
FROM  public.opportunities  o
LEFT  JOIN public.trust_scores ts ON ts.opportunity_id = o.id
LEFT  JOIN public.events       e  ON e.opportunity_id  = o.id
GROUP BY o.id, ts.score, ts.duplicate_flag, ts.quality_flags;

COMMENT ON VIEW public.opportunity_summary
    IS 'Denormalised read model for the discovery feed. Do not write to this view.';


-- ─────────────────────────────────────────────────────────────────────────────
-- VIEW: student_team_summary
-- Shows a student's current active team memberships.
-- ─────────────────────────────────────────────────────────────────────────────

CREATE OR REPLACE VIEW public.student_team_summary AS
SELECT
    s.id            AS student_id,
    s.name          AS student_name,
    t.id            AS team_id,
    t.name          AS team_name,
    tm.role,
    e.id            AS event_id,
    o.title         AS opportunity_title,
    e.status        AS event_status,
    tm.joined_at
FROM  public.team_members tm
JOIN  public.students     s  ON s.id  = tm.student_id
JOIN  public.teams        t  ON t.id  = tm.team_id
JOIN  public.events       e  ON e.id  = t.event_id
JOIN  public.opportunities o ON o.id  = e.opportunity_id;

COMMENT ON VIEW public.student_team_summary
    IS 'Flattened view of student ↔ team ↔ event ↔ opportunity relationships.';


-- ─────────────────────────────────────────────────────────────────────────────
-- FUNCTION: match_opportunities(query_embedding vector, top_k int, min_score float)
-- Encapsulates the cosine nearest-neighbour query so the API layer can call
-- it with a single RPC:
--   supabase.rpc("match_opportunities", {"query_embedding": [...], "top_k": 10})
-- ─────────────────────────────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION public.match_opportunities(
    query_embedding vector(384),
    top_k           INT     DEFAULT 10,
    min_score       FLOAT   DEFAULT 0.5
)
RETURNS TABLE (
    id          UUID,
    title       TEXT,
    description TEXT,
    domain      opportunity_domain,
    type        opportunity_type,
    trust_score SMALLINT,
    similarity  FLOAT
)
LANGUAGE sql STABLE
AS $$
    SELECT
        o.id,
        o.title,
        o.description,
        o.domain,
        o.type,
        COALESCE(ts.score, 0)                                   AS trust_score,
        1 - (o.embedding <=> query_embedding)                   AS similarity
    FROM  public.opportunities o
    LEFT  JOIN public.trust_scores ts ON ts.opportunity_id = o.id
    WHERE o.is_active = TRUE
      AND o.embedding IS NOT NULL
      AND (1 - (o.embedding <=> query_embedding)) >= min_score
    ORDER BY o.embedding <=> query_embedding   -- ascending distance = descending similarity
    LIMIT top_k;
$$;

COMMENT ON FUNCTION public.match_opportunities
    IS 'Cosine nearest-neighbour search over opportunities. Call via supabase.rpc("match_opportunities", ...).';


-- ─────────────────────────────────────────────────────────────────────────────
-- FUNCTION: match_students(query_embedding vector, top_k int, min_score float)
-- Mirror function for team-finder: find students similar to a role description.
-- ─────────────────────────────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION public.match_students(
    query_embedding vector(384),
    top_k           INT     DEFAULT 10,
    min_score       FLOAT   DEFAULT 0.4
)
RETURNS TABLE (
    id          UUID,
    name        TEXT,
    skills      TEXT[],
    department  TEXT,
    similarity  FLOAT
)
LANGUAGE sql STABLE
AS $$
    SELECT
        s.id,
        s.name,
        s.skills,
        s.department,
        1 - (s.embedding <=> query_embedding) AS similarity
    FROM  public.students s
    WHERE s.is_active = TRUE
      AND s.embedding IS NOT NULL
      AND (1 - (s.embedding <=> query_embedding)) >= min_score
    ORDER BY s.embedding <=> query_embedding
    LIMIT top_k;
$$;

COMMENT ON FUNCTION public.match_students
    IS 'Cosine nearest-neighbour search over student profiles. Call via supabase.rpc("match_students", ...).';
