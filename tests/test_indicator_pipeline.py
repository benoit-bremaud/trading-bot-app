from __future__ import annotations

from datetime import datetime, timedelta

from trading_bot.domain.entities import Candle
from trading_bot.infrastructure.indicators import (
    BollingerBandsCalculator,
    DefaultIndicatorPipeline,
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


class TestDefaultIndicatorPipeline:
    def test_init(self):
        pipeline = DefaultIndicatorPipeline()
        assert pipeline is not None

    def test_enrich_empty_candles(self):
        pipeline = DefaultIndicatorPipeline()
        pipeline.add_indicator(RSICalculator(period=5))
        result = pipeline.enrich([])
        assert len(result) == 0

    def test_enrich_no_indicators(self):
        pipeline = DefaultIndicatorPipeline()
        candles = _make_candles(50)
        result = pipeline.enrich(candles)
        assert len(result) == len(candles)
        # Toutes les candles devraient avoir des indicateurs vides
        assert all(len(ec.indicators) == 0 for ec in result)

    def test_enrich_single_indicator(self):
        pipeline = DefaultIndicatorPipeline()
        pipeline.add_indicator(RSICalculator(period=5))
        candles = _make_candles(50)
        result = pipeline.enrich(candles)

        assert len(result) == len(candles)
        # Les premières candles n'auront pas de RSI (pas assez de données)
        assert len(result[0].indicators) == 0
        assert len(result[4].indicators) == 0
        # À partir de min_periods, on devrait avoir le RSI
        assert len(result[5].indicators) == 1
        assert "RSI_5" in result[5].indicators
        # Dernière candle devrait avoir RSI
        assert "RSI_5" in result[-1].indicators
        assert 0 <= result[-1].indicators["RSI_5"].value <= 100

    def test_enrich_multiple_indicators(self):
        pipeline = DefaultIndicatorPipeline()
        pipeline.add_indicator(RSICalculator(period=5))
        pipeline.add_indicator(MACDCalculator(fast=5, slow=10, signal=3))
        pipeline.add_indicator(BollingerBandsCalculator(period=10, std_dev=2.0))

        candles = _make_candles(50)
        result = pipeline.enrich(candles)

        assert len(result) == len(candles)

        # La dernière candle devrait avoir tous les indicateurs
        last = result[-1]
        assert len(last.indicators) == 3
        assert "RSI_5" in last.indicators
        assert "MACD_5_10_3" in last.indicators
        assert "BB_10_2.0" in last.indicators

    def test_enrich_preserves_candle_data(self):
        pipeline = DefaultIndicatorPipeline()
        pipeline.add_indicator(RSICalculator(period=5))

        candles = _make_candles(20)
        result = pipeline.enrich(candles)

        # Vérifier que les candles originales sont préservées
        for i, enriched in enumerate(result):
            assert enriched.candle == candles[i]

    def test_enrich_indicators_aligned_with_candles(self):
        """Test que les indicateurs sont bien alignés avec les bonnes candles"""
        pipeline = DefaultIndicatorPipeline()
        pipeline.add_indicator(RSICalculator(period=5))

        candles = _make_candles(20)
        result = pipeline.enrich(candles)

        # Vérifier que les timestamps correspondent
        for enriched in result:
            for indicator in enriched.indicators.values():
                assert indicator.timestamp == enriched.candle.timestamp
