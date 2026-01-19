#!/usr/bin/env python
"""
CLI command for running the stock scanner.

Usage:
    python -m src.cli.scan --tickers AAPL,MSFT --analysts warren_buffett,michael_burry
    python -m src.cli.scan --universe sp500 --analysts-preset value
    python -m src.cli.scan --tickers AAPL --all-analysts
    python -m src.cli.scan --sector technology --conviction 75
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from colorama import Fore, Style, init
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from src.services.scanner import (
    Scanner,
    ScanConfig,
    ScanResult,
    load_universe_config,
    load_scanner_config,
    get_universe_tickers,
    get_sector_tickers,
    save_scan_result,
    DEFAULT_ANALYSTS,
)
from src.utils.analysts import ANALYST_CONFIG

# Initialize colorama
init(autoreset=True)

# Rich console for pretty output
console = Console()


def get_analyst_preset(preset_name: str, scanner_config: dict) -> list[str]:
    """Get list of analysts for a preset configuration."""
    analysts_config = scanner_config.get("analysts", {})
    return analysts_config.get(preset_name, DEFAULT_ANALYSTS)


def parse_tickers(tickers_str: str) -> list[str]:
    """Parse comma-separated tickers string."""
    if not tickers_str:
        return []
    return [t.strip().upper() for t in tickers_str.split(",") if t.strip()]


def parse_analysts(analysts_str: str) -> list[str]:
    """Parse comma-separated analysts string."""
    if not analysts_str:
        return []
    return [a.strip().lower() for a in analysts_str.split(",") if a.strip()]


def display_results_table(result: ScanResult):
    """Display scan results in a rich table."""
    table = Table(title=f"Scan Results - {result.universe_name}")

    table.add_column("Ticker", style="cyan", no_wrap=True)
    table.add_column("Analyst", style="magenta")
    table.add_column("Signal", style="bold")
    table.add_column("Conviction", justify="right")
    table.add_column("Price", justify="right", style="green")
    table.add_column("Target", justify="right", style="yellow")
    table.add_column("Thesis")

    for memo in result.high_conviction_memos:
        signal = memo.get("signal", "")
        signal_style = "green" if signal == "bullish" else "red"

        conviction = memo.get("conviction", 0)
        conviction_style = "green bold" if conviction >= 80 else "yellow"

        table.add_row(
            memo.get("ticker", ""),
            memo.get("analyst", "")[:20],
            f"[{signal_style}]{signal.upper()}[/{signal_style}]",
            f"[{conviction_style}]{conviction}%[/{conviction_style}]",
            f"${memo.get('current_price', 0):.2f}",
            f"${memo.get('target_price', 0):.2f}",
            memo.get("thesis", "")[:50] + "..." if len(memo.get("thesis", "")) > 50 else memo.get("thesis", ""),
        )

    console.print(table)


def display_summary(result: ScanResult):
    """Display scan summary."""
    duration = None
    if result.end_time and result.start_time:
        duration = (result.end_time - result.start_time).total_seconds()

    console.print("\n[bold]Scan Summary[/bold]")
    console.print(f"  Universe: {result.universe_name}")
    console.print(f"  Status: {result.status}")
    console.print(f"  Tickers Scanned: {result.tickers_scanned}/{result.total_tickers}")
    console.print(f"  High-Conviction Memos: {result.memos_generated}")
    console.print(f"  Analysts Used: {', '.join(result.analysts_used)}")
    console.print(f"  Conviction Threshold: {result.conviction_threshold}%")

    if duration:
        console.print(f"  Duration: {duration:.1f} seconds")
        if result.avg_processing_time_per_ticker:
            console.print(f"  Avg Time/Ticker: {result.avg_processing_time_per_ticker:.2f} seconds")

    if result.errors:
        console.print(f"\n[red]Errors ({len(result.errors)}):[/red]")
        for error in result.errors[:5]:  # Show first 5 errors
            console.print(f"  - {error}")
        if len(result.errors) > 5:
            console.print(f"  ... and {len(result.errors) - 5} more")


def list_analysts():
    """List all available analysts."""
    table = Table(title="Available Analysts")

    table.add_column("Key", style="cyan")
    table.add_column("Name", style="magenta")
    table.add_column("Description", style="dim")

    for key, config in sorted(ANALYST_CONFIG.items(), key=lambda x: x[1].get("order", 0)):
        table.add_row(
            key,
            config.get("display_name", ""),
            config.get("description", ""),
        )

    console.print(table)


def list_universes(universe_config: dict):
    """List available universes and their sizes."""
    table = Table(title="Available Universes")

    table.add_column("Name", style="cyan")
    table.add_column("Tickers", justify="right", style="green")
    table.add_column("Sample Tickers")

    for key in ["sp500", "russell2000_sample", "custom"]:
        tickers = universe_config.get(key, [])
        sample = ", ".join(tickers[:5]) + ("..." if len(tickers) > 5 else "")
        table.add_row(key, str(len(tickers)), sample)

    # Sectors
    sectors = universe_config.get("sectors", {})
    for sector, tickers in sectors.items():
        sample = ", ".join(tickers[:5]) + ("..." if len(tickers) > 5 else "")
        table.add_row(f"sector:{sector}", str(len(tickers)), sample)

    console.print(table)


async def run_scan_async(
    tickers: list[str],
    analysts: list[str],
    universe_name: str,
    conviction_threshold: int,
    model_name: str,
    model_provider: str,
    save_results: bool,
    output_file: Optional[str],
) -> ScanResult:
    """Run the scan asynchronously."""
    config = ScanConfig(conviction_threshold=conviction_threshold)

    scanner = Scanner(
        config=config,
        analysts=analysts,
        model_name=model_name,
        model_provider=model_provider,
    )

    console.print(f"\n[bold]Starting scan...[/bold]")
    console.print(f"  Tickers: {len(tickers)}")
    console.print(f"  Analysts: {', '.join(analysts)}")
    console.print(f"  Conviction Threshold: {conviction_threshold}%\n")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]Scanning...", total=len(tickers))

        # Run the scan
        result = await scanner.run_full_scan(
            universe=tickers,
            universe_name=universe_name,
        )

        progress.update(task, completed=len(tickers))

    # Display results
    if result.high_conviction_memos:
        display_results_table(result)
    else:
        console.print("\n[yellow]No high-conviction opportunities found.[/yellow]")

    display_summary(result)

    # Save results
    if save_results:
        if output_file:
            filepath = output_file
            with open(filepath, "w") as f:
                json.dump(result.model_dump(), f, indent=2, default=str)
        else:
            filepath = save_scan_result(result)
        console.print(f"\n[green]Results saved to: {filepath}[/green]")

    return result


def main():
    """Main entry point for the scan CLI."""
    parser = argparse.ArgumentParser(
        description="Stock Scanner - Identify high-conviction investment opportunities",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scan specific tickers with specific analysts
  python -m src.cli.scan --tickers AAPL,MSFT,GOOGL --analysts warren_buffett,charlie_munger

  # Scan entire S&P 500 with default analysts
  python -m src.cli.scan --universe sp500

  # Scan a sector with all analysts
  python -m src.cli.scan --sector technology --all-analysts

  # Scan with higher conviction threshold
  python -m src.cli.scan --tickers AAPL --conviction 80

  # List available analysts
  python -m src.cli.scan --list-analysts

  # List available universes
  python -m src.cli.scan --list-universes
        """,
    )

    # Ticker selection
    ticker_group = parser.add_mutually_exclusive_group()
    ticker_group.add_argument(
        "--tickers", "-t",
        type=str,
        help="Comma-separated list of stock tickers (e.g., AAPL,MSFT,GOOGL)",
    )
    ticker_group.add_argument(
        "--universe", "-u",
        type=str,
        choices=["sp500", "russell2000_sample", "custom"],
        help="Predefined universe of stocks to scan",
    )
    ticker_group.add_argument(
        "--sector", "-s",
        type=str,
        choices=["technology", "healthcare", "financials", "consumer", "energy", "industrials"],
        help="Scan stocks in a specific sector",
    )

    # Analyst selection
    analyst_group = parser.add_mutually_exclusive_group()
    analyst_group.add_argument(
        "--analysts", "-a",
        type=str,
        help="Comma-separated list of analyst keys (e.g., warren_buffett,michael_burry)",
    )
    analyst_group.add_argument(
        "--analysts-preset", "-p",
        type=str,
        choices=["default", "growth", "value", "technical", "full"],
        help="Use a preset group of analysts",
    )
    analyst_group.add_argument(
        "--all-analysts",
        action="store_true",
        help="Use all available analysts",
    )

    # Scan configuration
    parser.add_argument(
        "--conviction", "-c",
        type=int,
        default=70,
        help="Minimum conviction threshold (0-100, default: 70)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="gpt-4.1",
        help="LLM model to use (default: gpt-4.1)",
    )
    parser.add_argument(
        "--provider",
        type=str,
        default="OpenAI",
        help="LLM provider (default: OpenAI)",
    )

    # Output options
    parser.add_argument(
        "--output", "-o",
        type=str,
        help="Output file path for results (JSON)",
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Don't save results to file",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON to stdout",
    )

    # List commands
    parser.add_argument(
        "--list-analysts",
        action="store_true",
        help="List all available analysts",
    )
    parser.add_argument(
        "--list-universes",
        action="store_true",
        help="List available universes and sectors",
    )

    args = parser.parse_args()

    # Handle list commands
    if args.list_analysts:
        list_analysts()
        return

    universe_config = load_universe_config()

    if args.list_universes:
        list_universes(universe_config)
        return

    # Determine tickers to scan
    tickers = []
    universe_name = "custom"

    if args.tickers:
        tickers = parse_tickers(args.tickers)
        universe_name = "custom"
    elif args.universe:
        tickers = get_universe_tickers(universe_config, [args.universe])
        universe_name = args.universe
    elif args.sector:
        tickers = get_sector_tickers(universe_config, args.sector)
        universe_name = f"sector_{args.sector}"
    else:
        console.print("[red]Error: Must specify --tickers, --universe, or --sector[/red]")
        parser.print_help()
        sys.exit(1)

    if not tickers:
        console.print("[red]Error: No tickers found to scan[/red]")
        sys.exit(1)

    # Determine analysts to use
    scanner_config_data = {}
    try:
        import yaml
        config_path = Path(__file__).resolve().parent.parent.parent / "config" / "scanner.yaml"
        with open(config_path) as f:
            scanner_config_data = yaml.safe_load(f)
    except Exception:
        pass

    if args.analysts:
        analysts = parse_analysts(args.analysts)
    elif args.analysts_preset:
        analysts = get_analyst_preset(args.analysts_preset, scanner_config_data)
    elif args.all_analysts:
        analysts = list(ANALYST_CONFIG.keys())
    else:
        analysts = DEFAULT_ANALYSTS

    # Validate analysts
    valid_analysts = [a for a in analysts if a in ANALYST_CONFIG]
    if not valid_analysts:
        console.print(f"[red]Error: No valid analysts specified[/red]")
        console.print(f"Available analysts: {', '.join(ANALYST_CONFIG.keys())}")
        sys.exit(1)

    if len(valid_analysts) != len(analysts):
        invalid = set(analysts) - set(valid_analysts)
        console.print(f"[yellow]Warning: Ignoring invalid analysts: {', '.join(invalid)}[/yellow]")

    # Run the scan
    try:
        result = asyncio.run(run_scan_async(
            tickers=tickers,
            analysts=valid_analysts,
            universe_name=universe_name,
            conviction_threshold=args.conviction,
            model_name=args.model,
            model_provider=args.provider,
            save_results=not args.no_save,
            output_file=args.output,
        ))

        # JSON output if requested
        if args.json:
            print(json.dumps(result.model_dump(), indent=2, default=str))

        # Exit with error code if scan failed
        if result.status == "failed":
            sys.exit(1)

    except KeyboardInterrupt:
        console.print("\n[yellow]Scan cancelled by user[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
