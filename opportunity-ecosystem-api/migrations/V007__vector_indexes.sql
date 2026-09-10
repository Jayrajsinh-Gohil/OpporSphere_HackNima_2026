-- =============================================================================
-- V007 — IVFFlat vector indexes for cosine similarity search
--
-- IVFFlat partitions the vector space into `lists` Voronoi cells.
-- At query time, `ivfflat.probes` cells are searched — higher probes =
-- better recall at the cost of speed.
--
-- Rule of thumb for `lists`:
--   rows < 1 M  →  lists = sqrt(rows)   e.g. 100 for 10 000 rows
--   rows > 1 M  →  lists = rows / 1000
--
-- These indexes are created WITHOUT the `WITH (lists = N)` clause so they
-- work on an empty table. Re-run `REINDEX INDEX` (or recreate with an
-- appropriate lists value) once the table has data.
-- =============================================================================

-- ─────────────────────────────────────────────────────────────────────────────
-- students.embedding  — cosine similarity for profile ↔ opportunity matching
-- ─────────────────────────────────────────────────────────────────────────────

CREATE INDEX IF NOT EXISTS idx_students_embedding_cosine
    ON public.students
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

COMMENT ON INDEX public.idx_students_embedding_cosine
    IS 'IVFFlat cosine index on student embeddings. Increase lists= when row count grows past 10k.';


-- ─────────────────────────────────────────────────────────────────────────────
-- opportunities.embedding  — cosine similarity for opportunity ranking
-- ─────────────────────────────────────────────────────────────────────────────

CREATE INDEX IF NOT EXISTS idx_opportunities_embedding_cosine
    ON public.opportunities
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

COMMENT ON INDEX public.idx_opportunities_embedding_cosine
    IS 'IVFFlat cosine index on opportunity embeddings. Increase lists= when row count grows past 10k.';


-- ─────────────────────────────────────────────────────────────────────────────
-- Session-level probe tuning  (add to app connection setup / pgbouncer config)
-- ─────────────────────────────────────────────────────────────────────────────
-- SET ivfflat.probes = 10;   -- default 1; raise for higher recall
--
-- Example cosine similarity query:
--
--   SELECT id, title,
--          1 - (embedding <=> $1::vector) AS similarity
--   FROM   public.opportunities
--   WHERE  is_active = TRUE
--   ORDER  BY embedding <=> $1::vector
--   LIMIT  20;
--
-- $1 = the query embedding as a JSON array, e.g. '[0.1, 0.2, ...]'::vector
