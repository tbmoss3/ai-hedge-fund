"""
Fiscal.ai API Client for financial data.

This client provides access to financial data from Fiscal.ai's API,
including financial statements, ratios, business segments, and pricing data.
"""

import os
import httpx
import logging
from typing import Optional, Any
from pydantic import BaseModel
from datetime import datetime

logger = logging.getLogger(__name__)


class FinancialStatement(BaseModel):
    """Financial statement data model."""
    ticker: str
    period: str
    fiscal_year: int
    fiscal_quarter: Optional[int] = None
    currency: str = "USD"

    # Income Statement
    revenue: Optional[float] = None
    cost_of_revenue: Optional[float] = None
    gross_profit: Optional[float] = None
    operating_expenses: Optional[float] = None
    operating_income: Optional[float] = None
    net_income: Optional[float] = None
    ebitda: Optional[float] = None
    eps: Optional[float] = None
    eps_diluted: Optional[float] = None

    # Balance Sheet
    total_assets: Optional[float] = None
    total_liabilities: Optional[float] = None
    total_equity: Optional[float] = None
    cash_and_equivalents: Optional[float] = None
    total_debt: Optional[float] = None
    current_assets: Optional[float] = None
    current_liabilities: Optional[float] = None

    # Cash Flow
    operating_cash_flow: Optional[float] = None
    capital_expenditures: Optional[float] = None
    free_cash_flow: Optional[float] = None
    dividends_paid: Optional[float] = None

    model_config = {"extra": "allow"}


class FinancialRatios(BaseModel):
    """Financial ratios data model."""
    ticker: str
    period: str

    # Valuation Ratios
    pe_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None
    ps_ratio: Optional[float] = None
    ev_to_ebitda: Optional[float] = None
    ev_to_revenue: Optional[float] = None
    peg_ratio: Optional[float] = None

    # Profitability Ratios
    gross_margin: Optional[float] = None
    operating_margin: Optional[float] = None
    net_margin: Optional[float] = None
    roe: Optional[float] = None
    roa: Optional[float] = None
    roic: Optional[float] = None

    # Liquidity Ratios
    current_ratio: Optional[float] = None
    quick_ratio: Optional[float] = None
    cash_ratio: Optional[float] = None

    # Leverage Ratios
    debt_to_equity: Optional[float] = None
    debt_to_assets: Optional[float] = None
    interest_coverage: Optional[float] = None

    # Efficiency Ratios
    asset_turnover: Optional[float] = None
    inventory_turnover: Optional[float] = None
    receivables_turnover: Optional[float] = None

    # Growth Ratios
    revenue_growth: Optional[float] = None
    earnings_growth: Optional[float] = None
    fcf_growth: Optional[float] = None

    model_config = {"extra": "allow"}


class BusinessSegment(BaseModel):
    """Business segment data model."""
    segment_name: str
    revenue: Optional[float] = None
    operating_income: Optional[float] = None
    revenue_percentage: Optional[float] = None
    growth_rate: Optional[float] = None

    model_config = {"extra": "allow"}


class SegmentData(BaseModel):
    """Segment data response model."""
    ticker: str
    period: str
    segments: list[BusinessSegment] = []
    geographic_segments: list[BusinessSegment] = []
    kpis: dict[str, Any] = {}

    model_config = {"extra": "allow"}


class FiscalClient:
    """
    Client for Fiscal.ai financial data API.

    Provides methods to fetch financial statements, ratios, segments,
    and other financial data for stock analysis.
    """

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """
        Initialize the Fiscal.ai client.

        Args:
            api_key: Fiscal.ai API key. Falls back to FISCAL_API_KEY env var.
            base_url: Base URL for the API. Defaults to Fiscal.ai production URL.
        """
        self.api_key = api_key or os.getenv("FISCAL_API_KEY")
        self.base_url = base_url or os.getenv("FISCAL_BASE_URL", "https://api.fiscal.ai/v1")

        if not self.api_key:
            logger.warning("No FISCAL_API_KEY provided. Some API calls may fail.")

        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the async HTTP client."""
        if self._client is None or self._client.is_closed:
            headers = {
                "Content-Type": "application/json",
            }
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            self._client = httpx.AsyncClient(
                headers=headers,
                timeout=30.0,
                base_url=self.base_url,
            )
        return self._client

    async def close(self):
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[dict] = None,
        json_data: Optional[dict] = None,
    ) -> dict:
        """
        Make an API request.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            params: Query parameters
            json_data: JSON body for POST requests

        Returns:
            Response data as dict
        """
        client = await self._get_client()

        try:
            response = await client.request(
                method=method,
                url=endpoint,
                params=params,
                json=json_data,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code} for {endpoint}: {e.response.text}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Request error for {endpoint}: {e}")
            raise

    async def get_financials(
        self,
        ticker: str,
        period: str = "annual",
        limit: int = 5,
    ) -> list[FinancialStatement]:
        """
        Get financial statements (income statement, balance sheet, cash flow).

        Args:
            ticker: Stock ticker symbol
            period: 'annual' or 'quarterly'
            limit: Maximum number of periods to return

        Returns:
            List of FinancialStatement objects
        """
        try:
            data = await self._make_request(
                method="GET",
                endpoint=f"/financials/{ticker}",
                params={
                    "period": period,
                    "limit": limit,
                },
            )

            statements = data.get("financials", [])
            return [FinancialStatement(ticker=ticker, **stmt) for stmt in statements]
        except Exception as e:
            logger.error(f"Error fetching financials for {ticker}: {e}")
            return []

    async def get_income_statement(
        self,
        ticker: str,
        period: str = "annual",
        limit: int = 5,
    ) -> list[dict]:
        """
        Get income statement data.

        Args:
            ticker: Stock ticker symbol
            period: 'annual' or 'quarterly'
            limit: Maximum number of periods to return

        Returns:
            List of income statement data dicts
        """
        try:
            data = await self._make_request(
                method="GET",
                endpoint=f"/income-statement/{ticker}",
                params={
                    "period": period,
                    "limit": limit,
                },
            )
            return data.get("income_statements", [])
        except Exception as e:
            logger.error(f"Error fetching income statement for {ticker}: {e}")
            return []

    async def get_balance_sheet(
        self,
        ticker: str,
        period: str = "annual",
        limit: int = 5,
    ) -> list[dict]:
        """
        Get balance sheet data.

        Args:
            ticker: Stock ticker symbol
            period: 'annual' or 'quarterly'
            limit: Maximum number of periods to return

        Returns:
            List of balance sheet data dicts
        """
        try:
            data = await self._make_request(
                method="GET",
                endpoint=f"/balance-sheet/{ticker}",
                params={
                    "period": period,
                    "limit": limit,
                },
            )
            return data.get("balance_sheets", [])
        except Exception as e:
            logger.error(f"Error fetching balance sheet for {ticker}: {e}")
            return []

    async def get_cash_flow(
        self,
        ticker: str,
        period: str = "annual",
        limit: int = 5,
    ) -> list[dict]:
        """
        Get cash flow statement data.

        Args:
            ticker: Stock ticker symbol
            period: 'annual' or 'quarterly'
            limit: Maximum number of periods to return

        Returns:
            List of cash flow statement data dicts
        """
        try:
            data = await self._make_request(
                method="GET",
                endpoint=f"/cash-flow/{ticker}",
                params={
                    "period": period,
                    "limit": limit,
                },
            )
            return data.get("cash_flows", [])
        except Exception as e:
            logger.error(f"Error fetching cash flow for {ticker}: {e}")
            return []

    async def get_ratios(self, ticker: str) -> Optional[FinancialRatios]:
        """
        Get financial ratios (P/E, P/B, ROE, etc.).

        Args:
            ticker: Stock ticker symbol

        Returns:
            FinancialRatios object or None if not available
        """
        try:
            data = await self._make_request(
                method="GET",
                endpoint=f"/ratios/{ticker}",
            )

            ratios_data = data.get("ratios", {})
            if ratios_data:
                return FinancialRatios(ticker=ticker, **ratios_data)
            return None
        except Exception as e:
            logger.error(f"Error fetching ratios for {ticker}: {e}")
            return None

    async def get_key_metrics(
        self,
        ticker: str,
        period: str = "annual",
        limit: int = 5,
    ) -> list[dict]:
        """
        Get key financial metrics.

        Args:
            ticker: Stock ticker symbol
            period: 'annual' or 'quarterly'
            limit: Maximum number of periods to return

        Returns:
            List of key metrics data dicts
        """
        try:
            data = await self._make_request(
                method="GET",
                endpoint=f"/key-metrics/{ticker}",
                params={
                    "period": period,
                    "limit": limit,
                },
            )
            return data.get("metrics", [])
        except Exception as e:
            logger.error(f"Error fetching key metrics for {ticker}: {e}")
            return []

    async def get_segments(self, ticker: str) -> Optional[SegmentData]:
        """
        Get business segments and KPIs.

        Args:
            ticker: Stock ticker symbol

        Returns:
            SegmentData object or None if not available
        """
        try:
            data = await self._make_request(
                method="GET",
                endpoint=f"/segments/{ticker}",
            )

            segments_list = data.get("segments", [])
            geo_segments_list = data.get("geographic_segments", [])
            kpis = data.get("kpis", {})

            segments = [BusinessSegment(**seg) for seg in segments_list]
            geo_segments = [BusinessSegment(**seg) for seg in geo_segments_list]

            return SegmentData(
                ticker=ticker,
                period=data.get("period", "TTM"),
                segments=segments,
                geographic_segments=geo_segments,
                kpis=kpis,
            )
        except Exception as e:
            logger.error(f"Error fetching segments for {ticker}: {e}")
            return None

    async def get_company_profile(self, ticker: str) -> Optional[dict]:
        """
        Get company profile information.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Company profile dict or None if not available
        """
        try:
            data = await self._make_request(
                method="GET",
                endpoint=f"/profile/{ticker}",
            )
            return data.get("profile", {})
        except Exception as e:
            logger.error(f"Error fetching company profile for {ticker}: {e}")
            return None

    async def get_price(self, ticker: str) -> Optional[float]:
        """
        Get current stock price.

        Note: This method tries Fiscal.ai first, then falls back to yfinance
        if the Fiscal.ai endpoint is not available or returns no data.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Current stock price or None if not available
        """
        try:
            data = await self._make_request(
                method="GET",
                endpoint=f"/quote/{ticker}",
            )

            price = data.get("price") or data.get("current_price") or data.get("last_price")
            if price:
                return float(price)
        except Exception as e:
            logger.warning(f"Fiscal.ai price fetch failed for {ticker}: {e}")

        # Fallback to yfinance
        try:
            from src.data.yfinance_client import get_current_price
            return get_current_price(ticker)
        except Exception as e:
            logger.error(f"yfinance fallback failed for {ticker}: {e}")
            return None

    async def get_market_cap(self, ticker: str) -> Optional[float]:
        """
        Get current market capitalization.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Market cap or None if not available
        """
        try:
            data = await self._make_request(
                method="GET",
                endpoint=f"/quote/{ticker}",
            )

            market_cap = data.get("market_cap") or data.get("marketCap")
            if market_cap:
                return float(market_cap)
        except Exception as e:
            logger.warning(f"Fiscal.ai market cap fetch failed for {ticker}: {e}")

        # Fallback to yfinance
        try:
            from src.data.yfinance_client import get_market_cap
            return get_market_cap(ticker)
        except Exception as e:
            logger.error(f"yfinance market cap fallback failed for {ticker}: {e}")
            return None

    async def get_enterprise_value(self, ticker: str) -> Optional[float]:
        """
        Get enterprise value.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Enterprise value or None if not available
        """
        try:
            data = await self._make_request(
                method="GET",
                endpoint=f"/enterprise-value/{ticker}",
            )
            return data.get("enterprise_value")
        except Exception as e:
            logger.error(f"Error fetching enterprise value for {ticker}: {e}")
            return None

    async def search_tickers(self, query: str, limit: int = 10) -> list[dict]:
        """
        Search for tickers matching a query.

        Args:
            query: Search query string
            limit: Maximum number of results

        Returns:
            List of matching ticker info dicts
        """
        try:
            data = await self._make_request(
                method="GET",
                endpoint="/search",
                params={
                    "query": query,
                    "limit": limit,
                },
            )
            return data.get("results", [])
        except Exception as e:
            logger.error(f"Error searching tickers for '{query}': {e}")
            return []

    async def batch_get_financials(
        self,
        tickers: list[str],
        period: str = "annual",
        limit: int = 5,
    ) -> dict[str, list[FinancialStatement]]:
        """
        Get financial statements for multiple tickers.

        Args:
            tickers: List of stock ticker symbols
            period: 'annual' or 'quarterly'
            limit: Maximum number of periods per ticker

        Returns:
            Dict mapping ticker to list of FinancialStatement objects
        """
        results = {}
        for ticker in tickers:
            try:
                statements = await self.get_financials(ticker, period, limit)
                results[ticker] = statements
            except Exception as e:
                logger.error(f"Error in batch fetch for {ticker}: {e}")
                results[ticker] = []
        return results

    async def batch_get_ratios(
        self,
        tickers: list[str],
    ) -> dict[str, Optional[FinancialRatios]]:
        """
        Get financial ratios for multiple tickers.

        Args:
            tickers: List of stock ticker symbols

        Returns:
            Dict mapping ticker to FinancialRatios object or None
        """
        results = {}
        for ticker in tickers:
            try:
                ratios = await self.get_ratios(ticker)
                results[ticker] = ratios
            except Exception as e:
                logger.error(f"Error in batch ratios fetch for {ticker}: {e}")
                results[ticker] = None
        return results


# Convenience function to get a singleton client
_default_client: Optional[FiscalClient] = None


def get_fiscal_client() -> FiscalClient:
    """Get the default Fiscal.ai client instance."""
    global _default_client
    if _default_client is None:
        _default_client = FiscalClient()
    return _default_client
