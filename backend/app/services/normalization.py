from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import delete, outerjoin, select
from sqlalchemy.orm import Session

from app.models import Event, EventEntityLink, SourceDocument
from app.services.entity_extraction import extract_entity_candidates
from app.services.entity_resolution import resolve_entity_candidates
from app.services.event_extraction import extract_event_candidate
from app.services.normalization_types import NormalizationSummary
from app.services.theme_tagging import attach_themes_to_entity, classify_themes, ensure_theme_records
from app.utils.dates import ensure_utc

NORMALIZATION_VERSION = "v1_rule_normalization_2026_03"


def normalize_source_document(session: Session, source_document_id: str) -> NormalizationSummary:
    document_key = uuid.UUID(source_document_id) if isinstance(source_document_id, str) else source_document_id
    document = session.get(SourceDocument, document_key)
    if document is None:
        raise ValueError(f"Source document {source_document_id} was not found.")

    theme_matches = classify_themes(document)
    themes = ensure_theme_records(session, theme_matches)
    entity_candidates = extract_entity_candidates(document)
    resolved_entities = resolve_entity_candidates(session, entity_candidates)

    for resolved_entity in resolved_entities:
        attach_themes_to_entity(session, resolved_entity.entity, theme_matches, themes)

    event_candidate = extract_event_candidate(document, theme_matches, resolved_entities)
    event = session.scalar(
        select(Event).where(Event.source_document_id == document.id, Event.status == "normalized").limit(1)
    )
    if event is None:
        event = Event(source_document_id=document.id, status="normalized")
        session.add(event)

    event.event_type = event_candidate.event_type
    event.title = event_candidate.title
    event.summary = event_candidate.summary
    event.why_it_matters = event_candidate.why_it_matters
    event.skeptical_note = event_candidate.skeptical_note
    event.occurred_at = ensure_utc(document.published_at or document.detected_at) or datetime.now(tz=timezone.utc)
    event.detected_at = datetime.now(tz=timezone.utc)
    event.stack_layer = event_candidate.stack_layer
    event.confidence = event_candidate.confidence
    event.status = "normalized"
    event.metadata_json = {
        **event_candidate.metadata,
        "normalization_version": NORMALIZATION_VERSION,
        "source_document_id": str(document.id),
    }
    session.flush()

    session.execute(delete(EventEntityLink).where(EventEntityLink.event_id == event.id))
    session.flush()

    for resolved_entity in resolved_entities:
        session.add(
            EventEntityLink(
                event_id=event.id,
                entity_id=resolved_entity.entity.id,
                role=resolved_entity.role,
                confidence=resolved_entity.confidence,
            )
        )

    normalized_at = datetime.now(tz=timezone.utc)
    metadata = dict(document.metadata_json or {})
    metadata.update(
        {
            "normalized_at": normalized_at.isoformat(),
            "normalization_version": NORMALIZATION_VERSION,
            "theme_slugs": [theme.slug for theme in theme_matches],
            "event_type": event.event_type,
        }
    )
    document.metadata_json = metadata
    document.normalized_at = normalized_at
    document.normalization_version = NORMALIZATION_VERSION
    session.flush()

    return NormalizationSummary(
        source_document_id=str(document.id),
        entities_resolved=len(resolved_entities),
        themes_assigned=len(theme_matches),
        events_created=1,
        event_id=str(event.id),
    )


def normalize_pending_documents(
    session: Session,
    *,
    limit: int = 20,
    source_type: str | None = None,
    reprocess: bool = False,
) -> list[NormalizationSummary]:
    stmt = select(SourceDocument).order_by(SourceDocument.published_at.desc(), SourceDocument.detected_at.desc())
    if source_type:
        stmt = stmt.where(SourceDocument.source_type == source_type)

    if not reprocess:
        stmt = (
            select(SourceDocument)
            .where(SourceDocument.normalized_at.is_(None))
            .order_by(SourceDocument.published_at.desc(), SourceDocument.detected_at.desc())
        )
        if source_type:
            stmt = stmt.where(SourceDocument.source_type == source_type)

    documents = session.scalars(stmt.limit(limit)).all()
    summaries: list[NormalizationSummary] = []

    for document in documents:
        summaries.append(normalize_source_document(session, str(document.id)))
        session.commit()

    return summaries
