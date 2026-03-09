from sqlalchemy import func, select

from app.models import EntityScore, EventScore
from app.scoring.engine import get_ranked_events, score_entities, score_events
from app.services.ingestion import persist_ingestion_run
from app.services.normalization import normalize_pending_documents
from app.sources.base import FetchConfig
from app.sources.registry import build_adapter


def _ingest_and_normalize_all_sources(session, fixture_dir) -> None:
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


def test_scoring_is_deterministic_and_populates_scores(session, fixture_dir) -> None:
    _ingest_and_normalize_all_sources(session, fixture_dir)

    first_event_summaries = score_events(session, reprocess=True)
    first_entity_summaries = score_entities(session, reprocess=True)
    first_radar_scores = {
        str(score.event_id): score.radar_score for score in session.scalars(select(EventScore)).all()
    }

    second_event_summaries = score_events(session, reprocess=True)
    second_entity_summaries = score_entities(session, reprocess=True)
    second_radar_scores = {
        str(score.event_id): score.radar_score for score in session.scalars(select(EventScore)).all()
    }

    assert len(first_event_summaries) == len(second_event_summaries) == 4
    assert len(first_entity_summaries) == len(second_entity_summaries) >= 4
    assert first_radar_scores == second_radar_scores
    assert session.scalar(select(func.count()).select_from(EventScore)) == 4
    assert all(score.scored_at is not None for score in session.scalars(select(EventScore)).all())
    assert all(score.scored_at is not None for score in session.scalars(select(EntityScore)).all())


def test_ranking_helper_returns_descending_radar_scores(session, fixture_dir) -> None:
    _ingest_and_normalize_all_sources(session, fixture_dir)

    score_events(session, reprocess=True)
    score_entities(session, reprocess=True)

    ranked_events = get_ranked_events(session, limit=4)
    persisted_event_scores = session.scalars(select(EventScore)).all()
    persisted_entity_scores = session.scalars(select(EntityScore)).all()

    assert len(ranked_events) == 4
    assert len(persisted_event_scores) == 4
    assert len(persisted_entity_scores) >= 4
    assert ranked_events[0][1].radar_score >= ranked_events[-1][1].radar_score
    assert all(0.0 <= score.radar_score <= 10.0 for score in persisted_event_scores)
