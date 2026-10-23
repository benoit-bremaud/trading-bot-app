"""Conversions between BTC amounts and integer satoshis.

Money and BTC quantities are never ``float``: BTC amounts are whole sats (``int``),
prices and USDC amounts are ``Decimal`` (R02, class diagram 04).
"""

from __future__ import annotations

from decimal import Decimal

SATS_PER_BTC = 100_000_000


def btc_to_sats(btc: Decimal) -> int:
    """Convert a BTC ``Decimal`` to whole sats.

    Raises ``TypeError`` for anything but ``Decimal`` (floats are refused) and
    ``ValueError`` when the amount is not a whole number of sats.
    """
    if not isinstance(btc, Decimal):
        raise TypeError(f"btc must be a Decimal, got {type(btc).__name__}")
    sats = btc.scaleb(8)
    if sats != sats.to_integral_value():
        raise ValueError(f"{btc} BTC is not a whole number of sats")
    return int(sats)


def sats_to_btc(sats: int) -> Decimal:
    """Convert whole sats to a BTC ``Decimal`` (exact)."""
    if isinstance(sats, bool) or not isinstance(sats, int):
        raise TypeError(f"sats must be an int, got {type(sats).__name__}")
    return Decimal(sats).scaleb(-8)
