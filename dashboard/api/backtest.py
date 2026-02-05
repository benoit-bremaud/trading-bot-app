"""API endpoints for backtesting."""

from __future__ import annotations

from flask import Blueprint, jsonify, request

from trading_bot.application.backtest import BuyAndHoldBacktestEngine
from trading_bot.infrastructure.csv_candle_repository import (
    CsvCandleRepository,
)
from trading_bot.shared.logging import get_logger

bp = Blueprint("backtest", __name__)
logger = get_logger(__name__)


@bp.route("/backtest", methods=["POST"])
def run_backtest():
    """Run backtest with given parameters.

    Expected JSON body:
    {
        "symbol": "BTC-USDT",
        "timeframe": "1h",
        "initial_cash": 10000,
        "risk_per_trade": 0.02
    }

    Returns:
        JSON with backtest results (PnL, trades, etc.)
    """
    try:
        params = request.get_json()
        symbol = params.get("symbol", "BTC-USDT")
        timeframe = params.get("timeframe", "1h")
        initial_cash = params.get("initial_cash", 10000.0)

        logger.info(
            "backtest_request",
            symbol=symbol,
            timeframe=timeframe,
            initial_cash=initial_cash,
        )

        # Load candles
        repo = CsvCandleRepository()
        candles = repo.load(symbol, timeframe)

        if not candles:
            return jsonify({"error": "No candles found"}), 404

        # Run backtest (using simple buy-and-hold for now)
        # TODO: Implement proper signal-based backtest engine
        start_date = candles[0].timestamp
        end_date = candles[-1].timestamp

        engine = BuyAndHoldBacktestEngine(
            repository=repo,
            initial_cash=initial_cash,
        )

        result = engine.run(symbol, timeframe, start_date, end_date)

        # Format response
        response = {
            "symbol": result.symbol,
            "timeframe": result.timeframe,
            "start": result.start.isoformat(),
            "end": result.end.isoformat(),
            "initial_cash": result.initial_cash,
            "final_cash": result.final_cash,
            "pnl": result.pnl,
            "return_pct": result.return_pct * 100,  # Convert to percentage
            "trades": result.trades,
        }

        logger.info("backtest_success", **response)
        return jsonify(response)

    except Exception as exc:
        logger.exception("backtest_failed", error=str(exc))
        return jsonify({"error": str(exc)}), 500
