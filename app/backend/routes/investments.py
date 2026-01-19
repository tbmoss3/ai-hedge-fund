from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.backend.database import get_db
from app.backend.services.investment_service import InvestmentService
from app.backend.models.research_schemas import (
    InvestmentResponse,
    InvestmentWithMemoResponse,
    InvestmentListResponse,
    CloseInvestmentRequest,
    MemoResponse,
    ErrorResponse,
    InvestmentStatus,
)

router = APIRouter(prefix="/investments", tags=["investments"])


@router.get(
    "/",
    response_model=InvestmentListResponse,
    responses={
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def list_investments(
    status: Optional[InvestmentStatus] = Query(None, description="Filter by status (active/closed)"),
    analyst: Optional[str] = Query(None, description="Filter by analyst ID"),
    ticker: Optional[str] = Query(None, description="Filter by ticker symbol"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
):
    """
    List all investments with optional filtering.

    Supports filtering by:
    - status: "active" or "closed"
    - analyst: The analyst ID (e.g., "warren_buffett")
    - ticker: Stock ticker symbol
    """
    try:
        service = InvestmentService(db)
        investments, total = service.get_all_investments(
            status=status.value if status else None,
            analyst=analyst,
            ticker=ticker,
            page=page,
            page_size=page_size,
        )

        return InvestmentListResponse(
            items=[InvestmentResponse.model_validate(inv) for inv in investments],
            total=total,
            page=page,
            page_size=page_size,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve investments: {str(e)}")


@router.get(
    "/{investment_id}",
    response_model=InvestmentWithMemoResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Investment not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_investment(investment_id: str, db: Session = Depends(get_db)):
    """
    Get a single investment with its linked memo.

    Returns the investment details along with the full memo
    that was approved to create this investment.
    """
    try:
        service = InvestmentService(db)
        investment, memo = service.get_investment_with_memo(investment_id)

        if not investment:
            raise HTTPException(status_code=404, detail="Investment not found")

        return InvestmentWithMemoResponse(
            id=investment.id,
            memo_id=investment.memo_id,
            ticker=investment.ticker,
            analyst=investment.analyst,
            signal=investment.signal,
            entry_price=investment.entry_price,
            entry_date=investment.entry_date,
            status=investment.status,
            exit_price=investment.exit_price,
            exit_date=investment.exit_date,
            created_at=investment.created_at,
            memo=MemoResponse.model_validate(memo) if memo else None,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve investment: {str(e)}")


@router.patch(
    "/{investment_id}/close",
    response_model=InvestmentResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Investment not found"},
        400: {"model": ErrorResponse, "description": "Investment is not active"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def close_investment(
    investment_id: str,
    request: CloseInvestmentRequest,
    db: Session = Depends(get_db),
):
    """
    Close an active investment.

    Sets the exit_price, exit_date, and status to "closed".
    Also updates the analyst's stats with win/loss and return percentage.

    For bullish investments: profit = (exit_price - entry_price) / entry_price
    For bearish investments: profit = (entry_price - exit_price) / entry_price
    """
    try:
        service = InvestmentService(db)
        investment = service.close_investment(
            investment_id=investment_id,
            exit_price=request.exit_price,
            exit_date=request.exit_date,
        )

        if not investment:
            # Check if investment exists
            existing = service.get_investment_by_id(investment_id)
            if not existing:
                raise HTTPException(status_code=404, detail="Investment not found")
            else:
                raise HTTPException(status_code=400, detail="Investment is not in active status")

        return InvestmentResponse.model_validate(investment)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to close investment: {str(e)}")


@router.get(
    "/active/list",
    response_model=InvestmentListResponse,
    responses={
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def list_active_investments(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
):
    """
    List all active investments.

    Convenience endpoint equivalent to GET /investments?status=active
    """
    try:
        service = InvestmentService(db)
        investments, total = service.get_active_investments(page=page, page_size=page_size)

        return InvestmentListResponse(
            items=[InvestmentResponse.model_validate(inv) for inv in investments],
            total=total,
            page=page,
            page_size=page_size,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve active investments: {str(e)}")


@router.get(
    "/closed/list",
    response_model=InvestmentListResponse,
    responses={
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def list_closed_investments(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
):
    """
    List all closed investments.

    Convenience endpoint equivalent to GET /investments?status=closed
    """
    try:
        service = InvestmentService(db)
        investments, total = service.get_closed_investments(page=page, page_size=page_size)

        return InvestmentListResponse(
            items=[InvestmentResponse.model_validate(inv) for inv in investments],
            total=total,
            page=page,
            page_size=page_size,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve closed investments: {str(e)}")
