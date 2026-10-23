from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from typing import Protocol

from trading_bot.domain.entities import BacktestResult, Candle, PairProfile
from trading_bot.domain.fees import FeeSchedule
from trading_bot.domain.orders import Balances, OrderId, OrderIntent, OrderStatus


class MarketDataProvider(Protocol):
    def get_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        start: datetime,
        end: datetime,
    ) -> Sequence[Candle]: ...


class CandleRepository(Protocol):
    def save(self, symbol: str, timeframe: str, candles: Sequence[Candle]) -> None: ...

    def load(
        self,
        symbol: str,
        timeframe: str,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> Sequence[Candle]: ...


class SignalModel(Protocol):
    def score(self, candles: Sequence[Candle], profile: PairProfile) -> float: ...

    def is_entry(self, score: float) -> bool: ...


class RiskManager(Protocol):
    def position_size(
        self, profile: PairProfile, portfolio_value: float, score: float
    ) -> float: ...


class BacktestEngine(Protocol):
    def run(
        self, symbol: str, timeframe: str, start: datetime, end: datetime
    ) -> BacktestResult: ...


class OrderExecutor(Protocol):
    def place_market_order(self, symbol: str, size: float) -> None: ...


class ExchangePort(Protocol):
    """Venue access shared by backtest, paper and live (R32); only adapters implement it."""

    def fetch_fee_schedule(self) -> FeeSchedule:
        """Read the real maker and taker rates of the single BTC/USDC pair (R17)."""
        ...

    def fetch_balances(self) -> Balances:
        """Return the tradable BTC and USDC balances."""
        ...

    def place_order(self, intent: OrderIntent) -> OrderId:
        """Submit ``intent`` (post-only limit or market) and return its id.

        A post-only rejection shows as ``OrderState.REJECTED`` in ``fetch_order``;
        transport or venue failures raise, so the caller fails closed (R16c).
        """
        ...

    def cancel_order(self, order_id: OrderId) -> OrderStatus:
        """Cancel a resting order and return its final status, fills included.

        An order already filled is returned as filled, not an error.
        """
        ...

    def fetch_order(self, order_id: OrderId) -> OrderStatus:
        """Return the current status and fills of an order."""
        ...
