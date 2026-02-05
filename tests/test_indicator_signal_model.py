from __future__ import annotations

from datetime import datetime

import pytest

from trading_bot.application.signal_model import IndicatorBasedSignalModel
from trading_bot.domain.entities import Candle, EnrichedCandle, Indicator, PairProfile


def _make_candle(timestamp: datetime, close: float) -> Candle:
    return Candle(
        timestamp=timestamp,
        open=close,
        high=close + 1,
        low=close - 1,
        close=close,
        volume=1000.0,
    )


def _make_enriched_candle(
    timestamp: datetime, close: float, indicators: dict[str, Indicator]
) -> EnrichedCandle:
    candle = _make_candle(timestamp, close)
    return EnrichedCandle(candle=candle, indicators=indicators)


class TestIndicatorBasedSignalModel:
    def test_init_valid(self):
        model = IndicatorBasedSignalModel(
            entry_threshold=0.6,
            rsi_oversold=30.0,
            rsi_overbought=70.0,
        )
        assert model.entry_threshold == 0.6
        assert model.rsi_oversold == 30.0
        assert model.rsi_overbought == 70.0

    def test_init_invalid_threshold(self):
        with pytest.raises(ValueError, match="entry_threshold must be within"):
            IndicatorBasedSignalModel(entry_threshold=1.5)

    def test_init_invalid_rsi_bounds(self):
        with pytest.raises(ValueError, match="rsi_oversold must be within"):
            IndicatorBasedSignalModel(rsi_oversold=150)

        with pytest.raises(ValueError, match="rsi_oversold must be less than rsi_overbought"):
            IndicatorBasedSignalModel(rsi_oversold=80, rsi_overbought=20)

    def test_score_empty_candles(self):
        model = IndicatorBasedSignalModel()
        profile = PairProfile(
            symbol="BTC-USDT",
            timeframe="1h",
            avg_volume=1000.0,
            volatility=0.02,
        )
        score = model.score([], profile)
        assert score == 0.0

    def test_score_plain_candles_fallback(self):
        """Test avec des Candle normales (pas EnrichedCandle)"""
        model = IndicatorBasedSignalModel()
        profile = PairProfile(
            symbol="BTC-USDT",
            timeframe="1h",
            avg_volume=1000.0,
            volatility=0.02,
        )
        candles = [_make_candle(datetime(2024, 1, 1), 100.0)]
        score = model.score(candles, profile)
        # Devrait retourner score neutre
        assert score == 0.5

    def test_score_enriched_no_indicators(self):
        """Test avec EnrichedCandle mais sans indicateurs"""
        model = IndicatorBasedSignalModel()
        profile = PairProfile(
            symbol="BTC-USDT",
            timeframe="1h",
            avg_volume=1000.0,
            volatility=0.02,
        )
        enriched = [_make_enriched_candle(datetime(2024, 1, 1), 100.0, {})]
        score = model.score(enriched, profile)
        assert score == 0.5

    def test_score_rsi_oversold_bullish(self):
        """Test RSI oversold = signal bullish"""
        model = IndicatorBasedSignalModel(rsi_oversold=30.0, rsi_overbought=70.0)
        profile = PairProfile(
            symbol="BTC-USDT",
            timeframe="1h",
            avg_volume=1000.0,
            volatility=0.02,
        )

        timestamp = datetime(2024, 1, 1)
        rsi = Indicator(
            name="RSI_14",
            timestamp=timestamp,
            value=25.0,  # Oversold
            metadata={"avg_gain": 1.0, "avg_loss": 3.0},
        )
        enriched = [_make_enriched_candle(timestamp, 100.0, {"RSI_14": rsi})]

        score = model.score(enriched, profile)
        assert score > 0.7  # Score élevé = bullish

    def test_score_rsi_overbought_bearish(self):
        """Test RSI overbought = signal bearish"""
        model = IndicatorBasedSignalModel(rsi_oversold=30.0, rsi_overbought=70.0)
        profile = PairProfile(
            symbol="BTC-USDT",
            timeframe="1h",
            avg_volume=1000.0,
            volatility=0.02,
        )

        timestamp = datetime(2024, 1, 1)
        rsi = Indicator(
            name="RSI_14",
            timestamp=timestamp,
            value=75.0,  # Overbought
            metadata={"avg_gain": 3.0, "avg_loss": 1.0},
        )
        enriched = [_make_enriched_candle(timestamp, 100.0, {"RSI_14": rsi})]

        score = model.score(enriched, profile)
        assert score < 0.3  # Score faible = bearish

    def test_score_macd_bullish(self):
        """Test MACD histogram positif = bullish"""
        model = IndicatorBasedSignalModel(use_macd=True)
        profile = PairProfile(
            symbol="BTC-USDT",
            timeframe="1h",
            avg_volume=1000.0,
            volatility=0.02,
        )

        timestamp = datetime(2024, 1, 1)
        macd = Indicator(
            name="MACD_12_26_9",
            timestamp=timestamp,
            value=5.0,  # Histogram positif
            metadata={"macd_line": 10.0, "signal_line": 5.0, "histogram": 5.0},
        )
        enriched = [_make_enriched_candle(timestamp, 100.0, {"MACD_12_26_9": macd})]

        score = model.score(enriched, profile)
        assert score > 0.5  # Bullish

    def test_score_bollinger_bands_oversold(self):
        """Test BB position basse = oversold = bullish"""
        model = IndicatorBasedSignalModel(use_bollinger=True)
        profile = PairProfile(
            symbol="BTC-USDT",
            timeframe="1h",
            avg_volume=1000.0,
            volatility=0.02,
        )

        timestamp = datetime(2024, 1, 1)
        bb = Indicator(
            name="BB_20_2.0",
            timestamp=timestamp,
            value=0.1,  # Position basse dans la bande
            metadata={"upper": 110.0, "middle": 100.0, "lower": 90.0, "bandwidth": 0.2},
        )
        enriched = [_make_enriched_candle(timestamp, 100.0, {"BB_20_2.0": bb})]

        score = model.score(enriched, profile)
        assert score > 0.7  # Bullish (1.0 - 0.1 * weight)

    def test_score_combined_indicators(self):
        """Test avec plusieurs indicateurs combinés"""
        model = IndicatorBasedSignalModel(
            rsi_oversold=30.0,
            rsi_overbought=70.0,
            use_macd=True,
            use_bollinger=True,
        )
        profile = PairProfile(
            symbol="BTC-USDT",
            timeframe="1h",
            avg_volume=1000.0,
            volatility=0.02,
        )

        timestamp = datetime(2024, 1, 1)
        rsi = Indicator(
            name="RSI_14",
            timestamp=timestamp,
            value=25.0,  # Oversold
            metadata={"avg_gain": 1.0, "avg_loss": 3.0},
        )
        macd = Indicator(
            name="MACD_12_26_9",
            timestamp=timestamp,
            value=3.0,
            metadata={"macd_line": 8.0, "signal_line": 5.0, "histogram": 3.0},
        )
        bb = Indicator(
            name="BB_20_2.0",
            timestamp=timestamp,
            value=0.2,
            metadata={"upper": 110.0, "middle": 100.0, "lower": 90.0, "bandwidth": 0.2},
        )

        enriched = [
            _make_enriched_candle(
                timestamp, 100.0, {"RSI_14": rsi, "MACD_12_26_9": macd, "BB_20_2.0": bb}
            )
        ]

        score = model.score(enriched, profile)
        # Tous les indicateurs sont bullish
        assert 0.7 <= score <= 1.0

    def test_is_entry_above_threshold(self):
        model = IndicatorBasedSignalModel(entry_threshold=0.6)
        assert model.is_entry(0.7) is True
        assert model.is_entry(0.6) is True

    def test_is_entry_below_threshold(self):
        model = IndicatorBasedSignalModel(entry_threshold=0.6)
        assert model.is_entry(0.5) is False
        assert model.is_entry(0.0) is False
