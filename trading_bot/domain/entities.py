from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class Candle:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass(frozen=True, slots=True)
class PairProfile:
    symbol: str
    timeframe: str
    avg_volume: float
    volatility: float
    atr: float | None = None


@dataclass(frozen=True, slots=True)
class Indicator:
    """Value object représentant un indicateur technique calculé"""

    name: str
    timestamp: datetime
    value: float
    metadata: dict[str, float] | None = None


@dataclass(frozen=True, slots=True)
class EnrichedCandle:
    """Candle enrichie avec ses indicateurs techniques"""

    candle: Candle
    indicators: dict[str, Indicator]


@dataclass(frozen=True, slots=True)
class BacktestResult:
    symbol: str
    timeframe: str
    start: datetime
    end: datetime
    initial_cash: float
    final_cash: float
    pnl: float
    return_pct: float
    trades: int
