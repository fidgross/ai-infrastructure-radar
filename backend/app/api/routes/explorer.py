from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.schemas.api import (
    EntityDetail,
    EntityListResponse,
    EventDetail,
    EventListResponse,
    LatestBriefResponse,
    OpportunityListResponse,
    SearchResponse,
    ThemeDetail,
    ThemeListResponse,
    WatchlistListResponse,
)
from app.services.read_api import (
    get_entity_detail,
    get_event_detail,
    get_latest_brief,
    get_theme_detail,
    list_entities,
    list_events,
    list_opportunities,
    list_themes,
    list_watchlists,
    search_all,
)

router = APIRouter(prefix="/api", tags=["explorer"])


@router.get("/events", response_model=EventListResponse)
def events_list(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    source_type: str | None = None,
    event_type: str | None = None,
    stack_layer: str | None = None,
    theme_slug: str | None = None,
    min_score: float | None = Query(default=None, ge=0, le=10),
    days: int | None = Query(default=None, ge=1, le=365),
    sort: str = Query(default="radar_score"),
    session: Session = Depends(get_db_session),
) -> EventListResponse:
    return list_events(
        session,
        page=page,
        page_size=page_size,
        source_type=source_type,
        event_type=event_type,
        stack_layer=stack_layer,
        theme_slug=theme_slug,
        min_score=min_score,
        days=days,
        sort=sort,
    )


@router.get("/events/{event_id}", response_model=EventDetail)
def event_detail(event_id: str, session: Session = Depends(get_db_session)) -> EventDetail:
    try:
        event = get_event_detail(session, event_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@router.get("/entities", response_model=EntityListResponse)
def entities_list(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    entity_type: str | None = None,
    theme_slug: str | None = None,
    min_priority: float | None = Query(default=None, ge=0, le=10),
    is_public: bool | None = None,
    sort: str = Query(default="entity_priority_score"),
    session: Session = Depends(get_db_session),
) -> EntityListResponse:
    return list_entities(
        session,
        page=page,
        page_size=page_size,
        entity_type=entity_type,
        theme_slug=theme_slug,
        min_priority=min_priority,
        is_public=is_public,
        sort=sort,
    )


@router.get("/entities/{slug}", response_model=EntityDetail)
def entity_detail(slug: str, session: Session = Depends(get_db_session)) -> EntityDetail:
    entity = get_entity_detail(session, slug)
    if entity is None:
        raise HTTPException(status_code=404, detail="Entity not found")
    return entity


@router.get("/themes", response_model=ThemeListResponse)
def themes_list(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    sort: str = Query(default="entity_count"),
    session: Session = Depends(get_db_session),
) -> ThemeListResponse:
    return list_themes(session, page=page, page_size=page_size, sort=sort)


@router.get("/themes/{slug}", response_model=ThemeDetail)
def theme_detail(slug: str, session: Session = Depends(get_db_session)) -> ThemeDetail:
    theme = get_theme_detail(session, slug)
    if theme is None:
        raise HTTPException(status_code=404, detail="Theme not found")
    return theme


@router.get("/briefs/latest", response_model=LatestBriefResponse)
def latest_brief(session: Session = Depends(get_db_session)) -> LatestBriefResponse:
    brief = get_latest_brief(session)
    if brief is None:
        raise HTTPException(status_code=404, detail="No daily brief available")
    return brief


@router.get("/opportunities", response_model=OpportunityListResponse)
def opportunities_list(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status: str | None = None,
    opportunity_type: str | None = None,
    session: Session = Depends(get_db_session),
) -> OpportunityListResponse:
    return list_opportunities(session, page=page, page_size=page_size, status=status, opportunity_type=opportunity_type)


@router.get("/search", response_model=SearchResponse)
def search(
    q: str = Query(min_length=1),
    limit: int = Query(default=10, ge=1, le=25),
    session: Session = Depends(get_db_session),
) -> SearchResponse:
    return search_all(session, query=q, limit=limit)


@router.get("/watchlists", response_model=WatchlistListResponse)
def watchlists_list(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    session: Session = Depends(get_db_session),
) -> WatchlistListResponse:
    return list_watchlists(session, page=page, page_size=page_size)
