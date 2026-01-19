from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.backend.models.analyst_stats import AnalystStats


class AnalystStatsRepository:
    """Repository for AnalystStats CRUD operations"""

    def __init__(self, db: Session):
        self.db = db

    def get_or_create_stats(self, analyst: str) -> AnalystStats:
        """Get analyst stats or create if not exists"""
        stats = self.db.query(AnalystStats).filter(AnalystStats.analyst == analyst).first()
        if not stats:
            stats = AnalystStats(
                analyst=analyst,
                total_memos=0,
                approved_count=0,
                win_count=0,
                total_return=0.0,
            )
            self.db.add(stats)
            self.db.commit()
            self.db.refresh(stats)
        return stats

    def get_stats_by_analyst(self, analyst: str) -> Optional[AnalystStats]:
        """Get stats for a specific analyst"""
        return self.db.query(AnalystStats).filter(AnalystStats.analyst == analyst).first()

    def get_all_stats(self) -> List[AnalystStats]:
        """Get stats for all analysts"""
        return self.db.query(AnalystStats).all()

    def get_leaderboard_by_win_rate(self, limit: int = 10) -> List[AnalystStats]:
        """Get analyst leaderboard sorted by win rate (computed at service level)"""
        return self.db.query(AnalystStats).filter(AnalystStats.approved_count > 0).all()

    def get_leaderboard_by_total_return(self, limit: int = 10) -> List[AnalystStats]:
        """Get analyst leaderboard sorted by total return"""
        return (
            self.db.query(AnalystStats)
            .filter(AnalystStats.approved_count > 0)
            .order_by(desc(AnalystStats.total_return))
            .limit(limit)
            .all()
        )

    def increment_total_memos(self, analyst: str) -> AnalystStats:
        """Increment total memos count for an analyst"""
        stats = self.get_or_create_stats(analyst)
        stats.total_memos += 1
        self.db.commit()
        self.db.refresh(stats)
        return stats

    def increment_approved_count(self, analyst: str) -> AnalystStats:
        """Increment approved count for an analyst"""
        stats = self.get_or_create_stats(analyst)
        stats.approved_count += 1
        self.db.commit()
        self.db.refresh(stats)
        return stats

    def record_investment_result(
        self, analyst: str, is_win: bool, return_pct: float
    ) -> AnalystStats:
        """Record the result of a closed investment"""
        stats = self.get_or_create_stats(analyst)
        if is_win:
            stats.win_count += 1
        stats.total_return += return_pct
        self.db.commit()
        self.db.refresh(stats)
        return stats

    def update_stats(
        self,
        analyst: str,
        total_memos: Optional[int] = None,
        approved_count: Optional[int] = None,
        win_count: Optional[int] = None,
        total_return: Optional[float] = None,
    ) -> Optional[AnalystStats]:
        """Update stats for an analyst"""
        stats = self.get_or_create_stats(analyst)

        if total_memos is not None:
            stats.total_memos = total_memos
        if approved_count is not None:
            stats.approved_count = approved_count
        if win_count is not None:
            stats.win_count = win_count
        if total_return is not None:
            stats.total_return = total_return

        self.db.commit()
        self.db.refresh(stats)
        return stats
