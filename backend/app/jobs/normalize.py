from __future__ import annotations

from app.db.session import SessionLocal
from app.services.normalization import normalize_pending_documents, normalize_source_document


def run_normalize_pipeline(
    *,
    source_document_id: str | None = None,
    limit: int = 20,
    source_type: str | None = None,
    reprocess: bool = False,
) -> list[dict]:
    with SessionLocal() as session:
        if source_document_id:
            summary = normalize_source_document(session, source_document_id)
            session.commit()
            return [summary.__dict__]
        return [summary.__dict__ for summary in normalize_pending_documents(session, limit=limit, source_type=source_type, reprocess=reprocess)]
