from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.backend.database import get_db
from app.backend.services.inbox_service import InboxService
from app.backend.models.research_schemas import (
    MemoCreateRequest,
    MemoResponse,
    MemoListResponse,
    ApprovalResponse,
    RejectionResponse,
    InvestmentResponse,
    ErrorResponse,
    Signal,
)

router = APIRouter(prefix="/inbox", tags=["inbox"])


@router.get("/count")
async def get_pending_count(db: Session = Depends(get_db)):
    """Get count of pending memos in inbox"""
    try:
        service = InboxService(db)
        memos, total = service.get_pending_memos(page=1, page_size=1)
        return {"count": total}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get count: {str(e)}")


@router.get(
    "/",
    response_model=MemoListResponse,
    responses={
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def list_pending_memos(
    analyst: Optional[str] = Query(None, description="Filter by analyst ID"),
    signal: Optional[Signal] = Query(None, description="Filter by signal (bullish/bearish)"),
    min_conviction: Optional[int] = Query(None, ge=0, le=100, description="Minimum conviction level"),
    ticker: Optional[str] = Query(None, description="Filter by ticker symbol"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
):
    """
    List pending memos in the inbox.

    Supports filtering by:
    - analyst: The analyst ID (e.g., "warren_buffett")
    - signal: "bullish" or "bearish"
    - min_conviction: Minimum conviction level (0-100)
    - ticker: Stock ticker symbol
    """
    try:
        service = InboxService(db)
        memos, total = service.get_pending_memos(
            analyst=analyst,
            signal=signal.value if signal else None,
            min_conviction=min_conviction,
            ticker=ticker,
            page=page,
            page_size=page_size,
        )

        return MemoListResponse(
            items=[MemoResponse.model_validate(m) for m in memos],
            total=total,
            page=page,
            page_size=page_size,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve pending memos: {str(e)}")


@router.get(
    "/{memo_id}",
    response_model=MemoResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Memo not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_memo(memo_id: str, db: Session = Depends(get_db)):
    """Get a specific memo by ID"""
    try:
        service = InboxService(db)
        memo = service.get_memo_by_id(memo_id)
        if not memo:
            raise HTTPException(status_code=404, detail="Memo not found")
        return MemoResponse.model_validate(memo)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve memo: {str(e)}")


@router.post(
    "/",
    response_model=MemoResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def create_memo(request: MemoCreateRequest, db: Session = Depends(get_db)):
    """
    Create a new memo.

    This endpoint is typically called by the AI analysts to submit
    their investment recommendations for human review.
    """
    try:
        service = InboxService(db)
        memo = service.create_memo(
            ticker=request.ticker,
            analyst=request.analyst,
            signal=request.signal.value,
            conviction=request.conviction,
            thesis=request.thesis,
            bull_case=request.bull_case,
            bear_case=request.bear_case,
            metrics=request.metrics,
            current_price=request.current_price,
            target_price=request.target_price,
            time_horizon=request.time_horizon.value,
            generated_at=request.generated_at,
        )
        return MemoResponse.model_validate(memo)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create memo: {str(e)}")


@router.post(
    "/{memo_id}/approve",
    response_model=ApprovalResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Memo not found"},
        400: {"model": ErrorResponse, "description": "Memo is not pending"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def approve_memo(
    memo_id: str,
    entry_price: Optional[float] = Query(None, gt=0, description="Override entry price"),
    db: Session = Depends(get_db),
):
    """
    Approve a pending memo and create an investment record.

    The investment will be created with:
    - entry_price: Either the provided override or the memo's current_price
    - entry_date: Today's date
    - status: "active"
    """
    try:
        service = InboxService(db)
        memo, investment = service.approve_memo(memo_id, entry_price=entry_price)

        if not memo:
            # Check if memo exists
            existing_memo = service.get_memo_by_id(memo_id)
            if not existing_memo:
                raise HTTPException(status_code=404, detail="Memo not found")
            else:
                raise HTTPException(status_code=400, detail="Memo is not in pending status")

        return ApprovalResponse(
            memo=MemoResponse.model_validate(memo),
            investment=InvestmentResponse.model_validate(investment),
            message="Memo approved and investment created",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to approve memo: {str(e)}")


@router.post(
    "/{memo_id}/reject",
    response_model=RejectionResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Memo not found"},
        400: {"model": ErrorResponse, "description": "Memo is not pending"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def reject_memo(memo_id: str, db: Session = Depends(get_db)):
    """
    Reject a pending memo.

    The memo's status will be set to "rejected" and reviewed_at will be set.
    """
    try:
        service = InboxService(db)
        memo = service.reject_memo(memo_id)

        if not memo:
            # Check if memo exists
            existing_memo = service.get_memo_by_id(memo_id)
            if not existing_memo:
                raise HTTPException(status_code=404, detail="Memo not found")
            else:
                raise HTTPException(status_code=400, detail="Memo is not in pending status")

        return RejectionResponse(
            memo=MemoResponse.model_validate(memo),
            message="Memo rejected",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reject memo: {str(e)}")
