from datetime import UTC, datetime, timedelta

import pytest

from trading_bot.application.signal_model import MovingAverageCrossoverSignalModel
from trading_bot.domain.entities import Candle, PairProfile


def _profile() -> PairProfile:
    return PairProfile(symbol="BTC-USDT", timeframe="1h", avg_volume=1.0, volatility=0.1, atr=None)


def _candles(closes: list[float]) -> list[Candle]:
    base = datetime(2024, 1, 1, tzinfo=UTC)
    return [
        Candle(base + timedelta(hours=idx), close, close, close, close, 1.0)
        for idx, close in enumerate(closes)
    ]


def test_score_returns_zero_when_insufficient_candles():
    model = MovingAverageCrossoverSignalModel(short_window=2, long_window=5, entry_threshold=0.6)

    score = model.score(_candles([1.0, 2.0, 3.0]), _profile())

    assert score == 0.0


def test_score_positive_when_short_above_long():
    model = MovingAverageCrossoverSignalModel(short_window=2, long_window=4, entry_threshold=0.2)

    score = model.score(_candles([1.0, 1.0, 3.0, 3.0]), _profile())

    assert score > 0.0
    assert model.is_entry(score)


def test_score_clamps_to_one():
    model = MovingAverageCrossoverSignalModel(short_window=1, long_window=3, entry_threshold=0.9)

    score = model.score(_candles([1.0, 1.0, 10.0]), _profile())

    assert score == 1.0


def test_validation_errors():
    with pytest.raises(ValueError):
        MovingAverageCrossoverSignalModel(short_window=0, long_window=5, entry_threshold=0.5)
    with pytest.raises(ValueError):
        MovingAverageCrossoverSignalModel(short_window=5, long_window=5, entry_threshold=0.5)
    with pytest.raises(ValueError):
        MovingAverageCrossoverSignalModel(short_window=2, long_window=5, entry_threshold=1.1)
