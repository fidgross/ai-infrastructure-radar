from sqlalchemy import func, select

from app.models import IngestionRun, SourceDocument, SourcePayload
from app.services.ingestion import persist_ingestion_run
from app.sources.base import FetchConfig
from app.sources.github.adapter import GitHubAdapter


def test_ingestion_persistence_is_idempotent(session, fixture_dir) -> None:
    adapter = GitHubAdapter()
    documents = adapter.fetch(FetchConfig(fixture_path=fixture_dir / "github_releases.json"))

    first = persist_ingestion_run(session, source_type="github", documents=documents, run_metadata={"fixture": True})
    second = persist_ingestion_run(session, source_type="github", documents=documents, run_metadata={"fixture": True})

    source_document_count = session.scalar(select(func.count()).select_from(SourceDocument))
    source_payload_count = session.scalar(select(func.count()).select_from(SourcePayload))
    ingestion_run_count = session.scalar(select(func.count()).select_from(IngestionRun))

    assert first.documents_created == 1
    assert first.payloads_created == 1
    assert second.documents_created == 0
    assert second.payloads_created == 0
    assert source_document_count == 1
    assert source_payload_count == 1
    assert ingestion_run_count == 2
