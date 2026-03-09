from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import JSON, Boolean, Float, ForeignKey, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Entity(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "entities"

    entity_type: Mapped[str] = mapped_column(String(64), index=True)
    canonical_name: Mapped[str] = mapped_column(String(255), index=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True)
    website: Mapped[Optional[str]] = mapped_column(String(500))
    description: Mapped[Optional[str]] = mapped_column(Text)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    aliases: Mapped[list["EntityAlias"]] = relationship(back_populates="entity", cascade="all, delete-orphan")
    theme_links: Mapped[list["EntityThemeLink"]] = relationship(back_populates="entity", cascade="all, delete-orphan")
    event_links: Mapped[list["EventEntityLink"]] = relationship(back_populates="entity", cascade="all, delete-orphan")
    score: Mapped[Optional["EntityScore"]] = relationship(back_populates="entity", uselist=False, cascade="all, delete-orphan")
    watchlist_items: Mapped[list["WatchlistItem"]] = relationship(back_populates="entity")
    opportunities: Mapped[list["Opportunity"]] = relationship(back_populates="entity")
    daily_brief_items: Mapped[list["DailyBriefItem"]] = relationship(back_populates="entity")
    notes: Mapped[list["AnalystNote"]] = relationship(back_populates="entity")
    embeddings: Mapped[list["EmbeddingChunk"]] = relationship(back_populates="entity")


class EntityAlias(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "entity_aliases"

    entity_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("entities.id", ondelete="CASCADE"))
    alias: Mapped[str] = mapped_column(String(255), index=True)
    confidence: Mapped[float] = mapped_column(Float, default=1.0, server_default="1.0")
    is_manual: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    entity: Mapped[Entity] = relationship(back_populates="aliases")


class Theme(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "themes"

    name: Mapped[str] = mapped_column(String(255))
    slug: Mapped[str] = mapped_column(String(255), unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    entity_links: Mapped[list["EntityThemeLink"]] = relationship(back_populates="theme", cascade="all, delete-orphan")
    watchlist_items: Mapped[list["WatchlistItem"]] = relationship(back_populates="theme")
    opportunities: Mapped[list["Opportunity"]] = relationship(back_populates="theme")


class EntityThemeLink(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "entity_theme_links"
    __table_args__ = (UniqueConstraint("entity_id", "theme_id", name="uq_entity_theme_links_entity_theme"),)

    entity_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("entities.id", ondelete="CASCADE"))
    theme_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("themes.id", ondelete="CASCADE"))
    confidence: Mapped[float] = mapped_column(Float, default=1.0, server_default="1.0")
    is_manual: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")

    entity: Mapped[Entity] = relationship(back_populates="theme_links")
    theme: Mapped[Theme] = relationship(back_populates="entity_links")
