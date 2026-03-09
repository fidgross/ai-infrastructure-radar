from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.models import Entity


@dataclass
class EntityCandidate:
    canonical_name: str
    entity_type: str
    role: str = "subject"
    confidence: float = 0.8
    aliases: list[str] = field(default_factory=list)
    website: str | None = None
    description: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ResolvedEntity:
    entity: Entity
    role: str
    confidence: float


@dataclass
class ThemeMatch:
    name: str
    slug: str
    description: str
    stack_layer: str
    confidence: float
    rationale: str


@dataclass
class EventCandidate:
    event_type: str
    title: str
    summary: str
    why_it_matters: str
    skeptical_note: str
    stack_layer: str
    confidence: float
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class NormalizationSummary:
    source_document_id: str
    entities_resolved: int
    themes_assigned: int
    events_created: int
    event_id: str | None
