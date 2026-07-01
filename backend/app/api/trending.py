from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas import AnalyzeRequest, RefreshHistoryResponse, RefreshRequest, TrendingResponse, TrendingStatsResponse
from app.services.refresh import analyze_latest, get_refresh_history, get_stats, get_trending_response, refresh_trending

router = APIRouter(prefix="/api/trending", tags=["github-trending"])


@router.get("", response_model=TrendingResponse)
def read_trending(
    since: str | None = Query(default=None, pattern="^(daily|weekly|monthly)$"),
    language: str | None = None,
    run_id: int | None = Query(default=None, ge=1),
    db: Session = Depends(get_db),
) -> TrendingResponse:
    return get_trending_response(db, since=since, language=language, run_id=run_id)


@router.post("/refresh", response_model=TrendingResponse)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)) -> TrendingResponse:
    return refresh_trending(db, since=payload.since, language=payload.language)


@router.post("/analyze", response_model=TrendingResponse)
def analyze(payload: AnalyzeRequest, db: Session = Depends(get_db)) -> TrendingResponse:
    return analyze_latest(db, since=payload.since, language=payload.language)



@router.get("/history", response_model=RefreshHistoryResponse)
def history(limit: int = Query(default=20, ge=1, le=100), db: Session = Depends(get_db)) -> RefreshHistoryResponse:
    return get_refresh_history(db, limit=limit)

@router.get("/stats", response_model=TrendingStatsResponse)
def stats(
    since: str | None = Query(default=None, pattern="^(daily|weekly|monthly)$"),
    language: str | None = None,
    run_id: int | None = Query(default=None, ge=1),
    db: Session = Depends(get_db),
) -> TrendingStatsResponse:
    return get_stats(db, since=since, language=language, run_id=run_id)
