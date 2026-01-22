# Watchlist Repository - Data access layer
from typing import Optional, List
from sqlalchemy.orm import Session
from datetime import datetime

from app.backend.models.watchlist import Watchlist


class WatchlistRepository:
    """Repository for watchlist data access"""

    def __init__(self, db: Session):
        self.db = db

    def get_default_watchlist(self) -> Watchlist:
        """Get or create the default watchlist"""
        watchlist = self.db.query(Watchlist).filter(Watchlist.name == "default").first()
        if not watchlist:
            watchlist = Watchlist(name="default", tickers=[])
            self.db.add(watchlist)
            self.db.commit()
            self.db.refresh(watchlist)
        return watchlist

    def get_watchlist_by_name(self, name: str) -> Optional[Watchlist]:
        """Get a watchlist by name"""
        return self.db.query(Watchlist).filter(Watchlist.name == name).first()

    def get_all_watchlists(self) -> List[Watchlist]:
        """Get all watchlists"""
        return self.db.query(Watchlist).all()

    def add_tickers(self, tickers: List[str], watchlist_name: str = "default") -> Watchlist:
        """Add tickers to a watchlist (deduplicates)"""
        watchlist = self.get_watchlist_by_name(watchlist_name)
        if not watchlist:
            watchlist = Watchlist(name=watchlist_name, tickers=[])
            self.db.add(watchlist)

        # Normalize tickers (uppercase, strip whitespace)
        new_tickers = [t.strip().upper() for t in tickers if t.strip()]

        # Merge and deduplicate
        current_tickers = watchlist.tickers or []
        combined = list(set(current_tickers + new_tickers))
        combined.sort()  # Keep alphabetically sorted

        watchlist.tickers = combined
        self.db.commit()
        self.db.refresh(watchlist)
        return watchlist

    def remove_tickers(self, tickers: List[str], watchlist_name: str = "default") -> Optional[Watchlist]:
        """Remove tickers from a watchlist"""
        watchlist = self.get_watchlist_by_name(watchlist_name)
        if not watchlist:
            return None

        # Normalize tickers to remove
        tickers_to_remove = {t.strip().upper() for t in tickers if t.strip()}

        # Filter out the tickers
        current_tickers = watchlist.tickers or []
        watchlist.tickers = [t for t in current_tickers if t not in tickers_to_remove]

        self.db.commit()
        self.db.refresh(watchlist)
        return watchlist

    def set_tickers(self, tickers: List[str], watchlist_name: str = "default") -> Watchlist:
        """Replace all tickers in a watchlist"""
        watchlist = self.get_watchlist_by_name(watchlist_name)
        if not watchlist:
            watchlist = Watchlist(name=watchlist_name, tickers=[])
            self.db.add(watchlist)

        # Normalize and deduplicate
        normalized = list(set(t.strip().upper() for t in tickers if t.strip()))
        normalized.sort()

        watchlist.tickers = normalized
        self.db.commit()
        self.db.refresh(watchlist)
        return watchlist

    def update_last_scan(self, watchlist_name: str = "default") -> Optional[Watchlist]:
        """Update the last scan timestamp"""
        watchlist = self.get_watchlist_by_name(watchlist_name)
        if watchlist:
            watchlist.last_scan_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(watchlist)
        return watchlist

    def clear_watchlist(self, watchlist_name: str = "default") -> Optional[Watchlist]:
        """Clear all tickers from a watchlist"""
        watchlist = self.get_watchlist_by_name(watchlist_name)
        if watchlist:
            watchlist.tickers = []
            self.db.commit()
            self.db.refresh(watchlist)
        return watchlist
