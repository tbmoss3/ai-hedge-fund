from sqlalchemy import Column, String, Integer, Float, DateTime
from sqlalchemy.sql import func

from app.backend.database.connection import Base


class AnalystStats(Base):
    """Performance tracking for each AI analyst"""
    __tablename__ = "analyst_stats"

    analyst = Column(String(50), primary_key=True)  # e.g., "warren_buffett"
    total_memos = Column(Integer, default=0)
    approved_count = Column(Integer, default=0)
    win_count = Column(Integer, default=0)
    total_return = Column(Float, default=0.0)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
