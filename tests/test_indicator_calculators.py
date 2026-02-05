from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from trading_bot.domain.entities import Candle
from trading_bot.infrastructure.indicators import (
    BollingerBandsCalculator,
    MACDCalculator,
    RSICalculator,
)


def _make_candles(count: int, base_price: float = 100.0) -> list[Candle]:
    """Helper pour créer des candles de test"""
    start = datetime(2024, 1, 1)
    candles = []
    for i in range(count):
        candles.append(
            Candle(
                timestamp=start + timedelta(hours=i),
                open=base_price + i,
                high=base_price + i + 1,
                low=base_price + i - 1,
                close=base_price + i,
                volume=1000.0,
            )
        )
    return candles


class TestRSICalculator:
    def test_init_valid(self):
        calc = RSICalculator(period=14)
        assert calc.period == 14
        assert calc.name == "RSI_14"
        assert calc.min_periods() == 15

    def test_init_invalid_period(self):
        with pytest.raises(ValueError, match="period must be positive"):
            RSICalculator(period=0)

    def test_calculate_insufficient_data(self):
        calc = RSICalculator(period=14)
        candles = _make_candles(10)
        result = calc.calculate(candles)
        assert len(result) == 0

    def test_calculate_sufficient_data(self):
        calc = RSICalculator(period=14)
        candles = _make_candles(50)
        result = calc.calculate(candles)
        assert len(result) > 0
        assert all(0 <= ind.value <= 100 for ind in result)
        assert all(ind.name == "RSI_14" for ind in result)

    def test_calculate_trending_up(self):
        """Test RSI avec tendance haussière (prix croissants)"""
        calc = RSICalculator(period=5)
        candles = _make_candles(20, base_price=100.0)
        result = calc.calculate(candles)
        # Avec des prix strictement croissants, RSI devrait être élevé
        assert len(result) > 0
        last_rsi = result[-1].value
        assert last_rsi > 50  # Bullish

    def test_calculate_metadata(self):
        calc = RSICalculator(period=5)
        candles = _make_candles(20)
        result = calc.calculate(candles)
        assert len(result) > 0
        assert result[0].metadata is not None
        assert "avg_gain" in result[0].metadata
        assert "avg_loss" in result[0].metadata


class TestMACDCalculator:
    def test_init_valid(self):
        calc = MACDCalculator(fast=12, slow=26, signal=9)
        assert calc.fast == 12
        assert calc.slow == 26
        assert calc.signal == 9
        assert calc.name == "MACD_12_26_9"
        assert calc.min_periods() == 35

    def test_init_invalid_periods(self):
        with pytest.raises(ValueError, match="periods must be positive"):
            MACDCalculator(fast=0, slow=26, signal=9)

        with pytest.raises(ValueError, match="fast period must be less than slow period"):
            MACDCalculator(fast=26, slow=12, signal=9)

    def test_calculate_insufficient_data(self):
        calc = MACDCalculator(fast=12, slow=26, signal=9)
        candles = _make_candles(20)
        result = calc.calculate(candles)
        assert len(result) == 0

    def test_calculate_sufficient_data(self):
        calc = MACDCalculator(fast=12, slow=26, signal=9)
        candles = _make_candles(100)
        result = calc.calculate(candles)
        assert len(result) > 0
        assert all(ind.name == "MACD_12_26_9" for ind in result)

    def test_calculate_metadata(self):
        calc = MACDCalculator(fast=12, slow=26, signal=9)
        candles = _make_candles(100)
        result = calc.calculate(candles)
        assert len(result) > 0
        first = result[0]
        assert first.metadata is not None
        assert "macd_line" in first.metadata
        assert "signal_line" in first.metadata
        assert "histogram" in first.metadata
        # Histogram devrait être égal à value
        assert abs(first.value - first.metadata["histogram"]) < 1e-10

    def test_calculate_custom_periods(self):
        calc = MACDCalculator(fast=5, slow=10, signal=3)
        assert calc.min_periods() == 13
        candles = _make_candles(50)
        result = calc.calculate(candles)
        assert len(result) > 0


class TestBollingerBandsCalculator:
    def test_init_valid(self):
        calc = BollingerBandsCalculator(period=20, std_dev=2.0)
        assert calc.period == 20
        assert calc.std_dev == 2.0
        assert calc.name == "BB_20_2.0"
        assert calc.min_periods() == 20

    def test_init_invalid_params(self):
        with pytest.raises(ValueError, match="period must be positive"):
            BollingerBandsCalculator(period=0, std_dev=2.0)

        with pytest.raises(ValueError, match="std_dev must be positive"):
            BollingerBandsCalculator(period=20, std_dev=0)

    def test_calculate_insufficient_data(self):
        calc = BollingerBandsCalculator(period=20, std_dev=2.0)
        candles = _make_candles(10)
        result = calc.calculate(candles)
        assert len(result) == 0

    def test_calculate_sufficient_data(self):
        calc = BollingerBandsCalculator(period=20, std_dev=2.0)
        candles = _make_candles(50)
        result = calc.calculate(candles)
        assert len(result) > 0
        assert all(ind.name == "BB_20_2.0" for ind in result)
        # BB position devrait être entre 0 et 1
        assert all(0 <= ind.value <= 1 for ind in result)

    def test_calculate_metadata(self):
        calc = BollingerBandsCalculator(period=20, std_dev=2.0)
        candles = _make_candles(50)
        result = calc.calculate(candles)
        assert len(result) > 0
        first = result[0]
        assert first.metadata is not None
        assert "upper" in first.metadata
        assert "middle" in first.metadata
        assert "lower" in first.metadata
        assert "bandwidth" in first.metadata
        # Upper > Middle > Lower
        assert first.metadata["upper"] > first.metadata["middle"]
        assert first.metadata["middle"] > first.metadata["lower"]

    def test_calculate_position_in_band(self):
        """Test que la position BB est correctement calculée"""
        calc = BollingerBandsCalculator(period=5, std_dev=2.0)
        # Créer des candles avec peu de volatilité
        candles = []
        base_time = datetime(2024, 1, 1)
        for i in range(10):
            candles.append(
                Candle(
                    timestamp=base_time + timedelta(hours=i),
                    open=100.0,
                    high=100.0,
                    low=100.0,
                    close=100.0,
                    volume=1000.0,
                )
            )
        result = calc.calculate(candles)
        assert len(result) > 0
        # Avec prix constant, position devrait être ~0.5
        assert 0.4 <= result[-1].value <= 0.6
