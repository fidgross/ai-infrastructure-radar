from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, distinct, func, or_, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models import (
    DailyBrief,
    DailyBriefItem,
    Entity,
    EntityAlias,
    EntityScore,
    EntityThemeLink,
    Event,
    EventEntityLink,
    EventScore,
    Opportunity,
    SourceDocument,
    Theme,
    Watchlist,
    WatchlistItem,
)
from app.schemas.api import (
    BriefItemModel,
    EntityDetail,
    EntityListItem,
    EntityListResponse,
    EntityRef,
    EntityScoreModel,
    EventDetail,
    EventListItem,
    EventListResponse,
    EventScoreModel,
    LatestBriefResponse,
    OpportunityListItem,
    OpportunityListResponse,
    PaginationMeta,
    SearchResponse,
    SearchResultItem,
    SourceDocumentRef,
    ThemeDetail,
    ThemeListItem,
    ThemeListResponse,
    ThemeRef,
    WatchlistItemModel,
    WatchlistListResponse,
    WatchlistModel,
)


def list_events(
    session: Session,
    *,
    page: int,
    page_size: int,
    source_type: str | None = None,
    event_type: str | None = None,
    stack_layer: str | None = None,
    theme_slug: str | None = None,
    min_score: float | None = None,
    days: int | None = None,
    sort: str = "radar_score",
) -> EventListResponse:
    count_stmt = select(func.count(distinct(Event.id))).select_from(Event)
    data_stmt = (
        select(Event)
        .outerjoin(EventScore, EventScore.event_id == Event.id)
        .options(
            joinedload(Event.score),
            joinedload(Event.source_document),
            selectinload(Event.entity_links)
            .joinedload(EventEntityLink.entity)
            .selectinload(Entity.theme_links)
            .joinedload(EntityThemeLink.theme),
        )
    )
    count_stmt, data_stmt = _apply_event_filters(
        count_stmt,
        data_stmt,
        source_type=source_type,
        event_type=event_type,
        stack_layer=stack_layer,
        theme_slug=theme_slug,
        min_score=min_score,
        days=days,
    )
    if theme_slug:
        data_stmt = data_stmt.distinct()
    data_stmt = _order_events(data_stmt, sort)

    total = session.scalar(count_stmt) or 0
    events = session.scalars(_paginate_stmt(data_stmt, page, page_size)).unique().all()

    return EventListResponse(items=[_event_to_list_item(event) for event in events], meta=PaginationMeta(page=page, page_size=page_size, total=total))


def get_event_detail(session: Session, event_id: str) -> EventDetail | None:
    key = _coerce_uuid(event_id, "event_id")
    event = session.scalar(
        select(Event)
        .where(Event.id == key)
        .options(
            joinedload(Event.score),
            joinedload(Event.source_document),
            selectinload(Event.entity_links)
            .joinedload(EventEntityLink.entity)
            .selectinload(Entity.theme_links)
            .joinedload(EntityThemeLink.theme),
        )
    )
    if event is None:
        return None

    item = _event_to_list_item(event)
    return EventDetail(
        **item.model_dump(),
        why_it_matters=event.why_it_matters,
        skeptical_note=event.skeptical_note,
        metadata_json=event.metadata_json or {},
        score=_event_score_model(event.score),
    )


def list_entities(
    session: Session,
    *,
    page: int,
    page_size: int,
    entity_type: str | None = None,
    theme_slug: str | None = None,
    min_priority: float | None = None,
    is_public: bool | None = None,
    sort: str = "entity_priority_score",
) -> EntityListResponse:
    count_stmt = select(func.count(distinct(Entity.id))).select_from(Entity)
    data_stmt = select(Entity).outerjoin(EntityScore, EntityScore.entity_id == Entity.id).options(
        joinedload(Entity.score),
        selectinload(Entity.aliases),
        selectinload(Entity.theme_links).joinedload(EntityThemeLink.theme),
        selectinload(Entity.event_links).joinedload(EventEntityLink.event).joinedload(Event.score),
    )
    count_stmt, data_stmt = _apply_entity_filters(
        count_stmt,
        data_stmt,
        entity_type=entity_type,
        theme_slug=theme_slug,
        min_priority=min_priority,
        is_public=is_public,
    )
    data_stmt = _order_entities(data_stmt, sort)

    total = session.scalar(count_stmt) or 0
    entities = session.scalars(_paginate_stmt(data_stmt, page, page_size)).unique().all()
    return EntityListResponse(items=[_entity_to_list_item(entity) for entity in entities], meta=PaginationMeta(page=page, page_size=page_size, total=total))


def get_entity_detail(session: Session, slug: str) -> EntityDetail | None:
    entity = session.scalar(
        select(Entity)
        .where(Entity.slug == slug)
        .options(
            joinedload(Entity.score),
            selectinload(Entity.aliases),
            selectinload(Entity.theme_links).joinedload(EntityThemeLink.theme),
            selectinload(Entity.event_links).joinedload(EventEntityLink.event).joinedload(Event.score),
            selectinload(Entity.event_links).joinedload(EventEntityLink.event).joinedload(Event.source_document),
            selectinload(Entity.event_links)
            .joinedload(EventEntityLink.event)
            .selectinload(Event.entity_links)
            .joinedload(EventEntityLink.entity)
            .selectinload(Entity.theme_links)
            .joinedload(EntityThemeLink.theme),
        )
    )
    if entity is None:
        return None

    list_item = _entity_to_list_item(entity)
    linked_events = sorted(
        [link.event for link in entity.event_links if link.event is not None],
        key=lambda event: ((event.score.radar_score if event.score else 0.0), event.occurred_at),
        reverse=True,
    )

    return EntityDetail(**list_item.model_dump(), linked_events=[_event_to_list_item(event) for event in linked_events[:20]])


def list_themes(session: Session, *, page: int, page_size: int, sort: str = "entity_count") -> ThemeListResponse:
    entity_count = func.count(EntityThemeLink.entity_id)
    count_stmt = select(func.count(Theme.id))
    data_stmt = (
        select(Theme, entity_count.label("entity_count"))
        .outerjoin(EntityThemeLink, Theme.id == EntityThemeLink.theme_id)
        .group_by(Theme.id)
    )
    if sort == "name":
        data_stmt = data_stmt.order_by(Theme.name.asc())
    else:
        data_stmt = data_stmt.order_by(entity_count.desc(), Theme.name.asc())
    total = session.scalar(count_stmt) or 0
    rows = session.execute(_paginate_stmt(data_stmt, page, page_size)).all()
    return ThemeListResponse(
        items=[ThemeListItem(id=str(theme.id), slug=theme.slug, name=theme.name, description=theme.description, entity_count=row_count) for theme, row_count in rows],
        meta=PaginationMeta(page=page, page_size=page_size, total=total),
    )


def get_theme_detail(session: Session, slug: str) -> ThemeDetail | None:
    theme = session.scalar(
        select(Theme)
        .where(Theme.slug == slug)
        .options(selectinload(Theme.entity_links).joinedload(EntityThemeLink.entity).joinedload(Entity.score))
    )
    if theme is None:
        return None

    entities = [link.entity for link in theme.entity_links if link.entity is not None]
    entity_refs = [
        EntityRef(
            id=str(entity.id),
            slug=entity.slug,
            canonical_name=entity.canonical_name,
            entity_type=entity.entity_type,
            confidence=link.confidence,
        )
        for link, entity in ((link, link.entity) for link in theme.entity_links if link.entity is not None)
    ]

    if entities:
        top_events_stmt = (
            select(Event)
            .join(EventEntityLink, EventEntityLink.event_id == Event.id)
            .outerjoin(EventScore, EventScore.event_id == Event.id)
            .where(EventEntityLink.entity_id.in_([entity.id for entity in entities]))
            .options(
                joinedload(Event.score),
                joinedload(Event.source_document),
                selectinload(Event.entity_links)
                .joinedload(EventEntityLink.entity)
                .selectinload(Entity.theme_links)
                .joinedload(EntityThemeLink.theme),
            )
            .distinct()
            .order_by(func.coalesce(EventScore.radar_score, 0).desc(), Event.occurred_at.desc())
            .limit(10)
        )
        events = session.scalars(top_events_stmt).unique().all()
    else:
        events = []

    return ThemeDetail(
        id=str(theme.id),
        slug=theme.slug,
        name=theme.name,
        description=theme.description,
        entity_count=len(entity_refs),
        linked_entities=entity_refs,
        top_events=[_event_to_list_item(event) for event in events],
    )


def get_latest_brief(session: Session) -> LatestBriefResponse | None:
    brief = session.scalar(
        select(DailyBrief)
        .order_by(DailyBrief.brief_date.desc())
        .options(
            selectinload(DailyBrief.items).joinedload(DailyBriefItem.event).joinedload(Event.score),
            selectinload(DailyBrief.items).joinedload(DailyBriefItem.event).joinedload(Event.source_document),
            selectinload(DailyBrief.items)
            .joinedload(DailyBriefItem.event)
            .selectinload(Event.entity_links)
            .joinedload(EventEntityLink.entity)
            .selectinload(Entity.theme_links)
            .joinedload(EntityThemeLink.theme),
            selectinload(DailyBrief.items).joinedload(DailyBriefItem.entity),
        )
    )
    if brief is None:
        return None

    items = sorted(brief.items, key=lambda item: (item.item_type, item.rank))
    return LatestBriefResponse(
        id=str(brief.id),
        brief_date=brief.brief_date,
        title=brief.title,
        summary=brief.summary,
        aws_implications=brief.aws_implications,
        possible_actions=brief.possible_actions,
        skeptical_counterpoints=brief.skeptical_counterpoints,
        items=[
            BriefItemModel(
                id=str(item.id),
                item_type=item.item_type,
                rank=item.rank,
                title=item.title,
                summary=item.summary,
                event=_event_to_list_item(item.event) if item.event else None,
                entity=_entity_ref(item.entity) if item.entity else None,
            )
            for item in items
        ],
    )


def list_opportunities(
    session: Session,
    *,
    page: int,
    page_size: int,
    status: str | None = None,
    opportunity_type: str | None = None,
) -> OpportunityListResponse:
    count_stmt = select(func.count(Opportunity.id))
    data_stmt = select(Opportunity).options(joinedload(Opportunity.entity), joinedload(Opportunity.theme)).order_by(
        func.coalesce(Opportunity.priority_score, 0).desc(), Opportunity.created_at.desc()
    )
    if status:
        count_stmt = count_stmt.where(Opportunity.status == status)
        data_stmt = data_stmt.where(Opportunity.status == status)
    if opportunity_type:
        count_stmt = count_stmt.where(Opportunity.opportunity_type == opportunity_type)
        data_stmt = data_stmt.where(Opportunity.opportunity_type == opportunity_type)
    total = session.scalar(count_stmt) or 0
    opportunities = session.scalars(_paginate_stmt(data_stmt, page, page_size)).all()

    return OpportunityListResponse(
        items=[
            OpportunityListItem(
                id=str(opportunity.id),
                title=opportunity.title,
                opportunity_type=opportunity.opportunity_type,
                rationale=opportunity.rationale,
                risks=opportunity.risks,
                integration_notes=opportunity.integration_notes,
                priority_score=opportunity.priority_score,
                status=opportunity.status,
                entity=_entity_ref(opportunity.entity) if opportunity.entity else None,
                theme=_theme_ref(opportunity.theme) if opportunity.theme else None,
            )
            for opportunity in opportunities
        ],
        meta=PaginationMeta(page=page, page_size=page_size, total=total),
    )


def search_all(session: Session, *, query: str, limit: int = 10) -> SearchResponse:
    pattern = f"%{query.strip().lower()}%"
    event_rows = session.scalars(
        select(Event)
        .outerjoin(EventScore, EventScore.event_id == Event.id)
        .where(
            or_(
                func.lower(Event.title).like(pattern),
                func.lower(func.coalesce(Event.summary, "")).like(pattern),
                func.lower(func.coalesce(Event.why_it_matters, "")).like(pattern),
            )
        )
        .options(joinedload(Event.score), joinedload(Event.source_document))
        .order_by(func.coalesce(EventScore.radar_score, 0).desc(), Event.occurred_at.desc())
        .limit(limit)
    ).unique().all()

    entity_rows = session.scalars(
        select(Entity)
        .outerjoin(EntityScore, EntityScore.entity_id == Entity.id)
        .where(
            or_(
                func.lower(Entity.canonical_name).like(pattern),
                func.lower(func.coalesce(Entity.description, "")).like(pattern),
            )
        )
        .options(joinedload(Entity.score))
        .order_by(func.coalesce(EntityScore.entity_priority_score, 0).desc(), Entity.canonical_name.asc())
        .limit(limit)
    ).unique().all()

    document_rows = session.scalars(
        select(SourceDocument)
        .where(
            or_(
                func.lower(SourceDocument.title).like(pattern),
                func.lower(func.coalesce(SourceDocument.normalized_text, "")).like(pattern),
                func.lower(func.coalesce(SourceDocument.raw_text, "")).like(pattern),
            )
        )
        .order_by(SourceDocument.published_at.desc(), SourceDocument.detected_at.desc())
        .limit(limit)
    ).all()

    return SearchResponse(
        query=query,
        events=[
            SearchResultItem(
                result_type="event",
                id=str(event.id),
                title=event.title,
                subtitle=event.event_type.replace("_", " "),
                snippet=event.summary or event.why_it_matters,
                href=f"/events/{event.id}",
                score=event.score.radar_score if event.score else None,
                source_type=event.source_document.source_type if event.source_document else None,
            )
            for event in event_rows
        ],
        entities=[
            SearchResultItem(
                result_type="entity",
                id=str(entity.id),
                title=entity.canonical_name,
                subtitle=entity.entity_type,
                snippet=entity.description,
                href=f"/entities/{entity.slug}",
                score=entity.score.entity_priority_score if entity.score else None,
            )
            for entity in entity_rows
        ],
        documents=[
            SearchResultItem(
                result_type="document",
                id=str(document.id),
                title=document.title,
                subtitle=document.source_type,
                snippet=document.normalized_text or document.raw_text,
                href=document.url,
                score=None,
                source_type=document.source_type,
            )
            for document in document_rows
        ],
    )


def list_watchlists(session: Session, *, page: int, page_size: int) -> WatchlistListResponse:
    count_stmt = select(func.count(Watchlist.id))
    data_stmt = (
        select(Watchlist)
        .options(
            selectinload(Watchlist.items).joinedload(WatchlistItem.entity),
            selectinload(Watchlist.items).joinedload(WatchlistItem.theme),
        )
        .order_by(Watchlist.created_at.desc())
    )
    total = session.scalar(count_stmt) or 0
    watchlists = session.scalars(_paginate_stmt(data_stmt, page, page_size)).unique().all()
    return WatchlistListResponse(items=[_watchlist_to_model(watchlist) for watchlist in watchlists], meta=PaginationMeta(page=page, page_size=page_size, total=total))


def create_watchlist_record(session: Session, *, name: str, description: str | None, watchlist_type: str) -> WatchlistModel:
    watchlist = Watchlist(name=name, description=description, watchlist_type=watchlist_type)
    session.add(watchlist)
    session.commit()
    session.refresh(watchlist)
    loaded = _load_watchlist_with_items(session, watchlist.id)
    return _watchlist_to_model(loaded or watchlist)


def add_watchlist_item_record(
    session: Session,
    *,
    watchlist_id: str,
    entity_slug: str | None,
    theme_slug: str | None,
    notes: str | None,
) -> WatchlistModel | None:
    watchlist = _load_watchlist_with_items(session, _coerce_uuid(watchlist_id, "watchlist_id"))
    if watchlist is None:
        return None

    entity = session.scalar(select(Entity).where(Entity.slug == entity_slug)) if entity_slug else None
    theme = session.scalar(select(Theme).where(Theme.slug == theme_slug)) if theme_slug else None
    if entity_slug and entity is None:
        return None
    if theme_slug and theme is None:
        return None

    existing = session.scalar(
        select(WatchlistItem).where(
            WatchlistItem.watchlist_id == watchlist.id,
            WatchlistItem.entity_id == (entity.id if entity else None),
            WatchlistItem.theme_id == (theme.id if theme else None),
        )
    )
    if existing is None:
        session.add(
            WatchlistItem(
                watchlist_id=watchlist.id,
                entity_id=entity.id if entity else None,
                theme_id=theme.id if theme else None,
                notes=notes,
            )
        )
        session.commit()
        reloaded = _load_watchlist_with_items(session, watchlist.id)
        if reloaded is not None:
            watchlist = reloaded

    return _watchlist_to_model(watchlist)


def _apply_event_filters(count_stmt, data_stmt, *, source_type, event_type, stack_layer, theme_slug, min_score, days):
    if source_type:
        count_stmt = count_stmt.join(SourceDocument, SourceDocument.id == Event.source_document_id).where(SourceDocument.source_type == source_type)
        data_stmt = data_stmt.join(SourceDocument, SourceDocument.id == Event.source_document_id).where(SourceDocument.source_type == source_type)
    if event_type:
        count_stmt = count_stmt.where(Event.event_type == event_type)
        data_stmt = data_stmt.where(Event.event_type == event_type)
    if stack_layer:
        count_stmt = count_stmt.where(Event.stack_layer == stack_layer)
        data_stmt = data_stmt.where(Event.stack_layer == stack_layer)
    if min_score is not None:
        count_stmt = count_stmt.join(EventScore, EventScore.event_id == Event.id).where(EventScore.radar_score >= min_score)
        data_stmt = data_stmt.where(EventScore.radar_score >= min_score)
    if days is not None:
        cutoff = datetime.now(tz=timezone.utc) - timedelta(days=days)
        count_stmt = count_stmt.where(Event.occurred_at >= cutoff)
        data_stmt = data_stmt.where(Event.occurred_at >= cutoff)
    if theme_slug:
        count_stmt = count_stmt.join(EventEntityLink, EventEntityLink.event_id == Event.id).join(EntityThemeLink, EntityThemeLink.entity_id == EventEntityLink.entity_id).join(Theme, Theme.id == EntityThemeLink.theme_id).where(Theme.slug == theme_slug)
        data_stmt = data_stmt.join(EventEntityLink, EventEntityLink.event_id == Event.id).join(EntityThemeLink, EntityThemeLink.entity_id == EventEntityLink.entity_id).join(Theme, Theme.id == EntityThemeLink.theme_id).where(Theme.slug == theme_slug)
    return count_stmt, data_stmt


def _apply_entity_filters(count_stmt, data_stmt, *, entity_type, theme_slug, min_priority, is_public):
    if entity_type:
        count_stmt = count_stmt.where(Entity.entity_type == entity_type)
        data_stmt = data_stmt.where(Entity.entity_type == entity_type)
    if theme_slug:
        count_stmt = count_stmt.join(EntityThemeLink, EntityThemeLink.entity_id == Entity.id).join(Theme, Theme.id == EntityThemeLink.theme_id).where(Theme.slug == theme_slug)
        data_stmt = data_stmt.join(EntityThemeLink, EntityThemeLink.entity_id == Entity.id).join(Theme, Theme.id == EntityThemeLink.theme_id).where(Theme.slug == theme_slug)
    if min_priority is not None:
        count_stmt = count_stmt.join(EntityScore, EntityScore.entity_id == Entity.id).where(EntityScore.entity_priority_score >= min_priority)
        data_stmt = data_stmt.where(EntityScore.entity_priority_score >= min_priority)
    if is_public is not None:
        allowed = ["public_company"] if is_public else ["company", "product", "repository", "paper", "person", "theme"]
        count_stmt = count_stmt.where(Entity.entity_type.in_(allowed))
        data_stmt = data_stmt.where(Entity.entity_type.in_(allowed))
    return count_stmt, data_stmt


def _order_events(stmt, sort: str):
    if sort == "occurred_at":
        return stmt.order_by(Event.occurred_at.desc())
    if sort == "confidence":
        return stmt.order_by(Event.confidence.desc(), Event.occurred_at.desc())
    return stmt.order_by(func.coalesce(EventScore.radar_score, 0).desc(), Event.occurred_at.desc())


def _order_entities(stmt, sort: str):
    if sort == "momentum":
        return stmt.order_by(func.coalesce(EntityScore.momentum_score, 0).desc(), Entity.canonical_name.asc())
    if sort == "name":
        return stmt.order_by(Entity.canonical_name.asc())
    return stmt.order_by(func.coalesce(EntityScore.entity_priority_score, 0).desc(), Entity.canonical_name.asc())


def _paginate_stmt(stmt, page: int, page_size: int):
    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)
    return stmt.limit(page_size).offset((page - 1) * page_size)


def _event_to_list_item(event: Event) -> EventListItem:
    return EventListItem(
        id=str(event.id),
        title=event.title,
        summary=event.summary,
        event_type=event.event_type,
        occurred_at=event.occurred_at,
        detected_at=event.detected_at,
        stack_layer=event.stack_layer,
        confidence=event.confidence,
        radar_score=event.score.radar_score if event.score else None,
        source=_source_ref(event.source_document),
        linked_entities=[_entity_ref(link.entity, confidence=link.confidence) for link in event.entity_links if link.entity is not None],
        themes=_event_theme_refs(event),
    )


def _entity_to_list_item(entity: Entity) -> EntityListItem:
    return EntityListItem(
        id=str(entity.id),
        slug=entity.slug,
        canonical_name=entity.canonical_name,
        entity_type=entity.entity_type,
        website=entity.website,
        description=entity.description,
        themes=[_theme_ref(link.theme, confidence=link.confidence) for link in entity.theme_links if link.theme is not None],
        aliases=[alias.alias for alias in entity.aliases],
        score=_entity_score_model(entity.score),
    )


def _watchlist_to_model(watchlist: Watchlist) -> WatchlistModel:
    return WatchlistModel(
        id=str(watchlist.id),
        name=watchlist.name,
        description=watchlist.description,
        watchlist_type=watchlist.watchlist_type,
        created_at=watchlist.created_at,
        items=[
            WatchlistItemModel(
                id=str(item.id),
                notes=item.notes,
                entity=_entity_ref(item.entity) if item.entity else None,
                theme=_theme_ref(item.theme) if item.theme else None,
            )
            for item in watchlist.items
        ],
    )


def _load_watchlist_with_items(session: Session, watchlist_id: uuid.UUID) -> Watchlist | None:
    return session.scalar(
        select(Watchlist)
        .where(Watchlist.id == watchlist_id)
        .options(
            selectinload(Watchlist.items).joinedload(WatchlistItem.entity),
            selectinload(Watchlist.items).joinedload(WatchlistItem.theme),
        )
    )


def _source_ref(document: SourceDocument | None) -> SourceDocumentRef | None:
    if document is None:
        return None
    return SourceDocumentRef(
        id=str(document.id),
        source_type=document.source_type,
        source_external_id=document.source_external_id,
        title=document.title,
        url=document.url,
        published_at=document.published_at,
    )


def _entity_ref(entity: Entity | None, *, confidence: float | None = None) -> EntityRef | None:
    if entity is None:
        return None
    return EntityRef(
        id=str(entity.id),
        slug=entity.slug,
        canonical_name=entity.canonical_name,
        entity_type=entity.entity_type,
        confidence=confidence,
    )


def _theme_ref(theme: Theme | None, *, confidence: float | None = None) -> ThemeRef | None:
    if theme is None:
        return None
    return ThemeRef(
        id=str(theme.id),
        slug=theme.slug,
        name=theme.name,
        description=theme.description,
        confidence=confidence,
    )


def _event_theme_refs(event: Event) -> list[ThemeRef]:
    theme_refs: dict[str, ThemeRef] = {}
    for entity_link in event.entity_links:
        entity = entity_link.entity
        if entity is None:
            continue
        for theme_link in entity.theme_links:
            theme_ref = _theme_ref(theme_link.theme, confidence=theme_link.confidence)
            if theme_ref is None:
                continue
            existing = theme_refs.get(theme_ref.slug)
            if existing is None or (theme_ref.confidence or 0.0) > (existing.confidence or 0.0):
                theme_refs[theme_ref.slug] = theme_ref
    if theme_refs:
        return sorted(theme_refs.values(), key=lambda theme: theme.name.lower())

    return [
        ThemeRef(
            id=slug,
            slug=slug,
            name=slug.replace("-", " ").title(),
            description=None,
        )
        for slug in (event.metadata_json or {}).get("theme_slugs", [])
    ]


def _coerce_uuid(value: str, field_name: str) -> uuid.UUID:
    try:
        return uuid.UUID(value)
    except ValueError as exc:
        raise ValueError(f"Invalid {field_name}.") from exc


def _event_score_model(score: EventScore | None) -> EventScoreModel | None:
    if score is None:
        return None
    return EventScoreModel(
        novelty_score=score.novelty_score,
        momentum_score=score.momentum_score,
        strategic_importance_score=score.strategic_importance_score,
        aws_relevance_score=score.aws_relevance_score,
        corpdev_score=score.corpdev_score,
        confidence_score=score.confidence_score,
        radar_score=score.radar_score,
        scoring_version=score.scoring_version,
        rationale_json=score.rationale_json or {},
    )


def _entity_score_model(score: EntityScore | None) -> EntityScoreModel | None:
    if score is None:
        return None
    return EntityScoreModel(
        momentum_score=score.momentum_score,
        aws_relevance_score=score.aws_relevance_score,
        corpdev_interest_score=score.corpdev_interest_score,
        entity_priority_score=score.entity_priority_score,
        scoring_version=score.scoring_version,
        rationale_json=score.rationale_json or {},
    )
