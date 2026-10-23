"""Active pocket and exited tranches (class diagram 04, state diagram 05a).

All objects are immutable: each transition returns a new ``Pocket`` so a decision
cycle can be replayed exactly (R29). Exposure to a sats loss exists only out of
BTC (R09), so the pocket is either long BTC or flat in USDC.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from trading_bot.domain.orders import Fill

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

    @property
    def stop_price(self) -> Decimal:
        """Price at which the tranche is bought back (R16)."""
        return self.exit_vwap * STOP_MULTIPLIER

    def is_stop_reached(self, price: Decimal) -> bool:
        """True when ``price`` is at or above the stop price."""
        return price >= self.stop_price


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
        if self.btc_sats < 0 or self.usdc < 0:
            raise ValueError("pocket balances cannot be negative")
        if not 0 < self.pocket_target_bps <= 10_000:
            raise ValueError("pocket_target_bps must be in (0, 10000]")

    def open_tranches(self) -> tuple[Tranche, ...]:
        """Tranches sold and not yet bought back."""
        return self.tranches

    @property
    def position(self) -> PocketState:
        """Position implied by the holdings, ignoring pause and halt."""
        if not self.tranches:
            return PocketState.IN_BTC
        if self.btc_sats == 0:
            return PocketState.FULLY_OUT
        return PocketState.PARTIALLY_OUT

    def _after(self, **changes: object) -> Pocket:
        """Copy with ``changes``; the state follows the position unless paused or halted."""
        updated = replace(self, **changes)  # type: ignore[arg-type]
        if self.state in (PocketState.PAUSED, PocketState.HALTED):
            return updated
        return replace(updated, state=updated.position)

    def record_exit(self, tranche_id: UUID, fill: Fill) -> Pocket:
        """Apply a filled sell: opens a tranche, moves BTC to USDC net of the fee."""
        if self.state in (PocketState.PAUSED, PocketState.HALTED):
            raise PocketError(f"exits are blocked while {self.state}")
        if fill.sats > self.btc_sats:
            raise PocketError("cannot sell more sats than the pocket holds")
        tranche = Tranche(tranche_id, fill.sats, fill.price)
        return self._after(
            btc_sats=self.btc_sats - fill.sats,
            usdc=self.usdc + fill.notional_usdc - fill.fee_usdc,
            tranches=(*self.tranches, tranche),
        )

    def record_buyback(self, tranche_id: UUID, fill: Fill) -> Pocket:
        """Apply a filled buy against a tranche; buying at least its size closes it.

        Buying more sats than the tranche exited is the sats gain the bot aims for.

        Allowed while paused (R16c, R16d): returning to BTC is never blocked.
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
            kept = (*kept, replace(tranche, exited_sats=remaining))
        return self._after(
            btc_sats=self.btc_sats + fill.sats,
            usdc=self.usdc - cost,
            tranches=kept,
        )

    def pause(self) -> Pocket:
        """Block new exits (incident or supervisor pause)."""
        if self.state is PocketState.HALTED:
            raise PocketError("pocket is halted")
        return replace(self, state=PocketState.PAUSED)

    def resume(self) -> Pocket:
        """Leave the pause; the state follows the holdings (back to BTC when whole)."""
        if self.state is not PocketState.PAUSED:
            raise PocketError("only a paused pocket can resume")
        return replace(self, state=self.position)

    def halt(self) -> Pocket:
        """Operator halt, allowed from BTC or from a pause only (diagram 05a).

        Returning to BTC before halting is the caller's job (decision 2026-10-23).
        """
        if self.state not in (PocketState.IN_BTC, PocketState.PAUSED):
            raise PocketError("halt requires the pocket to be in BTC or paused")
        return replace(self, state=PocketState.HALTED)
