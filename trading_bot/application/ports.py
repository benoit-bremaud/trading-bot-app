from __future__ import annotations

from datetime import datetime
from typing import Protocol, Sequence

from trading_bot.domain.entities import Candle, PairProfile


class MarketDataProvider(Protocol):
    def get_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        start: datetime,
        end: datetime,
    ) -> Sequence[Candle]:
        ...


class SignalModel(Protocol):
    def score(self, candles: Sequence[Candle], profile: PairProfile) -> float:
        ...

    def is_entry(self, score: float) -> bool:
        ...


class RiskManager(Protocol):
    def position_size(
        self, profile: PairProfile, portfolio_value: float, score: float
    ) -> float:
        ...


class BacktestEngine(Protocol):
    def run(self, symbol: str, timeframe: str, start: datetime, end: datetime) -> None:
        ...


class OrderExecutor(Protocol):
    def place_market_order(self, symbol: str, size: float) -> None:
        ...
