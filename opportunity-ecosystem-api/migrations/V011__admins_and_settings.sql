-- =============================================================================
-- V011 — Admins table + App Settings table
--
-- admins:       Stores admin emails managed in Supabase (replaces ADMIN_EMAILS env var).
-- app_settings: Key-value store for live runtime config (e.g. LLM_PROVIDER switch).
--               Admins can update these via Supabase dashboard without restarting.
-- =============================================================================


-- ─────────────────────────────────────────────────────────────────────────────
-- ADMINS TABLE
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.admins (
    id          UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    email       CITEXT      NOT NULL UNIQUE,
    role        TEXT        NOT NULL DEFAULT 'admin'
                            CHECK (role IN ('admin', 'super_admin')),
    added_by    TEXT,                           -- email of who granted access
    is_active   BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE  public.admins IS 'Platform admins — replaces ADMIN_EMAILS env var. Manage via Supabase dashboard.';
COMMENT ON COLUMN public.admins.role IS 'admin = standard admin; super_admin = can manage other admins.';
COMMENT ON COLUMN public.admins.added_by IS 'Email of the admin who granted this access.';

CREATE TRIGGER trg_admins_updated_at
    BEFORE UPDATE ON public.admins
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- RLS: only service_role can read/write (backend uses service_role key)
ALTER TABLE public.admins ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Service role full access on admins"
    ON public.admins
    FOR ALL
    USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');


-- ─────────────────────────────────────────────────────────────────────────────
-- APP_SETTINGS TABLE
-- Key-value store for live runtime configuration.
-- Admins can change LLM_PROVIDER from "gemini" to "ollama" here without
-- restarting the backend server.
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.app_settings (
    key         TEXT        PRIMARY KEY,
    value       TEXT        NOT NULL,
    description TEXT,
    updated_by  TEXT,                           -- email of admin who last changed it
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE  public.app_settings IS 'Live runtime configuration. Changes take effect on next API request (no restart needed).';
COMMENT ON COLUMN public.app_settings.key IS 'Setting name, e.g. LLM_PROVIDER, OLLAMA_MODEL.';
COMMENT ON COLUMN public.app_settings.value IS 'Setting value as text, e.g. gemini, ollama, llama3.2:3b.';

-- RLS: service_role can write; authenticated users can read (so frontend can check settings)
ALTER TABLE public.app_settings ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Service role write access on app_settings"
    ON public.app_settings
    FOR ALL
    USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

CREATE POLICY "Authenticated users read app_settings"
    ON public.app_settings
    FOR SELECT
    USING (auth.role() = 'authenticated');


-- ─────────────────────────────────────────────────────────────────────────────
-- SEED DEFAULT SETTINGS
-- ─────────────────────────────────────────────────────────────────────────────

INSERT INTO public.app_settings (key, value, description, updated_by) VALUES
    ('LLM_PROVIDER',  'gemini',        'LLM backend: gemini | ollama', 'system'),
    ('GEMINI_MODEL',  'gemini-2.0-flash', 'Gemini model name', 'system'),
    ('OLLAMA_MODEL',  'llama3.2:3b',   'Ollama model name when provider=ollama', 'system'),
    ('OLLAMA_HOST',   'http://localhost:11434', 'Ollama server URL', 'system')
ON CONFLICT (key) DO NOTHING;
