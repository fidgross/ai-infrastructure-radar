from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.jobs.ingest import run_source_ingest
from app.jobs.score import run_scoring_pipeline
from app.schemas.api import (
    AddWatchlistItemRequest,
    CreateWatchlistRequest,
    IngestRunRequest,
    IngestRunResponse,
    OperationsStatusResponse,
    ScoreRecomputeRequest,
    ScoreRecomputeResponse,
    WatchlistModel,
)
from app.services.operations_status import get_operations_status
from app.services.read_api import add_watchlist_item_record, create_watchlist_record

router = APIRouter(prefix="/api", tags=["operations"])


@router.post("/watchlists", response_model=WatchlistModel)
def create_watchlist(payload: CreateWatchlistRequest, session: Session = Depends(get_db_session)) -> WatchlistModel:
    return create_watchlist_record(
        session,
        name=payload.name,
        description=payload.description,
        watchlist_type=payload.watchlist_type,
    )


@router.post("/watchlists/{watchlist_id}/items", response_model=WatchlistModel)
def add_watchlist_item(
    watchlist_id: str,
    payload: AddWatchlistItemRequest,
    session: Session = Depends(get_db_session),
) -> WatchlistModel:
    try:
        watchlist = add_watchlist_item_record(
            session,
            watchlist_id=watchlist_id,
            entity_slug=payload.entity_slug,
            theme_slug=payload.theme_slug,
            notes=payload.notes,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if watchlist is None:
        raise HTTPException(status_code=404, detail="Watchlist or target not found")
    return watchlist


@router.post("/ingest/run/{source}", response_model=IngestRunResponse)
def trigger_ingest(source: str, payload: IngestRunRequest) -> IngestRunResponse:
    try:
        summary = run_source_ingest(
            source_type=source,
            fixture_path=payload.fixture_path,
            query=payload.query,
            org=payload.org,
            repo=payload.repo,
            ticker=payload.ticker,
            cik=payload.cik,
            limit=payload.limit,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return IngestRunResponse(**summary.__dict__)


@router.post("/score/recompute", response_model=ScoreRecomputeResponse)
def recompute_scores(payload: ScoreRecomputeRequest) -> ScoreRecomputeResponse:
    return ScoreRecomputeResponse(**run_scoring_pipeline(reprocess=payload.reprocess, limit=payload.limit))


@router.get("/operations/status", response_model=OperationsStatusResponse)
def operations_status(session: Session = Depends(get_db_session)) -> OperationsStatusResponse:
    return get_operations_status(session)
