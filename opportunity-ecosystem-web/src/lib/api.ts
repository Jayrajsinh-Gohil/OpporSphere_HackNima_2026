import { supabase } from "./supabaseClient";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/+$/, "") || "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  data: unknown;

  constructor(status: number, message: string, data?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.data = data;
  }
}

/**
 * Retrieve current Supabase access token (JWT) if a user session exists.
 */
export async function getAuthToken(): Promise<string | null> {
  try {
    const {
      data: { session },
      error,
    } = await supabase.auth.getSession();
    if (error || !session) {
      return null;
    }
    return session.access_token;
  } catch (err) {
    console.error("Error retrieving Supabase session token:", err);
    return null;
  }
}

/**
 * Core fetch wrapper that automatically attaches the Supabase JWT Bearer token
 * and standard headers.
 */
export async function fetchWithAuth<T = unknown>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = await getAuthToken();
  const url = `${API_BASE_URL}${endpoint.startsWith("/") ? endpoint : `/${endpoint}`}`;

  const headers: Record<string, string> = {
    Accept: "application/json",
    ...(options.headers as Record<string, string>),
  };

  // Attach token if present
  if (token && !headers["Authorization"]) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  // Attach JSON content-type if body is an object string and not FormData
  if (options.body && typeof options.body === "string" && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  const contentType = response.headers.get("content-type");
  let responseData: unknown = null;
  if (contentType && contentType.includes("application/json")) {
    responseData = await response.json();
  } else {
    responseData = await response.text();
  }

  if (!response.ok) {
    const errorMessage =
      (responseData as { detail?: string })?.detail ||
      (typeof responseData === "string" && responseData) ||
      response.statusText ||
      "API request failed";
    throw new ApiError(response.status, errorMessage, responseData);
  }

  return responseData as T;
}

// ─────────────────────────────────────────────────────────────────────────────
// Convenience HTTP methods
// ─────────────────────────────────────────────────────────────────────────────

export const api = {
  get: <T = unknown>(endpoint: string, options?: RequestInit) =>
    fetchWithAuth<T>(endpoint, { ...options, method: "GET" }),

  post: <T = unknown>(endpoint: string, body?: unknown, options?: RequestInit) =>
    fetchWithAuth<T>(endpoint, {
      ...options,
      method: "POST",
      body: body ? JSON.stringify(body) : undefined,
    }),

  patch: <T = unknown>(endpoint: string, body?: unknown, options?: RequestInit) =>
    fetchWithAuth<T>(endpoint, {
      ...options,
      method: "PATCH",
      body: body ? JSON.stringify(body) : undefined,
    }),

  put: <T = unknown>(endpoint: string, body?: unknown, options?: RequestInit) =>
    fetchWithAuth<T>(endpoint, {
      ...options,
      method: "PUT",
      body: body ? JSON.stringify(body) : undefined,
    }),

  delete: <T = unknown>(endpoint: string, options?: RequestInit) =>
    fetchWithAuth<T>(endpoint, { ...options, method: "DELETE" }),

  // ───────────────────────────────────────────────────────────────────────────
  // Domain Specific Endpoints
  // ───────────────────────────────────────────────────────────────────────────

  health: () => api.get<{ status: string; version?: string }>("/health"),

  // Team Finder
  teamFinder: {
    getMatches: (eventId: string, preferredRole?: string, topK: number = 10) => {
      const roleParam = preferredRole ? `&preferred_role=${encodeURIComponent(preferredRole)}` : "";
      return api.get<APIResponseEnvelope<TeamMatchesResponse>>(
        `/api/team-finder/matches?event_id=${encodeURIComponent(eventId)}${roleParam}&top_k=${topK}`
      );
    },

    getEvents: () =>
      api.get<APIResponseEnvelope<Array<{
        id: string;
        opportunity_id: string;
        title: string;
        domain: string;
        type: string;
        location: string;
        organizer: string;
        deadline: string;
        date: string;
        status: string;
        prize_pool?: string;
        max_team_size?: number;
        format?: string;
      }>>>("/api/team-finder/events"),

    getCandidates: (params?: { limit?: number; role?: string; location?: string }) => {
      const qs = params ? `?${new URLSearchParams(params as Record<string, string>).toString()}` : "";
      return api.get<APIResponseEnvelope<Array<{
        student_id: string;
        name: string;
        department: string;
        location: string;
        preferred_role: string;
        skills: string[];
        interests: string[];
        career_goals: string;
        avatar_url?: string;
      }>>>(`/api/team-finder/candidates${qs}`);
    },

    invite: (payload: TeamInviteRequest) =>
      api.post<APIResponseEnvelope<TeamInviteResponse>>("/api/team-finder/invite", payload),

    createTeam: (payload: TeamCreateRequest) =>
      api.post<APIResponseEnvelope<TeamResponse>>("/api/team-finder/teams", payload),
  },

  // Smart Discovery
  discovery: {
    search: (query: string, topK: number = 10) =>
      api.post<APIResponseEnvelope<SmartSearchResponse>>("/api/discovery/search", { query, top_k: topK }),
    smartSearch: (query: string, topK: number = 10) =>
      api.post<APIResponseEnvelope<SmartSearchResponse>>("/api/discovery/search", { query, top_k: topK }),
  },

  // AI Student Copilot
  copilot: {
    chat: (payload: CopilotChatRequest) =>
      api.post<APIResponseEnvelope<CopilotChatResponse>>("/api/copilot/chat", payload),
  },

  // Student Profile
  student: {
    getProfile: () => api.get<APIResponseEnvelope<StudentProfileResponse>>("/api/students/me"),
    createOrUpdateProfile: (data: StudentCreateInput) =>
      api.post<APIResponseEnvelope<StudentProfileResponse>>("/api/students/me", data),
    updateProfile: (profile: Partial<StudentCreateInput>) =>
      api.patch<APIResponseEnvelope<StudentProfileResponse>>("/api/students/me", profile),
  },

  // Match Module
  match: {
    getRecommendations: (topK: number = 10, minScore: number = 0.0) =>
      api.get<APIResponseEnvelope<RecommendationsResponse>>(
        `/api/match/recommendations?top_k=${topK}&min_score=${minScore}`
      ),
    matchOpportunities: (payload: { user_id: string; top_k?: number; min_score?: number }) =>
      api.post<APIResponseEnvelope<unknown>>("/api/match/", payload),
  },

  // Opportunities & Events
  opportunities: {
    list: (params?: Record<string, string | number>) => {
      const qs = params ? `?${new URLSearchParams(params as Record<string, string>).toString()}` : "";
      return api.get<APIResponseEnvelope<OpportunityListItem[]> | OpportunityListItem[]>(`/api/opportunities${qs}`);
    },
    get: (id: string) => api.get<APIResponseEnvelope<OpportunityDetail> | OpportunityDetail>(`/api/opportunities/${id}`),
    events: () =>
      api.get<APIResponseEnvelope<Array<Record<string, unknown>>>>("/api/team-finder/events"),
  },

  // Admin Portal
  admin: {
    me: () =>
      api.get<APIResponseEnvelope<AdminMeResponse>>("/api/admin/me"),
    getMetrics: () =>
      api.get<APIResponseEnvelope<AdminMetricsResponse>>("/api/admin/metrics"),
    getOpportunities: (params?: { q?: string; domain?: string; type?: string; page?: number; page_size?: number }) => {
      const qs = params ? `?${new URLSearchParams(params as unknown as Record<string, string>).toString()}` : "";
      return api.get<APIResponseEnvelope<AdminOpportunitiesResponse>>(`/api/admin/opportunities${qs}`);
    },
    createOpportunity: (payload: AdminCreateOpportunityInput) =>
      api.post<APIResponseEnvelope<OpportunityDetail>>("/api/opportunities", payload),
    deleteOpportunity: (id: string) =>
      api.delete<APIResponseEnvelope<{ id: string }>>(`/api/admin/opportunities/${id}`),
    getStudents: (params?: { q?: string; page?: number; page_size?: number }) => {
      const qs = params ? `?${new URLSearchParams(params as unknown as Record<string, string>).toString()}` : "";
      return api.get<APIResponseEnvelope<AdminStudentsResponse>>(`/api/admin/students${qs}`);
    },
    getSettings: () =>
      api.get<APIResponseEnvelope<AdminSettingItem[]>>("/api/admin/settings"),
    updateSetting: (key: string, value: string) =>
      api.patch<APIResponseEnvelope<AdminSettingItem[]>>("/api/admin/settings", { key, value }),
    getRoster: () =>
      api.get<APIResponseEnvelope<AdminRosterItem[]>>("/api/admin/roster"),
  },
};

// ─────────────────────────────────────────────────────────────────────────────
// Type Definitions
// ─────────────────────────────────────────────────────────────────────────────

export interface TeamMatchItem {
  student_id: string;
  name: string;
  avatar_url?: string | null;
  department?: string | null;
  skills: string[];
  interests: string[];
  preferred_role: string;
  similarity_score: number;
  role_bonus: number;
  match_score: number;
  match_percentage: number;
  is_complementary: boolean;
  shared_skills: string[];
  complementary_skills: string[];
  recommendation_reason: string;
}

export interface TeamMatchesResponse {
  event_id: string;
  event_title: string;
  current_student_id: string;
  current_student_name: string;
  current_student_role: string;
  total_candidates: number;
  matches: TeamMatchItem[];
}

export interface TeamInviteRequest {
  event_id: string;
  invited_student_id: string;
  team_id?: string | null;
  role?: string;
  custom_message?: string | null;
}

export interface TeamInviteResponse {
  invite_id: string;
  team_id: string;
  team_name: string;
  event_id: string;
  inviter_id: string;
  inviter_name: string;
  invited_student_id: string;
  invited_student_name: string;
  role: string;
  status: string;
  message: string;
  created_at: string;
}

export interface TeamCreateRequest {
  event_id: string;
  name: string;
  member_ids?: string[];
  is_open?: boolean;
}

export interface TeamMemberOut {
  student_id: string;
  name: string;
  role: string;
  status: string;
  avatar_url?: string | null;
  joined_at?: string | null;
}

export interface TeamResponse {
  id: string;
  event_id: string;
  name: string;
  created_by: string;
  is_open: boolean;
  created_at: string;
  members: TeamMemberOut[];
}

export type TeamFinderMatch = TeamMatchItem;
export type TeamFinderMatchesResponse = TeamMatchesResponse;
export type CreateTeamRequest = TeamCreateRequest;
export type CreateTeamResponse = TeamResponse;

export interface ExtractedFilters {
  domain?: string | null;
  location?: string | null;
  department?: string | null;
  opportunity_type?: string | null;
  deadline_from?: string | null;
  deadline_to?: string | null;
  raw_entities?: Record<string, string[]>;
}

export interface DiscoveredOpportunityItem {
  id: string;
  title: string;
  description: string;
  domain?: string | null;
  type?: string | null;
  location?: string | null;
  organizer?: string | null;
  deadline?: string | null;
  trust_score?: number;
  relevance_score?: number;
  match_reason: string;
}

export interface SmartSearchResponse {
  query: string;
  search_mode: "structured_filter" | "semantic_fallback" | "hybrid" | string;
  confidence_score: number;
  filters_applied: ExtractedFilters;
  total: number;
  results: DiscoveredOpportunityItem[];
}

export type DiscoveryFilters = ExtractedFilters;
export type DiscoverySearchResponse = SmartSearchResponse;

export interface OpportunityListItem {
  id: string;
  title: string;
  description: string;
  domain: string;
  location: string;
  type: string;
  deadline?: string;
  tags?: string[];
  [key: string]: unknown;
}

export interface OpportunityDetail extends OpportunityListItem {
  requirements?: string[];
  created_at?: string;
}

export interface CopilotChatRequest {
  session_id?: string;
  message: string;
}

export interface OpportunitySourceCitation {
  id: string;
  title: string;
  domain?: string | null;
  type?: string | null;
  location?: string | null;
  deadline?: string | null;
  similarity: number;
}

export interface CopilotChatResponse {
  session_id: string;
  answer: string;
  source_opportunity_ids: string[];
  sources: OpportunitySourceCitation[];
  retrieval_guard_triggered: boolean;
  is_fallback?: boolean;
}

export interface APIResponseEnvelope<T> {
  success: boolean;
  message: string;
  data: T;
  errors?: string[];
}

export interface StudentCreateInput {
  name: string;
  email: string;
  department?: string;
  location?: string;
  skills: string[];
  interests: string[];
  career_goals?: string;
  preferred_role?: string;
  avatar_url?: string;
}

export interface StudentProfileResponse {
  id: string;
  name?: string;
  full_name?: string;
  email: string;
  department?: string;
  location?: string;
  preferred_role?: string;
  skills?: string[];
  interests?: string[];
  career_goals?: string;
  bio?: string;
  avatar_url?: string;
}

export interface RecommendationItem {
  id: string;
  title: string;
  description: string;
  domain?: string;
  type?: string;
  location?: string;
  organizer?: string;
  deadline?: string;
  trust_score: number;
  similarity: number;
  match_relevance_pct: number;
  is_fallback: boolean;
  reason?: string;
}

export interface RecommendationsResponse {
  student_id: string;
  has_profile_embedding: boolean;
  has_interaction_history: boolean;
  recommendations: RecommendationItem[];
  total: number;
}

// ─────────────────────────────────────────────────────────────────────────────
// Admin Types
// ─────────────────────────────────────────────────────────────────────────────

export interface AdminMeResponse {
  id: string;
  email: string;
  name: string;
  role: string;
  is_admin: boolean;
}

export interface AdminMetricsResponse {
  total_students: number;
  total_opportunities: number;
  active_opportunities: number;
  total_events: number;
  total_admins: number;
  active_llm_provider: string;
  domain_distribution: Record<string, number>;
  type_distribution: Record<string, number>;
  settings: Record<string, string>;
}

export interface AdminOpportunityItem {
  id: string;
  title: string;
  description: string;
  domain: string;
  type: string;
  eligibility?: string;
  deadline?: string;
  location?: string;
  organizer?: string;
  source_url?: string;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
}

export interface AdminOpportunitiesResponse {
  items: AdminOpportunityItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface AdminStudentItem {
  id: string;
  name: string;
  email: string;
  department?: string;
  location?: string;
  skills?: string[];
  interests?: string[];
  career_goals?: string;
  avatar_url?: string;
  is_active: boolean;
  created_at: string;
}

export interface AdminStudentsResponse {
  items: AdminStudentItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface AdminSettingItem {
  key: string;
  value: string;
  description?: string;
  updated_by?: string;
  updated_at?: string;
}

export interface AdminRosterItem {
  id: string;
  email: string;
  role: string;
  added_by?: string;
  is_active: boolean;
  created_at: string;
}

export interface AdminCreateOpportunityInput {
  title: string;
  description: string;
  domain: string;
  type: string;
  location?: string;
  organizer?: string;
  deadline?: string;
  eligibility?: string;
  source_url?: string;
}


