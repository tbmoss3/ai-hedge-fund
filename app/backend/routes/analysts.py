from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, Literal

from app.backend.database import get_db
from app.backend.services.analyst_service import AnalystService
from app.backend.models.research_schemas import (
    AnalystStatsResponse,
    LeaderboardResponse,
    ErrorResponse,
)

router = APIRouter(prefix="/analysts", tags=["analysts"])


@router.get(
    "/leaderboard",
    response_model=LeaderboardResponse,
    responses={
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_leaderboard(
    sort_by: Literal["win_rate", "total_return"] = Query(
        "win_rate",
        description="Sort metric: 'win_rate' or 'total_return'",
    ),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of analysts to return"),
    db: Session = Depends(get_db),
):
    """
    Get analyst leaderboard sorted by performance.

    Supports sorting by:
    - win_rate: Percentage of winning investments (win_count / approved_count)
    - total_return: Cumulative return percentage across all closed investments

    Only analysts with at least one approved investment are included.
    """
    try:
        service = AnalystService(db)
        stats_list = service.get_leaderboard(sort_by=sort_by, limit=limit)

        return LeaderboardResponse(
            analysts=[
                AnalystStatsResponse(
                    analyst=s.analyst,
                    total_memos=s.total_memos,
                    approved_count=s.approved_count,
                    win_count=s.win_count,
                    total_return=round(s.total_return, 2),
                    win_rate=round(s.win_rate, 2),
                    approval_rate=round(s.approval_rate, 2),
                    updated_at=s.updated_at,
                )
                for s in stats_list
            ]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve leaderboard: {str(e)}")


@router.get(
    "/stats",
    response_model=LeaderboardResponse,
    responses={
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_all_analyst_stats(db: Session = Depends(get_db)):
    """
    Get stats for all analysts.

    Returns all analysts regardless of whether they have approved investments.
    """
    try:
        service = AnalystService(db)
        stats_list = service.get_all_analyst_stats()

        return LeaderboardResponse(
            analysts=[
                AnalystStatsResponse(
                    analyst=s.analyst,
                    total_memos=s.total_memos,
                    approved_count=s.approved_count,
                    win_count=s.win_count,
                    total_return=round(s.total_return, 2),
                    win_rate=round(s.win_rate, 2),
                    approval_rate=round(s.approval_rate, 2),
                    updated_at=s.updated_at,
                )
                for s in stats_list
            ]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve analyst stats: {str(e)}")


@router.get(
    "/{analyst}",
    response_model=AnalystStatsResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Analyst not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_analyst_stats(analyst: str, db: Session = Depends(get_db)):
    """
    Get stats for a specific analyst.

    Returns the analyst's memo counts, approval rate, win rate, and total return.
    """
    try:
        service = AnalystService(db)
        stats = service.get_analyst_stats(analyst)

        if not stats:
            raise HTTPException(status_code=404, detail="Analyst not found")

        return AnalystStatsResponse(
            analyst=stats.analyst,
            total_memos=stats.total_memos,
            approved_count=stats.approved_count,
            win_count=stats.win_count,
            total_return=round(stats.total_return, 2),
            win_rate=round(stats.win_rate, 2),
            approval_rate=round(stats.approval_rate, 2),
            updated_at=stats.updated_at,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve analyst stats: {str(e)}")


@router.post(
    "/{analyst}/refresh",
    response_model=AnalystStatsResponse,
    responses={
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def refresh_analyst_stats(analyst: str, db: Session = Depends(get_db)):
    """
    Recalculate stats for an analyst from scratch.

    Useful for reconciliation if stats become out of sync with
    the actual memo and investment data.
    """
    try:
        service = AnalystService(db)
        stats = service.refresh_analyst_stats(analyst)

        return AnalystStatsResponse(
            analyst=stats.analyst,
            total_memos=stats.total_memos,
            approved_count=stats.approved_count,
            win_count=stats.win_count,
            total_return=round(stats.total_return, 2),
            win_rate=round(stats.win_rate, 2),
            approval_rate=round(stats.approval_rate, 2),
            updated_at=stats.updated_at,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to refresh analyst stats: {str(e)}")
