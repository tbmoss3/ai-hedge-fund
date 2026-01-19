from datetime import date
from typing import Optional
from sqlalchemy.orm import Session

from app.backend.repositories.investment_repository import InvestmentRepository
from app.backend.repositories.memo_repository import MemoRepository
from app.backend.repositories.analyst_stats_repository import AnalystStatsRepository
from app.backend.models.investment import Investment
from app.backend.models.memo import Memo


class InvestmentService:
    """Service for managing investments"""

    def __init__(self, db: Session):
        self.db = db
        self.investment_repo = InvestmentRepository(db)
        self.memo_repo = MemoRepository(db)
        self.analyst_stats_repo = AnalystStatsRepository(db)

    def get_all_investments(
        self,
        status: Optional[str] = None,
        analyst: Optional[str] = None,
        ticker: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Investment], int]:
        """Get all investments with optional filtering"""
        return self.investment_repo.get_all_investments(
            status=status,
            analyst=analyst,
            ticker=ticker,
            page=page,
            page_size=page_size,
        )

    def get_investment_by_id(self, investment_id: str) -> Optional[Investment]:
        """Get an investment by its ID"""
        return self.investment_repo.get_investment_by_id(investment_id)

    def get_investment_with_memo(
        self, investment_id: str
    ) -> tuple[Optional[Investment], Optional[Memo]]:
        """Get an investment with its linked memo"""
        investment = self.investment_repo.get_investment_by_id(investment_id)
        if not investment:
            return None, None

        memo = self.memo_repo.get_memo_by_id(investment.memo_id)
        return investment, memo

    def close_investment(
        self, investment_id: str, exit_price: float, exit_date: date
    ) -> Optional[Investment]:
        """
        Close an investment and update analyst stats.

        Args:
            investment_id: The ID of the investment to close
            exit_price: The exit price
            exit_date: The exit date

        Returns:
            The closed investment or None if not found/already closed
        """
        # Get the investment first to calculate return
        investment = self.investment_repo.get_investment_by_id(investment_id)
        if not investment:
            return None

        if investment.status != "active":
            return None

        # Calculate return percentage
        entry_price = investment.entry_price
        signal = investment.signal

        if signal == "bullish":
            # For bullish: profit if exit > entry
            return_pct = ((exit_price - entry_price) / entry_price) * 100
        else:
            # For bearish (short): profit if exit < entry
            return_pct = ((entry_price - exit_price) / entry_price) * 100

        is_win = return_pct > 0

        # Close the investment
        closed_investment = self.investment_repo.close_investment(
            investment_id=investment_id,
            exit_price=exit_price,
            exit_date=exit_date,
        )

        if closed_investment:
            # Update analyst stats
            self.analyst_stats_repo.record_investment_result(
                analyst=investment.analyst,
                is_win=is_win,
                return_pct=return_pct,
            )

        return closed_investment

    def get_active_investments(
        self, page: int = 1, page_size: int = 20
    ) -> tuple[list[Investment], int]:
        """Get all active investments"""
        return self.investment_repo.get_active_investments(page=page, page_size=page_size)

    def get_closed_investments(
        self, page: int = 1, page_size: int = 20
    ) -> tuple[list[Investment], int]:
        """Get all closed investments"""
        return self.investment_repo.get_closed_investments(page=page, page_size=page_size)

    def calculate_investment_return(self, investment: Investment, current_price: float) -> dict:
        """
        Calculate current return for an investment.

        Args:
            investment: The investment
            current_price: Current market price

        Returns:
            Dict with return_pct and is_winning
        """
        entry_price = investment.entry_price
        signal = investment.signal

        if signal == "bullish":
            return_pct = ((current_price - entry_price) / entry_price) * 100
        else:
            return_pct = ((entry_price - current_price) / entry_price) * 100

        return {
            "return_pct": round(return_pct, 2),
            "is_winning": return_pct > 0,
        }
