from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel


class DashboardEvent(BaseModel):
    id: str
    title: str
    event_type: str
    occurred_at: datetime
    summary: str | None
    radar_score: float
    source_type: str | None
    source_url: str | None


class DashboardEntity(BaseModel):
    id: str
    canonical_name: str
    slug: str
    entity_type: str
    entity_priority_score: float
    momentum_score: float
    corpdev_interest_score: float


class ThemeHeatmapItem(BaseModel):
    id: str
    name: str
    slug: str
    entity_count: int


class OpportunityCard(BaseModel):
    id: str
    title: str
    opportunity_type: str
    priority_score: float | None
    status: str


class LatestBriefCard(BaseModel):
    id: str
    brief_date: date
    title: str
    summary: str
    aws_implications: str | None


class DashboardSummaryResponse(BaseModel):
    top_events: list[DashboardEvent]
    emerging_entities: list[DashboardEntity]
    theme_heatmap: list[ThemeHeatmapItem]
    opportunities: list[OpportunityCard]
    latest_brief: LatestBriefCard | None
