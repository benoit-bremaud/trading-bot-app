#!/usr/bin/env python3
"""CLI script to run the trading bot in paper trading mode.

This script simulates live trading by fetching recent candles,
generating signals, and executing paper trades.

Usage:
    python scripts/run.py --symbol BTC-USDT --timeframe 1h --cash 10000
"""

from __future__ import annotations

import argparse
import sys
import time
from datetime import UTC, datetime, timedelta

from trading_bot.application.risk_manager import BaselineRiskManager
from trading_bot.application.signal_model import (
    MovingAverageCrossoverSignalModel,
)
from trading_bot.domain.entities import PairProfile
from trading_bot.infrastructure.kucoin_market_data import (
    KucoinMarketDataProvider,
)
from trading_bot.infrastructure.paper_order_executor import (
    PaperOrderExecutor,
)
from trading_bot.shared.config import load_config
from trading_bot.shared.logging import get_logger


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the trading bot in paper trading mode")
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
        "--cash",
        type=float,
        default=10000.0,
        help="Initial cash for paper trading (default: 10000.0)",
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config/config.example.json",
        help="Path to config file (default: config/config.example.json)",
    )
    parser.add_argument(
        "--lookback-days",
        type=int,
        default=7,
        help="Days of history to fetch for signal (default: 7)",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Check interval in seconds (default: 60)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Display signals without executing trades",
    )

    args = parser.parse_args()

    logger = get_logger(__name__)
    logger.info(
        "paper_trading_start",
        symbol=args.symbol,
        timeframe=args.timeframe,
        initial_cash=args.cash,
        dry_run=args.dry_run,
    )

    try:
        # Load configuration
        config = load_config(args.config)
        pair_config = config.for_pair(args.symbol, args.timeframe)

        # Setup components
        market_data = KucoinMarketDataProvider()
        signal_model = MovingAverageCrossoverSignalModel(
            short_window=pair_config.get("signal_short_window", 10),
            long_window=pair_config.get("signal_long_window", 30),
        )

        # Configure risk manager
        max_position_pct = pair_config.get("max_position_pct", 0.02)
        use_volatility = pair_config.get("use_volatility_sizing", False)
        risk_manager = BaselineRiskManager(
            max_position_pct=max_position_pct,
            volatility_target=0.02 if use_volatility else None,
        )

        # Price getter for paper executor
        def price_getter(symbol: str) -> float:
            end = datetime.now(tz=UTC)
            start = end - timedelta(minutes=5)
            candles = market_data.get_ohlcv(symbol, "1m", start, end)
            if not candles:
                raise ValueError(f"No recent price data for {symbol}")
            return candles[-1].close

        executor = PaperOrderExecutor(
            initial_cash=args.cash,
            price_getter=price_getter,
        )

        print("\n" + "=" * 60)
        print("🤖 PAPER TRADING BOT STARTED")
        print("=" * 60)
        print(f"Symbol:        {args.symbol}")
        print(f"Timeframe:     {args.timeframe}")
        print(f"Initial Cash:  ${args.cash:,.2f}")
        print(f"Check Every:   {args.interval}s")
        print(f"Mode:          {'DRY RUN' if args.dry_run else 'LIVE PAPER'}")
        print("=" * 60)
        print("\nPress Ctrl+C to stop.\n")

        iteration = 0
        while True:
            iteration += 1
            logger.info("iteration_start", iteration=iteration)

            # Fetch recent candles
            end = datetime.now(tz=UTC)
            start = end - timedelta(days=args.lookback_days)
            candles = market_data.get_ohlcv(args.symbol, args.timeframe, start, end)

            if not candles:
                logger.warning("no_candles", iteration=iteration)
                time.sleep(args.interval)
                continue

            # Calculate profile for risk manager
            prices = [c.close for c in candles]
            returns = [(prices[i] - prices[i - 1]) / prices[i - 1] for i in range(1, len(prices))]
            volatility = (sum(r * r for r in returns) / len(returns)) ** 0.5 if returns else 0.0

            profile = PairProfile(
                symbol=args.symbol,
                timeframe=args.timeframe,
                avg_volume=sum(c.volume for c in candles) / len(candles),
                volatility=volatility,
            )

            # Generate signal
            score = signal_model.score(candles, profile)
            is_entry = signal_model.is_entry(score)

            current_price = candles[-1].close
            position = executor.positions.get(args.symbol, 0.0)

            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]")
            print(f"  Price: ${current_price:,.2f}")
            print(f"  Signal Score: {score:.4f}")
            print(f"  Position: {position:.6f}")
            print(f"  Cash: ${executor.cash:,.2f}")

            # Execute trading logic
            if is_entry and position == 0:
                # Entry signal and no position -> BUY
                size = risk_manager.position_size(profile, executor.cash, score)
                if size > 0:
                    print(f"  📈 BUY SIGNAL: {size:.6f} units")
                    logger.info(
                        "buy_signal",
                        symbol=args.symbol,
                        size=size,
                        price=current_price,
                    )
                    if not args.dry_run:
                        executor.place_market_order(args.symbol, size)
                        print("  ✅ Order executed")
            elif not is_entry and position > 0:
                # Exit signal and have position -> SELL
                print(f"  📉 SELL SIGNAL: {position:.6f} units")
                logger.info(
                    "sell_signal",
                    symbol=args.symbol,
                    size=-position,
                    price=current_price,
                )
                if not args.dry_run:
                    executor.place_market_order(args.symbol, -position)
                    print("  ✅ Order executed")

            print(f"  Total Trades: {len(executor.trades)}")
            print()

            logger.info(
                "iteration_complete",
                iteration=iteration,
                score=score,
                is_entry=is_entry,
                position=position,
            )

            # Wait for next iteration
            time.sleep(args.interval)

    except KeyboardInterrupt:
        print("\n\n" + "=" * 60)
        print("🛑 STOPPING PAPER TRADING BOT")
        print("=" * 60)
        logger.info("paper_trading_stopped")

        if not args.dry_run:
            print(f"Final Cash:    ${executor.cash:,.2f}")
            print(f"Positions:     {executor.positions}")
            print(f"Total Trades:  {len(executor.trades)}")
        print("=" * 60 + "\n")
        return 0

    except Exception as exc:
        logger.exception("paper_trading_failed", error=str(exc))
        print(f"\n❌ Paper trading failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
