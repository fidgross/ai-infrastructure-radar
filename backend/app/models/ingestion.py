from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDPrimaryKeyMixin


class IngestionRun(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "ingestion_runs"

    source_type: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(32))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    documents_seen: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    documents_created: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    source_documents: Mapped[list["SourceDocument"]] = relationship(back_populates="ingestion_run")
    source_payloads: Mapped[list["SourcePayload"]] = relationship(back_populates="ingestion_run")


class SourceDocument(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "source_documents"
    __table_args__ = (UniqueConstraint("fingerprint", name="uq_source_documents_fingerprint"),)

    ingestion_run_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid(as_uuid=True), ForeignKey("ingestion_runs.id", ondelete="SET NULL"))
    source_type: Mapped[str] = mapped_column(String(64), index=True)
    source_external_id: Mapped[str] = mapped_column(String(255))
    title: Mapped[str] = mapped_column(String(500))
    url: Mapped[str] = mapped_column(String(1000))
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), index=True)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    normalized_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    normalization_version: Mapped[Optional[str]] = mapped_column(String(64))
    raw_text: Mapped[Optional[str]] = mapped_column(Text)
    normalized_text: Mapped[Optional[str]] = mapped_column(Text)
    fingerprint: Mapped[str] = mapped_column(String(255))
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    ingestion_run: Mapped[Optional[IngestionRun]] = relationship(back_populates="source_documents")
    source_payloads: Mapped[list["SourcePayload"]] = relationship(back_populates="source_document")
    events: Mapped[list["Event"]] = relationship(back_populates="source_document")


class SourcePayload(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "source_payloads"
    __table_args__ = (UniqueConstraint("payload_hash", name="uq_source_payloads_payload_hash"),)

    ingestion_run_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("ingestion_runs.id", ondelete="CASCADE"))
    source_document_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid(as_uuid=True), ForeignKey("source_documents.id", ondelete="CASCADE"))
    source_type: Mapped[str] = mapped_column(String(64), index=True)
    payload_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    payload_hash: Mapped[str] = mapped_column(String(255))
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    ingestion_run: Mapped[IngestionRun] = relationship(back_populates="source_payloads")
    source_document: Mapped[Optional[SourceDocument]] = relationship(back_populates="source_payloads")
