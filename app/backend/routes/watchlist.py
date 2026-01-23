# Watchlist Routes - API endpoints for watchlist management
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.backend.database import get_db
from app.backend.services.watchlist_service import WatchlistService
from app.backend.services.scheduler_service import run_manual_scan, get_next_run_time


# Pydantic schemas for request/response
class WatchlistResponse(BaseModel):
    id: int
    name: str
    tickers: List[str]
    created_at: datetime
    updated_at: datetime
    last_scan_at: Optional[datetime]

    class Config:
        from_attributes = True


class TickersRequest(BaseModel):
    tickers: List[str]


class TickersResponse(BaseModel):
    tickers: List[str]
    count: int


router = APIRouter(prefix="/watchlist", tags=["watchlist"])


@router.get("/", response_model=WatchlistResponse)
async def get_watchlist(db: Session = Depends(get_db)):
    """Get the default watchlist"""
    try:
        service = WatchlistService(db)
        watchlist = service.get_or_create_default()
        return WatchlistResponse.model_validate(watchlist)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get watchlist: {str(e)}")


@router.get("/tickers", response_model=TickersResponse)
async def get_tickers(db: Session = Depends(get_db)):
    """Get all tickers from the default watchlist"""
    try:
        service = WatchlistService(db)
        tickers = service.get_tickers()
        return TickersResponse(tickers=tickers, count=len(tickers))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get tickers: {str(e)}")


@router.post("/tickers", response_model=WatchlistResponse)
async def add_tickers(request: TickersRequest, db: Session = Depends(get_db)):
    """Add tickers to the default watchlist"""
    try:
        if not request.tickers:
            raise HTTPException(status_code=400, detail="No tickers provided")

        service = WatchlistService(db)
        watchlist = service.add_tickers(request.tickers)
        return WatchlistResponse.model_validate(watchlist)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add tickers: {str(e)}")


@router.delete("/tickers", response_model=WatchlistResponse)
async def remove_tickers(request: TickersRequest, db: Session = Depends(get_db)):
    """Remove tickers from the default watchlist"""
    try:
        if not request.tickers:
            raise HTTPException(status_code=400, detail="No tickers provided")

        service = WatchlistService(db)
        watchlist = service.remove_tickers(request.tickers)
        if not watchlist:
            raise HTTPException(status_code=404, detail="Watchlist not found")
        return WatchlistResponse.model_validate(watchlist)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to remove tickers: {str(e)}")


@router.put("/tickers", response_model=WatchlistResponse)
async def set_tickers(request: TickersRequest, db: Session = Depends(get_db)):
    """Replace all tickers in the default watchlist"""
    try:
        service = WatchlistService(db)
        watchlist = service.set_tickers(request.tickers)
        return WatchlistResponse.model_validate(watchlist)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to set tickers: {str(e)}")


@router.delete("/clear", response_model=WatchlistResponse)
async def clear_watchlist(db: Session = Depends(get_db)):
    """Clear all tickers from the default watchlist"""
    try:
        service = WatchlistService(db)
        watchlist = service.clear_watchlist()
        if not watchlist:
            raise HTTPException(status_code=404, detail="Watchlist not found")
        return WatchlistResponse.model_validate(watchlist)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear watchlist: {str(e)}")


class ScanResponse(BaseModel):
    status: str
    tickers_scanned: int
    memos_generated: int
    errors: List[str]


class ScheduleInfoResponse(BaseModel):
    next_scan: Optional[datetime]
    schedule: str


@router.post("/scan", response_model=ScanResponse)
async def trigger_scan(db: Session = Depends(get_db)):
    """
    Trigger a manual scan of the watchlist.

    This runs the AI analysts on all tickers in the watchlist and
    submits high-conviction memos to the inbox.
    """
    try:
        service = WatchlistService(db)
        tickers = service.get_tickers()

        if not tickers:
            raise HTTPException(status_code=400, detail="Watchlist is empty. Add tickers before scanning.")

        result = await run_manual_scan(tickers)
        return ScanResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scan failed: {str(e)}")


@router.get("/schedule", response_model=ScheduleInfoResponse)
async def get_schedule_info():
    """Get information about the scheduled scans"""
    next_run = get_next_run_time()
    return ScheduleInfoResponse(
        next_scan=next_run,
        schedule="Quarterly (Jan 15, Apr 15, Jul 15, Oct 15) at 6:00 AM UTC"
    )
