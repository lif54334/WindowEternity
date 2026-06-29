export type SinceValue = "daily" | "weekly" | "monthly";

export interface SettingsResponse {
  auto_refresh_enabled: boolean;
  refresh_interval_minutes: number;
  refresh_time_of_day: string;
  default_since: SinceValue;
  default_language: string | null;
  max_repositories_per_refresh: number;
  font_size_percent: number;
  llm_base_url: string | null;
  llm_model: string | null;
  llm_timeout_seconds: number;
  llm_custom_prompt: string | null;
  has_llm_api_key: boolean;
  updated_at: string | null;
}

export interface SettingsUpdate extends Omit<SettingsResponse, "has_llm_api_key" | "updated_at"> {
  llm_api_key?: string | null;
}

export interface AnalysisResponse {
  status: string;
  summary: string | null;
  category: string | null;
  reasons: string | null;
  error_message: string | null;
  created_at: string | null;
}

export interface RepositoryResponse {
  id: number;
  owner: string;
  name: string;
  url: string;
  description: string | null;
  detail_description: string | null;
  topics: string[];
  readme_excerpt: string | null;
  language: string | null;
  stars: number | null;
  forks: number | null;
  stars_today: number | null;
  rank: number;
  analysis: AnalysisResponse | null;
}

export interface RefreshRunResponse {
  id: number;
  source_url: string;
  since: string;
  language: string | null;
  status: string;
  started_at: string | null;
  finished_at: string | null;
  error_message: string | null;
  ai_summary_status: string | null;
  ai_summary: string | null;
  ai_summary_error: string | null;
}

export interface TrendingResponse {
  repositories: RepositoryResponse[];
  latest_run: RefreshRunResponse | null;
  settings: SettingsResponse;
}

export interface RefreshHistoryResponse {
  runs: RefreshRunResponse[];
}

export interface LanguageStat {
  language: string;
  count: number;
}

export interface CategoryStat {
  category: string;
  count: number;
}

export interface TrendingStatsResponse {
  repository_count: number;
  language_distribution: LanguageStat[];
  top_repositories: RepositoryResponse[];
  category_distribution: CategoryStat[];
}

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

const jsonHeaders = { "Content-Type": "application/json" };

export async function getSettings(): Promise<SettingsResponse> {
  return request<SettingsResponse>("/api/settings");
}

export async function saveSettings(payload: SettingsUpdate): Promise<SettingsResponse> {
  return request<SettingsResponse>("/api/settings", {
    method: "PUT",
    headers: jsonHeaders,
    body: JSON.stringify(payload),
  });
}

export async function getTrending(since?: SinceValue, language?: string): Promise<TrendingResponse> {
  const params = trendingParams(since, language);
  const query = params.toString();
  return request<TrendingResponse>(`/api/trending${query ? `?${query}` : ""}`);
}

export async function refreshTrending(since?: SinceValue, language?: string): Promise<TrendingResponse> {
  return request<TrendingResponse>("/api/trending/refresh", {
    method: "POST",
    headers: jsonHeaders,
    body: JSON.stringify({ since, language: language?.trim() || null, force_analyze: true }),
  });
}

export async function analyzeTrending(since?: SinceValue, language?: string): Promise<TrendingResponse> {
  return request<TrendingResponse>("/api/trending/analyze", {
    method: "POST",
    headers: jsonHeaders,
    body: JSON.stringify({ since, language: language?.trim() || null }),
  });
}

export async function getTrendingStats(since?: SinceValue, language?: string): Promise<TrendingStatsResponse> {
  const params = trendingParams(since, language);
  const query = params.toString();
  return request<TrendingStatsResponse>(`/api/trending/stats${query ? `?${query}` : ""}`);
}

export async function getRefreshHistory(limit = 20): Promise<RefreshHistoryResponse> {
  const params = new URLSearchParams({ limit: String(limit) });
  return request<RefreshHistoryResponse>(`/api/trending/history?${params.toString()}`);
}

function trendingParams(since?: SinceValue, language?: string): URLSearchParams {
  const params = new URLSearchParams();
  if (since) params.set("since", since);
  if (language?.trim()) params.set("language", language.trim());
  return params;
}

async function request<T>(input: RequestInfo, init?: RequestInit): Promise<T> {
  const response = await fetch(input, init);
  if (!response.ok) {
    let message = `Request failed with status ${response.status}`;
    try {
      const data = (await response.json()) as { detail?: unknown };
      if (typeof data.detail === "string") message = data.detail;
    } catch {
      // Keep default message when the response is not JSON.
    }
    throw new ApiError(response.status, message);
  }
  return (await response.json()) as T;
}