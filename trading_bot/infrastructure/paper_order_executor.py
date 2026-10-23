from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime

from trading_bot.application.ports import OrderExecutor

# Below this, a size or position is floating-point dust, not a real quantity.
_DUST_EPSILON = 1e-12


@dataclass(frozen=True, slots=True)
class PaperTrade:
    timestamp: datetime
    symbol: str
    size: float
    price: float


class PaperOrderExecutor(OrderExecutor):
    """In-memory paper trading executor.

    This adapter simulates market orders against a provided price source.
    It tracks cash balance, per-symbol positions and executed trades.
    """

    def __init__(self, initial_cash: float, price_getter: Callable[[str], float]) -> None:
        if initial_cash < 0:
            raise ValueError("initial_cash must be >= 0")

        self._cash = float(initial_cash)
        self._positions: dict[str, float] = {}
        self._trades: list[PaperTrade] = []
        self._price_getter = price_getter

    @property
    def cash(self) -> float:
        return self._cash

    @property
    def positions(self) -> dict[str, float]:
        # Return a shallow copy to avoid external mutation of internal state.
        return dict(self._positions)

    @property
    def trades(self) -> Sequence[PaperTrade]:
        return tuple(self._trades)

    def place_market_order(self, symbol: str, size: float) -> None:
        if abs(size) < _DUST_EPSILON:
            return

        price = float(self._price_getter(symbol))
        if price <= 0:
            raise ValueError("price must be positive")

        if size > 0:
            self._buy(symbol, size, price)
        else:
            self._sell(symbol, size, price)

        trade = PaperTrade(
            timestamp=datetime.now(tz=UTC),
            symbol=symbol,
            size=size,
            price=price,
        )
        self._trades.append(trade)

    def _buy(self, symbol: str, size: float, price: float) -> None:
        cost = size * price
        if cost > self._cash:
            raise ValueError("insufficient cash for buy order")

        self._cash -= cost
        self._positions[symbol] = self._positions.get(symbol, 0.0) + size

    def _sell(self, symbol: str, size: float, price: float) -> None:
        current = self._positions.get(symbol, 0.0)
        # size is negative for sell orders
        new_position = current + size
        if new_position < -_DUST_EPSILON:
            raise ValueError("insufficient position for sell order")

        # Selling reduces position (size is negative) and increases cash
        self._cash -= size * price
        if abs(new_position) < _DUST_EPSILON:
            self._positions.pop(symbol, None)
        else:
            self._positions[symbol] = new_position
