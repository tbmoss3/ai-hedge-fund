from typing import List, Optional
from sqlalchemy.orm import Session

from app.backend.repositories.analyst_stats_repository import AnalystStatsRepository
from app.backend.models.analyst_stats import AnalystStats


class AnalystStatsWithRates:
    """Analyst stats with computed win rate and approval rate"""

    def __init__(self, stats: AnalystStats):
        self.analyst = stats.analyst
        self.total_memos = stats.total_memos
        self.approved_count = stats.approved_count
        self.win_count = stats.win_count
        self.total_return = stats.total_return
        self.updated_at = stats.updated_at

        # Compute rates
        self.win_rate = (
            (stats.win_count / stats.approved_count * 100)
            if stats.approved_count > 0
            else 0.0
        )
        self.approval_rate = (
            (stats.approved_count / stats.total_memos * 100)
            if stats.total_memos > 0
            else 0.0
        )


class AnalystService:
    """Service for managing analyst statistics and leaderboards"""

    def __init__(self, db: Session):
        self.db = db
        self.stats_repo = AnalystStatsRepository(db)

    def get_analyst_stats(self, analyst: str) -> Optional[AnalystStatsWithRates]:
        """Get stats for a specific analyst"""
        stats = self.stats_repo.get_stats_by_analyst(analyst)
        if not stats:
            return None
        return AnalystStatsWithRates(stats)

    def get_all_analyst_stats(self) -> List[AnalystStatsWithRates]:
        """Get stats for all analysts"""
        stats_list = self.stats_repo.get_all_stats()
        return [AnalystStatsWithRates(s) for s in stats_list]

    def get_leaderboard(
        self, sort_by: str = "win_rate", limit: int = 10
    ) -> List[AnalystStatsWithRates]:
        """
        Get analyst leaderboard sorted by specified metric.

        Args:
            sort_by: "win_rate" or "total_return"
            limit: Maximum number of analysts to return

        Returns:
            List of analyst stats sorted by the specified metric
        """
        if sort_by == "total_return":
            stats_list = self.stats_repo.get_leaderboard_by_total_return(limit=limit)
            return [AnalystStatsWithRates(s) for s in stats_list]

        # For win_rate, we need to compute and sort in Python
        # since it's a computed field
        stats_list = self.stats_repo.get_leaderboard_by_win_rate(limit=100)
        stats_with_rates = [AnalystStatsWithRates(s) for s in stats_list]

        # Sort by win rate descending
        stats_with_rates.sort(key=lambda x: x.win_rate, reverse=True)

        return stats_with_rates[:limit]

    def get_or_create_stats(self, analyst: str) -> AnalystStatsWithRates:
        """Get or create stats for an analyst"""
        stats = self.stats_repo.get_or_create_stats(analyst)
        return AnalystStatsWithRates(stats)

    def refresh_analyst_stats(self, analyst: str) -> AnalystStatsWithRates:
        """
        Recalculate stats for an analyst from scratch.
        Useful for reconciliation.
        """
        from app.backend.repositories.memo_repository import MemoRepository
        from app.backend.repositories.investment_repository import InvestmentRepository

        memo_repo = MemoRepository(self.db)
        investment_repo = InvestmentRepository(self.db)

        # Count memos
        total_memos = memo_repo.count_memos_by_analyst(analyst)
        approved_count = memo_repo.count_approved_by_analyst(analyst)

        # Calculate win/loss from closed investments
        closed_investments = investment_repo.get_closed_investments_by_analyst(analyst)
        win_count = 0
        total_return = 0.0

        for inv in closed_investments:
            if inv.exit_price is None:
                continue

            if inv.signal == "bullish":
                return_pct = ((inv.exit_price - inv.entry_price) / inv.entry_price) * 100
            else:
                return_pct = ((inv.entry_price - inv.exit_price) / inv.entry_price) * 100

            total_return += return_pct
            if return_pct > 0:
                win_count += 1

        # Update stats
        stats = self.stats_repo.update_stats(
            analyst=analyst,
            total_memos=total_memos,
            approved_count=approved_count,
            win_count=win_count,
            total_return=round(total_return, 2),
        )

        return AnalystStatsWithRates(stats)
