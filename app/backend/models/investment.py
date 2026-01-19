from sqlalchemy import Column, String, Integer, Float, Date, DateTime, ForeignKey
from sqlalchemy.sql import func
from uuid import uuid4

from app.backend.database.connection import Base


class Investment(Base):
    """Approved investments with tracking for performance measurement"""
    __tablename__ = "investments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    memo_id = Column(String(36), ForeignKey("memos.id"), nullable=False, index=True)
    ticker = Column(String(10), nullable=False, index=True)
    analyst = Column(String(50), nullable=False, index=True)
    signal = Column(String(10), nullable=False)  # "bullish" or "bearish"
    entry_price = Column(Float, nullable=False)
    entry_date = Column(Date, nullable=False)
    status = Column(String(20), default="active", index=True)  # "active" or "closed"
    exit_price = Column(Float, nullable=True)
    exit_date = Column(Date, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
