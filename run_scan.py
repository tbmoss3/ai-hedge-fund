#!/usr/bin/env python
"""
Quick scan script that runs analysts and submits memos to the backend.
"""
import asyncio
import requests
from datetime import datetime
from src.services.scanner import Scanner, ScanConfig
from src.utils.analysts import ANALYST_CONFIG

# Backend URL
BACKEND_URL = "https://ai-hedge-fund-production-1e22.up.railway.app"

def submit_memo_to_backend(memo: dict):
    """Submit a memo to the backend API."""
    payload = {
        "ticker": memo["ticker"],
        "analyst": memo["analyst"],
        "signal": memo["signal"],
        "conviction": memo["conviction"],
        "thesis": memo["thesis"],
        "bull_case": memo.get("bull_case", ["See thesis"]),
        "bear_case": memo.get("bear_case", ["See thesis"]),
        "metrics": memo.get("metrics", {}),
        "current_price": memo["current_price"],
        "target_price": memo["target_price"],
        "time_horizon": memo.get("time_horizon", "medium"),
        "generated_at": datetime.utcnow().isoformat(),
    }

    try:
        response = requests.post(
            f"{BACKEND_URL}/api/inbox/",
            json=payload,
            headers={"Content-Type": "application/json"},
        )
        if response.status_code == 200:
            print(f"  [OK] Submitted memo for {memo['ticker']} from {memo['analyst']}")
            return True
        else:
            print(f"  [ERROR] Failed to submit memo: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"  [ERROR] Failed to submit memo: {e}")
        return False


async def run_scan(tickers: list[str], analysts: list[str] = None):
    """Run a scan and submit memos to backend."""
    if analysts is None:
        analysts = list(ANALYST_CONFIG.keys())

    print(f"\n{'='*60}")
    print(f"AI Hedge Fund Stock Scanner")
    print(f"{'='*60}")
    print(f"Tickers: {', '.join(tickers)}")
    print(f"Analysts: {', '.join(analysts)}")
    print(f"Backend: {BACKEND_URL}")
    print(f"{'='*60}\n")

    # Create scanner with DeepSeek
    config = ScanConfig(conviction_threshold=60)  # Lower threshold for testing
    scanner = Scanner(
        config=config,
        analysts=analysts,
        model_name="deepseek-chat",
        model_provider="DeepSeek",
    )

    print("Starting scan...")
    result = await scanner.run_full_scan(
        universe=tickers,
        universe_name="manual_scan",
    )

    print(f"\n{'='*60}")
    print(f"Scan Complete!")
    print(f"{'='*60}")
    print(f"Status: {result.status}")
    print(f"Tickers Scanned: {result.tickers_scanned}")
    print(f"High-Conviction Memos: {result.memos_generated}")

    if result.errors:
        print(f"\nErrors ({len(result.errors)}):")
        for error in result.errors[:5]:
            print(f"  - {error}")

    # Submit memos to backend
    if result.high_conviction_memos:
        print(f"\nSubmitting {len(result.high_conviction_memos)} memos to backend...")
        submitted = 0
        for memo in result.high_conviction_memos:
            if submit_memo_to_backend(memo):
                submitted += 1
        print(f"\nSubmitted {submitted}/{len(result.high_conviction_memos)} memos successfully!")
    else:
        print("\nNo high-conviction memos to submit.")

    return result


if __name__ == "__main__":
    import sys

    # Default tickers for a quick test
    tickers = ["AAPL", "MSFT", "NVDA"]

    # Allow override from command line
    if len(sys.argv) > 1:
        tickers = [t.strip().upper() for t in sys.argv[1].split(",")]

    # Use a subset of analysts for faster testing
    analysts = ["warren_buffett", "michael_burry", "peter_lynch"]

    asyncio.run(run_scan(tickers, analysts))
