from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import cast

from trading_bot.domain.entities import Candle, EnrichedCandle, Indicator


def _ema(values: list[float], period: int) -> list[float]:
    """Calcule l'Exponential Moving Average (EMA)"""
    if len(values) < period:
        return []

    multiplier = 2.0 / (period + 1)
    ema_values = [sum(values[:period]) / period]  # SMA initial

    for i in range(period, len(values)):
        ema_val = (values[i] - ema_values[-1]) * multiplier + ema_values[-1]
        ema_values.append(ema_val)

    return ema_values


def _sma(values: list[float], period: int) -> list[float]:
    """Calcule la Simple Moving Average (SMA)"""
    if len(values) < period:
        return []

    sma_values = []
    for i in range(period - 1, len(values)):
        sma_val = sum(values[i - period + 1 : i + 1]) / period
        sma_values.append(sma_val)

    return sma_values


def _std_dev(values: list[float]) -> float:
    """Calcule l'écart-type"""
    if not values:
        return 0.0
    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / len(values)
    return variance**0.5


@dataclass(frozen=True, slots=True)
class RSICalculator:
    """Calcule le Relative Strength Index (RSI)"""

    period: int = 14

    def __post_init__(self) -> None:
        if self.period <= 0:
            raise ValueError("period must be positive")

    @property
    def name(self) -> str:
        return f"RSI_{self.period}"

    def min_periods(self) -> int:
        return self.period + 1

    def calculate(self, candles: Sequence[Candle]) -> Sequence[Indicator]:
        if len(candles) < self.min_periods():
            return []

        closes = [c.close for c in candles]
        gains = []
        losses = []

        for i in range(1, len(closes)):
            change = closes[i] - closes[i - 1]
            gains.append(max(change, 0.0))
            losses.append(max(-change, 0.0))

        indicators: list[Indicator] = []

        # Premier RSI avec SMA
        avg_gain = sum(gains[: self.period]) / self.period
        avg_loss = sum(losses[: self.period]) / self.period

        for i in range(self.period, len(candles)):
            if avg_loss == 0:
                rsi_value = 100.0
            else:
                rs = avg_gain / avg_loss
                rsi_value = 100.0 - (100.0 / (1.0 + rs))

            indicators.append(
                Indicator(
                    name=self.name,
                    timestamp=candles[i].timestamp,
                    value=rsi_value,
                    metadata={"avg_gain": avg_gain, "avg_loss": avg_loss},
                )
            )

            # Mise à jour EMA pour le prochain
            if i < len(gains):
                avg_gain = (avg_gain * (self.period - 1) + gains[i]) / self.period
                avg_loss = (avg_loss * (self.period - 1) + losses[i]) / self.period

        return indicators


@dataclass(frozen=True, slots=True)
class MACDCalculator:
    """Calcule le MACD (Moving Average Convergence Divergence)"""

    fast: int = 12
    slow: int = 26
    signal: int = 9

    def __post_init__(self) -> None:
        if self.fast <= 0 or self.slow <= 0 or self.signal <= 0:
            raise ValueError("periods must be positive")
        if self.fast >= self.slow:
            raise ValueError("fast period must be less than slow period")

    @property
    def name(self) -> str:
        return f"MACD_{self.fast}_{self.slow}_{self.signal}"

    def min_periods(self) -> int:
        return self.slow + self.signal

    def calculate(self, candles: Sequence[Candle]) -> Sequence[Indicator]:
        if len(candles) < self.min_periods():
            return []

        closes = [c.close for c in candles]

        # Calcul des EMA
        ema_fast = _ema(closes, self.fast)
        ema_slow = _ema(closes, self.slow)

        # Calcul de la MACD line
        # ema_fast commence à l'index fast-1, ema_slow à slow-1
        # On doit aligner : ema_fast[i + (slow - fast)] correspond à ema_slow[i]
        offset_fast = self.slow - self.fast
        macd_line = [ema_fast[i + offset_fast] - ema_slow[i] for i in range(len(ema_slow))]

        # Calcul du signal line (EMA de la MACD)
        signal_line = _ema(macd_line, self.signal)

        # Construction des indicateurs
        indicators: list[Indicator] = []
        # Le premier signal_line[0] correspond à macd_line[signal-1]
        # qui correspond à candle[slow-1 + signal-1]
        candle_offset = self.slow - 1 + self.signal - 1

        for i in range(len(signal_line)):
            candle_idx = candle_offset + i
            macd_idx = self.signal - 1 + i
            macd_val = macd_line[macd_idx]
            signal_val = signal_line[i]
            histogram_val = macd_val - signal_val

            indicators.append(
                Indicator(
                    name=self.name,
                    timestamp=candles[candle_idx].timestamp,
                    value=histogram_val,
                    metadata={
                        "macd_line": macd_val,
                        "signal_line": signal_val,
                        "histogram": histogram_val,
                    },
                )
            )

        return indicators


@dataclass(frozen=True, slots=True)
class BollingerBandsCalculator:
    """Calcule les Bandes de Bollinger"""

    period: int = 20
    std_dev: float = 2.0

    def __post_init__(self) -> None:
        if self.period <= 0:
            raise ValueError("period must be positive")
        if self.std_dev <= 0:
            raise ValueError("std_dev must be positive")

    @property
    def name(self) -> str:
        return f"BB_{self.period}_{self.std_dev}"

    def min_periods(self) -> int:
        return self.period

    def calculate(self, candles: Sequence[Candle]) -> Sequence[Indicator]:
        if len(candles) < self.min_periods():
            return []

        closes = [c.close for c in candles]
        indicators: list[Indicator] = []

        for i in range(self.period - 1, len(candles)):
            window = closes[i - self.period + 1 : i + 1]
            middle = sum(window) / self.period
            std = _std_dev(window)

            upper = middle + (self.std_dev * std)
            lower = middle - (self.std_dev * std)

            # Valeur principale = position relative dans la bande (0-1)
            if upper == lower:
                bb_position = 0.5
            else:
                bb_position = (closes[i] - lower) / (upper - lower)

            indicators.append(
                Indicator(
                    name=self.name,
                    timestamp=candles[i].timestamp,
                    value=bb_position,
                    metadata={
                        "upper": upper,
                        "middle": middle,
                        "lower": lower,
                        "bandwidth": (upper - lower) / middle if middle != 0 else 0,
                    },
                )
            )

        return indicators


@dataclass
class DefaultIndicatorPipeline:
    """Orchestrateur pour calculer plusieurs indicateurs sur des candles"""

    def __init__(self) -> None:
        self._calculators: list[object] = []

    def add_indicator(self, calculator: object) -> None:
        """Ajoute un calculateur d'indicateur au pipeline"""
        self._calculators.append(calculator)

    def enrich(self, candles: Sequence[Candle]) -> Sequence[EnrichedCandle]:
        """Enrichit les candles avec tous les indicateurs configurés"""
        if not candles:
            return []

        # Calculer tous les indicateurs
        all_indicators: dict[int, dict[str, Indicator]] = {i: {} for i in range(len(candles))}

        for calc in self._calculators:
            calc_typed = cast(RSICalculator | MACDCalculator | BollingerBandsCalculator, calc)
            indicators = calc_typed.calculate(candles)

            # Les indicateurs sont alignés avec les dernières candles
            min_periods = calc_typed.min_periods()
            start_idx = min_periods - 1

            for idx, indicator in enumerate(indicators):
                candle_idx = start_idx + idx
                if candle_idx < len(candles):
                    all_indicators[candle_idx][indicator.name] = indicator

        # Construire les EnrichedCandle
        enriched = []
        for i, candle in enumerate(candles):
            enriched.append(EnrichedCandle(candle=candle, indicators=all_indicators[i]))

        return enriched
