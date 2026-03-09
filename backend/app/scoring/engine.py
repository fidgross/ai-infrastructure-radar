from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session, joinedload

from app.models import Entity, EntityScore, Event, EventEntityLink, EventScore, SourceDocument
from app.scoring.weights import (
    AWS_LAYER_WEIGHTS,
    ENTITY_TYPE_CORPDEV_BONUS,
    EVENT_SCORE_WEIGHTS,
    EVENT_TYPE_WEIGHTS,
    STACK_LAYER_WEIGHTS,
    THEME_AWS_BONUS,
    THEME_CORPDEV_BONUS,
)
from app.utils.dates import ensure_utc

SCORING_VERSION = "v1_rule_scoring_2026_03"
NOVELTY_KEYWORDS = (
    "launch",
    "release",
    "new",
    "update",
    "sparse",
    "speculative",
    "routing",
    "capex",
    "capacity",
    "benchmark",
)


@dataclass
class EventScoreSummary:
    event_id: str
    radar_score: float
    scoring_version: str


@dataclass
class EntityScoreSummary:
    entity_id: str
    entity_priority_score: float
    scoring_version: str


def score_events(session: Session, *, reprocess: bool = False, limit: int | None = None) -> list[EventScoreSummary]:
    stmt = select(Event).options(joinedload(Event.source_document), joinedload(Event.entity_links).joinedload(EventEntityLink.entity))
    if not reprocess:
        stmt = stmt.outerjoin(EventScore, EventScore.event_id == Event.id).where(EventScore.event_id.is_(None))
    stmt = stmt.order_by(Event.occurred_at.desc())
    if limit is not None:
        stmt = stmt.limit(limit)

    events = session.scalars(stmt).unique().all()
    summaries: list[EventScoreSummary] = []
    now = datetime.now(tz=timezone.utc)

    for event in events:
        breakdown = _score_event(session, event, now=now)
        record = session.get(EventScore, event.id)
        if record is None:
            record = EventScore(event_id=event.id, scoring_version=SCORING_VERSION)
            session.add(record)

        record.novelty_score = breakdown["novelty_score"]
        record.momentum_score = breakdown["momentum_score"]
        record.strategic_importance_score = breakdown["strategic_importance_score"]
        record.aws_relevance_score = breakdown["aws_relevance_score"]
        record.corpdev_score = breakdown["corpdev_score"]
        record.confidence_score = breakdown["confidence_score"]
        record.radar_score = breakdown["radar_score"]
        record.scored_at = now
        record.scoring_version = SCORING_VERSION
        record.rationale_json = breakdown["rationale_json"]
        summaries.append(EventScoreSummary(event_id=str(event.id), radar_score=record.radar_score, scoring_version=SCORING_VERSION))

    session.commit()
    return summaries


def score_events_only(session: Session, *, reprocess: bool = False, limit: int | None = None) -> list[EventScoreSummary]:
    return score_events(session, reprocess=reprocess, limit=limit)


def score_entities(session: Session, *, reprocess: bool = False, limit: int | None = None) -> list[EntityScoreSummary]:
    stmt = select(Entity).options(joinedload(Entity.event_links).joinedload(EventEntityLink.event).joinedload(Event.score))
    if not reprocess:
        stmt = stmt.outerjoin(EntityScore, EntityScore.entity_id == Entity.id).where(EntityScore.entity_id.is_(None))
    stmt = stmt.order_by(Entity.canonical_name.asc())
    if limit is not None:
        stmt = stmt.limit(limit)

    entities = session.scalars(stmt).unique().all()
    now = datetime.now(tz=timezone.utc)
    summaries: list[EntityScoreSummary] = []

    for entity in entities:
        breakdown = _score_entity(entity, now=now)
        record = session.get(EntityScore, entity.id)
        if record is None:
            record = EntityScore(entity_id=entity.id, scoring_version=SCORING_VERSION)
            session.add(record)

        record.momentum_score = breakdown["momentum_score"]
        record.aws_relevance_score = breakdown["aws_relevance_score"]
        record.corpdev_interest_score = breakdown["corpdev_interest_score"]
        record.entity_priority_score = breakdown["entity_priority_score"]
        record.scored_at = now
        record.scoring_version = SCORING_VERSION
        record.rationale_json = breakdown["rationale_json"]
        summaries.append(
            EntityScoreSummary(
                entity_id=str(entity.id),
                entity_priority_score=record.entity_priority_score,
                scoring_version=SCORING_VERSION,
            )
        )

    session.commit()
    return summaries


def score_entities_only(session: Session, *, reprocess: bool = False, limit: int | None = None) -> list[EntityScoreSummary]:
    return score_entities(session, reprocess=reprocess, limit=limit)


def get_ranked_events(session: Session, *, limit: int = 10) -> list[tuple[Event, EventScore]]:
    rows = session.execute(
        select(Event, EventScore)
        .join(EventScore, EventScore.event_id == Event.id)
        .order_by(EventScore.radar_score.desc(), Event.occurred_at.desc())
        .limit(limit)
    ).all()
    return [(event, score) for event, score in rows]


def get_ranked_entities(session: Session, *, limit: int = 10) -> list[tuple[Entity, EntityScore]]:
    rows = session.execute(
        select(Entity, EntityScore)
        .join(EntityScore, EntityScore.entity_id == Entity.id)
        .order_by(EntityScore.entity_priority_score.desc(), Entity.canonical_name.asc())
        .limit(limit)
    ).all()
    return [(entity, score) for entity, score in rows]


def _score_event(session: Session, event: Event, *, now: datetime) -> dict:
    entity_ids = [link.entity_id for link in event.entity_links]
    source_document = event.source_document
    source_type = source_document.source_type if source_document else event.metadata_json.get("source_type", "unknown")
    theme_slugs = event.metadata_json.get("theme_slugs", [])
    text = " ".join(piece for piece in [event.title, event.summary or "", event.why_it_matters or ""] if piece).lower()
    occurred_at = ensure_utc(event.occurred_at) or now
    days_old = max(0, (now - occurred_at).days)
    recent_related_count = _recent_related_event_count(session, entity_ids, window_days=30, now=now)
    repeat_count = _similar_recent_event_count(session, event, entity_ids, now=now, window_days=14)
    source_diversity = _source_diversity(session, entity_ids, window_days=30, now=now)
    corroboration_bonus = max(0.0, float(source_diversity - 1))
    technical_commercial = _technical_commercial_coincidence(session, entity_ids, now=now)
    control_point_bonus = 1.0 if "model-portability" in theme_slugs or "control plane" in (event.stack_layer or "").lower() else 0.0

    recency_score = _clamp(10 - min(days_old, 90) * 0.09)
    novelty_keyword_hits = sum(1 for keyword in NOVELTY_KEYWORDS if keyword in text)
    novelty_score = _clamp(0.55 * recency_score + (novelty_keyword_hits * 0.55) + 1.15 - max(0, repeat_count - 1) * 0.8)

    momentum_score = _clamp(
        2.5
        + min(4.0, recent_related_count * 1.1)
        + corroboration_bonus * 1.0
        + (1.0 if event.event_type in {"major_release", "product_launch", "capex_signal", "repo_acceleration"} else 0.5)
        - max(0, repeat_count - 1) * 0.5
    )

    type_weight = EVENT_TYPE_WEIGHTS.get(event.event_type, 6.5)
    layer_weight = STACK_LAYER_WEIGHTS.get(event.stack_layer or "", 7.0)
    strategic_importance_score = _clamp(
        0.58 * type_weight
        + 0.42 * layer_weight
        + control_point_bonus
        + (1.2 if technical_commercial else 0.0)
        + corroboration_bonus * 0.5
    )

    theme_aws_bonus = max((THEME_AWS_BONUS.get(slug, 0.0) for slug in theme_slugs), default=0.0)
    keyword_bonus = min(1.2, sum(1 for keyword in ("inference", "aws", "routing", "latency", "gpu", "cloud") if keyword in text) * 0.35)
    aws_relevance_score = _clamp(
        0.7 * AWS_LAYER_WEIGHTS.get(event.stack_layer or "", 7.4)
        + theme_aws_bonus
        + keyword_bonus
        + corroboration_bonus * 0.3
    )

    linked_entity_bonus = _average([ENTITY_TYPE_CORPDEV_BONUS.get(link.entity.entity_type, 0.2) for link in event.entity_links])
    theme_corpdev_bonus = max((THEME_CORPDEV_BONUS.get(slug, 0.0) for slug in theme_slugs), default=0.0)
    corpdev_score = _clamp(
        1.5
        + linked_entity_bonus * 2
        + theme_corpdev_bonus
        + (1.0 if technical_commercial else 0.0)
        + corroboration_bonus * 0.35
        + (0.6 if source_type == "edgar" else 0.25)
    )

    confidence_score = _clamp((event.confidence * 10) + min(1.0, corroboration_bonus * 0.5) - max(0, repeat_count - 1) * 0.4)

    radar_score = round(
        sum(
            [
                novelty_score * EVENT_SCORE_WEIGHTS["novelty_score"],
                momentum_score * EVENT_SCORE_WEIGHTS["momentum_score"],
                strategic_importance_score * EVENT_SCORE_WEIGHTS["strategic_importance_score"],
                aws_relevance_score * EVENT_SCORE_WEIGHTS["aws_relevance_score"],
                corpdev_score * EVENT_SCORE_WEIGHTS["corpdev_score"],
                confidence_score * EVENT_SCORE_WEIGHTS["confidence_score"],
            ]
        ),
        4,
    )

    rationale_json = {
        "scoring_version": SCORING_VERSION,
        "days_old": days_old,
        "recent_related_event_count": recent_related_count,
        "repeat_count": repeat_count,
        "source_diversity": source_diversity,
        "technical_commercial_coincidence": technical_commercial,
        "theme_slugs": theme_slugs,
        "component_scores": {
            "novelty_score": round(novelty_score, 4),
            "momentum_score": round(momentum_score, 4),
            "strategic_importance_score": round(strategic_importance_score, 4),
            "aws_relevance_score": round(aws_relevance_score, 4),
            "corpdev_score": round(corpdev_score, 4),
            "confidence_score": round(confidence_score, 4),
            "radar_score": radar_score,
        },
    }

    return {
        "novelty_score": round(novelty_score, 4),
        "momentum_score": round(momentum_score, 4),
        "strategic_importance_score": round(strategic_importance_score, 4),
        "aws_relevance_score": round(aws_relevance_score, 4),
        "corpdev_score": round(corpdev_score, 4),
        "confidence_score": round(confidence_score, 4),
        "radar_score": radar_score,
        "rationale_json": rationale_json,
    }


def _score_entity(entity: Entity, *, now: datetime) -> dict:
    scored_events = [link.event.score for link in entity.event_links if link.event and link.event.score is not None]
    if not scored_events:
        return {
            "momentum_score": 0.0,
            "aws_relevance_score": 0.0,
            "corpdev_interest_score": 0.0,
            "entity_priority_score": 0.0,
            "rationale_json": {"scoring_version": SCORING_VERSION, "reason": "No scored events linked to entity."},
        }

    now_minus_30 = now - timedelta(days=30)
    now_minus_90 = now - timedelta(days=90)
    recent_event_scores: list[float] = []
    prior_event_scores: list[float] = []
    event_momentum_scores: list[float] = []
    event_aws_scores: list[float] = []
    event_corpdev_scores: list[float] = []

    for link in entity.event_links:
        event = link.event
        event_occurred_at = ensure_utc(event.occurred_at) if event is not None else None
        if event is None or event.score is None or event_occurred_at is None or event_occurred_at < now_minus_90:
            continue
        event_momentum_scores.append(event.score.momentum_score)
        event_aws_scores.append(event.score.aws_relevance_score)
        event_corpdev_scores.append(event.score.corpdev_score)
        if event_occurred_at >= now_minus_30:
            recent_event_scores.append(event.score.radar_score)
        else:
            prior_event_scores.append(event.score.radar_score)

    all_radar_scores = [score.radar_score for score in scored_events]
    base_avg = _average(all_radar_scores)
    recent_avg = _average(recent_event_scores)
    prior_avg = _average(prior_event_scores)
    acceleration_bonus = max(0.0, recent_avg - prior_avg) * 0.2 + min(1.0, len(recent_event_scores) * 0.15)
    manual_override = float((entity.metadata_json or {}).get("analyst_priority_override", 0.0))
    entity_type_bonus = ENTITY_TYPE_CORPDEV_BONUS.get(entity.entity_type, 0.2)

    momentum_score = _clamp(_average(event_momentum_scores) + acceleration_bonus)
    aws_relevance_score = _clamp(_average(event_aws_scores) + (0.4 if entity.entity_type in {"company", "public_company", "repository"} else 0.0))
    corpdev_interest_score = _clamp(_average(event_corpdev_scores) + entity_type_bonus)
    entity_priority_score = _clamp(
        (base_avg * 0.6)
        + (momentum_score * 0.15)
        + (aws_relevance_score * 0.15)
        + (corpdev_interest_score * 0.1)
        + acceleration_bonus * 0.5
        + manual_override
    )

    return {
        "momentum_score": round(momentum_score, 4),
        "aws_relevance_score": round(aws_relevance_score, 4),
        "corpdev_interest_score": round(corpdev_interest_score, 4),
        "entity_priority_score": round(entity_priority_score, 4),
        "rationale_json": {
            "scoring_version": SCORING_VERSION,
            "base_average_radar_score": round(base_avg, 4),
            "recent_average_radar_score": round(recent_avg, 4),
            "prior_average_radar_score": round(prior_avg, 4),
            "acceleration_bonus": round(acceleration_bonus, 4),
            "manual_override": manual_override,
        },
    }


def _recent_related_event_count(session: Session, entity_ids: list, *, window_days: int, now: datetime) -> int:
    if not entity_ids:
        return 0
    cutoff = now - timedelta(days=window_days)
    return session.scalar(
        select(func.count(distinct(Event.id)))
        .join(EventEntityLink, EventEntityLink.event_id == Event.id)
        .where(EventEntityLink.entity_id.in_(entity_ids), Event.occurred_at >= cutoff)
    ) or 0


def _similar_recent_event_count(session: Session, event: Event, entity_ids: list, *, now: datetime, window_days: int) -> int:
    if not entity_ids:
        return 0
    cutoff = now - timedelta(days=window_days)
    return session.scalar(
        select(func.count(distinct(Event.id)))
        .join(EventEntityLink, EventEntityLink.event_id == Event.id)
        .where(
            EventEntityLink.entity_id.in_(entity_ids),
            Event.event_type == event.event_type,
            Event.occurred_at >= cutoff,
        )
    ) or 0


def _source_diversity(session: Session, entity_ids: list, *, window_days: int, now: datetime) -> int:
    if not entity_ids:
        return 0
    cutoff = now - timedelta(days=window_days)
    return session.scalar(
        select(func.count(distinct(SourceDocument.source_type)))
        .select_from(Event)
        .join(EventEntityLink, EventEntityLink.event_id == Event.id)
        .join(SourceDocument, SourceDocument.id == Event.source_document_id)
        .where(EventEntityLink.entity_id.in_(entity_ids), Event.occurred_at >= cutoff)
    ) or 0


def _technical_commercial_coincidence(session: Session, entity_ids: list, *, now: datetime) -> bool:
    if not entity_ids:
        return False
    cutoff = now - timedelta(days=30)
    rows = session.scalars(
        select(distinct(SourceDocument.source_type))
        .select_from(Event)
        .join(EventEntityLink, EventEntityLink.event_id == Event.id)
        .join(SourceDocument, SourceDocument.id == Event.source_document_id)
        .where(EventEntityLink.entity_id.in_(entity_ids), Event.occurred_at >= cutoff)
    ).all()
    sources = set(rows)
    return "edgar" in sources and bool(sources.intersection({"arxiv", "github", "huggingface"}))


def _average(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _clamp(value: float, lower: float = 0.0, upper: float = 10.0) -> float:
    return round(max(lower, min(upper, value)), 4)
