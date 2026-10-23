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

from trading_bot.application.indicators import IndicatorPipeline
from trading_bot.application.risk_manager import BaselineRiskManager
from trading_bot.application.signal_model import (
    IndicatorBasedSignalModel,
)
from trading_bot.application.trading_safety import (
    IdempotencyGuard,
    RiskPolicy,
    TradingSafetyController,
    TradingSafetyState,
)
from trading_bot.domain.entities import PairProfile
from trading_bot.infrastructure.indicators import (
    BollingerBandsCalculator,
    DefaultIndicatorPipeline,
    MACDCalculator,
    RSICalculator,
)
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
    parser.add_argument(
        "--kill-switch",
        action="store_true",
        help="Immediately block entries and close open positions",
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
        signal_cfg = pair_config.get("signal", {})
        signal_model = IndicatorBasedSignalModel(
            entry_threshold=float(
                signal_cfg.get("entry_threshold", signal_cfg.get("threshold", 0.6))
            ),
            rsi_oversold=float(signal_cfg.get("rsi_oversold", 30.0)),
            rsi_overbought=float(signal_cfg.get("rsi_overbought", 70.0)),
            use_macd=bool(signal_cfg.get("use_macd", True)),
            use_bollinger=bool(signal_cfg.get("use_bollinger", True)),
        )
        indicator_pipeline: IndicatorPipeline = DefaultIndicatorPipeline()
        indicator_pipeline.add_indicator(
            RSICalculator(period=int(signal_cfg.get("rsi_period", 14)))
        )
        indicator_pipeline.add_indicator(
            MACDCalculator(
                fast=int(signal_cfg.get("macd_fast", 12)),
                slow=int(signal_cfg.get("macd_slow", 26)),
                signal=int(signal_cfg.get("macd_signal", 9)),
            )
        )
        indicator_pipeline.add_indicator(
            BollingerBandsCalculator(
                period=int(signal_cfg.get("bb_period", 20)),
                std_dev=float(signal_cfg.get("bb_std_dev", 2.0)),
            )
        )

        risk_cfg = pair_config.get("risk", {})

        # Configure risk manager
        max_position_pct = float(
            risk_cfg.get(
                "max_position_pct",
                pair_config.get("max_position_pct", 0.02),
            )
        )
        max_total_exposure_pct = float(
            risk_cfg.get(
                "max_total_exposure_pct",
                pair_config.get("max_total_exposure_pct", max_position_pct),
            )
        )
        max_daily_loss_pct = float(
            risk_cfg.get(
                "max_daily_loss_pct",
                pair_config.get("max_daily_loss_pct", 0.03),
            )
        )
        max_open_positions = int(
            risk_cfg.get(
                "max_open_positions",
                pair_config.get("max_open_positions", 1),
            )
        )
        stop_loss_pct = float(
            risk_cfg.get(
                "stop_loss_pct",
                pair_config.get("stop_loss_pct", 0.03),
            )
        )
        kill_switch_cfg = bool(pair_config.get("kill_switch", False))
        kill_switch_enabled = args.kill_switch or kill_switch_cfg

        use_volatility = pair_config.get("use_volatility_sizing", False)
        risk_manager = BaselineRiskManager(
            max_position_pct=max_position_pct,
            volatility_target=0.02 if use_volatility else None,
        )
        policy = RiskPolicy(
            max_position_pct=max_position_pct,
            max_total_exposure_pct=max_total_exposure_pct,
            max_daily_loss_pct=max_daily_loss_pct,
            max_open_positions=max_open_positions,
        )
        safety = TradingSafetyState(policy=policy)
        controller = TradingSafetyController(
            safety=safety,
            idempotency=IdempotencyGuard(),
            kill_switch=kill_switch_enabled,
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
        print(f"Kill Switch:   {'ON' if kill_switch_enabled else 'OFF'}")
        print("=" * 60)
        print("\nPress Ctrl+C to stop.\n")

        iteration = 0
        stop_loss_by_symbol: dict[str, float] = {}
        entry_price_by_symbol: dict[str, float] = {}
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

            avg_volume = sum(c.volume for c in candles) / len(candles)
            profile = PairProfile(
                symbol=args.symbol,
                timeframe=args.timeframe,
                avg_volume=avg_volume,
                volatility=volatility,
            )

            # Generate signal
            enriched = indicator_pipeline.enrich(candles)
            score = signal_model.score(enriched, profile)
            is_entry = signal_model.is_entry(score)

            current_price = candles[-1].close
            position = executor.positions.get(args.symbol, 0.0)
            current_exposure = abs(position * current_price)
            current_equity = executor.cash + current_exposure
            safety.sync_day(candles[-1].timestamp, current_equity)

            stop_loss_price = stop_loss_by_symbol.get(args.symbol)
            stop_loss_triggered = (
                position > 0 and stop_loss_price is not None and current_price <= stop_loss_price
            )

            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]")
            print(f"  Price: ${current_price:,.2f}")
            print(f"  Signal Score: {score:.4f}")
            print(f"  Position: {position:.6f}")
            print(f"  Cash: ${executor.cash:,.2f}")
            print(f"  Daily PnL: {safety.daily_realized_pnl:.2f}")

            # Execute trading logic
            if controller.should_force_exit() and position > 0:
                key = controller.make_key(
                    args.symbol,
                    args.timeframe,
                    candles[-1].timestamp,
                    "kill_switch_exit",
                )
                if controller.can_exit(key):
                    print(f"  🛑 KILL-SWITCH EXIT: {position:.6f} units")
                    logger.warning(
                        "kill_switch_exit",
                        symbol=args.symbol,
                        size=-position,
                        price=current_price,
                    )
                    if not args.dry_run:
                        executor.place_market_order(args.symbol, -position)
                        entry_price = entry_price_by_symbol.get(args.symbol, current_price)
                        realized_pnl = (current_price - entry_price) * position
                        safety.on_exit(realized_pnl)
                        entry_price_by_symbol.pop(args.symbol, None)
                        stop_loss_by_symbol.pop(args.symbol, None)
                        print("  ✅ Order executed")
            elif stop_loss_triggered and position > 0:
                key = controller.make_key(
                    args.symbol,
                    args.timeframe,
                    candles[-1].timestamp,
                    "stop_loss_exit",
                )
                if controller.can_exit(key):
                    print(f"  🧯 STOP-LOSS EXIT: {position:.6f} units")
                    logger.warning(
                        "stop_loss_exit",
                        symbol=args.symbol,
                        size=-position,
                        price=current_price,
                        stop_loss=stop_loss_price,
                    )
                    if not args.dry_run:
                        executor.place_market_order(args.symbol, -position)
                        entry_price = entry_price_by_symbol.get(args.symbol, current_price)
                        realized_pnl = (current_price - entry_price) * position
                        safety.on_exit(realized_pnl)
                        entry_price_by_symbol.pop(args.symbol, None)
                        stop_loss_by_symbol.pop(args.symbol, None)
                        print("  ✅ Order executed")
            elif is_entry and position == 0:
                # Entry signal and no position -> BUY
                key = controller.make_key(
                    args.symbol,
                    args.timeframe,
                    candles[-1].timestamp,
                    "buy_entry",
                )
                can_open, reason = controller.can_enter(
                    current_equity,
                    current_exposure,
                    key,
                )
                if not can_open:
                    logger.info("entry_blocked", reason=reason)
                target_notional = risk_manager.position_size(profile, current_equity, score)
                max_notional = safety.max_entry_notional(current_equity, current_exposure)
                entry_notional = min(target_notional, max_notional)
                size = entry_notional / current_price if current_price > 0 else 0.0

                if size > 0 and can_open:
                    print(f"  📈 BUY SIGNAL: {size:.6f} units ({entry_notional:.2f} quote)")
                    logger.info(
                        "buy_signal",
                        symbol=args.symbol,
                        size=size,
                        price=current_price,
                    )
                    if not args.dry_run:
                        executor.place_market_order(args.symbol, size)
                        entry_price_by_symbol[args.symbol] = current_price
                        stop_loss_by_symbol[args.symbol] = current_price * (1 - stop_loss_pct)
                        safety.on_entry()
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
                key = controller.make_key(
                    args.symbol,
                    args.timeframe,
                    candles[-1].timestamp,
                    "signal_exit",
                )
                if not args.dry_run and controller.can_exit(key):
                    executor.place_market_order(args.symbol, -position)
                    entry_price = entry_price_by_symbol.get(args.symbol, current_price)
                    realized_pnl = (current_price - entry_price) * position
                    safety.on_exit(realized_pnl)
                    entry_price_by_symbol.pop(args.symbol, None)
                    stop_loss_by_symbol.pop(args.symbol, None)
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
