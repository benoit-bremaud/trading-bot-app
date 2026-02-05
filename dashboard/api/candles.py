"""API endpoints for candle data."""

from __future__ import annotations

from flask import Blueprint, jsonify

from trading_bot.infrastructure.csv_candle_repository import (
    CsvCandleRepository,
)
from trading_bot.shared.logging import get_logger

bp = Blueprint("candles", __name__)
logger = get_logger(__name__)


@bp.route("/candles/<symbol>/<timeframe>")
def get_candles(symbol: str, timeframe: str):
    """Get candles for symbol/timeframe.

    Args:
        symbol: Trading pair symbol (e.g., BTC-USDT)
        timeframe: Candle timeframe (e.g., 1h, 4h, 1d)

    Returns:
        JSON array of candles with OHLCV data
    """
    try:
        logger.info("get_candles_request", symbol=symbol, timeframe=timeframe)

        repo = CsvCandleRepository()
        candles = repo.load(symbol, timeframe)

        if not candles:
            logger.warning("no_candles_found", symbol=symbol, timeframe=timeframe)
            return jsonify([])

        # Convert to JSON-serializable format
        data = [
            {
                "timestamp": c.timestamp.isoformat(),
                "open": c.open,
                "high": c.high,
                "low": c.low,
                "close": c.close,
                "volume": c.volume,
            }
            for c in candles
        ]

        logger.info(
            "get_candles_success",
            symbol=symbol,
            timeframe=timeframe,
            count=len(data),
        )
        return jsonify(data)

    except Exception as exc:
        logger.exception(
            "get_candles_failed",
            symbol=symbol,
            timeframe=timeframe,
            error=str(exc),
        )
        return jsonify({"error": str(exc)}), 500
