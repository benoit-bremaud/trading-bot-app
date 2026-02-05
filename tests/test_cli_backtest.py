"""Tests for the backtest CLI script."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_backtest_cli_help():
    """Test that backtest.py --help returns successfully."""
    result = subprocess.run(
        [sys.executable, "scripts/backtest.py", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "Run a backtest on historical candle data" in result.stdout


def test_backtest_cli_without_data_fails():
    """Test that backtest.py fails gracefully when no data is available."""
    # Use a non-existent base directory to ensure no data is found
    result = subprocess.run(
        [
            sys.executable,
            "scripts/backtest.py",
            "--symbol",
            "BTC-USDT",
            "--timeframe",
            "1h",
            "--days",
            "7",
            "--cash",
            "1000",
            "--base-dir",
            "data/nonexistent",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1
    # Should fail due to missing data
    assert "Backtest failed" in result.stderr or "No such file" in result.stderr


def test_backtest_script_exists():
    """Ensure the backtest script file exists and is readable."""
    script_path = Path("scripts/backtest.py")
    assert script_path.exists()
    assert script_path.is_file()
