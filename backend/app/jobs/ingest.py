from __future__ import annotations

from pathlib import Path

from app.db.session import SessionLocal
from app.services.ingestion import IngestionSummary, persist_ingestion_run
from app.sources.base import FetchConfig
from app.sources.registry import build_adapter


def run_source_ingest(
    *,
    source_type: str,
    fixture_path: str | None = None,
    query: str | None = None,
    org: str | None = None,
    repo: str | None = None,
    ticker: str | None = None,
    cik: str | None = None,
    limit: int = 10,
) -> IngestionSummary:
    adapter = build_adapter(source_type)
    config = FetchConfig(
        fixture_path=Path(fixture_path) if fixture_path else None,
        query=query,
        org=org,
        repo=repo,
        ticker=ticker,
        cik=cik,
        limit=limit,
    )
    documents = adapter.fetch(config)
    metadata = {
        "query": query,
        "org": org,
        "repo": repo,
        "ticker": ticker,
        "cik": cik,
        "fixture_path": fixture_path,
        "limit": limit,
    }
    with SessionLocal() as session:
        return persist_ingestion_run(session, source_type=source_type, documents=documents, run_metadata=metadata)
