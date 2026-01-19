from typing import List, Optional
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.backend.models.investment import Investment


class InvestmentRepository:
    """Repository for Investment CRUD operations"""

    def __init__(self, db: Session):
        self.db = db

    def create_investment(
        self,
        memo_id: str,
        ticker: str,
        analyst: str,
        signal: str,
        entry_price: float,
        entry_date: date,
    ) -> Investment:
        """Create a new investment"""
        investment = Investment(
            memo_id=memo_id,
            ticker=ticker,
            analyst=analyst,
            signal=signal,
            entry_price=entry_price,
            entry_date=entry_date,
            status="active",
        )
        self.db.add(investment)
        self.db.commit()
        self.db.refresh(investment)
        return investment

    def get_investment_by_id(self, investment_id: str) -> Optional[Investment]:
        """Get an investment by its ID"""
        return self.db.query(Investment).filter(Investment.id == investment_id).first()

    def get_investment_by_memo_id(self, memo_id: str) -> Optional[Investment]:
        """Get an investment by its memo ID"""
        return self.db.query(Investment).filter(Investment.memo_id == memo_id).first()

    def get_all_investments(
        self,
        status: Optional[str] = None,
        analyst: Optional[str] = None,
        ticker: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[List[Investment], int]:
        """Get all investments with optional filtering"""
        query = self.db.query(Investment)

        if status:
            query = query.filter(Investment.status == status)
        if analyst:
            query = query.filter(Investment.analyst == analyst)
        if ticker:
            query = query.filter(Investment.ticker == ticker)

        total = query.count()
        investments = (
            query.order_by(desc(Investment.created_at))
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return investments, total

    def get_active_investments(
        self, page: int = 1, page_size: int = 20
    ) -> tuple[List[Investment], int]:
        """Get all active investments"""
        return self.get_all_investments(status="active", page=page, page_size=page_size)

    def get_closed_investments(
        self, page: int = 1, page_size: int = 20
    ) -> tuple[List[Investment], int]:
        """Get all closed investments"""
        return self.get_all_investments(status="closed", page=page, page_size=page_size)

    def close_investment(
        self, investment_id: str, exit_price: float, exit_date: date
    ) -> Optional[Investment]:
        """Close an investment"""
        investment = self.get_investment_by_id(investment_id)
        if not investment:
            return None
        if investment.status != "active":
            return None

        investment.status = "closed"
        investment.exit_price = exit_price
        investment.exit_date = exit_date
        self.db.commit()
        self.db.refresh(investment)
        return investment

    def get_investments_by_analyst(self, analyst: str) -> List[Investment]:
        """Get all investments for an analyst"""
        return (
            self.db.query(Investment)
            .filter(Investment.analyst == analyst)
            .order_by(desc(Investment.created_at))
            .all()
        )

    def count_closed_investments_by_analyst(self, analyst: str) -> int:
        """Count closed investments for an analyst"""
        return (
            self.db.query(Investment)
            .filter(Investment.analyst == analyst, Investment.status == "closed")
            .count()
        )

    def get_closed_investments_by_analyst(self, analyst: str) -> List[Investment]:
        """Get all closed investments for an analyst"""
        return (
            self.db.query(Investment)
            .filter(Investment.analyst == analyst, Investment.status == "closed")
            .all()
        )
