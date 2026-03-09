from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import DailyBrief, EntityScore, EventScore, IngestionRun, SourceDocument
from app.schemas.api import IngestionRunStatusModel, OperationsStatusResponse
from app.sources.registry import SOURCE_ADAPTERS
from app.utils.dates import ensure_utc

STALE_AFTER = timedelta(hours=12)


def get_operations_status(session: Session) -> OperationsStatusResponse:
    now = datetime.now(tz=timezone.utc)
    ingest_runs = []
    stale_reasons: list[str] = []
    degraded = False

    for source_type in sorted(SOURCE_ADAPTERS):
        run = session.scalar(
            select(IngestionRun)
            .where(IngestionRun.source_type == source_type)
            .order_by(IngestionRun.started_at.desc())
            .limit(1)
        )
        if run is None:
            stale_reasons.append(f"No ingest run has completed for {source_type}.")
            ingest_runs.append(
                IngestionRunStatusModel(
                    source_type=source_type,
                    status="missing",
                    started_at=None,
                    finished_at=None,
                    documents_seen=0,
                    documents_created=0,
                    error_message=None,
                )
            )
            continue
        if run.status == "failed":
            degraded = True
        ingest_runs.append(
            IngestionRunStatusModel(
                source_type=source_type,
                status=run.status,
                started_at=run.started_at,
                finished_at=run.finished_at,
                documents_seen=run.documents_seen,
                documents_created=run.documents_created,
                error_message=run.error_message,
            )
        )

    pending_normalization_count = session.scalar(
        select(func.count(SourceDocument.id)).where(SourceDocument.normalized_at.is_(None))
    ) or 0
    if pending_normalization_count:
        stale_reasons.append(f"{pending_normalization_count} source documents are still pending normalization.")

    latest_event_scored_at = session.scalar(select(func.max(EventScore.scored_at)))
    latest_entity_scored_at = session.scalar(select(func.max(EntityScore.scored_at)))
    latest_brief = session.scalar(select(DailyBrief).order_by(DailyBrief.brief_date.desc()).limit(1))

    latest_event_scored_at = ensure_utc(latest_event_scored_at)
    latest_entity_scored_at = ensure_utc(latest_entity_scored_at)
    latest_brief_updated_at = ensure_utc(latest_brief.updated_at) if latest_brief is not None else None

    if latest_event_scored_at is None or now - latest_event_scored_at > STALE_AFTER:
        stale_reasons.append("Event scores are older than 12 hours.")
    if latest_entity_scored_at is None or now - latest_entity_scored_at > STALE_AFTER:
        stale_reasons.append("Entity scores are older than 12 hours.")

    latest_brief_date = latest_brief.brief_date if latest_brief is not None else None
    if latest_brief is None:
        stale_reasons.append("No generated brief is available.")
    else:
        if latest_brief_date < now.date():
            stale_reasons.append("Latest brief date is behind today UTC.")
        if latest_brief_updated_at is None or now - latest_brief_updated_at > STALE_AFTER:
            stale_reasons.append("Latest brief has not been updated in the last 12 hours.")

    overall_status = "ok"
    if degraded:
        overall_status = "degraded"
    elif stale_reasons:
        overall_status = "stale"

    return OperationsStatusResponse(
        overall_status=overall_status,
        ingest_runs=ingest_runs,
        pending_normalization_count=int(pending_normalization_count),
        latest_event_scored_at=latest_event_scored_at,
        latest_entity_scored_at=latest_entity_scored_at,
        latest_brief_date=latest_brief_date,
        latest_brief_updated_at=latest_brief_updated_at,
        stale_reasons=stale_reasons,
    )
