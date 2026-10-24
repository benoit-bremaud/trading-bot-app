"""Orders, fills and exchange-side value objects (class diagram 04)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from trading_bot.domain.checks import require_decimal, require_int
from trading_bot.domain.sats import SATS_PER_BTC


class Side(StrEnum):
    """Order direction."""

    BUY = "buy"
    SELL = "sell"


class OrderKind(StrEnum):
    """Maker post-only limit (R18) or market (stop and depeg buy-backs)."""

    LIMIT_POST_ONLY = "limit_post_only"
    MARKET = "market"


class OrderState(StrEnum):
    """Order state as reported by the exchange (finer lifecycle: diagram 05b)."""

    RESTING = "resting"
    FILLED = "filled"
    CANCELED = "canceled"
    REJECTED = "rejected"


def _require_sats(sats: int) -> None:
    """Raise ``ValueError`` unless ``sats`` is a positive ``int``."""
    if isinstance(sats, bool) or not isinstance(sats, int) or sats <= 0:
        raise ValueError(f"sats must be a positive int, got {sats!r}")


def _require_price(name: str, price: Decimal) -> None:
    """Raise unless ``price`` is a finite, positive ``Decimal``."""
    require_decimal(name, price)
    if price <= 0:
        raise ValueError(f"{name} must be positive, got {price}")


@dataclass(frozen=True, slots=True)
class OrderIntent:
    """What the bot wants to trade, before the exchange sees it."""

    side: Side
    sats: int
    kind: OrderKind
    limit_price: Decimal | None = None
    deadline: datetime | None = None

    def __post_init__(self) -> None:
        """Enforce that a post-only limit has a price and a timezone-aware deadline."""
        if not isinstance(self.side, Side) or not isinstance(self.kind, OrderKind):
            raise TypeError("side and kind must be Side and OrderKind members")
        _require_sats(self.sats)
        if self.kind is OrderKind.LIMIT_POST_ONLY:
            if self.limit_price is None or self.deadline is None:
                raise ValueError("a post-only limit needs limit_price and deadline")
            _require_price("limit_price", self.limit_price)
            if self.deadline.tzinfo is None:
                raise ValueError("deadline must be timezone-aware")
        elif self.limit_price is not None or self.deadline is not None:
            raise ValueError("a market order has no limit_price or deadline")


@dataclass(frozen=True, slots=True)
class Fill:
    """One execution: size in sats, price in USDC per BTC, fee rate charged.

    ``fee_rate`` is the maker or taker rate that applied, as flagged by ``maker``.
    """

    sats: int
    price: Decimal
    fee_rate: Decimal
    maker: bool

    def __post_init__(self) -> None:
        """Validate sizes and rates."""
        _require_sats(self.sats)
        _require_price("price", self.price)
        require_decimal("fee_rate", self.fee_rate)
        if not 0 <= self.fee_rate < 1:
            raise ValueError(f"fee_rate must be in [0, 1), got {self.fee_rate}")

    @property
    def notional_usdc(self) -> Decimal:
        """Traded value in USDC, before fees."""
        return self.price * self.sats / SATS_PER_BTC

    @property
    def fee_usdc(self) -> Decimal:
        """Fee in USDC, charged on the notional for both sides.

        A conservative single convention, to reconcile with the real OKX accounting
        in the adapter brick.
        """
        return self.notional_usdc * self.fee_rate


@dataclass(frozen=True, slots=True)
class OrderId:
    """Opaque exchange order identifier."""

    value: str

    def __post_init__(self) -> None:
        """An identifier cannot be empty."""
        if not self.value:
            raise ValueError("order id cannot be empty")


@dataclass(frozen=True, slots=True)
class OrderStatus:
    """Exchange report for one order: its state and the fills so far."""

    order_id: OrderId
    state: OrderState
    fills: tuple[Fill, ...] = ()

    @property
    def filled_sats(self) -> int:
        """Total sats executed so far."""
        return sum(fill.sats for fill in self.fills)


@dataclass(frozen=True, slots=True)
class Balances:
    """Tradable balances of the account: BTC in sats, USDC as ``Decimal``."""

    btc_sats: int
    usdc: Decimal

    def __post_init__(self) -> None:
        """Balances cannot be negative."""
        require_int("btc_sats", self.btc_sats)
        require_decimal("usdc", self.usdc)
        if self.btc_sats < 0 or self.usdc < 0:
            raise ValueError("balances cannot be negative")
