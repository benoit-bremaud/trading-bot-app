"""Tests pour les entités du domaine."""

from datetime import UTC, datetime

import pytest

from trading_bot.domain.entities import BacktestResult, Candle, PairProfile


class TestCandle:
    """Tests pour l'entité Candle."""

    def test_candle_creation(self):
        """Test la création d'une bougie avec des valeurs valides."""
        timestamp = datetime(2024, 1, 1, 12, 0, tzinfo=UTC)
        candle = Candle(
            timestamp=timestamp,
            open=100.0,
            high=105.0,
            low=95.0,
            close=102.0,
            volume=1000.0,
        )

        assert candle.timestamp == timestamp
        assert candle.open == 100.0
        assert candle.high == 105.0
        assert candle.low == 95.0
        assert candle.close == 102.0
        assert candle.volume == 1000.0

    def test_candle_immutability(self):
        """Test que Candle est immuable (frozen)."""
        candle = Candle(
            timestamp=datetime(2024, 1, 1, tzinfo=UTC),
            open=100.0,
            high=105.0,
            low=95.0,
            close=102.0,
            volume=1000.0,
        )

        with pytest.raises(AttributeError):
            candle.close = 103.0

    def test_candle_equality(self):
        """Test l'égalité entre deux bougies identiques."""
        timestamp = datetime(2024, 1, 1, 12, 0, tzinfo=UTC)
        candle1 = Candle(timestamp, 100.0, 105.0, 95.0, 102.0, 1000.0)
        candle2 = Candle(timestamp, 100.0, 105.0, 95.0, 102.0, 1000.0)

        assert candle1 == candle2


class TestPairProfile:
    """Tests pour l'entité PairProfile."""

    def test_pair_profile_creation(self):
        """Test la création d'un profil de paire."""
        profile = PairProfile(
            symbol="BTC-USDT",
            timeframe="1h",
            avg_volume=1000000.0,
            volatility=0.05,
            atr=500.0,
        )

        assert profile.symbol == "BTC-USDT"
        assert profile.timeframe == "1h"
        assert profile.avg_volume == 1000000.0
        assert profile.volatility == 0.05
        assert profile.atr == 500.0

    def test_pair_profile_without_atr(self):
        """Test la création d'un profil sans ATR (optionnel)."""
        profile = PairProfile(
            symbol="ETH-USDT",
            timeframe="5m",
            avg_volume=500000.0,
            volatility=0.08,
        )

        assert profile.symbol == "ETH-USDT"
        assert profile.atr is None

    def test_pair_profile_immutability(self):
        """Test que PairProfile est immuable."""
        profile = PairProfile("BTC-USDT", "1h", 1000000.0, 0.05)

        with pytest.raises(AttributeError):
            profile.volatility = 0.1


class TestBacktestResult:
    """Tests pour l'entité BacktestResult."""

    def test_backtest_result_creation(self):
        """Test la création d'un résultat de backtest."""
        start = datetime(2024, 1, 1, tzinfo=UTC)
        end = datetime(2024, 1, 31, tzinfo=UTC)

        result = BacktestResult(
            symbol="BTC-USDT",
            timeframe="1h",
            start=start,
            end=end,
            initial_cash=10000.0,
            final_cash=12000.0,
            pnl=2000.0,
            return_pct=0.2,
            trades=15,
        )

        assert result.symbol == "BTC-USDT"
        assert result.timeframe == "1h"
        assert result.start == start
        assert result.end == end
        assert result.initial_cash == 10000.0
        assert result.final_cash == 12000.0
        assert result.pnl == 2000.0
        assert result.return_pct == 0.2
        assert result.trades == 15

    def test_backtest_result_negative_pnl(self):
        """Test un résultat de backtest avec perte."""
        start = datetime(2024, 1, 1, tzinfo=UTC)
        end = datetime(2024, 1, 31, tzinfo=UTC)

        result = BacktestResult(
            symbol="ETH-USDT",
            timeframe="5m",
            start=start,
            end=end,
            initial_cash=10000.0,
            final_cash=8500.0,
            pnl=-1500.0,
            return_pct=-0.15,
            trades=20,
        )

        assert result.pnl == -1500.0
        assert result.return_pct == -0.15
        assert result.final_cash < result.initial_cash

    def test_backtest_result_immutability(self):
        """Test que BacktestResult est immuable."""
        result = BacktestResult(
            symbol="BTC-USDT",
            timeframe="1h",
            start=datetime(2024, 1, 1, tzinfo=UTC),
            end=datetime(2024, 1, 31, tzinfo=UTC),
            initial_cash=10000.0,
            final_cash=12000.0,
            pnl=2000.0,
            return_pct=0.2,
            trades=15,
        )

        with pytest.raises(AttributeError):
            result.pnl = 3000.0
