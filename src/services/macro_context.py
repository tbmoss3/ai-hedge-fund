"""
Macro Context Service - Provides market-wide context for investment decisions.

Fetches and analyzes:
- VIX (volatility index)
- 10-Year Treasury rate
- S&P 500 trend and market regime
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

import yfinance as yf

logger = logging.getLogger(__name__)


def get_macro_context() -> dict:
    """
    Get current macro market context.

    Returns:
        Dict with VIX, treasury rate, and market regime assessment
    """
    context = {
        "vix": None,
        "vix_level": None,  # low, normal, elevated, high
        "treasury_10y": None,
        "sp500_trend": None,  # bullish, neutral, bearish
        "market_regime": None,  # risk-on, neutral, risk-off
        "fetched_at": datetime.utcnow().isoformat(),
    }

    try:
        # Fetch VIX
        vix = yf.Ticker("^VIX")
        vix_hist = vix.history(period="5d")
        if not vix_hist.empty:
            context["vix"] = round(vix_hist["Close"].iloc[-1], 2)
            context["vix_level"] = _classify_vix(context["vix"])

        # Fetch 10-Year Treasury
        tnx = yf.Ticker("^TNX")
        tnx_hist = tnx.history(period="5d")
        if not tnx_hist.empty:
            context["treasury_10y"] = round(tnx_hist["Close"].iloc[-1], 2)

        # Fetch S&P 500 trend
        spy = yf.Ticker("^GSPC")
        spy_hist = spy.history(period="60d")
        if not spy_hist.empty and len(spy_hist) >= 20:
            context["sp500_trend"] = _calculate_trend(spy_hist)

        # Determine overall market regime
        context["market_regime"] = _determine_regime(
            context["vix"],
            context["sp500_trend"]
        )

    except Exception as e:
        logger.error(f"Error fetching macro context: {e}")

    return context


def _classify_vix(vix: float) -> str:
    """Classify VIX level."""
    if vix < 15:
        return "low"
    elif vix < 20:
        return "normal"
    elif vix < 30:
        return "elevated"
    else:
        return "high"


def _calculate_trend(hist) -> str:
    """Calculate S&P 500 trend based on moving averages."""
    current = hist["Close"].iloc[-1]
    ma20 = hist["Close"].tail(20).mean()
    ma50 = hist["Close"].tail(50).mean() if len(hist) >= 50 else ma20

    # Simple trend calculation
    if current > ma20 > ma50:
        return "bullish"
    elif current < ma20 < ma50:
        return "bearish"
    else:
        return "neutral"


def _determine_regime(vix: Optional[float], sp500_trend: Optional[str]) -> str:
    """Determine overall market regime."""
    if vix is None or sp500_trend is None:
        return "neutral"

    # Risk-off: high VIX + bearish trend
    if vix > 25 and sp500_trend == "bearish":
        return "risk-off"

    # Risk-on: low VIX + bullish trend
    if vix < 18 and sp500_trend == "bullish":
        return "risk-on"

    return "neutral"
