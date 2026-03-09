from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path
from typing import Callable

from sqlalchemy.orm import Session

from app.brief import generate_daily_brief
from app.db.session import SessionLocal
from app.pipeline.manifest import PipelineSourceSpec, default_manifest_path, load_source_manifest
from app.scoring.engine import get_ranked_events, score_entities_only, score_events_only
from app.services.ingestion import persist_ingestion_run
from app.services.normalization import normalize_pending_documents
from app.sources.base import FetchConfig
from app.sources.registry import build_adapter

SessionFactory = Callable[[], Session]


def run_pipeline(
    *,
    manifest_path: str | Path | None = None,
    normalize_batch_size: int = 100,
    brief_date: date | None = None,
    session_factory: SessionFactory = SessionLocal,
) -> dict:
    started_at = datetime.now(tz=timezone.utc)
    specs = load_source_manifest(manifest_path)
    ingest_results: list[dict] = []
    failures: list[str] = []

    for spec in specs:
        if not spec.enabled:
            continue
        try:
            ingest_results.append(_run_ingest_spec(spec, session_factory=session_factory))
        except Exception as exc:
            failures.append(f"{spec.source_type}:{exc}")
            ingest_results.append(
                {
                    "source_type": spec.source_type,
                    "status": "failed",
                    "documents_seen": 0,
                    "documents_created": 0,
                    "payloads_created": 0,
                    "error": str(exc),
                }
            )

    normalization_results: list[dict] = []
    while True:
        with session_factory() as session:
            batch = [summary.__dict__ for summary in normalize_pending_documents(session, limit=normalize_batch_size)]
        normalization_results.extend(batch)
        if len(batch) < normalize_batch_size:
            break

    with session_factory() as session:
        event_summaries = [summary.__dict__ for summary in score_events_only(session, reprocess=True)]
        entity_summaries = [summary.__dict__ for summary in score_entities_only(session, reprocess=True)]
        ranked_events = [
            {"event_id": str(event.id), "title": event.title, "radar_score": score.radar_score}
            for event, score in get_ranked_events(session, limit=10)
        ]

    with session_factory() as session:
        brief_summary = generate_daily_brief(session, brief_date=brief_date)

    finished_at = datetime.now(tz=timezone.utc)
    status = "degraded" if failures else "success"

    return {
        "manifest_path": str(Path(manifest_path) if manifest_path is not None else default_manifest_path()),
        "started_at": started_at.isoformat(),
        "finished_at": finished_at.isoformat(),
        "duration_seconds": round((finished_at - started_at).total_seconds(), 3),
        "status": status,
        "ingest_runs": ingest_results,
        "normalization": {
            "documents_processed": len(normalization_results),
            "documents": normalization_results,
        },
        "scoring": {
            "events_scored": event_summaries,
            "entities_scored": entity_summaries,
            "top_events": ranked_events,
        },
        "brief": brief_summary.__dict__,
        "failures": failures,
    }


def _run_ingest_spec(spec: PipelineSourceSpec, *, session_factory: SessionFactory) -> dict:
    adapter = build_adapter(spec.source_type)
    config = FetchConfig(
        fixture_path=Path(spec.fixture_path) if spec.fixture_path else None,
        query=spec.query,
        org=spec.org,
        repo=spec.repo,
        ticker=spec.ticker,
        cik=spec.cik,
        limit=spec.limit,
    )
    documents = adapter.fetch(config)
    metadata = {
        "query": spec.query,
        "org": spec.org,
        "repo": spec.repo,
        "ticker": spec.ticker,
        "cik": spec.cik,
        "fixture_path": spec.fixture_path,
        "limit": spec.limit,
        "scheduled": True,
    }
    with session_factory() as session:
        summary = persist_ingestion_run(session, source_type=spec.source_type, documents=documents, run_metadata=metadata)
    return summary.__dict__
