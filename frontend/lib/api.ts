import type {
  DashboardSummary,
  EntityDetail,
  EntityListResponse,
  EventDetail,
  EventListResponse,
  LatestBriefResponse,
  OpportunityListResponse,
  SearchResponse,
  ThemeDetail,
  ThemeListResponse,
  WatchlistListResponse
} from "@/types/api";
import { getApiBaseUrl } from "@/lib/api-base";

const EMPTY_DASHBOARD: DashboardSummary = { top_events: [], emerging_entities: [], theme_heatmap: [], opportunities: [], latest_brief: null };
const EMPTY_EVENTS: EventListResponse = { items: [], meta: { page: 1, page_size: 20, total: 0 } };
const EMPTY_ENTITIES: EntityListResponse = { items: [], meta: { page: 1, page_size: 20, total: 0 } };
const EMPTY_THEMES: ThemeListResponse = { items: [], meta: { page: 1, page_size: 20, total: 0 } };
const EMPTY_OPPORTUNITIES: OpportunityListResponse = { items: [], meta: { page: 1, page_size: 20, total: 0 } };
const EMPTY_WATCHLISTS: WatchlistListResponse = { items: [], meta: { page: 1, page_size: 20, total: 0 } };
const EMPTY_SEARCH: SearchResponse = { query: "", events: [], entities: [], documents: [] };

async function fetchJson<T>(path: string, fallback: T): Promise<T> {
  try {
    const response = await fetch(`${getApiBaseUrl()}${path}`, { cache: "no-store" });

    if (!response.ok) {
      return fallback;
    }

    return (await response.json()) as T;
  } catch {
    return fallback;
  }
}

function buildQuery(params: Record<string, string | number | undefined | null>): string {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null || value === "") {
      continue;
    }
    query.set(key, String(value));
  }
  const encoded = query.toString();
  return encoded ? `?${encoded}` : "";
}

export async function fetchDashboardSummary(): Promise<DashboardSummary> {
  return fetchJson("/api/dashboard/summary", EMPTY_DASHBOARD);
}

export async function fetchEvents(params: Record<string, string | number | undefined> = {}): Promise<EventListResponse> {
  return fetchJson(`/api/events${buildQuery(params)}`, EMPTY_EVENTS);
}

export async function fetchEvent(id: string): Promise<EventDetail | null> {
  return fetchJson(`/api/events/${id}`, null);
}

export async function fetchEntities(params: Record<string, string | number | undefined> = {}): Promise<EntityListResponse> {
  return fetchJson(`/api/entities${buildQuery(params)}`, EMPTY_ENTITIES);
}

export async function fetchEntity(slug: string): Promise<EntityDetail | null> {
  return fetchJson(`/api/entities/${slug}`, null);
}

export async function fetchThemes(params: Record<string, string | number | undefined> = {}): Promise<ThemeListResponse> {
  return fetchJson(`/api/themes${buildQuery(params)}`, EMPTY_THEMES);
}

export async function fetchTheme(slug: string): Promise<ThemeDetail | null> {
  return fetchJson(`/api/themes/${slug}`, null);
}

export async function fetchLatestBrief(): Promise<LatestBriefResponse | null> {
  return fetchJson("/api/briefs/latest", null);
}

export async function fetchOpportunities(params: Record<string, string | number | undefined> = {}): Promise<OpportunityListResponse> {
  return fetchJson(`/api/opportunities${buildQuery(params)}`, EMPTY_OPPORTUNITIES);
}

export async function fetchSearch(query: string, limit = 10): Promise<SearchResponse> {
  if (!query.trim()) {
    return EMPTY_SEARCH;
  }
  return fetchJson(`/api/search${buildQuery({ q: query, limit })}`, { ...EMPTY_SEARCH, query });
}

export async function fetchWatchlists(params: Record<string, string | number | undefined> = {}): Promise<WatchlistListResponse> {
  return fetchJson(`/api/watchlists${buildQuery(params)}`, EMPTY_WATCHLISTS);
}
