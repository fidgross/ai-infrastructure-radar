from __future__ import annotations

from collections.abc import Iterable

from slugify import slugify
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Entity, EntityAlias
from app.services.normalization_types import EntityCandidate, ResolvedEntity


def resolve_entity_candidates(session: Session, candidates: Iterable[EntityCandidate]) -> list[ResolvedEntity]:
    resolved: list[ResolvedEntity] = []

    for candidate in candidates:
        entity = _find_existing_entity(session, candidate)
        if entity is None:
            entity = Entity(
                entity_type=candidate.entity_type,
                canonical_name=candidate.canonical_name,
                slug=_unique_slug(session, candidate.canonical_name),
                website=candidate.website,
                description=candidate.description,
                metadata_json=dict(candidate.metadata),
            )
            session.add(entity)
            session.flush()
        else:
            if not entity.website and candidate.website:
                entity.website = candidate.website
            if not entity.description and candidate.description:
                entity.description = candidate.description
            merged_metadata = dict(entity.metadata_json or {})
            merged_metadata.update(candidate.metadata)
            entity.metadata_json = merged_metadata

        _ensure_aliases(session, entity, [candidate.canonical_name, *candidate.aliases], candidate.confidence)
        resolved.append(ResolvedEntity(entity=entity, role=candidate.role, confidence=candidate.confidence))

    return resolved


def _find_existing_entity(session: Session, candidate: EntityCandidate) -> Entity | None:
    aliases = [candidate.canonical_name, *candidate.aliases]
    for alias in aliases:
        normalized = alias.strip().casefold()
        if not normalized:
            continue

        alias_match = session.scalar(
            select(Entity)
            .join(EntityAlias, EntityAlias.entity_id == Entity.id)
            .where(func.lower(EntityAlias.alias) == normalized)
        )
        if alias_match is not None:
            return alias_match

        canonical_match = session.scalar(select(Entity).where(func.lower(Entity.canonical_name) == normalized))
        if canonical_match is not None:
            return canonical_match

    return None


def _ensure_aliases(session: Session, entity: Entity, aliases: list[str], confidence: float) -> None:
    existing_aliases = {
        alias.casefold()
        for alias in session.scalars(select(EntityAlias.alias).where(EntityAlias.entity_id == entity.id)).all()
    }

    for alias in aliases:
        clean_alias = alias.strip()
        if not clean_alias:
            continue
        normalized = clean_alias.casefold()
        if normalized in existing_aliases:
            continue
        session.add(
            EntityAlias(
                entity_id=entity.id,
                alias=clean_alias,
                confidence=confidence,
                is_manual=False,
                metadata_json={"resolver": "rule_based"},
            )
        )
        existing_aliases.add(normalized)


def _unique_slug(session: Session, name: str) -> str:
    base_slug = slugify(name) or "entity"
    slug = base_slug
    counter = 2
    while session.scalar(select(Entity).where(Entity.slug == slug)) is not None:
        slug = f"{base_slug}-{counter}"
        counter += 1
    return slug
