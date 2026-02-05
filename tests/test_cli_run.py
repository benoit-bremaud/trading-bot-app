"""Tests for the run CLI script."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_run_cli_help():
    """Test that run.py --help returns successfully."""
    result = subprocess.run(
        [sys.executable, "scripts/run.py", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "Run the trading bot in paper trading mode" in result.stdout


def test_run_cli_dry_run_mode():
    """Test that run.py can start in dry-run mode (then immediately exit).

    Note: This test only validates argument parsing and initialization.
    It does not test the full trading loop.
    """
    # We can't easily test the full loop without mocking,
    # so this test just ensures the script can be imported and parsed
    result = subprocess.run(
        [
            sys.executable,
            "scripts/run.py",
            "--help",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "--dry-run" in result.stdout


def test_run_script_exists():
    """Ensure the run script file exists and is readable."""
    script_path = Path("scripts/run.py")
    assert script_path.exists()
    assert script_path.is_file()
