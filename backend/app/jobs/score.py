from __future__ import annotations

from app.db.session import SessionLocal
from app.scoring.engine import get_ranked_events, score_entities_only, score_events_only


def run_event_scoring(*, reprocess: bool = False, limit: int | None = None) -> list[dict]:
    with SessionLocal() as session:
        return [summary.__dict__ for summary in score_events_only(session, reprocess=reprocess, limit=limit)]


def run_entity_scoring(*, reprocess: bool = False, limit: int | None = None) -> list[dict]:
    with SessionLocal() as session:
        return [summary.__dict__ for summary in score_entities_only(session, reprocess=reprocess, limit=limit)]


def run_scoring_pipeline(*, reprocess: bool = False, limit: int | None = None) -> dict:
    with SessionLocal() as session:
        event_summaries = [summary.__dict__ for summary in score_events_only(session, reprocess=reprocess, limit=limit)]
        entity_summaries = [summary.__dict__ for summary in score_entities_only(session, reprocess=reprocess, limit=limit)]
        ranked_events = [
            {"event_id": str(event.id), "title": event.title, "radar_score": score.radar_score}
            for event, score in get_ranked_events(session, limit=10)
        ]
    return {
        "events_scored": event_summaries,
        "entities_scored": entity_summaries,
        "top_events": ranked_events,
    }
