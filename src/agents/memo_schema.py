"""
Standardized Investment Memo schema for all analyst agents.

Each agent can generate an InvestmentMemo when conviction >= 70%,
providing a detailed, structured investment thesis.
"""

from pydantic import BaseModel, Field
from typing import Literal, Optional
from datetime import datetime
from uuid import uuid4


class InvestmentMemo(BaseModel):
    """
    Standardized output format for high-conviction investment recommendations.
    Generated when an analyst's conviction level >= 70%.
    """
    id: str = Field(default_factory=lambda: str(uuid4()))
    ticker: str = Field(description="Stock ticker symbol")
    analyst: str = Field(description="Name of the analyst agent")
    signal: Literal["bullish", "bearish"] = Field(description="Investment direction")
    conviction: int = Field(ge=0, le=100, description="Conviction level 0-100")
    thesis: str = Field(description="2-3 sentence investment thesis")
    bull_case: list[str] = Field(description="3 bullet points for bull case")
    bear_case: list[str] = Field(description="3 bullet points for bear case")
    metrics: dict = Field(description="Analyst-specific key metrics")
    current_price: float = Field(description="Current stock price")
    target_price: float = Field(description="Target price based on valuation methodology")
    time_horizon: Literal["short", "medium", "long"] = Field(description="Investment time horizon")
    generated_at: datetime = Field(default_factory=datetime.utcnow)

    # New enrichment fields
    catalysts: Optional[dict] = Field(default=None, description="Upcoming catalysts: earnings dates, ex-dividend, etc.")
    conviction_breakdown: Optional[list[dict]] = Field(default=None, description="Component scores that contributed to conviction")
    macro_context: Optional[dict] = Field(default=None, description="Current macro environment: VIX, rates, market regime")
    position_sizing: Optional[dict] = Field(default=None, description="Recommended position size based on conviction and volatility")


class MemoGenerationRequest(BaseModel):
    """
    Internal model for LLM memo generation prompts.
    Used to structure the input for generating investment memos.
    """
    thesis: str = Field(description="2-3 sentence investment thesis")
    bull_case: list[str] = Field(description="3 bullet points for bull case")
    bear_case: list[str] = Field(description="3 bullet points for bear case")
    target_price: float = Field(description="Target price based on valuation methodology")


def generate_investment_memo(
    ticker: str,
    analyst: str,
    signal: Literal["bullish", "bearish"],
    conviction: int,
    current_price: float,
    target_price: float,
    time_horizon: Literal["short", "medium", "long"],
    thesis: str,
    bull_case: list[str],
    bear_case: list[str],
    metrics: dict,
    catalysts: Optional[dict] = None,
    conviction_breakdown: Optional[list[dict]] = None,
    macro_context: Optional[dict] = None,
    position_sizing: Optional[dict] = None,
) -> InvestmentMemo:
    """
    Factory function to create an InvestmentMemo with all required fields.
    """
    return InvestmentMemo(
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
        catalysts=catalysts,
        conviction_breakdown=conviction_breakdown,
        macro_context=macro_context,
        position_sizing=position_sizing,
    )


def should_generate_memo(conviction: int) -> bool:
    """
    Determines if a memo should be generated based on conviction threshold.
    Returns True if conviction >= 70%.
    """
    return conviction >= 70
