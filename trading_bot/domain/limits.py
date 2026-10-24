"""Hard limits independent of the strategy (R06)."""

from __future__ import annotations

from dataclasses import dataclass

from trading_bot.domain.checks import require_int


@dataclass(frozen=True, slots=True)
class HardLimits:
    """Maximum orders per day and maximum order size, bounding software defects."""

    max_orders_per_day: int
    max_order_sats: int

    def __post_init__(self) -> None:
        """Both limits must be positive integers."""
        for name, value in (
            ("max_orders_per_day", self.max_orders_per_day),
            ("max_order_sats", self.max_order_sats),
        ):
            if require_int(name, value) <= 0:
                raise ValueError(f"{name} must be positive, got {value}")

    def check(self, *, order_count: int, sats: int) -> bool:
        """Return True when one more order of ``sats`` is allowed.

        ``order_count`` is the number of orders already placed today. Returns a bool
        and raises ``ValueError`` for a negative count or a non-positive size (caller bug).
        """
        if require_int("order_count", order_count) < 0 or require_int("sats", sats) <= 0:
            raise ValueError("order_count must be >= 0 and sats > 0")
        return order_count < self.max_orders_per_day and sats <= self.max_order_sats
