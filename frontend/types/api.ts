export type PaginationMeta = {
  page: number;
  page_size: number;
  total: number;
};

export type SourceDocumentRef = {
  id: string;
  source_type: string;
  source_external_id: string;
  title: string;
  url: string;
  published_at: string | null;
};

export type ThemeRef = {
  id: string;
  slug: string;
  name: string;
  description: string | null;
  confidence: number | null;
};

export type EntityRef = {
  id: string;
  slug: string;
  canonical_name: string;
  entity_type: string;
  confidence: number | null;
};

export type EventScoreModel = {
  novelty_score: number;
  momentum_score: number;
  strategic_importance_score: number;
  aws_relevance_score: number;
  corpdev_score: number;
  confidence_score: number;
  radar_score: number;
  scoring_version: string;
  rationale_json: Record<string, unknown>;
};

export type EntityScoreModel = {
  momentum_score: number;
  aws_relevance_score: number;
  corpdev_interest_score: number;
  entity_priority_score: number;
  scoring_version: string;
  rationale_json: Record<string, unknown>;
};

export type EventListItem = {
  id: string;
  title: string;
  summary: string | null;
  event_type: string;
  occurred_at: string;
  detected_at: string;
  stack_layer: string | null;
  confidence: number;
  radar_score: number | null;
  source: SourceDocumentRef | null;
  linked_entities: EntityRef[];
  themes: ThemeRef[];
};

export type EventDetail = EventListItem & {
  why_it_matters: string | null;
  skeptical_note: string | null;
  metadata_json: Record<string, unknown>;
  score: EventScoreModel | null;
};

export type EventListResponse = {
  items: EventListItem[];
  meta: PaginationMeta;
};

export type EntityListItem = {
  id: string;
  slug: string;
  canonical_name: string;
  entity_type: string;
  website: string | null;
  description: string | null;
  themes: ThemeRef[];
  aliases: string[];
  score: EntityScoreModel | null;
};

export type EntityDetail = EntityListItem & {
  linked_events: EventListItem[];
};

export type EntityListResponse = {
  items: EntityListItem[];
  meta: PaginationMeta;
};

export type ThemeListItem = {
  id: string;
  slug: string;
  name: string;
  description: string | null;
  entity_count: number;
};

export type ThemeDetail = ThemeListItem & {
  linked_entities: EntityRef[];
  top_events: EventListItem[];
};

export type ThemeListResponse = {
  items: ThemeListItem[];
  meta: PaginationMeta;
};

export type BriefItemModel = {
  id: string;
  item_type: string;
  rank: number;
  title: string;
  summary: string;
  event: EventListItem | null;
  entity: EntityRef | null;
};

export type LatestBriefResponse = {
  id: string;
  brief_date: string;
  title: string;
  summary: string;
  aws_implications: string | null;
  possible_actions: string | null;
  skeptical_counterpoints: string | null;
  items: BriefItemModel[];
};

export type OpportunityListItem = {
  id: string;
  title: string;
  opportunity_type: string;
  rationale: string;
  risks: string | null;
  integration_notes: string | null;
  priority_score: number | null;
  status: string;
  entity: EntityRef | null;
  theme: ThemeRef | null;
};

export type OpportunityListResponse = {
  items: OpportunityListItem[];
  meta: PaginationMeta;
};

export type SearchResultItem = {
  result_type: string;
  id: string;
  title: string;
  subtitle: string | null;
  snippet: string | null;
  href: string | null;
  score: number | null;
  source_type?: string | null;
};

export type SearchResponse = {
  query: string;
  events: SearchResultItem[];
  entities: SearchResultItem[];
  documents: SearchResultItem[];
};

export type WatchlistItemModel = {
  id: string;
  notes: string | null;
  entity: EntityRef | null;
  theme: ThemeRef | null;
};

export type WatchlistModel = {
  id: string;
  name: string;
  description: string | null;
  watchlist_type: string;
  created_at: string;
  items: WatchlistItemModel[];
};

export type WatchlistListResponse = {
  items: WatchlistModel[];
  meta: PaginationMeta;
};

export type DashboardSummary = {
  top_events: {
    id: string;
    title: string;
    event_type: string;
    occurred_at: string;
    summary: string | null;
    radar_score: number;
    source_type: string | null;
    source_url: string | null;
  }[];
  emerging_entities: {
    id: string;
    canonical_name: string;
    slug: string;
    entity_type: string;
    entity_priority_score: number;
    momentum_score: number;
    corpdev_interest_score: number;
  }[];
  theme_heatmap: {
    id: string;
    name: string;
    slug: string;
    entity_count: number;
  }[];
  opportunities: {
    id: string;
    title: string;
    opportunity_type: string;
    priority_score: number | null;
    status: string;
  }[];
  latest_brief: {
    id: string;
    brief_date: string;
    title: string;
    summary: string;
    aws_implications: string | null;
  } | null;
};
