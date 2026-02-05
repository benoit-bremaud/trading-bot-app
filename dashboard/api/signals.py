"""API endpoints for trading signals."""

from __future__ import annotations

from dataclasses import dataclass

from flask import Blueprint, jsonify

from trading_bot.application.signal_model import IndicatorBasedSignalModel
from trading_bot.domain.entities import PairProfile
from trading_bot.infrastructure.csv_candle_repository import (
    CsvCandleRepository,
)
from trading_bot.infrastructure.indicators import DefaultIndicatorPipeline
from trading_bot.shared.logging import get_logger

bp = Blueprint("signals", __name__)
logger = get_logger(__name__)


@dataclass
class SignalData:
    """Data class for API signal response."""

    signal_type: str
    confidence: float
    reason: str


@bp.route("/signals/<symbol>/<timeframe>")
def get_signals(symbol: str, timeframe: str):
    """Generate trading signals for symbol/timeframe.

    Args:
        symbol: Trading pair symbol (e.g., BTC-USDT)
        timeframe: Candle timeframe (e.g., 1h, 4h, 1d)

    Returns:
        JSON array of signals with timestamp, type, and price
    """
    try:
        logger.info("get_signals_request", symbol=symbol, timeframe=timeframe)

        # Load candles
        repo = CsvCandleRepository()
        candles = repo.load(symbol, timeframe)

        if not candles:
            logger.warning("no_candles_found", symbol=symbol, timeframe=timeframe)
            return jsonify([])

        # Enrich with indicators
        pipeline = DefaultIndicatorPipeline()
        enriched_candles = pipeline.enrich(candles)

        # Generate signals using signal model
        signal_model = IndicatorBasedSignalModel()
        signals = []

        # Calculate profile for signal model
        if len(enriched_candles) < 2:
            return jsonify([])

        prices = [c.candle.close for c in enriched_candles]
        returns = [(prices[i] - prices[i - 1]) / prices[i - 1] for i in range(1, len(prices))]
        volatility = (sum(r * r for r in returns) / len(returns)) ** 0.5 if returns else 0.0

        profile = PairProfile(
            symbol=symbol,
            timeframe=timeframe,
            avg_volume=sum(c.candle.volume for c in enriched_candles) / len(enriched_candles),
            volatility=volatility,
        )

        # Generate signals at each timestamp
        for i in range(20, len(enriched_candles)):  # Skip first 20 for indicators
            window = enriched_candles[: i + 1]
            score = signal_model.score(window, profile)
            is_entry = signal_model.is_entry(score)

            candle = enriched_candles[i]

            # Check for signal change (buy or sell)
            if i > 20:
                prev_window = enriched_candles[:i]
                prev_score = signal_model.score(prev_window, profile)
                prev_is_entry = signal_model.is_entry(prev_score)

                # Buy signal: entry triggered
                if is_entry and not prev_is_entry:
                    signals.append(
                        {
                            "timestamp": candle.candle.timestamp.isoformat(),
                            "type": "buy",
                            "price": candle.candle.close,
                            "confidence": score,
                            "reason": f"Entry signal (score: {score:.2f})",
                        }
                    )
                # Sell signal: exit triggered
                elif not is_entry and prev_is_entry:
                    signals.append(
                        {
                            "timestamp": candle.candle.timestamp.isoformat(),
                            "type": "sell",
                            "price": candle.candle.close,
                            "confidence": 1 - score,
                            "reason": f"Exit signal (score: {score:.2f})",
                        }
                    )

        logger.info(
            "get_signals_success",
            symbol=symbol,
            timeframe=timeframe,
            count=len(signals),
        )
        return jsonify(signals)

    except Exception as exc:
        logger.exception(
            "get_signals_failed",
            symbol=symbol,
            timeframe=timeframe,
            error=str(exc),
        )
        return jsonify({"error": str(exc)}), 500
