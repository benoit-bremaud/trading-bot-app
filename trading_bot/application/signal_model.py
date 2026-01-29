from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from trading_bot.application.ports import SignalModel
from trading_bot.domain.entities import Candle, PairProfile


def _clamp(value: float, min_value: float, max_value: float) -> float:
    return max(min_value, min(max_value, value))


def _sma(values: list[float]) -> float:
    return sum(values) / len(values)


@dataclass(frozen=True, slots=True)
class MovingAverageCrossoverSignalModel(SignalModel):
    short_window: int = 5
    long_window: int = 20
    entry_threshold: float = 0.6

    def __post_init__(self) -> None:
        if self.short_window <= 0 or self.long_window <= 0:
            raise ValueError("window sizes must be positive")
        if self.short_window >= self.long_window:
            raise ValueError("short_window must be smaller than long_window")
        if not 0 <= self.entry_threshold <= 1:
            raise ValueError("entry_threshold must be within [0, 1]")

    def score(self, candles: Sequence[Candle], profile: PairProfile) -> float:
        if len(candles) < self.long_window:
            return 0.0

        closes = [candle.close for candle in candles]
        short_sma = _sma(closes[-self.short_window :])
        long_sma = _sma(closes[-self.long_window :])

        if long_sma == 0:
            return 0.0

        raw = (short_sma - long_sma) / long_sma
        return _clamp(raw, 0.0, 1.0)

    def is_entry(self, score: float) -> bool:
        return score >= self.entry_threshold
