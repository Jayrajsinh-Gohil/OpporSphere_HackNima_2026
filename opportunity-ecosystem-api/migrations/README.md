# Database Migrations

SQL migration scripts for the Supabase Postgres project.  
Files are prefixed with `V<number>__<description>.sql` and must be run **in order**.

## Execution Order

| File | Description |
|------|-------------|
| `V001__enable_extensions.sql` | Enable `pgvector`, `uuid-ossp`, `citext`, `pg_trgm` |
| `V002__students_and_opportunities.sql` | Core tables + ENUMs + `updated_at` trigger |
| `V003__events.sql` | Events table (FK → opportunities) |
| `V004__trust_scores.sql` | Trust score table with partial indexes |
| `V005__teams_and_members.sql` | Teams + team_members junction table |
| `V006__applications.sql` | Application lifecycle table |
| `V007__vector_indexes.sql` | IVFFlat cosine indexes on both embedding columns |
| `V008__rls_policies.sql` | Row Level Security policies for all tables |
| `V009__views_and_functions.sql` | Read views + `match_opportunities` / `match_students` RPCs |
| `V010__team_finder_invites.sql` | Team invites, status, and preferred roles for Phase B6 |
| `seed.sql` | **Dev only** — sample opportunities, events, trust scores |

## How to Apply

### Option A — Supabase Dashboard (recommended for first setup)
1. Open your Supabase project → **SQL Editor**
2. Paste and run each file in order

### Option B — Supabase CLI
```bash
# Install Supabase CLI
npm install -g supabase

# Link to your project
supabase link --project-ref <your-project-ref>

# Push migrations (requires supabase/migrations/ layout — copy files there)
supabase db push
```

### Option C — psql directly
```bash
psql "$DATABASE_URL" \
  -f migrations/V001__enable_extensions.sql \
  -f migrations/V002__students_and_opportunities.sql \
  -f migrations/V003__events.sql \
  -f migrations/V004__trust_scores.sql \
  -f migrations/V005__teams_and_members.sql \
  -f migrations/V006__applications.sql \
  -f migrations/V007__vector_indexes.sql \
  -f migrations/V008__rls_policies.sql \
  -f migrations/V009__views_and_functions.sql

# Seed dev data (skip in production)
psql "$DATABASE_URL" -f migrations/seed.sql
```

## Key Design Decisions

### Vector dimensions — `vector(384)`
Matches `sentence-transformers/all-MiniLM-L6-v2` and OpenAI `text-embedding-3-small` (truncated).  
**If using full OpenAI 1536-dim embeddings**, change all `vector(384)` → `vector(1536)` and update `lists` in V007.

### IVFFlat index tuning
```sql
-- Set before any similarity query in your session / connection pool
SET ivfflat.probes = 10;  -- default 1; raise for better recall
```

Rebuild indexes after bulk data loads:
```sql
REINDEX INDEX idx_students_embedding_cosine;
REINDEX INDEX idx_opportunities_embedding_cosine;
```

### RLS quick reference
| Table | anon | authenticated | service_role |
|-------|------|---------------|--------------|
| students | ❌ | SELECT all, INSERT/UPDATE own | ✅ all |
| opportunities | SELECT active | SELECT active | ✅ all |
| events | SELECT open | SELECT all | ✅ all |
| trust_scores | SELECT | SELECT | ✅ all |
| teams | ❌ | SELECT open + own, INSERT/UPDATE/DELETE own | ✅ all |
| team_members | ❌ | SELECT own teams, INSERT self/by creator | ✅ all |
| applications | ❌ | SELECT/INSERT/UPDATE/DELETE own | ✅ all |

### Supabase RPC calls (from Python)
```python
# Similarity search — replaces manual embedding query in FastAPI service
result = supabase.rpc(
    "match_opportunities",
    {"query_embedding": vector_list, "top_k": 10, "min_score": 0.5}
).execute()
```
