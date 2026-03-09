from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import IngestionRun, SourceDocument, SourcePayload
from app.sources.base import FetchedDocument


@dataclass
class IngestionSummary:
    run_id: str
    source_type: str
    status: str
    documents_seen: int
    documents_created: int
    payloads_created: int


def persist_ingestion_run(
    session: Session,
    *,
    source_type: str,
    documents: list[FetchedDocument],
    run_metadata: dict[str, Any] | None = None,
) -> IngestionSummary:
    run = IngestionRun(
        source_type=source_type,
        status="running",
        started_at=datetime.now(tz=timezone.utc),
        metadata_json=run_metadata or {},
    )
    session.add(run)
    session.flush()

    documents_created = 0
    payloads_created = 0

    try:
        for document in documents:
            existing_document = session.scalar(
                select(SourceDocument).where(SourceDocument.fingerprint == document.fingerprint)
            )

            if existing_document is None:
                existing_document = SourceDocument(
                    ingestion_run_id=run.id,
                    source_type=document.source_type,
                    source_external_id=document.source_external_id,
                    title=document.title,
                    url=document.url,
                    published_at=document.published_at,
                    detected_at=document.detected_at,
                    raw_text=document.raw_text,
                    normalized_text=document.normalized_text,
                    fingerprint=document.fingerprint,
                    metadata_json=document.metadata,
                )
                session.add(existing_document)
                session.flush()
                documents_created += 1
            else:
                existing_document.ingestion_run_id = run.id
                existing_document.title = document.title
                existing_document.url = document.url
                existing_document.published_at = document.published_at
                existing_document.detected_at = document.detected_at
                existing_document.raw_text = document.raw_text
                existing_document.normalized_text = document.normalized_text
                existing_document.metadata_json = document.metadata

            existing_payload = session.scalar(
                select(SourcePayload).where(SourcePayload.payload_hash == document.payload_hash)
            )
            if existing_payload is None:
                session.add(
                    SourcePayload(
                        ingestion_run_id=run.id,
                        source_document_id=existing_document.id,
                        source_type=document.source_type,
                        payload_json=document.payload,
                        payload_hash=document.payload_hash,
                        received_at=document.detected_at,
                    )
                )
                payloads_created += 1

        run.documents_seen = len(documents)
        run.documents_created = documents_created
        run.finished_at = datetime.now(tz=timezone.utc)
        run.status = "success"
        session.commit()
    except Exception as exc:
        session.rollback()
        failed_run = session.get(IngestionRun, run.id)
        if failed_run is None:
            failed_run = IngestionRun(id=run.id, source_type=source_type, status="failed")
            session.add(failed_run)
        failed_run.finished_at = datetime.now(tz=timezone.utc)
        failed_run.status = "failed"
        failed_run.error_message = str(exc)
        failed_run.documents_seen = len(documents)
        failed_run.documents_created = documents_created
        failed_run.metadata_json = run_metadata or {}
        session.commit()
        raise

    return IngestionSummary(
        run_id=str(run.id),
        source_type=source_type,
        status=run.status,
        documents_seen=run.documents_seen,
        documents_created=run.documents_created,
        payloads_created=payloads_created,
    )
