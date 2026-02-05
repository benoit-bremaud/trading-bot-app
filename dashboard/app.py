#!/usr/bin/env python3
"""Flask application for trading bot dashboard.

This dashboard provides a web interface to visualize:
- Historical candle data (candlestick charts)
- Technical indicators (RSI, MACD, Bollinger Bands)
- Trading signals (buy/sell markers)
- Backtest results (PnL, trades, metrics)

Usage:
    python dashboard/app.py
    or
    python scripts/start_dashboard.py
"""

from __future__ import annotations

from flask import Flask, render_template

from dashboard.api import backtest, candles, signals
from trading_bot.shared.logging import get_logger

logger = get_logger(__name__)

app = Flask(__name__)

# Register API blueprints
app.register_blueprint(candles.bp, url_prefix="/api")
app.register_blueprint(signals.bp, url_prefix="/api")
app.register_blueprint(backtest.bp, url_prefix="/api")


@app.route("/")
def index():
    """Render main dashboard page."""
    return render_template("index.html")


@app.route("/health")
def health():
    """Health check endpoint."""
    return {"status": "ok"}


if __name__ == "__main__":
    logger.info("starting_dashboard", host="localhost", port=5000)
    app.run(debug=True, host="0.0.0.0", port=5000)
