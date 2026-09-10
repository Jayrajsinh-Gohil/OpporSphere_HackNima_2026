-- =============================================================================
-- seed.sql — Development seed data
-- Run ONLY in development / staging environments.
-- Safe to re-run: uses ON CONFLICT DO NOTHING.
-- =============================================================================

-- ─── Opportunities ─────────────────────────────────────────────────────────
INSERT INTO public.opportunities
    (id, title, description, domain, type, eligibility, deadline, location, organizer, source_url)
VALUES
(
    '00000000-0000-0000-0000-000000000001',
    'HackNima 2025',
    'A 48-hour hackathon focused on AI-powered social impact solutions for students across India.',
    'technology',
    'hackathon',
    'Open to undergraduate and postgraduate students enrolled in any Indian university.',
    '2025-11-15',
    'Bengaluru, India (Hybrid)',
    'NimaTech Foundation',
    'https://hacknima.dev'
),
(
    '00000000-0000-0000-0000-000000000002',
    'Google Summer Internship 2025',
    'Join Google''s engineering team for a 12-week paid summer internship. Work on real products used by billions.',
    'technology',
    'internship',
    'Final-year undergraduate or first-year postgraduate students in CS or related fields.',
    '2025-12-01',
    'Hyderabad, India',
    'Google LLC',
    'https://careers.google.com/students/'
),
(
    '00000000-0000-0000-0000-000000000003',
    'ML Foundations Workshop',
    'A 3-day intensive workshop covering core ML concepts: regression, classification, clustering, and neural nets.',
    'technology',
    'workshop',
    'Basic Python knowledge required. Open to all levels.',
    '2025-10-05',
    'Online',
    'DeepLearn Institute',
    'https://deeplearn.institute/ml-foundations'
),
(
    '00000000-0000-0000-0000-000000000004',
    'National Climate Action Competition 2025',
    'Submit a policy brief or tech prototype addressing climate change in a developing nation context.',
    'environment',
    'competition',
    'Open to teams of 1–4 students from any discipline.',
    '2025-09-30',
    'New Delhi, India',
    'Ministry of Environment, Forest and Climate Change',
    'https://moefcc.nic.in/competition'
)
ON CONFLICT (id) DO NOTHING;


-- ─── Trust scores for seeded opportunities ─────────────────────────────────
INSERT INTO public.trust_scores
    (opportunity_id, score, duplicate_flag, quality_flags, computed_at)
VALUES
(
    '00000000-0000-0000-0000-000000000001',
    88, FALSE,
    '{"has_organizer": true, "has_deadline": true, "has_url": true, "url_reachable": true}',
    NOW()
),
(
    '00000000-0000-0000-0000-000000000002',
    95, FALSE,
    '{"has_organizer": true, "has_deadline": true, "has_url": true, "url_reachable": true, "known_brand": true}',
    NOW()
),
(
    '00000000-0000-0000-0000-000000000003',
    72, FALSE,
    '{"has_organizer": true, "has_deadline": true, "has_url": true}',
    NOW()
),
(
    '00000000-0000-0000-0000-000000000004',
    91, FALSE,
    '{"has_organizer": true, "has_deadline": true, "has_url": true, "government_source": true}',
    NOW()
)
ON CONFLICT (opportunity_id) DO NOTHING;


-- ─── Events linked to opportunities ────────────────────────────────────────
INSERT INTO public.events
    (id, opportunity_id, status, registration_link, extra_details)
VALUES
(
    '10000000-0000-0000-0000-000000000001',
    '00000000-0000-0000-0000-000000000001',
    'open',
    'https://hacknima.dev/register',
    '{"start_date": "2025-11-15", "end_date": "2025-11-17", "max_team_size": 4, "prize_pool": "₹5,00,000"}'
),
(
    '10000000-0000-0000-0000-000000000002',
    '00000000-0000-0000-0000-000000000003',
    'upcoming',
    'https://deeplearn.institute/register',
    '{"start_date": "2025-10-05", "end_date": "2025-10-07", "seats": 200, "format": "online"}'
)
ON CONFLICT (id) DO NOTHING;
