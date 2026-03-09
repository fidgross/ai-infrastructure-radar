from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import JSON, Date, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDPrimaryKeyMixin
from app.db.types import EmbeddingVector


class Event(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "events"

    event_type: Mapped[str] = mapped_column(String(64), index=True)
    title: Mapped[str] = mapped_column(String(500))
    summary: Mapped[Optional[str]] = mapped_column(Text)
    why_it_matters: Mapped[Optional[str]] = mapped_column(Text)
    skeptical_note: Mapped[Optional[str]] = mapped_column(Text)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    source_document_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid(as_uuid=True), ForeignKey("source_documents.id", ondelete="SET NULL"))
    stack_layer: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.0, server_default="0.0")
    status: Mapped[str] = mapped_column(String(32), default="candidate", server_default="candidate")
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    source_document: Mapped[Optional["SourceDocument"]] = relationship(back_populates="events")
    entity_links: Mapped[list["EventEntityLink"]] = relationship(back_populates="event", cascade="all, delete-orphan")
    score: Mapped[Optional["EventScore"]] = relationship(back_populates="event", uselist=False, cascade="all, delete-orphan")
    opportunity_links: Mapped[list["OpportunityEventLink"]] = relationship(back_populates="event", cascade="all, delete-orphan")
    daily_brief_items: Mapped[list["DailyBriefItem"]] = relationship(back_populates="event")
    embeddings: Mapped[list["EmbeddingChunk"]] = relationship(back_populates="event")


class EventEntityLink(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "event_entity_links"
    __table_args__ = (UniqueConstraint("event_id", "entity_id", "role", name="uq_event_entity_links_event_entity_role"),)

    event_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("events.id", ondelete="CASCADE"))
    entity_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("entities.id", ondelete="CASCADE"))
    role: Mapped[Optional[str]] = mapped_column(String(64))
    confidence: Mapped[float] = mapped_column(Float, default=1.0, server_default="1.0")

    event: Mapped[Event] = relationship(back_populates="entity_links")
    entity: Mapped["Entity"] = relationship(back_populates="event_links")


class EventScore(Base):
    __tablename__ = "event_scores"

    event_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("events.id", ondelete="CASCADE"), primary_key=True)
    novelty_score: Mapped[float] = mapped_column(Float, default=0.0, server_default="0.0")
    momentum_score: Mapped[float] = mapped_column(Float, default=0.0, server_default="0.0")
    strategic_importance_score: Mapped[float] = mapped_column(Float, default=0.0, server_default="0.0")
    aws_relevance_score: Mapped[float] = mapped_column(Float, default=0.0, server_default="0.0")
    corpdev_score: Mapped[float] = mapped_column(Float, default=0.0, server_default="0.0")
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0, server_default="0.0")
    radar_score: Mapped[float] = mapped_column(Float, default=0.0, server_default="0.0", index=True)
    scored_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    scoring_version: Mapped[str] = mapped_column(String(32))
    rationale_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    event: Mapped[Event] = relationship(back_populates="score")


class EntityScore(Base):
    __tablename__ = "entity_scores"

    entity_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("entities.id", ondelete="CASCADE"), primary_key=True)
    momentum_score: Mapped[float] = mapped_column(Float, default=0.0, server_default="0.0")
    aws_relevance_score: Mapped[float] = mapped_column(Float, default=0.0, server_default="0.0")
    corpdev_interest_score: Mapped[float] = mapped_column(Float, default=0.0, server_default="0.0")
    entity_priority_score: Mapped[float] = mapped_column(Float, default=0.0, server_default="0.0", index=True)
    scored_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    scoring_version: Mapped[str] = mapped_column(String(32))
    rationale_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    entity: Mapped["Entity"] = relationship(back_populates="score")


class Watchlist(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "watchlists"

    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text)
    watchlist_type: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    items: Mapped[list["WatchlistItem"]] = relationship(back_populates="watchlist", cascade="all, delete-orphan")


class WatchlistItem(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "watchlist_items"

    watchlist_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("watchlists.id", ondelete="CASCADE"))
    entity_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid(as_uuid=True), ForeignKey("entities.id", ondelete="SET NULL"))
    theme_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid(as_uuid=True), ForeignKey("themes.id", ondelete="SET NULL"))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    watchlist: Mapped[Watchlist] = relationship(back_populates="items")
    entity: Mapped[Optional["Entity"]] = relationship(back_populates="watchlist_items")
    theme: Mapped[Optional["Theme"]] = relationship(back_populates="watchlist_items")


class Opportunity(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "opportunities"

    entity_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid(as_uuid=True), ForeignKey("entities.id", ondelete="SET NULL"))
    theme_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid(as_uuid=True), ForeignKey("themes.id", ondelete="SET NULL"))
    opportunity_type: Mapped[str] = mapped_column(String(64))
    title: Mapped[str] = mapped_column(String(500))
    rationale: Mapped[str] = mapped_column(Text)
    risks: Mapped[Optional[str]] = mapped_column(Text)
    integration_notes: Mapped[Optional[str]] = mapped_column(Text)
    priority_score: Mapped[Optional[float]] = mapped_column(Float, index=True)
    status: Mapped[str] = mapped_column(String(32), default="open", server_default="open")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    entity: Mapped[Optional["Entity"]] = relationship(back_populates="opportunities")
    theme: Mapped[Optional["Theme"]] = relationship(back_populates="opportunities")
    event_links: Mapped[list["OpportunityEventLink"]] = relationship(back_populates="opportunity", cascade="all, delete-orphan")
    notes: Mapped[list["AnalystNote"]] = relationship(back_populates="opportunity")


class OpportunityEventLink(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "opportunity_event_links"
    __table_args__ = (UniqueConstraint("opportunity_id", "event_id", name="uq_opportunity_event_links_opportunity_event"),)

    opportunity_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("opportunities.id", ondelete="CASCADE"))
    event_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("events.id", ondelete="CASCADE"))

    opportunity: Mapped[Opportunity] = relationship(back_populates="event_links")
    event: Mapped[Event] = relationship(back_populates="opportunity_links")


class DailyBrief(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "daily_briefs"

    brief_date: Mapped[date] = mapped_column(Date, unique=True)
    title: Mapped[str] = mapped_column(String(500))
    summary: Mapped[str] = mapped_column(Text)
    aws_implications: Mapped[Optional[str]] = mapped_column(Text)
    possible_actions: Mapped[Optional[str]] = mapped_column(Text)
    skeptical_counterpoints: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="published", server_default="published")
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    items: Mapped[list["DailyBriefItem"]] = relationship(back_populates="daily_brief", cascade="all, delete-orphan")


class DailyBriefItem(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "daily_brief_items"

    daily_brief_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("daily_briefs.id", ondelete="CASCADE"))
    item_type: Mapped[str] = mapped_column(String(64))
    rank: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(500))
    summary: Mapped[str] = mapped_column(Text)
    event_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid(as_uuid=True), ForeignKey("events.id", ondelete="SET NULL"))
    entity_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid(as_uuid=True), ForeignKey("entities.id", ondelete="SET NULL"))
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    daily_brief: Mapped[DailyBrief] = relationship(back_populates="items")
    event: Mapped[Optional[Event]] = relationship(back_populates="daily_brief_items")
    entity: Mapped[Optional["Entity"]] = relationship(back_populates="daily_brief_items")


class AnalystNote(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "analyst_notes"

    entity_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid(as_uuid=True), ForeignKey("entities.id", ondelete="SET NULL"))
    opportunity_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid(as_uuid=True), ForeignKey("opportunities.id", ondelete="SET NULL"))
    note_type: Mapped[str] = mapped_column(String(64))
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    entity: Mapped[Optional["Entity"]] = relationship(back_populates="notes")
    opportunity: Mapped[Optional[Opportunity]] = relationship(back_populates="notes")


class EmbeddingChunk(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "embedding_chunks"

    source_document_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid(as_uuid=True), ForeignKey("source_documents.id", ondelete="SET NULL"))
    entity_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid(as_uuid=True), ForeignKey("entities.id", ondelete="SET NULL"))
    event_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid(as_uuid=True), ForeignKey("events.id", ondelete="SET NULL"))
    chunk_text: Mapped[str] = mapped_column(Text)
    chunk_index: Mapped[int] = mapped_column(Integer, index=True)
    embedding: Mapped[Optional[list[float]]] = mapped_column(EmbeddingVector(), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    source_document: Mapped[Optional["SourceDocument"]] = relationship()
    entity: Mapped[Optional["Entity"]] = relationship(back_populates="embeddings")
    event: Mapped[Optional[Event]] = relationship(back_populates="embeddings")
