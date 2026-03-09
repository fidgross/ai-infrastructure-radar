from __future__ import annotations

import json

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.models import DailyBrief, EntityScore, Event, EventScore, SourceDocument
from app.pipeline.orchestrator import run_pipeline


def test_run_pipeline_processes_manifest_and_is_idempotent(tmp_path, fixture_dir) -> None:
    manifest_path = tmp_path / "source_manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "sources": [
                    {"source_type": "arxiv", "enabled": True, "limit": 10, "fixture_path": str(fixture_dir / "arxiv_feed.xml")},
                    {"source_type": "github", "enabled": True, "limit": 10, "fixture_path": str(fixture_dir / "github_releases.json")},
                    {"source_type": "huggingface", "enabled": True, "limit": 10, "fixture_path": str(fixture_dir / "huggingface_models.json")},
                    {"source_type": "edgar", "enabled": True, "limit": 10, "fixture_path": str(fixture_dir / "edgar_submissions.json")},
                ]
            }
        ),
        encoding="utf-8",
    )

    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

    first = run_pipeline(manifest_path=manifest_path, session_factory=SessionLocal)
    second = run_pipeline(manifest_path=manifest_path, session_factory=SessionLocal)

    with SessionLocal() as session:
        assert first["status"] == "success"
        assert first["normalization"]["documents_processed"] == 4
        assert first["brief"]["generated"] is True
        assert second["status"] == "success"
        assert second["normalization"]["documents_processed"] == 0
        assert session.scalar(select(func.count()).select_from(SourceDocument)) == 4
        assert session.scalar(select(func.count()).select_from(Event)) == 4
        assert session.scalar(select(func.count()).select_from(EventScore)) == 4
        assert session.scalar(select(func.count()).select_from(EntityScore)) >= 4
        assert session.scalar(select(func.count()).select_from(DailyBrief)) == 1
