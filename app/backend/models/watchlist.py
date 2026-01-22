# Watchlist ORM Model
from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.sql import func

from app.backend.database.connection import Base


class Watchlist(Base):
    """Stores user watchlists for scheduled scans"""
    __tablename__ = "watchlists"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, default="default", unique=True)
    tickers = Column(JSON, nullable=False, default=[])  # ["AAPL", "MSFT", ...]
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_scan_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<Watchlist(name='{self.name}', tickers={len(self.tickers or [])})>"
