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

Binds to 127.0.0.1:5000 by default; see `run_dashboard` for the DASHBOARD_* variables.
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


_LOOPBACK_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})


def run_dashboard() -> None:
    """Serve the dashboard. Local-only and without the debugger unless asked for.

    Environment: `DASHBOARD_HOST` (default `127.0.0.1`; `0.0.0.0` exposes it on the
    network), `DASHBOARD_PORT` (default 5000), `DASHBOARD_DEBUG` (debugger only when
    exactly `"1"`). The Werkzeug debugger allows code execution, so it is refused on a
    non-loopback host.

    Raises SystemExit on an invalid port or on debug with a non-loopback host.
    """
    host = os.environ.get("DASHBOARD_HOST", "127.0.0.1")
    raw_port = os.environ.get("DASHBOARD_PORT", "5000")
    try:
        port = int(raw_port)
    except ValueError:
        raise SystemExit(f"DASHBOARD_PORT must be an integer, got {raw_port!r}") from None
    debug = os.environ.get("DASHBOARD_DEBUG") == "1"
    if debug and host not in _LOOPBACK_HOSTS:
        raise SystemExit(f"DASHBOARD_DEBUG=1 is only allowed on a loopback host, not {host!r}")
    logger.info("starting_dashboard", host=host, port=port, debug=debug)
    app.run(debug=debug, host=host, port=port)


if __name__ == "__main__":
    run_dashboard()
