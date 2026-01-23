# Scheduler Service - APScheduler for quarterly watchlist scans (post-earnings)
import asyncio
import logging
import os
from datetime import datetime
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.backend.database import get_db, SessionLocal
from app.backend.services.watchlist_service import WatchlistService
from app.backend.services.inbox_service import InboxService
from app.backend.services.email_service import email_service

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler: Optional[AsyncIOScheduler] = None


async def run_quarterly_scan():
    """
    Run the quarterly watchlist scan (post-earnings).

    Scheduled for Jan 15, Apr 15, Jul 15, Oct 15 - after most earnings reports.

    This job:
    1. Fetches the watchlist from the database
    2. Runs the Scanner with Claude Sonnet on all tickers
    3. Submits high-conviction memos to the inbox
    4. Sends email notification with summary
    """
    logger.info("Starting quarterly watchlist scan (post-earnings)...")

    db = SessionLocal()
    try:
        # 1. Get watchlist
        watchlist_service = WatchlistService(db)
        tickers = watchlist_service.get_tickers()

        if not tickers:
            logger.info("Watchlist is empty, skipping scan")
            return

        logger.info(f"Scanning {len(tickers)} tickers from watchlist...")

        # 2. Run the scanner
        from src.services.scanner import Scanner, ScanConfig
        from src.utils.analysts import ANALYST_CONFIG

        # Use Claude Sonnet for quarterly scans (high-quality analysis)
        model_name = os.getenv("SCANNER_MODEL", "claude-sonnet-4-5-20250929")
        model_provider = os.getenv("SCANNER_PROVIDER", "Anthropic")

        # All analysts
        analysts = [
            key for key, config in ANALYST_CONFIG.items()
            if config.get("type") == "analyst"
        ]

        config = ScanConfig(conviction_threshold=70)
        scanner = Scanner(
            config=config,
            analysts=analysts,
            model_name=model_name,
            model_provider=model_provider,
        )

        result = await scanner.run_full_scan(
            universe=tickers,
            universe_name="monthly_watchlist",
        )

        logger.info(f"Quarterly scan complete: {result.tickers_scanned} tickers, {result.memos_generated} memos")

        # 3. Submit memos to inbox
        inbox_service = InboxService(db)
        submitted_memos = []

        for memo in result.high_conviction_memos:
            try:
                created_memo = inbox_service.create_memo(
                    ticker=memo["ticker"],
                    analyst=memo["analyst"],
                    signal=memo["signal"],
                    conviction=memo["conviction"],
                    thesis=memo["thesis"],
                    bull_case=memo.get("bull_case", ["See thesis"]),
                    bear_case=memo.get("bear_case", ["See thesis"]),
                    metrics=memo.get("metrics", {}),
                    current_price=memo["current_price"],
                    target_price=memo["target_price"],
                    time_horizon=memo.get("time_horizon", "medium"),
                    generated_at=datetime.utcnow().isoformat(),
                )
                submitted_memos.append(created_memo)
                logger.info(f"Submitted memo for {memo['ticker']} from {memo['analyst']}")
            except Exception as e:
                logger.error(f"Failed to submit memo for {memo['ticker']}: {e}")

        # 4. Update watchlist last_scan_at
        watchlist_service.mark_scanned()

        # 5. Send email notification
        if email_service.is_configured():
            try:
                await email_service.notify_scan_complete(
                    tickers_scanned=result.tickers_scanned,
                    memos_generated=len(submitted_memos),
                    memos=result.high_conviction_memos,
                )
                logger.info("Email notification sent")
            except Exception as e:
                logger.error(f"Failed to send email notification: {e}")
        else:
            logger.info("Email service not configured, skipping notification")

        logger.info(f"Quarterly scan complete: submitted {len(submitted_memos)} memos")

    except Exception as e:
        logger.error(f"Quarterly scan failed: {e}")
        raise
    finally:
        db.close()


async def run_manual_scan(tickers: list[str]) -> dict:
    """
    Run a manual scan on specific tickers.

    Args:
        tickers: List of ticker symbols to scan

    Returns:
        Dict with scan results summary
    """
    logger.info(f"Starting manual scan of {len(tickers)} tickers...")

    db = SessionLocal()
    try:
        from src.services.scanner import Scanner, ScanConfig
        from src.utils.analysts import ANALYST_CONFIG

        # Use Claude Sonnet for high-quality analysis
        model_name = os.getenv("SCANNER_MODEL", "claude-sonnet-4-5-20250929")
        model_provider = os.getenv("SCANNER_PROVIDER", "Anthropic")

        analysts = [
            key for key, config in ANALYST_CONFIG.items()
            if config.get("type") == "analyst"
        ]

        config = ScanConfig(conviction_threshold=70)
        scanner = Scanner(
            config=config,
            analysts=analysts,
            model_name=model_name,
            model_provider=model_provider,
        )

        result = await scanner.run_full_scan(
            universe=tickers,
            universe_name="manual_scan",
        )

        # Submit memos to inbox
        inbox_service = InboxService(db)
        submitted_count = 0

        for memo in result.high_conviction_memos:
            try:
                inbox_service.create_memo(
                    ticker=memo["ticker"],
                    analyst=memo["analyst"],
                    signal=memo["signal"],
                    conviction=memo["conviction"],
                    thesis=memo["thesis"],
                    bull_case=memo.get("bull_case", ["See thesis"]),
                    bear_case=memo.get("bear_case", ["See thesis"]),
                    metrics=memo.get("metrics", {}),
                    current_price=memo["current_price"],
                    target_price=memo["target_price"],
                    time_horizon=memo.get("time_horizon", "medium"),
                    generated_at=datetime.utcnow().isoformat(),
                )
                submitted_count += 1
            except Exception as e:
                logger.error(f"Failed to submit memo for {memo['ticker']}: {e}")

        # Update watchlist last_scan_at
        watchlist_service = WatchlistService(db)
        watchlist_service.mark_scanned()

        # Send email if configured
        if email_service.is_configured() and result.high_conviction_memos:
            try:
                await email_service.notify_scan_complete(
                    tickers_scanned=result.tickers_scanned,
                    memos_generated=submitted_count,
                    memos=result.high_conviction_memos,
                )
            except Exception as e:
                logger.error(f"Failed to send email notification: {e}")

        return {
            "status": result.status,
            "tickers_scanned": result.tickers_scanned,
            "memos_generated": submitted_count,
            "errors": result.errors[:5] if result.errors else [],
        }

    finally:
        db.close()


def start_scheduler():
    """Start the APScheduler with quarterly scan jobs (post-earnings)."""
    global scheduler

    if scheduler is not None:
        logger.warning("Scheduler already running")
        return

    scheduler = AsyncIOScheduler()

    # Schedule quarterly scans: 15th of Jan, Apr, Jul, Oct at 6 AM UTC
    # These dates are ~2 weeks after quarter-end when most earnings are released
    scheduler.add_job(
        run_quarterly_scan,
        CronTrigger(month='1,4,7,10', day=15, hour=6, minute=0),
        id="quarterly_watchlist_scan",
        name="Quarterly Watchlist Scan (Post-Earnings)",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("Scheduler started - quarterly scans scheduled for Jan 15, Apr 15, Jul 15, Oct 15 at 6:00 AM UTC")


def stop_scheduler():
    """Stop the APScheduler."""
    global scheduler

    if scheduler is not None:
        scheduler.shutdown(wait=False)
        scheduler = None
        logger.info("Scheduler stopped")


def get_next_run_time() -> Optional[datetime]:
    """Get the next scheduled scan time."""
    global scheduler

    if scheduler is None:
        return None

    job = scheduler.get_job("quarterly_watchlist_scan")
    if job and job.next_run_time:
        return job.next_run_time

    return None
