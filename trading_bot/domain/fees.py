"""Fee schedule read from the venue at start-up (R03, R17)."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

FEE_CAP = Decimal("0.001")
"""Maximum fee rate the bot accepts (0.10 %, R17)."""


class FeeCapExceededError(ValueError):
    """Raised when the venue's fees are above the allowed cap, so trading must stop."""


@dataclass(frozen=True, slots=True)
class FeeSchedule:
    """Maker and taker fee rates as fractions (``0.0008`` is 0.08 %)."""

    maker_rate: Decimal
    taker_rate: Decimal

    def __post_init__(self) -> None:
        """Reject non-Decimal rates and rates outside [0, 1)."""
        for name, rate in (("maker_rate", self.maker_rate), ("taker_rate", self.taker_rate)):
            if not isinstance(rate, Decimal):
                raise TypeError(f"{name} must be a Decimal, got {type(rate).__name__}")
            if not Decimal(0) <= rate < Decimal(1):
                raise ValueError(f"{name} must be in [0, 1), got {rate}")

    def rate_for(self, *, maker: bool) -> Decimal:
        """Return the maker rate when ``maker`` is true, else the taker rate."""
        return self.maker_rate if maker else self.taker_rate

    def assert_below_cap(self, cap: Decimal = FEE_CAP) -> None:
        """Raise ``FeeCapExceededError`` if either rate is above ``cap`` (R17)."""
        worst = max(self.maker_rate, self.taker_rate)
        if worst > cap:
            raise FeeCapExceededError(f"fee rate {worst} is above the cap {cap}")
