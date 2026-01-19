from datetime import datetime, date
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum


class MemoStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class Signal(str, Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"


class TimeHorizon(str, Enum):
    SHORT = "short"
    MEDIUM = "medium"
    LONG = "long"


class InvestmentStatus(str, Enum):
    ACTIVE = "active"
    CLOSED = "closed"


# ----- Memo Schemas -----

class MemoBase(BaseModel):
    """Base schema for memo data"""
    ticker: str = Field(..., min_length=1, max_length=10)
    analyst: str = Field(..., min_length=1, max_length=50)
    signal: Signal
    conviction: int = Field(..., ge=0, le=100)
    thesis: str = Field(..., min_length=1)
    bull_case: List[str] = Field(..., min_length=1, max_length=5)
    bear_case: List[str] = Field(..., min_length=1, max_length=5)
    metrics: Dict[str, Any]
    current_price: float = Field(..., gt=0)
    target_price: float = Field(..., gt=0)
    time_horizon: TimeHorizon


class MemoCreateRequest(MemoBase):
    """Request to create a new memo"""
    generated_at: datetime


class MemoResponse(MemoBase):
    """Complete memo response"""
    id: str
    status: MemoStatus
    generated_at: datetime
    reviewed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class MemoSummaryResponse(BaseModel):
    """Lightweight memo response for listing"""
    id: str
    ticker: str
    analyst: str
    signal: Signal
    conviction: int
    current_price: float
    target_price: float
    time_horizon: TimeHorizon
    status: MemoStatus
    generated_at: datetime

    class Config:
        from_attributes = True


class MemoListResponse(BaseModel):
    """Paginated list of memos"""
    items: List[MemoSummaryResponse]
    total: int
    page: int
    page_size: int


# ----- Investment Schemas -----

class InvestmentBase(BaseModel):
    """Base schema for investment data"""
    ticker: str = Field(..., min_length=1, max_length=10)
    analyst: str = Field(..., min_length=1, max_length=50)
    signal: Signal
    entry_price: float = Field(..., gt=0)
    entry_date: date


class InvestmentCreateRequest(InvestmentBase):
    """Request to create a new investment"""
    memo_id: str


class InvestmentResponse(InvestmentBase):
    """Complete investment response"""
    id: str
    memo_id: str
    status: InvestmentStatus
    exit_price: Optional[float] = None
    exit_date: Optional[date] = None
    created_at: datetime

    class Config:
        from_attributes = True


class InvestmentWithMemoResponse(InvestmentResponse):
    """Investment response with linked memo"""
    memo: MemoResponse


class InvestmentListResponse(BaseModel):
    """Paginated list of investments"""
    items: List[InvestmentResponse]
    total: int
    page: int
    page_size: int


class CloseInvestmentRequest(BaseModel):
    """Request to close an investment"""
    exit_price: float = Field(..., gt=0)
    exit_date: date


# ----- Analyst Stats Schemas -----

class AnalystStatsResponse(BaseModel):
    """Analyst performance statistics"""
    analyst: str
    total_memos: int
    approved_count: int
    win_count: int
    total_return: float
    win_rate: float  # Computed field: win_count / approved_count if approved_count > 0 else 0
    approval_rate: float  # Computed field: approved_count / total_memos if total_memos > 0 else 0
    updated_at: datetime

    class Config:
        from_attributes = True


class LeaderboardResponse(BaseModel):
    """Analyst leaderboard"""
    analysts: List[AnalystStatsResponse]


# ----- Inbox Approval/Rejection -----

class ApprovalResponse(BaseModel):
    """Response after approving a memo"""
    memo: MemoResponse
    investment: InvestmentResponse
    message: str = "Memo approved and investment created"


class RejectionResponse(BaseModel):
    """Response after rejecting a memo"""
    memo: MemoResponse
    message: str = "Memo rejected"
