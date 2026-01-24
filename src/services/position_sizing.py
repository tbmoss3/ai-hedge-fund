"""
Position Sizing Service - Calculates recommended position sizes.

Based on:
- Conviction level
- Stock volatility (standard deviation of returns)
- Current portfolio concentration
"""

import logging
from typing import Optional

import yfinance as yf
import numpy as np

logger = logging.getLogger(__name__)


def calculate_position_sizing(
    ticker: str,
    conviction: int,
    signal: str,
    max_position_pct: float = 10.0,
    min_position_pct: float = 1.0,
) -> dict:
    """
    Calculate recommended position size based on conviction and volatility.

    Args:
        ticker: Stock ticker symbol
        conviction: Conviction level 0-100
        signal: "bullish" or "bearish"
        max_position_pct: Maximum position size as % of portfolio
        min_position_pct: Minimum position size as % of portfolio

    Returns:
        Dict with recommended position size and risk metrics
    """
    result = {
        "recommended_pct": None,
        "max_risk_pct": None,  # Max loss at 2 standard deviations
        "volatility_annual": None,
        "volatility_daily": None,
        "sizing_rationale": None,
    }

    try:
        # Fetch historical data for volatility calculation
        stock = yf.Ticker(ticker)
        hist = stock.history(period="6mo")

        if hist.empty or len(hist) < 20:
            result["sizing_rationale"] = "Insufficient price history for volatility calculation"
            result["recommended_pct"] = min_position_pct
            return result

        # Calculate daily returns and volatility
        returns = hist["Close"].pct_change().dropna()
        daily_vol = returns.std()
        annual_vol = daily_vol * np.sqrt(252)  # Annualize

        result["volatility_daily"] = round(daily_vol * 100, 2)  # As percentage
        result["volatility_annual"] = round(annual_vol * 100, 2)

        # Position sizing formula:
        # Higher conviction = larger position
        # Higher volatility = smaller position
        # Base size: conviction/100 * max_position
        # Volatility adjustment: inverse of volatility relative to market avg (20%)

        base_size = (conviction / 100) * max_position_pct
        market_avg_vol = 0.20  # ~20% is typical S&P 500 annual volatility

        # Volatility adjustment factor (1.0 at market avg, lower for high vol stocks)
        vol_factor = min(1.0, market_avg_vol / max(annual_vol, 0.10))

        recommended = base_size * vol_factor
        recommended = max(min_position_pct, min(max_position_pct, recommended))

        result["recommended_pct"] = round(recommended, 2)

        # Calculate max risk (2 std dev move)
        max_risk = recommended * (daily_vol * 2 * 100)  # 2-sigma daily move
        result["max_risk_pct"] = round(max_risk, 2)

        # Rationale
        vol_desc = "high" if annual_vol > 0.40 else "moderate" if annual_vol > 0.25 else "low"
        result["sizing_rationale"] = (
            f"{conviction}% conviction with {vol_desc} volatility ({result['volatility_annual']}% annual). "
            f"Recommended {result['recommended_pct']}% position."
        )

    except Exception as e:
        logger.error(f"Error calculating position size for {ticker}: {e}")
        result["recommended_pct"] = min_position_pct
        result["sizing_rationale"] = f"Error in calculation: {str(e)}"

    return result
