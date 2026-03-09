from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.brief import generate_daily_brief
from app.models import IngestionRun
from app.scoring.engine import score_entities, score_events
from app.services.ingestion import persist_ingestion_run
from app.services.normalization import normalize_pending_documents
from app.services.operations_status import get_operations_status
from app.sources.base import FetchConfig
from app.sources.registry import build_adapter


def _build_healthy_state(session, fixture_dir) -> None:
    for source_type, fixture_name in [
        ("arxiv", "arxiv_feed.xml"),
        ("github", "github_releases.json"),
        ("huggingface", "huggingface_models.json"),
        ("edgar", "edgar_submissions.json"),
    ]:
        adapter = build_adapter(source_type)
        documents = adapter.fetch(FetchConfig(fixture_path=fixture_dir / fixture_name))
        persist_ingestion_run(session, source_type=source_type, documents=documents, run_metadata={"fixture": True})

    normalize_pending_documents(session, limit=20)
    score_events(session, reprocess=True)
    score_entities(session, reprocess=True)
    generate_daily_brief(session)


def test_operations_status_reports_ok_for_fresh_pipeline(session, fixture_dir) -> None:
    _build_healthy_state(session, fixture_dir)

    status = get_operations_status(session)

    assert status.overall_status == "ok"
    assert status.pending_normalization_count == 0
    assert status.latest_event_scored_at is not None
    assert status.latest_entity_scored_at is not None
    assert status.latest_brief_updated_at is not None
    assert not status.stale_reasons


def test_operations_status_reports_degraded_for_failed_latest_ingest(session, fixture_dir) -> None:
    _build_healthy_state(session, fixture_dir)

    session.add(
        IngestionRun(
            source_type="github",
            status="failed",
            started_at=datetime.now(tz=timezone.utc) + timedelta(minutes=1),
            finished_at=datetime.now(tz=timezone.utc) + timedelta(minutes=1),
            documents_seen=0,
            documents_created=0,
            error_message="boom",
            metadata_json={"fixture": True},
        )
    )
    session.commit()

    status = get_operations_status(session)

    assert status.overall_status == "degraded"
    assert any(run.source_type == "github" and run.status == "failed" for run in status.ingest_runs)
