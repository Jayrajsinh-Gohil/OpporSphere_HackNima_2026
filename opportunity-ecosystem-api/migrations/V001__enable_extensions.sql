-- =============================================================================
-- V001 — Enable required Postgres extensions
-- Run once per Supabase project (safe to re-run; uses IF NOT EXISTS).
-- =============================================================================

-- Vector similarity search (required for embedding columns)
CREATE EXTENSION IF NOT EXISTS vector;

-- UUID generation helpers
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Case-insensitive text (used for email uniqueness)
CREATE EXTENSION IF NOT EXISTS citext;

-- Full-text search improvements
CREATE EXTENSION IF NOT EXISTS pg_trgm;
