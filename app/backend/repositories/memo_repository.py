from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.backend.models.memo import Memo


class MemoRepository:
    """Repository for Memo CRUD operations"""

    def __init__(self, db: Session):
        self.db = db

    def create_memo(
        self,
        ticker: str,
        analyst: str,
        signal: str,
        conviction: int,
        thesis: str,
        bull_case: list,
        bear_case: list,
        metrics: dict,
        current_price: float,
        target_price: float,
        time_horizon: str,
        generated_at: datetime,
    ) -> Memo:
        """Create a new memo"""
        memo = Memo(
            ticker=ticker,
            analyst=analyst,
            signal=signal,
            conviction=conviction,
            thesis=thesis,
            bull_case=bull_case,
            bear_case=bear_case,
            metrics=metrics,
            current_price=current_price,
            target_price=target_price,
            time_horizon=time_horizon,
            generated_at=generated_at,
            status="pending",
        )
        self.db.add(memo)
        self.db.commit()
        self.db.refresh(memo)
        return memo

    def get_memo_by_id(self, memo_id: str) -> Optional[Memo]:
        """Get a memo by its ID"""
        return self.db.query(Memo).filter(Memo.id == memo_id).first()

    def get_pending_memos(
        self,
        analyst: Optional[str] = None,
        signal: Optional[str] = None,
        min_conviction: Optional[int] = None,
        ticker: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[List[Memo], int]:
        """Get pending memos with optional filtering"""
        query = self.db.query(Memo).filter(Memo.status == "pending")

        if analyst:
            query = query.filter(Memo.analyst == analyst)
        if signal:
            query = query.filter(Memo.signal == signal)
        if min_conviction is not None:
            query = query.filter(Memo.conviction >= min_conviction)
        if ticker:
            query = query.filter(Memo.ticker == ticker)

        total = query.count()
        memos = (
            query.order_by(desc(Memo.generated_at))
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return memos, total

    def get_memos_by_status(
        self, status: str, page: int = 1, page_size: int = 20
    ) -> tuple[List[Memo], int]:
        """Get memos by status"""
        query = self.db.query(Memo).filter(Memo.status == status)
        total = query.count()
        memos = (
            query.order_by(desc(Memo.generated_at))
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return memos, total

    def approve_memo(self, memo_id: str) -> Optional[Memo]:
        """Approve a memo"""
        memo = self.get_memo_by_id(memo_id)
        if not memo:
            return None
        if memo.status != "pending":
            return None

        memo.status = "approved"
        memo.reviewed_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(memo)
        return memo

    def reject_memo(self, memo_id: str) -> Optional[Memo]:
        """Reject a memo"""
        memo = self.get_memo_by_id(memo_id)
        if not memo:
            return None
        if memo.status != "pending":
            return None

        memo.status = "rejected"
        memo.reviewed_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(memo)
        return memo

    def get_all_memos(
        self, page: int = 1, page_size: int = 20
    ) -> tuple[List[Memo], int]:
        """Get all memos"""
        query = self.db.query(Memo)
        total = query.count()
        memos = (
            query.order_by(desc(Memo.generated_at))
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return memos, total

    def count_memos_by_analyst(self, analyst: str) -> int:
        """Count total memos for an analyst"""
        return self.db.query(Memo).filter(Memo.analyst == analyst).count()

    def count_approved_by_analyst(self, analyst: str) -> int:
        """Count approved memos for an analyst"""
        return (
            self.db.query(Memo)
            .filter(Memo.analyst == analyst, Memo.status == "approved")
            .count()
        )
