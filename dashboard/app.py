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

import os

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


def run_dashboard() -> None:
    """Serve the dashboard. Local-only and without the debugger unless asked for.

    `DASHBOARD_HOST=0.0.0.0` exposes it on the network; `DASHBOARD_DEBUG=1` enables
    the Werkzeug debugger, which allows code execution and must stay off outside
    development.
    """
    host = os.environ.get("DASHBOARD_HOST", "127.0.0.1")
    port = int(os.environ.get("DASHBOARD_PORT", "5000"))
    debug = os.environ.get("DASHBOARD_DEBUG") == "1"
    logger.info("starting_dashboard", host=host, port=port, debug=debug)
    app.run(debug=debug, host=host, port=port)


if __name__ == "__main__":
    run_dashboard()
