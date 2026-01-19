"""
Scanner Service for bi-weekly stock universe rotation.

This service scans through a universe of stocks (S&P 500 + Russell 2000)
using multiple analyst agents to identify high-conviction investment opportunities.
"""

import asyncio
import logging
import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Callable, Any
from uuid import uuid4

import yaml
from pydantic import BaseModel, Field

from src.agents.memo_schema import InvestmentMemo, should_generate_memo
from src.data.yfinance_client import get_current_price, get_market_cap, get_price_change
from src.graph.state import AgentState
from src.utils.analysts import ANALYST_CONFIG


logger = logging.getLogger(__name__)


# Default conviction threshold
DEFAULT_CONVICTION_THRESHOLD = 70


class ScanConfig(BaseModel):
    """Configuration for a scan run."""
    conviction_threshold: int = DEFAULT_CONVICTION_THRESHOLD
    batch_size: int = 100
    rate_limit_delay: float = 1.0  # seconds between batches
    max_retries: int = 3
    timeout_per_ticker: float = 60.0  # seconds


class ScanResult(BaseModel):
    """Result of a scanner run on a universe of stocks."""
    scan_id: str = Field(default_factory=lambda: str(uuid4()))
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    status: str = "running"  # running, completed, failed, cancelled

    # Configuration
    universe_name: str = ""
    total_tickers: int = 0
    analysts_used: list[str] = []
    conviction_threshold: int = DEFAULT_CONVICTION_THRESHOLD

    # Results
    tickers_scanned: int = 0
    memos_generated: int = 0
    high_conviction_memos: list[dict] = []
    errors: list[str] = []

    # Performance metrics
    avg_processing_time_per_ticker: Optional[float] = None

    def add_memo(self, memo: InvestmentMemo):
        """Add a high conviction memo to results."""
        if memo.conviction >= self.conviction_threshold:
            self.high_conviction_memos.append(memo.model_dump())
            self.memos_generated += 1

    def complete(self):
        """Mark scan as completed."""
        self.end_time = datetime.utcnow()
        self.status = "completed"

        if self.tickers_scanned > 0 and self.start_time and self.end_time:
            duration = (self.end_time - self.start_time).total_seconds()
            self.avg_processing_time_per_ticker = duration / self.tickers_scanned

    def fail(self, error: str):
        """Mark scan as failed."""
        self.end_time = datetime.utcnow()
        self.status = "failed"
        self.errors.append(error)


def load_universe_config(config_path: Optional[str] = None) -> dict:
    """
    Load universe configuration from YAML file.

    Args:
        config_path: Path to config file. Defaults to config/universe.yaml

    Returns:
        Universe configuration dictionary
    """
    if config_path is None:
        # Find the project root and config file
        current_dir = Path(__file__).resolve().parent
        project_root = current_dir.parent.parent
        config_path = project_root / "config" / "universe.yaml"

    try:
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logger.warning(f"Universe config not found at {config_path}, using defaults")
        return {"sp500": [], "russell2000_sample": []}
    except Exception as e:
        logger.error(f"Error loading universe config: {e}")
        return {"sp500": [], "russell2000_sample": []}


def load_scanner_config(config_path: Optional[str] = None) -> ScanConfig:
    """
    Load scanner configuration from YAML file.

    Args:
        config_path: Path to config file. Defaults to config/scanner.yaml

    Returns:
        ScanConfig object
    """
    if config_path is None:
        current_dir = Path(__file__).resolve().parent
        project_root = current_dir.parent.parent
        config_path = project_root / "config" / "scanner.yaml"

    try:
        with open(config_path, "r") as f:
            config_data = yaml.safe_load(f)
            scanner_config = config_data.get("scanner", {})
            return ScanConfig(**scanner_config)
    except FileNotFoundError:
        logger.warning(f"Scanner config not found at {config_path}, using defaults")
        return ScanConfig()
    except Exception as e:
        logger.error(f"Error loading scanner config: {e}")
        return ScanConfig()


def get_universe_tickers(
    universe_config: dict,
    sources: Optional[list[str]] = None,
) -> list[str]:
    """
    Get list of tickers from universe configuration.

    Args:
        universe_config: Universe configuration dictionary
        sources: List of sources to include (e.g., ['sp500', 'russell2000_sample'])
                 If None, includes sp500 by default

    Returns:
        List of unique ticker symbols
    """
    if sources is None:
        sources = ["sp500"]

    tickers = set()
    for source in sources:
        source_tickers = universe_config.get(source, [])
        if source_tickers:
            tickers.update(source_tickers)

    # Also check for custom tickers
    custom = universe_config.get("custom", [])
    if custom:
        tickers.update(custom)

    return sorted(list(tickers))


def get_sector_tickers(
    universe_config: dict,
    sector: str,
) -> list[str]:
    """
    Get tickers for a specific sector.

    Args:
        universe_config: Universe configuration dictionary
        sector: Sector name (e.g., 'technology', 'healthcare')

    Returns:
        List of ticker symbols for the sector
    """
    sectors = universe_config.get("sectors", {})
    return sectors.get(sector, [])


# Map analyst keys to their agent functions
def get_analyst_agents() -> dict[str, tuple[str, Callable]]:
    """
    Get mapping of analyst keys to their agent functions.

    Returns:
        Dict mapping analyst key to (display_name, agent_function)
    """
    return {
        key: (config["display_name"], config["agent_func"])
        for key, config in ANALYST_CONFIG.items()
        if config.get("type") == "analyst"
    }


# Default set of value-oriented analysts for scanning
DEFAULT_ANALYSTS = [
    "warren_buffett",
    "charlie_munger",
    "peter_lynch",
    "phil_fisher",
    "michael_burry",
    "bill_ackman",
    "stanley_druckenmiller",
]


class Scanner:
    """
    Stock scanner service for identifying high-conviction opportunities.

    Scans through a universe of stocks using multiple analyst agents
    and generates investment memos for high-conviction ideas.
    """

    def __init__(
        self,
        config: Optional[ScanConfig] = None,
        analysts: Optional[list[str]] = None,
        model_name: str = "gpt-4.1",
        model_provider: str = "OpenAI",
    ):
        """
        Initialize the scanner.

        Args:
            config: Scanner configuration
            analysts: List of analyst keys to use (defaults to DEFAULT_ANALYSTS)
            model_name: LLM model name to use
            model_provider: LLM provider name
        """
        self.config = config or load_scanner_config()
        self.analyst_keys = analysts or DEFAULT_ANALYSTS
        self.model_name = model_name
        self.model_provider = model_provider

        # Get analyst agent functions
        all_agents = get_analyst_agents()
        self.analysts = {
            key: all_agents[key]
            for key in self.analyst_keys
            if key in all_agents
        }

        if not self.analysts:
            raise ValueError("No valid analysts specified")

        logger.info(f"Scanner initialized with {len(self.analysts)} analysts: {list(self.analysts.keys())}")

    def _create_agent_state(
        self,
        ticker: str,
        end_date: Optional[str] = None,
    ) -> AgentState:
        """
        Create an AgentState for analyzing a single ticker.

        Args:
            ticker: Stock ticker symbol
            end_date: End date for analysis (defaults to today)

        Returns:
            AgentState object
        """
        if end_date is None:
            end_date = datetime.now().strftime("%Y-%m-%d")

        start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")

        return {
            "messages": [],
            "data": {
                "tickers": [ticker],
                "portfolio": {},
                "start_date": start_date,
                "end_date": end_date,
                "analyst_signals": {},
            },
            "metadata": {
                "show_reasoning": False,
                "model_name": self.model_name,
                "model_provider": self.model_provider,
            },
        }

    def _extract_memo_from_signal(
        self,
        ticker: str,
        analyst_key: str,
        signal_data: dict,
        current_price: Optional[float] = None,
    ) -> Optional[InvestmentMemo]:
        """
        Extract an InvestmentMemo from analyst signal data.

        Args:
            ticker: Stock ticker
            analyst_key: Analyst identifier
            signal_data: Signal data from analyst
            current_price: Current stock price

        Returns:
            InvestmentMemo if signal meets conviction threshold, else None
        """
        try:
            signal = signal_data.get("signal", "neutral")
            confidence = signal_data.get("confidence", 0)
            reasoning = signal_data.get("reasoning", "")

            # Only create memo for bullish/bearish signals with high conviction
            if signal == "neutral" or not should_generate_memo(confidence):
                return None

            # Get price if not provided
            if current_price is None:
                current_price = get_current_price(ticker) or 0.0

            # Simple target price estimation based on signal
            # In a real implementation, this would come from the analyst
            if signal == "bullish":
                target_price = current_price * 1.20  # 20% upside target
            else:
                target_price = current_price * 0.80  # 20% downside target

            analyst_name = self.analysts.get(analyst_key, (analyst_key, None))[0]

            return InvestmentMemo(
                ticker=ticker,
                analyst=analyst_name,
                signal=signal,
                conviction=confidence,
                thesis=reasoning,
                bull_case=[reasoning] if signal == "bullish" else ["See reasoning"],
                bear_case=[reasoning] if signal == "bearish" else ["See reasoning"],
                metrics={"signal": signal, "confidence": confidence},
                current_price=current_price,
                target_price=target_price,
                time_horizon="medium",
            )
        except Exception as e:
            logger.error(f"Error extracting memo for {ticker}/{analyst_key}: {e}")
            return None

    def analyze_ticker(
        self,
        ticker: str,
        end_date: Optional[str] = None,
    ) -> list[InvestmentMemo]:
        """
        Analyze a single ticker with all configured analysts.

        Args:
            ticker: Stock ticker symbol
            end_date: End date for analysis

        Returns:
            List of high-conviction InvestmentMemos
        """
        memos = []
        state = self._create_agent_state(ticker, end_date)

        # Get current price once for all analysts
        current_price = get_current_price(ticker)

        for analyst_key, (analyst_name, agent_func) in self.analysts.items():
            try:
                logger.debug(f"Analyzing {ticker} with {analyst_name}")

                # Run the analyst agent
                result = agent_func(state, agent_id=f"{analyst_key}_agent")

                # Extract signal from result
                signals = result.get("data", {}).get("analyst_signals", {})
                agent_signal = signals.get(f"{analyst_key}_agent", {})
                ticker_signal = agent_signal.get(ticker, {})

                if ticker_signal:
                    memo = self._extract_memo_from_signal(
                        ticker,
                        analyst_key,
                        ticker_signal,
                        current_price,
                    )
                    if memo:
                        memos.append(memo)
                        logger.info(
                            f"Generated memo for {ticker} from {analyst_name}: "
                            f"{memo.signal} ({memo.conviction}%)"
                        )

            except Exception as e:
                logger.error(f"Error running {analyst_name} on {ticker}: {e}")

        return memos

    async def analyze_ticker_async(
        self,
        ticker: str,
        end_date: Optional[str] = None,
    ) -> list[InvestmentMemo]:
        """
        Async wrapper for analyze_ticker.

        Args:
            ticker: Stock ticker symbol
            end_date: End date for analysis

        Returns:
            List of high-conviction InvestmentMemos
        """
        # Run in executor to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.analyze_ticker,
            ticker,
            end_date,
        )

    async def scan_batch(
        self,
        tickers: list[str],
        result: ScanResult,
        end_date: Optional[str] = None,
    ) -> list[InvestmentMemo]:
        """
        Scan a batch of tickers.

        Args:
            tickers: List of ticker symbols
            result: ScanResult to update
            end_date: End date for analysis

        Returns:
            List of high-conviction memos from the batch
        """
        batch_memos = []

        for ticker in tickers:
            try:
                memos = await self.analyze_ticker_async(ticker, end_date)
                batch_memos.extend(memos)

                for memo in memos:
                    result.add_memo(memo)

                result.tickers_scanned += 1
                logger.info(f"Scanned {ticker}: {len(memos)} high-conviction signals")

            except Exception as e:
                error_msg = f"Error scanning {ticker}: {e}"
                logger.error(error_msg)
                result.errors.append(error_msg)

        return batch_memos

    async def run_full_scan(
        self,
        universe: list[str],
        universe_name: str = "custom",
        end_date: Optional[str] = None,
    ) -> ScanResult:
        """
        Run a full scan on the entire universe.

        Args:
            universe: List of ticker symbols to scan
            universe_name: Name of the universe for tracking
            end_date: End date for analysis

        Returns:
            ScanResult with all high-conviction memos
        """
        result = ScanResult(
            universe_name=universe_name,
            total_tickers=len(universe),
            analysts_used=list(self.analysts.keys()),
            conviction_threshold=self.config.conviction_threshold,
        )

        logger.info(
            f"Starting scan of {len(universe)} tickers with "
            f"{len(self.analysts)} analysts (threshold: {self.config.conviction_threshold}%)"
        )

        try:
            # Process in batches
            batches = [
                universe[i:i + self.config.batch_size]
                for i in range(0, len(universe), self.config.batch_size)
            ]

            for batch_num, batch in enumerate(batches, 1):
                logger.info(f"Processing batch {batch_num}/{len(batches)} ({len(batch)} tickers)")

                await self.scan_batch(batch, result, end_date)

                # Rate limiting between batches
                if batch_num < len(batches):
                    await asyncio.sleep(self.config.rate_limit_delay)

            result.complete()
            logger.info(
                f"Scan completed: {result.tickers_scanned} tickers, "
                f"{result.memos_generated} high-conviction memos"
            )

        except Exception as e:
            result.fail(str(e))
            logger.error(f"Scan failed: {e}")

        return result

    def run_scan_sync(
        self,
        universe: list[str],
        universe_name: str = "custom",
        end_date: Optional[str] = None,
    ) -> ScanResult:
        """
        Synchronous wrapper for run_full_scan.

        Args:
            universe: List of ticker symbols to scan
            universe_name: Name of the universe for tracking
            end_date: End date for analysis

        Returns:
            ScanResult with all high-conviction memos
        """
        return asyncio.run(self.run_full_scan(universe, universe_name, end_date))


def check_price_trigger(
    ticker: str,
    threshold: float = 0.05,
    days: int = 1,
) -> bool:
    """
    Check if a ticker has had a significant price move.

    Used to trigger re-analysis outside the regular bi-weekly schedule.

    Args:
        ticker: Stock ticker symbol
        threshold: Price change threshold (e.g., 0.05 for 5%)
        days: Number of days to look back

    Returns:
        True if price move exceeds threshold
    """
    try:
        price_change = get_price_change(ticker, days)
        if price_change is not None:
            return abs(price_change) >= threshold
    except Exception as e:
        logger.error(f"Error checking price trigger for {ticker}: {e}")

    return False


def get_triggered_tickers(
    tickers: list[str],
    threshold: float = 0.05,
    days: int = 1,
) -> list[str]:
    """
    Get list of tickers that have had significant price moves.

    Args:
        tickers: List of tickers to check
        threshold: Price change threshold
        days: Number of days to look back

    Returns:
        List of tickers that exceeded the threshold
    """
    triggered = []
    for ticker in tickers:
        if check_price_trigger(ticker, threshold, days):
            triggered.append(ticker)
    return triggered


def save_scan_result(result: ScanResult, output_dir: Optional[str] = None) -> str:
    """
    Save scan results to JSON file.

    Args:
        result: ScanResult to save
        output_dir: Output directory (defaults to .cache/scans/)

    Returns:
        Path to saved file
    """
    if output_dir is None:
        current_dir = Path(__file__).resolve().parent
        project_root = current_dir.parent.parent
        output_dir = project_root / ".cache" / "scans"

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    timestamp = result.start_time.strftime("%Y%m%d_%H%M%S")
    filename = f"scan_{result.universe_name}_{timestamp}.json"
    filepath = output_path / filename

    with open(filepath, "w") as f:
        json.dump(result.model_dump(), f, indent=2, default=str)

    logger.info(f"Scan results saved to {filepath}")
    return str(filepath)


def load_scan_result(filepath: str) -> ScanResult:
    """
    Load scan results from JSON file.

    Args:
        filepath: Path to JSON file

    Returns:
        ScanResult object
    """
    with open(filepath, "r") as f:
        data = json.load(f)
    return ScanResult(**data)
