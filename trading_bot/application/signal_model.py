from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from trading_bot.application.ports import SignalModel
from trading_bot.domain.entities import Candle, EnrichedCandle, PairProfile


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


@dataclass(frozen=True, slots=True)
class IndicatorBasedSignalModel(SignalModel):
    """Signal model utilisant des indicateurs techniques (RSI, MACD, BB)"""

    entry_threshold: float = 0.6
    rsi_oversold: float = 30.0
    rsi_overbought: float = 70.0
    use_macd: bool = True
    use_bollinger: bool = True

    def __post_init__(self) -> None:
        if not 0 <= self.entry_threshold <= 1:
            raise ValueError("entry_threshold must be within [0, 1]")
        if not 0 <= self.rsi_oversold <= 100:
            raise ValueError("rsi_oversold must be within [0, 100]")
        if not 0 <= self.rsi_overbought <= 100:
            raise ValueError("rsi_overbought must be within [0, 100]")
        if self.rsi_oversold >= self.rsi_overbought:
            raise ValueError("rsi_oversold must be less than rsi_overbought")

    def score(
        self, candles: Sequence[Candle] | Sequence[EnrichedCandle], profile: PairProfile
    ) -> float:
        """
        Calcule un score basé sur les indicateurs techniques.
        Si les candles sont EnrichedCandle, utilise les indicateurs.
        Sinon, fallback sur le dernier prix (score neutre).
        """
        if not candles:
            return 0.0

        # Check if we have EnrichedCandle
        last_candle = candles[-1]
        if not isinstance(last_candle, EnrichedCandle):
            # Fallback: pas d'indicateurs disponibles
            return 0.5

        indicators = last_candle.indicators
        if not indicators:
            return 0.5

        # Composantes du score
        scores = []
        weights = []

        # 1. RSI Score
        rsi_indicators = [ind for name, ind in indicators.items() if name.startswith("RSI_")]
        if rsi_indicators:
            rsi = rsi_indicators[0].value
            # RSI oversold = bullish (score élevé)
            # RSI overbought = bearish (score faible)
            if rsi <= self.rsi_oversold:
                rsi_score = 1.0
            elif rsi >= self.rsi_overbought:
                rsi_score = 0.0
            else:
                # Interpolation linéaire
                range_size = self.rsi_overbought - self.rsi_oversold
                rsi_score = 1.0 - (rsi - self.rsi_oversold) / range_size
            scores.append(rsi_score)
            weights.append(1.0)

        # 2. MACD Score
        if self.use_macd:
            macd_indicators = [ind for name, ind in indicators.items() if name.startswith("MACD_")]
            if macd_indicators:
                macd = macd_indicators[0]
                histogram = macd.value  # histogram = MACD line - signal line
                # Histogram positif = bullish
                if macd.metadata:
                    macd_line = macd.metadata.get("macd_line", 0.0)
                    signal_line = macd.metadata.get("signal_line", 0.0)
                    # Bullish si MACD line > signal line
                    if macd_line > signal_line:
                        macd_score = 0.5 + min(abs(histogram) * 0.1, 0.5)
                    else:
                        macd_score = 0.5 - min(abs(histogram) * 0.1, 0.5)
                    scores.append(_clamp(macd_score, 0.0, 1.0))
                    weights.append(1.0)

        # 3. Bollinger Bands Score
        if self.use_bollinger:
            bb_indicators = [ind for name, ind in indicators.items() if name.startswith("BB_")]
            if bb_indicators:
                bb = bb_indicators[0]
                bb_position = bb.value  # Position dans la bande (0-1)
                # Prix proche de la bande basse = oversold (bullish)
                # Prix proche de la bande haute = overbought (bearish)
                bb_score = 1.0 - bb_position
                scores.append(bb_score)
                weights.append(0.8)  # Poids légèrement inférieur

        # Calcul du score pondéré
        if not scores:
            return 0.5

        total_weight = sum(weights)
        if total_weight == 0:
            return 0.5

        weighted_score = sum(s * w for s, w in zip(scores, weights, strict=True)) / total_weight
        return _clamp(weighted_score, 0.0, 1.0)

    def is_entry(self, score: float) -> bool:
        return score >= self.entry_threshold
