from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Iterable

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models import DailyBrief, DailyBriefItem, Entity, EntityScore, EntityThemeLink, Event, EventEntityLink, EventScore, Opportunity, SourceDocument

BRIEF_WINDOW_HOURS = 72
MAX_BRIEF_EVENTS = 5
MAX_EVENTS_PER_SOURCE = 2
MAX_ENTITY_SPOTLIGHTS = 2
BRIEF_STATUS = "published"


@dataclass
class BriefGenerationSummary:
    generated: bool
    brief_id: str | None
    brief_date: str
    top_event_count: int
    entity_spotlight_count: int
    source_types: list[str]


def generate_daily_brief(
    session: Session,
    *,
    brief_date: date | None = None,
    lookback_hours: int = BRIEF_WINDOW_HOURS,
) -> BriefGenerationSummary:
    target_date = brief_date or datetime.now(tz=timezone.utc).date()
    now = datetime.now(tz=timezone.utc)
    candidate_events = _load_candidate_events(session, now=now, lookback_hours=lookback_hours)
    selected_events = _select_brief_events(candidate_events)

    if not selected_events:
        return BriefGenerationSummary(
            generated=False,
            brief_id=None,
            brief_date=target_date.isoformat(),
            top_event_count=0,
            entity_spotlight_count=0,
            source_types=[],
        )

    excluded_entity_ids = {link.entity_id for event in selected_events for link in event.entity_links}
    entity_spotlights = _select_entity_spotlights(session, excluded_entity_ids=excluded_entity_ids)
    theme_names = _theme_names_for_events(selected_events)

    brief = session.scalar(select(DailyBrief).where(DailyBrief.brief_date == target_date))
    if brief is None:
        brief = DailyBrief(
            brief_date=target_date,
            title="AI Infrastructure Radar daily brief",
            summary="",
            status=BRIEF_STATUS,
            updated_at=now,
            metadata_json={},
        )
        session.add(brief)
        session.flush()

    summary = _build_summary_text(selected_events, theme_names)
    aws_implications = _build_aws_implications(selected_events)
    possible_actions = _build_possible_actions(session, entity_spotlights)
    skeptical_counterpoints = _build_skeptical_counterpoints(selected_events)

    brief.title = "AI Infrastructure Radar daily brief"
    brief.summary = summary
    brief.aws_implications = aws_implications
    brief.possible_actions = possible_actions
    brief.skeptical_counterpoints = skeptical_counterpoints
    brief.status = BRIEF_STATUS
    brief.updated_at = now
    brief.metadata_json = {
        "generated": True,
        "generated_at": now.isoformat(),
        "lookback_hours": lookback_hours,
        "top_event_ids": [str(event.id) for event in selected_events],
        "entity_spotlight_ids": [str(entity.id) for entity, _score in entity_spotlights],
        "source_types": sorted({_source_type_for_event(event) for event in selected_events}),
        "theme_names": theme_names,
    }

    session.execute(delete(DailyBriefItem).where(DailyBriefItem.daily_brief_id == brief.id))
    session.flush()

    items: list[DailyBriefItem] = []
    for index, event in enumerate(selected_events, start=1):
        items.append(
            DailyBriefItem(
                daily_brief_id=brief.id,
                item_type="top_event",
                rank=index,
                title=event.title,
                summary=event.summary or event.why_it_matters or event.title,
                event_id=event.id,
                metadata_json={
                    "source_type": _source_type_for_event(event),
                    "radar_score": round(event.score.radar_score, 4) if event.score else None,
                },
            )
        )

    for index, (entity, entity_score) in enumerate(entity_spotlights, start=1):
        items.append(
            DailyBriefItem(
                daily_brief_id=brief.id,
                item_type="emerging_entity",
                rank=index,
                title=entity.canonical_name,
                summary=_build_entity_spotlight_summary(entity, entity_score),
                entity_id=entity.id,
                metadata_json={"entity_priority_score": round(entity_score.entity_priority_score, 4)},
            )
        )

    session.add_all(items)
    session.commit()

    return BriefGenerationSummary(
        generated=True,
        brief_id=str(brief.id),
        brief_date=target_date.isoformat(),
        top_event_count=len(selected_events),
        entity_spotlight_count=len(entity_spotlights),
        source_types=sorted({_source_type_for_event(event) for event in selected_events}),
    )


def _load_candidate_events(session: Session, *, now: datetime, lookback_hours: int) -> list[Event]:
    cutoff = now - timedelta(hours=lookback_hours)
    stmt = (
        select(Event)
        .join(EventScore, EventScore.event_id == Event.id)
        .outerjoin(SourceDocument, SourceDocument.id == Event.source_document_id)
        .where(Event.occurred_at >= cutoff)
        .options(
            joinedload(Event.score),
            joinedload(Event.source_document),
            selectinload(Event.entity_links)
            .joinedload(EventEntityLink.entity)
            .selectinload(Entity.theme_links)
            .joinedload(EntityThemeLink.theme),
        )
        .order_by(EventScore.radar_score.desc(), Event.occurred_at.desc())
    )
    return session.scalars(stmt).unique().all()


def _select_brief_events(events: Iterable[Event]) -> list[Event]:
    selected: list[Event] = []
    source_counts: dict[str, int] = {}

    for candidate in events:
        source_type = _source_type_for_event(candidate)
        if source_counts.get(source_type, 0) >= MAX_EVENTS_PER_SOURCE:
            continue
        if any(_is_duplicate_story(candidate, existing) for existing in selected):
            continue
        selected.append(candidate)
        source_counts[source_type] = source_counts.get(source_type, 0) + 1
        if len(selected) >= MAX_BRIEF_EVENTS:
            break

    return selected


def _select_entity_spotlights(
    session: Session,
    *,
    excluded_entity_ids: set,
) -> list[tuple[Entity, EntityScore]]:
    stmt = (
        select(Entity, EntityScore)
        .join(EntityScore, EntityScore.entity_id == Entity.id)
        .order_by(EntityScore.entity_priority_score.desc(), Entity.canonical_name.asc())
        .limit(20)
    )
    rows = session.execute(stmt).all()
    selected: list[tuple[Entity, EntityScore]] = []

    for entity, entity_score in rows:
        if entity.id in excluded_entity_ids:
            continue
        selected.append((entity, entity_score))
        if len(selected) >= MAX_ENTITY_SPOTLIGHTS:
            break

    return selected


def _build_summary_text(events: list[Event], theme_names: list[str]) -> str:
    lead = events[:3]
    theme_clause = f"Top signals cluster around {', '.join(theme_names[:2])}." if theme_names else "Top signals span the current AI infrastructure watchlist."
    lead_titles = ", ".join(event.title for event in lead[:2])
    if len(lead) >= 3:
        trailing = f"{lead[2].title} rounds out the highest-conviction developments."
    elif len(lead) == 2:
        trailing = f"These are led by {lead[0].title} and {lead[1].title}."
    else:
        trailing = f"The lead development is {lead[0].title}."
    return " ".join([theme_clause, f"Highest-ranked events include {lead_titles}." if len(lead) >= 2 else trailing, trailing if len(lead) >= 3 else ""]).strip()


def _build_aws_implications(events: list[Event]) -> str:
    ranked = sorted(
        [event for event in events if event.score is not None],
        key=lambda event: (event.score.aws_relevance_score, event.score.radar_score),
        reverse=True,
    )[:2]
    if not ranked:
        return "AWS implications remain muted until higher-confidence infrastructure signals emerge."
    titles = " and ".join(event.title for event in ranked)
    layers = ", ".join(dict.fromkeys(event.stack_layer or "infrastructure" for event in ranked))
    return f"AWS should track {titles} because they affect {layers} economics and partner leverage in the current stack."


def _build_possible_actions(session: Session, entity_spotlights: list[tuple[Entity, EntityScore]]) -> str:
    opportunities = session.scalars(
        select(Opportunity)
        .where(Opportunity.status == "open")
        .order_by(Opportunity.priority_score.desc(), Opportunity.created_at.desc())
        .limit(2)
    ).all()
    if opportunities:
        titles = "; ".join(opportunity.title for opportunity in opportunities)
        return f"Near-term actions: {titles}."
    if entity_spotlights:
        names = ", ".join(entity.canonical_name for entity, _score in entity_spotlights)
        return f"Prioritize deeper diligence on {names} for follow-up monitoring and partner mapping."
    return "No immediate action items stand out beyond maintaining the current watchlist and rerunning the pipeline."


def _build_skeptical_counterpoints(events: list[Event]) -> str | None:
    notes: list[str] = []
    for event in events:
        note = (event.skeptical_note or "").strip()
        if note and note not in notes:
            notes.append(note)
        if len(notes) >= 2:
            break
    if not notes:
        return None
    return " ".join(notes)


def _build_entity_spotlight_summary(entity: Entity, entity_score: EntityScore) -> str:
    return (
        f"{entity.canonical_name} remains a priority watch target with "
        f"{entity_score.entity_priority_score:.2f} priority score and "
        f"{entity_score.corpdev_interest_score:.2f} corpdev interest."
    )


def _theme_names_for_events(events: Iterable[Event]) -> list[str]:
    ordered: dict[str, None] = {}
    for event in events:
        for link in event.entity_links:
            entity = link.entity
            if entity is None:
                continue
            for theme_link in entity.theme_links:
                theme = theme_link.theme
                if theme is not None and theme.name not in ordered:
                    ordered[theme.name] = None
    return list(ordered.keys())


def _source_type_for_event(event: Event) -> str:
    if event.source_document is not None:
        return event.source_document.source_type
    return str((event.metadata_json or {}).get("source_type") or "unknown")


def _is_duplicate_story(candidate: Event, existing: Event) -> bool:
    if candidate.source_document_id and candidate.source_document_id == existing.source_document_id:
        return True

    candidate_title = _normalized_title(candidate.title)
    existing_title = _normalized_title(existing.title)
    if candidate_title == existing_title:
        return True

    candidate_entities = {str(link.entity_id) for link in candidate.entity_links}
    existing_entities = {str(link.entity_id) for link in existing.entity_links}
    shared_entities = candidate_entities.intersection(existing_entities)
    if shared_entities and candidate.event_type == existing.event_type:
        return _title_similarity(candidate_title, existing_title) >= 0.6

    return False


def _normalized_title(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9\s]", " ", value.lower())
    return " ".join(cleaned.split())


def _title_similarity(left: str, right: str) -> float:
    left_tokens = set(left.split())
    right_tokens = set(right.split())
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)
