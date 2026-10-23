"""Conversions between BTC amounts and integer satoshis.

Money and BTC quantities are never ``float``: BTC amounts are whole sats (``int``),
prices and USDC amounts are ``Decimal`` (R02, class diagram 04).
"""

from __future__ import annotations

from decimal import Decimal

from trading_bot.domain.checks import require_decimal, require_int

SATS_PER_BTC = 100_000_000


def btc_to_sats(btc: Decimal) -> int:
    """Convert a BTC ``Decimal`` to whole sats.

    Raises ``TypeError`` for anything but ``Decimal`` (floats are refused) and
    ``ValueError`` for NaN, infinity or an amount that is not a whole number of sats.
    """
    require_decimal("btc", btc)
    try:
        sats = btc.scaleb(8)
        whole = sats == sats.to_integral_value()
    except ArithmeticError as error:  # exponent beyond the Decimal context
        raise ValueError(f"{btc} BTC is out of range") from error
    if not whole:
        raise ValueError(f"{btc} BTC is not a whole number of sats")
    return int(sats)


def sats_to_btc(sats: int) -> Decimal:
    """Convert whole sats to a BTC ``Decimal`` (exact)."""
    return Decimal(require_int("sats", sats)).scaleb(-8)
