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

from dashboard.app import run_dashboard  # noqa: E402


def main() -> int:
    """Start the dashboard server (see `run_dashboard` for the environment variables)."""
    run_dashboard()
    return 0


if __name__ == "__main__":
    sys.exit(main())
