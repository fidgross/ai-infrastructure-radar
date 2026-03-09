from __future__ import annotations

from dataclasses import dataclass

from slugify import slugify
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Entity, EntityThemeLink, SourceDocument, Theme
from app.services.normalization_types import ThemeMatch


@dataclass(frozen=True)
class ThemeRule:
    name: str
    description: str
    stack_layer: str
    keywords: tuple[str, ...]


THEME_RULES: tuple[ThemeRule, ...] = (
    ThemeRule(
        name="Inference Economics",
        description="Cost and throughput shifts that materially alter inference deployment choices.",
        stack_layer="Training and inference systems",
        keywords=("inference", "throughput", "latency", "speculative decoding", "serving", "runtime", "token cost", "sparse"),
    ),
    ThemeRule(
        name="Model Portability",
        description="Control points for routing, portability, and platform leverage.",
        stack_layer="Model routing / portability / gateway layer",
        keywords=("routing", "router", "failover", "portability", "gateway", "policy routing", "provider"),
    ),
    ThemeRule(
        name="AI Capex Signals",
        description="Public signals about infrastructure demand and spending.",
        stack_layer="Cloud / AI factories / GPU clouds",
        keywords=("capex", "capacity", "gpu", "datacenter", "factory", "commitment", "expansion", "annual report"),
    ),
    ThemeRule(
        name="Developer Workflow Control Plane",
        description="Developer workflow and orchestration layers that influence operational control points.",
        stack_layer="Developer workflow / orchestration / control plane",
        keywords=("orchestration", "control plane", "workflow", "telemetry", "scheduler"),
    ),
)

DEFAULT_THEME_BY_SOURCE = {
    "arxiv": "Inference Economics",
    "github": "Model Portability",
    "huggingface": "Inference Economics",
    "edgar": "AI Capex Signals",
}


def classify_themes(document: SourceDocument) -> list[ThemeMatch]:
    haystack = _build_haystack(document)
    matches: list[ThemeMatch] = []

    for rule in THEME_RULES:
        matched_keywords = [keyword for keyword in rule.keywords if keyword in haystack]
        if not matched_keywords:
            continue
        confidence = min(0.95, 0.58 + len(matched_keywords) * 0.08)
        matches.append(
            ThemeMatch(
                name=rule.name,
                slug=slugify(rule.name),
                description=rule.description,
                stack_layer=rule.stack_layer,
                confidence=confidence,
                rationale=f"Matched keywords: {', '.join(matched_keywords[:4])}",
            )
        )

    if matches:
        matches.sort(key=lambda match: (-match.confidence, match.name))
        return matches[:3]

    default_name = DEFAULT_THEME_BY_SOURCE.get(document.source_type, "Inference Economics")
    rule = next(rule for rule in THEME_RULES if rule.name == default_name)
    return [
        ThemeMatch(
            name=rule.name,
            slug=slugify(rule.name),
            description=rule.description,
            stack_layer=rule.stack_layer,
            confidence=0.55,
            rationale=f"Applied deterministic default theme for source type {document.source_type}.",
        )
    ]


def ensure_theme_records(session: Session, matches: list[ThemeMatch]) -> list[Theme]:
    themes: list[Theme] = []
    for match in matches:
        theme = session.scalar(select(Theme).where(Theme.slug == match.slug))
        if theme is None:
            theme = Theme(
                name=match.name,
                slug=match.slug,
                description=match.description,
                metadata_json={"source": "rule_based_theme_tagging"},
            )
            session.add(theme)
            session.flush()
        themes.append(theme)
    return themes


def attach_themes_to_entity(session: Session, entity: Entity, matches: list[ThemeMatch], themes: list[Theme]) -> None:
    existing_links = {
        link.theme_id: link
        for link in session.scalars(select(EntityThemeLink).where(EntityThemeLink.entity_id == entity.id)).all()
    }
    for pending_link in session.new:
        if isinstance(pending_link, EntityThemeLink) and pending_link.entity_id == entity.id:
            existing_links[pending_link.theme_id] = pending_link

    for match, theme in zip(matches, themes):
        existing = existing_links.get(theme.id)
        if existing is None:
            existing = EntityThemeLink(
                entity_id=entity.id,
                theme_id=theme.id,
                confidence=match.confidence,
                is_manual=False,
            )
            session.add(existing)
            existing_links[theme.id] = existing
            continue

        existing.confidence = max(existing.confidence, match.confidence)


def _build_haystack(document: SourceDocument) -> str:
    metadata = document.metadata_json or {}
    metadata_text = " ".join(f"{key} {value}" for key, value in metadata.items())
    return " ".join(
        piece.lower()
        for piece in [document.title, document.normalized_text or "", document.raw_text or "", metadata_text]
        if piece
    )
