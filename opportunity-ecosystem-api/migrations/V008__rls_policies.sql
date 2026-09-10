-- =============================================================================
-- V008 — Row Level Security (RLS) policies
--
-- All tables have RLS ENABLED.  Policy logic is documented per table.
-- The `auth.uid()` function is provided by Supabase Auth middleware and
-- returns the UUID of the currently authenticated user.
--
-- Convention:
--   - "authenticated" role  = logged-in users (Supabase JWT verified)
--   - "service_role"        = backend server using the service-role key
--     (bypasses RLS automatically — no explicit policy needed)
--   - "anon"                = unauthenticated / public API callers
-- =============================================================================


-- ─────────────────────────────────────────────────────────────────────────────
-- STUDENTS
-- ─────────────────────────────────────────────────────────────────────────────

ALTER TABLE public.students ENABLE ROW LEVEL SECURITY;

-- Any authenticated user can read any student profile (directory mode).
-- Tighten to `auth.uid() = id` if you want private-by-default profiles.
CREATE POLICY "students_select_authenticated"
    ON public.students
    FOR SELECT
    TO authenticated
    USING (TRUE);

-- A student can only insert their own profile row.
CREATE POLICY "students_insert_own"
    ON public.students
    FOR INSERT
    TO authenticated
    WITH CHECK (auth.uid() = id);

-- A student can only update their own profile row.
CREATE POLICY "students_update_own"
    ON public.students
    FOR UPDATE
    TO authenticated
    USING (auth.uid() = id)
    WITH CHECK (auth.uid() = id);

-- Hard-delete is disallowed for students via API; use is_active = FALSE.
-- (service_role can still hard-delete via admin endpoints.)


-- ─────────────────────────────────────────────────────────────────────────────
-- OPPORTUNITIES
-- ─────────────────────────────────────────────────────────────────────────────

ALTER TABLE public.opportunities ENABLE ROW LEVEL SECURITY;

-- Public read — anyone (even anon) can browse opportunities.
CREATE POLICY "opportunities_select_public"
    ON public.opportunities
    FOR SELECT
    TO anon, authenticated
    USING (is_active = TRUE);

-- Only the service_role (backend) can insert/update/delete opportunities.
-- No explicit policy = blocked for anon/authenticated by default.
-- If you add an "organizer" role later, expand this policy.


-- ─────────────────────────────────────────────────────────────────────────────
-- EVENTS
-- ─────────────────────────────────────────────────────────────────────────────

ALTER TABLE public.events ENABLE ROW LEVEL SECURITY;

-- Public read for active/upcoming events.
CREATE POLICY "events_select_public"
    ON public.events
    FOR SELECT
    TO anon, authenticated
    USING (status IN ('upcoming', 'open'));

-- Authenticated users can see all event statuses (including closed/cancelled)
-- so they can track events they participated in.
CREATE POLICY "events_select_authenticated_all"
    ON public.events
    FOR SELECT
    TO authenticated
    USING (TRUE);

-- Write access: service_role only (handled via backend service).


-- ─────────────────────────────────────────────────────────────────────────────
-- TRUST SCORES
-- ─────────────────────────────────────────────────────────────────────────────

ALTER TABLE public.trust_scores ENABLE ROW LEVEL SECURITY;

-- Trust scores are read-only for all client roles; written only by the backend.
CREATE POLICY "trust_scores_select_authenticated"
    ON public.trust_scores
    FOR SELECT
    TO authenticated
    USING (TRUE);

-- Anonymous users can also read trust scores (helps surface quality signals).
CREATE POLICY "trust_scores_select_anon"
    ON public.trust_scores
    FOR SELECT
    TO anon
    USING (TRUE);

-- INSERT / UPDATE / DELETE: service_role only (no client policy needed).


-- ─────────────────────────────────────────────────────────────────────────────
-- TEAMS
-- ─────────────────────────────────────────────────────────────────────────────

ALTER TABLE public.teams ENABLE ROW LEVEL SECURITY;

-- Any authenticated user can see open teams.
CREATE POLICY "teams_select_open"
    ON public.teams
    FOR SELECT
    TO authenticated
    USING (is_open = TRUE);

-- A student can always see teams they created (even invite-only).
CREATE POLICY "teams_select_own"
    ON public.teams
    FOR SELECT
    TO authenticated
    USING (created_by = auth.uid());

-- Any authenticated user may create a team.
CREATE POLICY "teams_insert_authenticated"
    ON public.teams
    FOR INSERT
    TO authenticated
    WITH CHECK (created_by = auth.uid());

-- Only the team creator can update team metadata.
CREATE POLICY "teams_update_creator"
    ON public.teams
    FOR UPDATE
    TO authenticated
    USING (created_by = auth.uid())
    WITH CHECK (created_by = auth.uid());

-- Only the team creator can delete the team.
CREATE POLICY "teams_delete_creator"
    ON public.teams
    FOR DELETE
    TO authenticated
    USING (created_by = auth.uid());


-- ─────────────────────────────────────────────────────────────────────────────
-- TEAM MEMBERS
-- ─────────────────────────────────────────────────────────────────────────────

ALTER TABLE public.team_members ENABLE ROW LEVEL SECURITY;

-- A student can see members of any team they belong to.
CREATE POLICY "team_members_select_own_teams"
    ON public.team_members
    FOR SELECT
    TO authenticated
    USING (
        team_id IN (
            SELECT team_id FROM public.team_members WHERE student_id = auth.uid()
        )
    );

-- A student can add themselves to an open team.
CREATE POLICY "team_members_insert_self"
    ON public.team_members
    FOR INSERT
    TO authenticated
    WITH CHECK (
        student_id = auth.uid()
        AND EXISTS (
            SELECT 1 FROM public.teams
            WHERE id = team_id AND is_open = TRUE
        )
    );

-- Team creator can add any student (invite flow).
CREATE POLICY "team_members_insert_creator"
    ON public.team_members
    FOR INSERT
    TO authenticated
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.teams
            WHERE id = team_id AND created_by = auth.uid()
        )
    );

-- A student can remove themselves; team creator can remove any member.
CREATE POLICY "team_members_delete_self_or_creator"
    ON public.team_members
    FOR DELETE
    TO authenticated
    USING (
        student_id = auth.uid()
        OR EXISTS (
            SELECT 1 FROM public.teams
            WHERE id = team_id AND created_by = auth.uid()
        )
    );


-- ─────────────────────────────────────────────────────────────────────────────
-- APPLICATIONS
-- ─────────────────────────────────────────────────────────────────────────────

ALTER TABLE public.applications ENABLE ROW LEVEL SECURITY;

-- A student can only see their own applications.
CREATE POLICY "applications_select_own"
    ON public.applications
    FOR SELECT
    TO authenticated
    USING (student_id = auth.uid());

-- A student can create their own application.
CREATE POLICY "applications_insert_own"
    ON public.applications
    FOR INSERT
    TO authenticated
    WITH CHECK (student_id = auth.uid());

-- A student can update their own application (e.g. change notes, withdraw).
CREATE POLICY "applications_update_own"
    ON public.applications
    FOR UPDATE
    TO authenticated
    USING (student_id = auth.uid())
    WITH CHECK (student_id = auth.uid());

-- A student can withdraw (delete) their own application.
CREATE POLICY "applications_delete_own"
    ON public.applications
    FOR DELETE
    TO authenticated
    USING (student_id = auth.uid() AND status = 'draft');
