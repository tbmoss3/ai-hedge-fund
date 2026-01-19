from datetime import datetime, date
from typing import Optional
from sqlalchemy.orm import Session

from app.backend.repositories.memo_repository import MemoRepository
from app.backend.repositories.investment_repository import InvestmentRepository
from app.backend.repositories.analyst_stats_repository import AnalystStatsRepository
from app.backend.models.memo import Memo
from app.backend.models.investment import Investment


class InboxService:
    """Service for managing the research inbox (pending memos)"""

    def __init__(self, db: Session):
        self.db = db
        self.memo_repo = MemoRepository(db)
        self.investment_repo = InvestmentRepository(db)
        self.analyst_stats_repo = AnalystStatsRepository(db)

    def get_pending_memos(
        self,
        analyst: Optional[str] = None,
        signal: Optional[str] = None,
        min_conviction: Optional[int] = None,
        ticker: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Memo], int]:
        """Get pending memos with optional filtering"""
        return self.memo_repo.get_pending_memos(
            analyst=analyst,
            signal=signal,
            min_conviction=min_conviction,
            ticker=ticker,
            page=page,
            page_size=page_size,
        )

    def approve_memo(
        self, memo_id: str, entry_price: Optional[float] = None
    ) -> tuple[Optional[Memo], Optional[Investment]]:
        """
        Approve a memo and create an investment record.

        Args:
            memo_id: The ID of the memo to approve
            entry_price: Optional override for entry price (defaults to memo's current_price)

        Returns:
            Tuple of (approved memo, created investment) or (None, None) if memo not found
        """
        # Get the memo
        memo = self.memo_repo.get_memo_by_id(memo_id)
        if not memo:
            return None, None

        if memo.status != "pending":
            return None, None

        # Use provided entry price or default to memo's current price
        actual_entry_price = entry_price if entry_price is not None else memo.current_price

        # Approve the memo
        approved_memo = self.memo_repo.approve_memo(memo_id)
        if not approved_memo:
            return None, None

        # Create the investment
        investment = self.investment_repo.create_investment(
            memo_id=memo_id,
            ticker=memo.ticker,
            analyst=memo.analyst,
            signal=memo.signal,
            entry_price=actual_entry_price,
            entry_date=date.today(),
        )

        # Update analyst stats
        self.analyst_stats_repo.increment_approved_count(memo.analyst)

        return approved_memo, investment

    def reject_memo(self, memo_id: str) -> Optional[Memo]:
        """
        Reject a memo.

        Args:
            memo_id: The ID of the memo to reject

        Returns:
            The rejected memo or None if not found
        """
        return self.memo_repo.reject_memo(memo_id)

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
        generated_at: Optional[datetime] = None,
    ) -> Memo:
        """
        Create a new memo (typically called by the AI analysts).

        Args:
            ticker: Stock ticker symbol
            analyst: Analyst ID (e.g., "warren_buffett")
            signal: "bullish" or "bearish"
            conviction: 0-100
            thesis: Investment thesis text
            bull_case: List of bull case points
            bear_case: List of bear case points
            metrics: Analyst-specific metrics dict
            current_price: Current stock price
            target_price: Target price
            time_horizon: "short", "medium", or "long"
            generated_at: When the memo was generated (defaults to now)

        Returns:
            The created memo
        """
        if generated_at is None:
            generated_at = datetime.utcnow()

        memo = self.memo_repo.create_memo(
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
        )

        # Update analyst stats
        self.analyst_stats_repo.increment_total_memos(analyst)

        return memo

    def get_memo_by_id(self, memo_id: str) -> Optional[Memo]:
        """Get a memo by its ID"""
        return self.memo_repo.get_memo_by_id(memo_id)
