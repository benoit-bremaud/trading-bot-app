#!/usr/bin/env python3
"""CLI script to ingest candles from KuCoin and save to CSV repository.

This script fetches OHLCV candles for a given symbol and timeframe,
then stores them in the local CSV repository for later use in backtesting
or analysis.

Usage:
    python scripts/ingest_candles.py --symbol BTC-USDT --timeframe 1h --days 7
"""

from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime, timedelta

from trading_bot.infrastructure.csv_candle_repository import CsvCandleRepository
from trading_bot.infrastructure.kucoin_market_data import KucoinMarketDataProvider
from trading_bot.shared.logging import get_logger


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Ingest candles from KuCoin and save to CSV repository"
    )
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
        default=7,
        help="Number of days to fetch (default: 7)",
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
        "ingest_start",
        symbol=args.symbol,
        timeframe=args.timeframe,
        days=args.days,
    )

    try:
        provider = KucoinMarketDataProvider()
        repository = CsvCandleRepository(base_dir=args.base_dir)

        end = datetime.now(tz=UTC)
        start = end - timedelta(days=args.days)

        logger.info("fetching_candles", start=start.isoformat(), end=end.isoformat())
        candles = provider.get_ohlcv(args.symbol, args.timeframe, start, end)

        if not candles:
            logger.warning("no_candles_fetched")
            return 1

        logger.info("saving_candles", count=len(candles))
        repository.save(args.symbol, args.timeframe, candles)

        logger.info(
            "ingest_complete",
            count=len(candles),
            first=candles[0].timestamp.isoformat(),
            last=candles[-1].timestamp.isoformat(),
        )
        return 0

    except Exception as exc:
        logger.exception("ingest_failed", error=str(exc))
        return 1


if __name__ == "__main__":
    sys.exit(main())
