#!/usr/bin/env python3
"""Start the trading bot dashboard server.

This script starts the Flask dashboard application.

Usage:
    python scripts/start_dashboard.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dashboard.app import app  # noqa: E402
from trading_bot.shared.logging import get_logger  # noqa: E402

logger = get_logger(__name__)


def main() -> int:
    """Start the dashboard server."""
    logger.info("starting_dashboard", host="0.0.0.0", port=5000)
    app.run(debug=True, host="0.0.0.0", port=5000)
    return 0


if __name__ == "__main__":
    sys.exit(main())
