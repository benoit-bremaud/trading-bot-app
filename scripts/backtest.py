#!/usr/bin/env python3
"""CLI script to run a backtest on historical data.

This script loads candles from the CSV repository and executes
a simulated buy-and-hold trading session with detailed results.

Usage:
    python scripts/backtest.py --symbol BTC-USDT --timeframe 1h \
        --days 30 --cash 10000
"""

from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime, timedelta

from trading_bot.application.backtest import BuyAndHoldBacktestEngine
from trading_bot.infrastructure.csv_candle_repository import (
    CsvCandleRepository,
)
from trading_bot.shared.logging import get_logger


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a backtest on historical candle data")
    parser.add_argument(
        "--symbol",
        type=str,
        default="BTC-USDT",
        help="Trading pair symbol (default: BTC-USDT)",
    )
    parser.add_argument(
        "--timeframe",
        type=str,
        default="1h",
        help="Candle timeframe (default: 1h)",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Number of days to backtest (default: 30)",
    )
    parser.add_argument(
        "--cash",
        type=float,
        default=10000.0,
        help="Initial cash for the backtest (default: 10000.0)",
    )
    parser.add_argument(
        "--base-dir",
        type=str,
        default="data/candles",
        help="Base directory for CSV storage (default: data/candles)",
    )

    args = parser.parse_args()

    logger = get_logger(__name__)
    logger.info(
        "backtest_start",
        symbol=args.symbol,
        timeframe=args.timeframe,
        days=args.days,
        initial_cash=args.cash,
    )

    try:
        # Setup components
        repository = CsvCandleRepository(base_dir=args.base_dir)

        # Setup backtest engine (buy-and-hold strategy)
        engine = BuyAndHoldBacktestEngine(
            repository=repository,
            initial_cash=args.cash,
        )

        # Calculate time range
        end = datetime.now(tz=UTC)
        start = end - timedelta(days=args.days)

        logger.info(
            "running_backtest",
            start=start.isoformat(),
            end=end.isoformat(),
        )

        # Run backtest
        result = engine.run(
            symbol=args.symbol,
            timeframe=args.timeframe,
            start=start,
            end=end,
        )

        # Display results
        logger.info(
            "backtest_complete",
            symbol=result.symbol,
            timeframe=result.timeframe,
            initial_cash=result.initial_cash,
            final_cash=result.final_cash,
            pnl=result.pnl,
            return_pct=result.return_pct,
            trades=result.trades,
        )

        print("\n" + "=" * 60)
        print("BACKTEST RESULTS")
        print("=" * 60)
        print(f"Symbol:        {result.symbol}")
        print(f"Timeframe:     {result.timeframe}")
        print(f"Period:        {result.start.date()} to {result.end.date()}")
        print(f"Initial Cash:  ${result.initial_cash:,.2f}")
        print(f"Final Cash:    ${result.final_cash:,.2f}")
        print(f"PnL:           ${result.pnl:,.2f}")
        print(f"Return:        {result.return_pct:.2f}%")
        print(f"Trades:        {result.trades}")
        print("=" * 60 + "\n")

        return 0

    except FileNotFoundError as exc:
        logger.exception("backtest_failed", error=str(exc))
        print(
            f"\n❌ Backtest failed: {exc}\nHint: Run 'python scripts/ingest_candles.py' first.",
            file=sys.stderr,
        )
        return 1
    except Exception as exc:
        logger.exception("backtest_failed", error=str(exc))
        print(f"\n❌ Backtest failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
