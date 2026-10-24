"""Shared input guards for the money types: exact ``Decimal`` and ``int``, never float."""

from __future__ import annotations

from decimal import Decimal


def require_decimal(name: str, value: object) -> Decimal:
    """Return ``value`` if it is a finite ``Decimal``.

    Raises ``TypeError`` for any other type (floats included) and ``ValueError`` for
    NaN or infinity, so a corrupt exchange payload cannot become a price or a balance.
    """
    if not isinstance(value, Decimal):
        raise TypeError(f"{name} must be a Decimal, got {type(value).__name__}")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite, got {value}")
    return value


def require_int(name: str, value: object) -> int:
    """Return ``value`` if it is an ``int`` (``bool`` is refused); else raise ``TypeError``."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an int, got {type(value).__name__}")
    return value
