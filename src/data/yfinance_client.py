"""
Yahoo Finance client for price and market data.

This module provides functions to fetch stock price data using yfinance
as a reliable fallback for price information.
"""

import logging
from typing import Optional
from datetime import datetime, timedelta

import pandas as pd

logger = logging.getLogger(__name__)

# Lazy import yfinance to avoid startup delays
_yf = None


def _get_yf():
    """Lazy load yfinance module."""
    global _yf
    if _yf is None:
        import yfinance as yf
        _yf = yf
    return _yf


def get_current_price(ticker: str) -> Optional[float]:
    """
    Get the current stock price for a ticker.

    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'MSFT')

    Returns:
        Current stock price as float, or None if not available
    """
    try:
        yf = _get_yf()
        stock = yf.Ticker(ticker)
        info = stock.info

        # Try different price fields in order of preference
        price = (
            info.get('currentPrice') or
            info.get('regularMarketPrice') or
            info.get('previousClose') or
            info.get('open')
        )

        if price is not None:
            return float(price)

        # Fallback: get the latest close from history
        hist = stock.history(period="1d")
        if not hist.empty:
            return float(hist['Close'].iloc[-1])

        logger.warning(f"No price data available for {ticker}")
        return None

    except Exception as e:
        logger.error(f"Error fetching current price for {ticker}: {e}")
        return None


def get_price_history(
    ticker: str,
    period: str = "1y",
    interval: str = "1d",
) -> pd.DataFrame:
    """
    Get historical price data for a ticker.

    Args:
        ticker: Stock ticker symbol
        period: Time period (e.g., '1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max')
        interval: Data interval (e.g., '1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h', '1d', '5d', '1wk', '1mo', '3mo')

    Returns:
        DataFrame with columns: Open, High, Low, Close, Volume, Dividends, Stock Splits
    """
    try:
        yf = _get_yf()
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period, interval=interval)

        if hist.empty:
            logger.warning(f"No historical data available for {ticker}")
            return pd.DataFrame()

        return hist

    except Exception as e:
        logger.error(f"Error fetching price history for {ticker}: {e}")
        return pd.DataFrame()


def get_price_history_range(
    ticker: str,
    start_date: str,
    end_date: str,
    interval: str = "1d",
) -> pd.DataFrame:
    """
    Get historical price data for a specific date range.

    Args:
        ticker: Stock ticker symbol
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        interval: Data interval

    Returns:
        DataFrame with price data
    """
    try:
        yf = _get_yf()
        stock = yf.Ticker(ticker)
        hist = stock.history(start=start_date, end=end_date, interval=interval)

        if hist.empty:
            logger.warning(f"No historical data for {ticker} from {start_date} to {end_date}")
            return pd.DataFrame()

        return hist

    except Exception as e:
        logger.error(f"Error fetching price history range for {ticker}: {e}")
        return pd.DataFrame()


def get_market_cap(ticker: str) -> Optional[float]:
    """
    Get the current market capitalization for a ticker.

    Args:
        ticker: Stock ticker symbol

    Returns:
        Market cap as float, or None if not available
    """
    try:
        yf = _get_yf()
        stock = yf.Ticker(ticker)
        info = stock.info

        market_cap = info.get('marketCap')
        if market_cap is not None:
            return float(market_cap)

        logger.warning(f"No market cap data available for {ticker}")
        return None

    except Exception as e:
        logger.error(f"Error fetching market cap for {ticker}: {e}")
        return None


def get_stock_info(ticker: str) -> dict:
    """
    Get comprehensive stock information.

    Args:
        ticker: Stock ticker symbol

    Returns:
        Dict containing stock info (sector, industry, employees, etc.)
    """
    try:
        yf = _get_yf()
        stock = yf.Ticker(ticker)
        return stock.info

    except Exception as e:
        logger.error(f"Error fetching stock info for {ticker}: {e}")
        return {}


def get_price_change(ticker: str, days: int = 1) -> Optional[float]:
    """
    Get the price change percentage over a number of days.

    Args:
        ticker: Stock ticker symbol
        days: Number of days to look back

    Returns:
        Price change as decimal (e.g., 0.05 for 5% increase)
    """
    try:
        yf = _get_yf()
        stock = yf.Ticker(ticker)

        # Fetch a bit more data to ensure we have enough
        period = f"{days + 5}d"
        hist = stock.history(period=period)

        if len(hist) < 2:
            logger.warning(f"Insufficient data for {ticker} price change calculation")
            return None

        # Get the price from 'days' ago and current
        if len(hist) > days:
            old_price = float(hist['Close'].iloc[-(days + 1)])
            current_price = float(hist['Close'].iloc[-1])
            return (current_price - old_price) / old_price

        # If we don't have enough history, use what we have
        old_price = float(hist['Close'].iloc[0])
        current_price = float(hist['Close'].iloc[-1])
        return (current_price - old_price) / old_price

    except Exception as e:
        logger.error(f"Error calculating price change for {ticker}: {e}")
        return None


def get_volatility(ticker: str, period: str = "1y") -> Optional[float]:
    """
    Calculate annualized volatility for a ticker.

    Args:
        ticker: Stock ticker symbol
        period: Time period for calculation

    Returns:
        Annualized volatility as decimal
    """
    try:
        hist = get_price_history(ticker, period=period)
        if hist.empty or len(hist) < 20:
            return None

        # Calculate daily returns
        returns = hist['Close'].pct_change().dropna()

        # Annualize the standard deviation (assuming ~252 trading days)
        daily_vol = returns.std()
        annual_vol = daily_vol * (252 ** 0.5)

        return float(annual_vol)

    except Exception as e:
        logger.error(f"Error calculating volatility for {ticker}: {e}")
        return None


def get_dividend_yield(ticker: str) -> Optional[float]:
    """
    Get the trailing dividend yield.

    Args:
        ticker: Stock ticker symbol

    Returns:
        Dividend yield as decimal (e.g., 0.025 for 2.5%)
    """
    try:
        yf = _get_yf()
        stock = yf.Ticker(ticker)
        info = stock.info

        div_yield = info.get('dividendYield') or info.get('trailingAnnualDividendYield')
        if div_yield is not None:
            return float(div_yield)

        return None

    except Exception as e:
        logger.error(f"Error fetching dividend yield for {ticker}: {e}")
        return None


def get_pe_ratio(ticker: str) -> Optional[float]:
    """
    Get the trailing P/E ratio.

    Args:
        ticker: Stock ticker symbol

    Returns:
        P/E ratio as float, or None if not available
    """
    try:
        yf = _get_yf()
        stock = yf.Ticker(ticker)
        info = stock.info

        pe = info.get('trailingPE') or info.get('forwardPE')
        if pe is not None:
            return float(pe)

        return None

    except Exception as e:
        logger.error(f"Error fetching P/E ratio for {ticker}: {e}")
        return None


def get_52_week_range(ticker: str) -> tuple[Optional[float], Optional[float]]:
    """
    Get the 52-week high and low prices.

    Args:
        ticker: Stock ticker symbol

    Returns:
        Tuple of (52_week_low, 52_week_high)
    """
    try:
        yf = _get_yf()
        stock = yf.Ticker(ticker)
        info = stock.info

        low = info.get('fiftyTwoWeekLow')
        high = info.get('fiftyTwoWeekHigh')

        return (
            float(low) if low is not None else None,
            float(high) if high is not None else None,
        )

    except Exception as e:
        logger.error(f"Error fetching 52-week range for {ticker}: {e}")
        return (None, None)


def batch_get_prices(tickers: list[str]) -> dict[str, Optional[float]]:
    """
    Get current prices for multiple tickers.

    Args:
        tickers: List of stock ticker symbols

    Returns:
        Dict mapping ticker to price
    """
    results = {}
    for ticker in tickers:
        results[ticker] = get_current_price(ticker)
    return results


def batch_get_price_changes(tickers: list[str], days: int = 1) -> dict[str, Optional[float]]:
    """
    Get price changes for multiple tickers.

    Args:
        tickers: List of stock ticker symbols
        days: Number of days to look back

    Returns:
        Dict mapping ticker to price change percentage
    """
    results = {}
    for ticker in tickers:
        results[ticker] = get_price_change(ticker, days)
    return results


def is_market_open() -> bool:
    """
    Check if the US stock market is currently open.

    Returns:
        True if market is open, False otherwise
    """
    try:
        yf = _get_yf()

        # Get SPY as a proxy for market status
        spy = yf.Ticker("SPY")
        info = spy.info

        market_state = info.get('marketState', '')
        return market_state.upper() in ['REGULAR', 'PRE', 'POST']

    except Exception as e:
        logger.error(f"Error checking market status: {e}")
        return False


def get_earnings_dates(ticker: str) -> pd.DataFrame:
    """
    Get upcoming and past earnings dates.

    Args:
        ticker: Stock ticker symbol

    Returns:
        DataFrame with earnings dates
    """
    try:
        yf = _get_yf()
        stock = yf.Ticker(ticker)
        return stock.earnings_dates

    except Exception as e:
        logger.error(f"Error fetching earnings dates for {ticker}: {e}")
        return pd.DataFrame()


def get_recommendations(ticker: str) -> pd.DataFrame:
    """
    Get analyst recommendations.

    Args:
        ticker: Stock ticker symbol

    Returns:
        DataFrame with recommendation history
    """
    try:
        yf = _get_yf()
        stock = yf.Ticker(ticker)
        return stock.recommendations

    except Exception as e:
        logger.error(f"Error fetching recommendations for {ticker}: {e}")
        return pd.DataFrame()


def get_institutional_holders(ticker: str) -> pd.DataFrame:
    """
    Get institutional holders data.

    Args:
        ticker: Stock ticker symbol

    Returns:
        DataFrame with institutional holders
    """
    try:
        yf = _get_yf()
        stock = yf.Ticker(ticker)
        return stock.institutional_holders

    except Exception as e:
        logger.error(f"Error fetching institutional holders for {ticker}: {e}")
        return pd.DataFrame()
