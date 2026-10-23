"""Active pocket and exited tranches (class diagram 04, state diagram 05a).

All objects are immutable: each transition returns a new ``Pocket`` so a decision
cycle can be replayed exactly (R29). Exposure to a sats loss exists only out of
BTC (R09), so the pocket is either long BTC or flat in USDC.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from trading_bot.domain.checks import require_decimal, require_int
from trading_bot.domain.orders import Fill
from trading_bot.domain.sats import SATS_PER_BTC

STOP_MULTIPLIER = Decimal("1.05")
"""Buy-back stop: 5 % above the tranche's exit VWAP (R16)."""


class PocketError(ValueError):
    """Raised when a transition is not allowed in the current state."""


class PocketState(StrEnum):
    """Lifecycle of the pocket position (diagram 05a)."""

    IN_BTC = "in_btc"
    PARTIALLY_OUT = "partially_out"
    FULLY_OUT = "fully_out"
    PAUSED = "paused"
    HALTED = "halted"


@dataclass(frozen=True, slots=True)
class Tranche:
    """BTC sold in one exit, kept until bought back."""

    id: UUID
    exited_sats: int
    exit_vwap: Decimal

    def __post_init__(self) -> None:
        """A tranche holds a positive number of sats sold at a positive finite price."""
        if require_int("exited_sats", self.exited_sats) <= 0:
            raise ValueError("exited_sats must be positive")
        if require_decimal("exit_vwap", self.exit_vwap) <= 0:
            raise ValueError("exit_vwap must be positive")

    @property
    def stop_price(self) -> Decimal:
        """Price at which the tranche is bought back (R16)."""
        return self.exit_vwap * STOP_MULTIPLIER

    def is_stop_reached(self, price: Decimal) -> bool:
        """True when ``price`` is at or above the stop price (R16 buy-back trigger)."""
        return price >= self.stop_price


def _position_of(btc_sats: int, tranches: tuple[Tranche, ...]) -> PocketState:
    """Position implied by holdings: in BTC, partly out or fully out."""
    if not tranches:
        return PocketState.IN_BTC
    return PocketState.FULLY_OUT if btc_sats == 0 else PocketState.PARTIALLY_OUT


@dataclass(frozen=True, slots=True)
class Pocket:
    """The fraction of the stack the bot trades (R04): BTC, USDC and open tranches."""

    btc_sats: int
    usdc: Decimal
    pocket_target_bps: int
    state: PocketState = PocketState.IN_BTC
    tranches: tuple[Tranche, ...] = ()

    def __post_init__(self) -> None:
        """Balances cannot be negative and the target is in basis points."""
        require_int("btc_sats", self.btc_sats)
        require_decimal("usdc", self.usdc)
        require_int("pocket_target_bps", self.pocket_target_bps)
        if self.btc_sats < 0 or self.usdc < 0:
            raise ValueError("pocket balances cannot be negative")
        if not 0 < self.pocket_target_bps <= 10_000:
            raise ValueError("pocket_target_bps must be in (0, 10000]")
        if (
            self.state not in (PocketState.PAUSED, PocketState.HALTED)
            and self.state is not self.position
        ):
            raise ValueError(f"state {self.state} contradicts the holdings ({self.position})")

    def open_tranches(self) -> tuple[Tranche, ...]:
        """Tranches sold and not yet bought back."""
        return self.tranches

    @property
    def position(self) -> PocketState:
        """Position implied by the holdings, ignoring pause and halt."""
        return _position_of(self.btc_sats, self.tranches)

    def _with_state(self, state: PocketState) -> Pocket:
        """Copy of this pocket in ``state``, holdings unchanged."""
        return Pocket(self.btc_sats, self.usdc, self.pocket_target_bps, state, self.tranches)

    def _after(self, btc_sats: int, usdc: Decimal, tranches: tuple[Tranche, ...]) -> Pocket:
        """New holdings; the state follows the position unless paused or halted."""
        state = self.state
        if state not in (PocketState.PAUSED, PocketState.HALTED):
            state = _position_of(btc_sats, tranches)
        return Pocket(btc_sats, usdc, self.pocket_target_bps, state, tranches)

    def record_exit(self, tranche_id: UUID, fills: Sequence[Fill]) -> Pocket:
        """Apply the fills of one sell order: opens one tranche at their VWAP.

        BTC moves to USDC net of the fees. Raises ``PocketError`` when paused or
        halted, when there is no fill, when the fills exceed the BTC held, or when
        ``tranche_id`` is already open.
        """
        if self.state in (PocketState.PAUSED, PocketState.HALTED):
            raise PocketError(f"exits are blocked while {self.state}")
        if not fills:
            raise PocketError("an exit needs at least one fill")
        sats = sum(fill.sats for fill in fills)
        if sats > self.btc_sats:
            raise PocketError("cannot sell more sats than the pocket holds")
        if any(t.id == tranche_id for t in self.tranches):
            raise PocketError(f"tranche {tranche_id} already exists")
        notional = sum((fill.notional_usdc for fill in fills), Decimal(0))
        fees = sum((fill.fee_usdc for fill in fills), Decimal(0))
        tranche = Tranche(tranche_id, sats, notional * SATS_PER_BTC / sats)
        return self._after(
            self.btc_sats - sats, self.usdc + notional - fees, (*self.tranches, tranche)
        )

    def record_buyback(self, tranche_id: UUID, fill: Fill) -> Pocket:
        """Apply a filled buy against a tranche; buying at least its size closes it.

        Buying more sats than the tranche exited is the sats gain the bot aims for.

        Allowed while paused (R16c, R16d): returning to BTC is never blocked. Raises
        ``PocketError`` when halted, when the tranche is unknown or when USDC is short.
        """
        if self.state is PocketState.HALTED:
            raise PocketError("pocket is halted")
        tranche = next((t for t in self.tranches if t.id == tranche_id), None)
        if tranche is None:
            raise PocketError(f"unknown tranche {tranche_id}")
        cost = fill.notional_usdc + fill.fee_usdc
        if cost > self.usdc:
            raise PocketError("not enough USDC for this buy-back")
        remaining = max(0, tranche.exited_sats - fill.sats)
        kept = tuple(t for t in self.tranches if t.id != tranche_id)
        if remaining:
            kept = (*kept, Tranche(tranche.id, remaining, tranche.exit_vwap))
        return self._after(
            self.btc_sats + fill.sats,
            self.usdc - cost,
            kept,
        )

    def pause(self) -> Pocket:
        """Block new exits (incident or supervisor pause)."""
        if self.state is PocketState.HALTED:
            raise PocketError("pocket is halted")
        return self._with_state(PocketState.PAUSED)

    def resume(self) -> Pocket:
        """Leave the pause; the state follows the holdings (back to BTC when whole)."""
        if self.state is not PocketState.PAUSED:
            raise PocketError("only a paused pocket can resume")
        return self._with_state(self.position)

    def halt(self) -> Pocket:
        """Operator halt, allowed from BTC or from a pause, with no open tranche (05a).

        Returning to BTC before halting is the caller's job (diagram 05a, R16c).
        """
        if self.state not in (PocketState.IN_BTC, PocketState.PAUSED) or self.tranches:
            raise PocketError("halt requires the pocket to be back in BTC")
        return self._with_state(PocketState.HALTED)
