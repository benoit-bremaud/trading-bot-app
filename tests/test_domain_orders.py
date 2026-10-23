"""Behaviour tests for order intents, fills and exchange value objects."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from trading_bot.domain.orders import (
    Balances,
    Fill,
    OrderId,
    OrderIntent,
    OrderKind,
    OrderState,
    OrderStatus,
    Side,
)

DEADLINE = datetime(2026, 1, 1, tzinfo=UTC)


class TestOrderIntent:
    """A post-only limit needs a price and deadline; a market order needs neither."""

    def test_post_only_limit(self):
        intent = OrderIntent(Side.SELL, 1000, OrderKind.LIMIT_POST_ONLY, Decimal("60000"), DEADLINE)
        assert intent.limit_price == Decimal("60000")

    def test_market_order(self):
        assert OrderIntent(Side.BUY, 1000, OrderKind.MARKET).limit_price is None

    def test_post_only_without_price_or_deadline_is_refused(self):
        with pytest.raises(ValueError):
            OrderIntent(Side.BUY, 1000, OrderKind.LIMIT_POST_ONLY, None, DEADLINE)
        with pytest.raises(ValueError):
            OrderIntent(Side.BUY, 1000, OrderKind.LIMIT_POST_ONLY, Decimal("1"), None)

    def test_naive_deadline_is_refused(self):
        with pytest.raises(ValueError):
            OrderIntent(Side.BUY, 1, OrderKind.LIMIT_POST_ONLY, Decimal("1"), datetime(2026, 1, 1))

    def test_market_with_price_is_refused(self):
        with pytest.raises(ValueError):
            OrderIntent(Side.BUY, 1, OrderKind.MARKET, Decimal("1"))

    @pytest.mark.parametrize("sats", [0, -5, True, 1.5])
    def test_sats_must_be_positive_int(self, sats):
        with pytest.raises(ValueError):
            OrderIntent(Side.BUY, sats, OrderKind.MARKET)

    def test_float_price_is_refused(self):
        with pytest.raises(TypeError):
            OrderIntent(Side.BUY, 1, OrderKind.LIMIT_POST_ONLY, 1.0, DEADLINE)

    def test_non_positive_price_is_refused(self):
        with pytest.raises(ValueError):
            OrderIntent(Side.BUY, 1, OrderKind.LIMIT_POST_ONLY, Decimal("0"), DEADLINE)


class TestFill:
    """Notional and fee are exact Decimals."""

    def test_notional_and_fee(self):
        fill = Fill(sats=50_000_000, price=Decimal("60000"), fee_rate=Decimal("0.0008"), maker=True)
        assert fill.notional_usdc == Decimal("30000")
        assert fill.fee_usdc == Decimal("24")

    def test_invalid_fill_is_refused(self):
        with pytest.raises(ValueError):
            Fill(0, Decimal("1"), Decimal("0"), True)
        with pytest.raises(ValueError):
            Fill(1, Decimal("1"), Decimal("-0.1"), True)


class TestExchangeValues:
    """Order id, status and balances."""

    def test_order_id_cannot_be_empty(self):
        with pytest.raises(ValueError):
            OrderId("")

    def test_status_sums_fills(self):
        fills = (
            Fill(100, Decimal("1"), Decimal("0"), True),
            Fill(250, Decimal("1"), Decimal("0"), True),
        )
        status = OrderStatus(OrderId("a"), OrderState.FILLED, fills)
        assert status.filled_sats == 350
        assert OrderStatus(OrderId("a"), OrderState.RESTING).filled_sats == 0

    def test_balances_validation(self):
        assert Balances(10, Decimal("5")).btc_sats == 10
        with pytest.raises(TypeError):
            Balances(1.5, Decimal("5"))
        with pytest.raises(TypeError):
            Balances(1, 5.0)
        with pytest.raises(ValueError):
            Balances(-1, Decimal("5"))
