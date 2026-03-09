from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field, model_validator


class PaginationMeta(BaseModel):
    page: int
    page_size: int
    total: int


class SourceDocumentRef(BaseModel):
    id: str
    source_type: str
    source_external_id: str
    title: str
    url: str
    published_at: datetime | None


class ThemeRef(BaseModel):
    id: str
    slug: str
    name: str
    description: str | None
    confidence: float | None = None


class EntityRef(BaseModel):
    id: str
    slug: str
    canonical_name: str
    entity_type: str
    confidence: float | None = None


class EventScoreModel(BaseModel):
    novelty_score: float
    momentum_score: float
    strategic_importance_score: float
    aws_relevance_score: float
    corpdev_score: float
    confidence_score: float
    radar_score: float
    scoring_version: str
    rationale_json: dict


class EntityScoreModel(BaseModel):
    momentum_score: float
    aws_relevance_score: float
    corpdev_interest_score: float
    entity_priority_score: float
    scoring_version: str
    rationale_json: dict


class EventListItem(BaseModel):
    id: str
    title: str
    summary: str | None
    event_type: str
    occurred_at: datetime
    detected_at: datetime
    stack_layer: str | None
    confidence: float
    radar_score: float | None
    source: SourceDocumentRef | None
    linked_entities: list[EntityRef]
    themes: list[ThemeRef]


class EventDetail(EventListItem):
    why_it_matters: str | None
    skeptical_note: str | None
    metadata_json: dict
    score: EventScoreModel | None


class EventListResponse(BaseModel):
    items: list[EventListItem]
    meta: PaginationMeta


class EntityListItem(BaseModel):
    id: str
    slug: str
    canonical_name: str
    entity_type: str
    website: str | None
    description: str | None
    themes: list[ThemeRef]
    aliases: list[str]
    score: EntityScoreModel | None


class EntityDetail(EntityListItem):
    linked_events: list[EventListItem]


class EntityListResponse(BaseModel):
    items: list[EntityListItem]
    meta: PaginationMeta


class ThemeListItem(BaseModel):
    id: str
    slug: str
    name: str
    description: str | None
    entity_count: int


class ThemeDetail(ThemeListItem):
    linked_entities: list[EntityRef]
    top_events: list[EventListItem]


class ThemeListResponse(BaseModel):
    items: list[ThemeListItem]
    meta: PaginationMeta


class BriefItemModel(BaseModel):
    id: str
    item_type: str
    rank: int
    title: str
    summary: str
    event: EventListItem | None = None
    entity: EntityRef | None = None


class LatestBriefResponse(BaseModel):
    id: str
    brief_date: date
    title: str
    summary: str
    aws_implications: str | None
    possible_actions: str | None
    skeptical_counterpoints: str | None
    items: list[BriefItemModel]


class OpportunityListItem(BaseModel):
    id: str
    title: str
    opportunity_type: str
    rationale: str
    risks: str | None
    integration_notes: str | None
    priority_score: float | None
    status: str
    entity: EntityRef | None
    theme: ThemeRef | None


class OpportunityListResponse(BaseModel):
    items: list[OpportunityListItem]
    meta: PaginationMeta


class SearchResultItem(BaseModel):
    result_type: str
    id: str
    title: str
    subtitle: str | None
    snippet: str | None
    href: str | None
    score: float | None
    source_type: str | None = None


class SearchResponse(BaseModel):
    query: str
    events: list[SearchResultItem]
    entities: list[SearchResultItem]
    documents: list[SearchResultItem]


class WatchlistItemModel(BaseModel):
    id: str
    notes: str | None
    entity: EntityRef | None
    theme: ThemeRef | None


class WatchlistModel(BaseModel):
    id: str
    name: str
    description: str | None
    watchlist_type: str
    created_at: datetime
    items: list[WatchlistItemModel]


class WatchlistListResponse(BaseModel):
    items: list[WatchlistModel]
    meta: PaginationMeta


class CreateWatchlistRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    watchlist_type: str = Field(min_length=1, max_length=64)


class AddWatchlistItemRequest(BaseModel):
    entity_slug: str | None = None
    theme_slug: str | None = None
    notes: str | None = None

    @model_validator(mode="after")
    def validate_target(self):
        if bool(self.entity_slug) == bool(self.theme_slug):
            raise ValueError("Exactly one of entity_slug or theme_slug must be provided.")
        return self


class IngestRunRequest(BaseModel):
    fixture_path: str | None = None
    query: str | None = None
    org: str | None = None
    repo: str | None = None
    ticker: str | None = None
    cik: str | None = None
    limit: int = Field(default=10, ge=1, le=100)


class IngestRunResponse(BaseModel):
    run_id: str
    source_type: str
    status: str
    documents_seen: int
    documents_created: int
    payloads_created: int


class ScoreRecomputeRequest(BaseModel):
    reprocess: bool = False
    limit: int | None = Field(default=None, ge=1, le=500)


class ScoreRecomputeResponse(BaseModel):
    events_scored: list[dict]
    entities_scored: list[dict]
    top_events: list[dict]


class IngestionRunStatusModel(BaseModel):
    source_type: str
    status: str
    started_at: datetime | None
    finished_at: datetime | None
    documents_seen: int
    documents_created: int
    error_message: str | None


class OperationsStatusResponse(BaseModel):
    overall_status: str
    ingest_runs: list[IngestionRunStatusModel]
    pending_normalization_count: int
    latest_event_scored_at: datetime | None
    latest_entity_scored_at: datetime | None
    latest_brief_date: date | None
    latest_brief_updated_at: datetime | None
    stale_reasons: list[str]
