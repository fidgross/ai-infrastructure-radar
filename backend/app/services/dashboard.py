from __future__ import annotations

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.models import DailyBrief, Entity, EntityScore, EntityThemeLink, Event, EventScore, Opportunity, SourceDocument, Theme
from app.schemas.dashboard import (
    DashboardEntity,
    DashboardEvent,
    DashboardSummaryResponse,
    LatestBriefCard,
    OpportunityCard,
    ThemeHeatmapItem,
)


def get_dashboard_summary(session: Session) -> DashboardSummaryResponse:
    entity_count = func.count(EntityThemeLink.entity_id)

    top_event_rows = session.execute(
        select(Event, EventScore, SourceDocument)
        .join(EventScore, Event.id == EventScore.event_id)
        .join(SourceDocument, Event.source_document_id == SourceDocument.id, isouter=True)
        .order_by(desc(EventScore.radar_score), desc(Event.occurred_at))
        .limit(5)
    ).all()

    emerging_entity_rows = session.execute(
        select(Entity, EntityScore)
        .join(EntityScore, Entity.id == EntityScore.entity_id)
        .order_by(desc(EntityScore.entity_priority_score), desc(EntityScore.momentum_score))
        .limit(3)
    ).all()

    theme_rows = session.execute(
        select(Theme, entity_count.label("entity_count"))
        .join(EntityThemeLink, Theme.id == EntityThemeLink.theme_id)
        .group_by(Theme.id)
        .order_by(desc(entity_count), Theme.name.asc())
        .limit(6)
    ).all()

    opportunity_rows = session.execute(
        select(Opportunity).order_by(desc(Opportunity.priority_score), Opportunity.created_at.desc()).limit(3)
    ).scalars()

    latest_brief = session.execute(select(DailyBrief).order_by(DailyBrief.brief_date.desc()).limit(1)).scalar_one_or_none()

    return DashboardSummaryResponse(
        top_events=[
            DashboardEvent(
                id=str(event.id),
                title=event.title,
                event_type=event.event_type,
                occurred_at=event.occurred_at,
                summary=event.summary,
                radar_score=round(score.radar_score, 2),
                source_type=source_document.source_type if source_document else None,
                source_url=source_document.url if source_document else None,
            )
            for event, score, source_document in top_event_rows
        ],
        emerging_entities=[
            DashboardEntity(
                id=str(entity.id),
                canonical_name=entity.canonical_name,
                slug=entity.slug,
                entity_type=entity.entity_type,
                entity_priority_score=round(score.entity_priority_score, 2),
                momentum_score=round(score.momentum_score, 2),
                corpdev_interest_score=round(score.corpdev_interest_score, 2),
            )
            for entity, score in emerging_entity_rows
        ],
        theme_heatmap=[
            ThemeHeatmapItem(
                id=str(theme.id),
                name=theme.name,
                slug=theme.slug,
                entity_count=entity_count,
            )
            for theme, entity_count in theme_rows
        ],
        opportunities=[
            OpportunityCard(
                id=str(opportunity.id),
                title=opportunity.title,
                opportunity_type=opportunity.opportunity_type,
                priority_score=round(opportunity.priority_score, 2) if opportunity.priority_score is not None else None,
                status=opportunity.status,
            )
            for opportunity in opportunity_rows
        ],
        latest_brief=(
            LatestBriefCard(
                id=str(latest_brief.id),
                brief_date=latest_brief.brief_date,
                title=latest_brief.title,
                summary=latest_brief.summary,
                aws_implications=latest_brief.aws_implications,
            )
            if latest_brief
            else None
        ),
    )
