# Watchlist Service - Business logic layer
from typing import List, Optional
from sqlalchemy.orm import Session

from app.backend.repositories.watchlist_repository import WatchlistRepository
from app.backend.models.watchlist import Watchlist


class WatchlistService:
    """Service layer for watchlist operations"""

    def __init__(self, db: Session):
        self.repo = WatchlistRepository(db)

    def get_watchlist(self, name: str = "default") -> Optional[Watchlist]:
        """Get a watchlist by name"""
        return self.repo.get_watchlist_by_name(name)

    def get_or_create_default(self) -> Watchlist:
        """Get the default watchlist, creating it if needed"""
        return self.repo.get_default_watchlist()

    def get_tickers(self, watchlist_name: str = "default") -> List[str]:
        """Get all tickers from a watchlist"""
        watchlist = self.repo.get_watchlist_by_name(watchlist_name)
        if not watchlist:
            return []
        return watchlist.tickers or []

    def add_tickers(self, tickers: List[str], watchlist_name: str = "default") -> Watchlist:
        """Add tickers to a watchlist"""
        return self.repo.add_tickers(tickers, watchlist_name)

    def remove_tickers(self, tickers: List[str], watchlist_name: str = "default") -> Optional[Watchlist]:
        """Remove tickers from a watchlist"""
        return self.repo.remove_tickers(tickers, watchlist_name)

    def set_tickers(self, tickers: List[str], watchlist_name: str = "default") -> Watchlist:
        """Replace all tickers in a watchlist"""
        return self.repo.set_tickers(tickers, watchlist_name)

    def clear_watchlist(self, watchlist_name: str = "default") -> Optional[Watchlist]:
        """Clear all tickers from a watchlist"""
        return self.repo.clear_watchlist(watchlist_name)

    def mark_scanned(self, watchlist_name: str = "default") -> Optional[Watchlist]:
        """Update the last_scan_at timestamp"""
        return self.repo.update_last_scan(watchlist_name)
