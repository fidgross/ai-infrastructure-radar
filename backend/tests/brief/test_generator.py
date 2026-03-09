from __future__ import annotations

from datetime import date

from sqlalchemy import func, select

from app.brief import generate_daily_brief
from app.models import DailyBrief, DailyBriefItem
from app.scoring.engine import score_entities, score_events
from app.services.ingestion import persist_ingestion_run
from app.services.normalization import normalize_pending_documents
from app.sources.base import FetchConfig
from app.sources.registry import build_adapter


def _ingest_normalize_and_score(session, fixture_dir) -> None:
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


def test_generate_daily_brief_creates_one_brief_with_items(session, fixture_dir) -> None:
    _ingest_normalize_and_score(session, fixture_dir)

    summary = generate_daily_brief(session, brief_date=date(2026, 3, 8))
    brief = session.scalar(select(DailyBrief))
    item_count = session.scalar(select(func.count()).select_from(DailyBriefItem))
    top_event_items = session.scalar(
        select(func.count()).select_from(DailyBriefItem).where(DailyBriefItem.item_type == "top_event")
    )

    assert summary.generated is True
    assert 1 <= summary.top_event_count <= 4
    assert summary.entity_spotlight_count >= 0
    assert brief is not None
    assert brief.updated_at is not None
    assert item_count == summary.top_event_count + summary.entity_spotlight_count
    assert top_event_items == summary.top_event_count


def test_generate_daily_brief_is_idempotent_for_same_day(session, fixture_dir) -> None:
    _ingest_normalize_and_score(session, fixture_dir)

    first = generate_daily_brief(session, brief_date=date(2026, 3, 8))
    second = generate_daily_brief(session, brief_date=date(2026, 3, 8))

    assert first.generated is True
    assert second.generated is True
    assert session.scalar(select(func.count()).select_from(DailyBrief)) == 1
    assert session.scalar(select(func.count()).select_from(DailyBriefItem)) == second.top_event_count + second.entity_spotlight_count


def test_generate_daily_brief_is_noop_without_candidates(session) -> None:
    summary = generate_daily_brief(session, brief_date=date(2026, 3, 8))

    assert summary.generated is False
    assert session.scalar(select(func.count()).select_from(DailyBrief)) == 0
