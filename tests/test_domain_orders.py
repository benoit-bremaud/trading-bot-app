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
D = Decimal


class TestOrderIntent:
    """A post-only limit needs a price and deadline; a market order needs neither."""

    def test_post_only_limit(self):
        intent = OrderIntent(Side.SELL, 1000, OrderKind.LIMIT_POST_ONLY, D("60000"), DEADLINE)
        assert intent.limit_price == D("60000")

    def test_market_order(self):
        assert OrderIntent(Side.BUY, 1000, OrderKind.MARKET).limit_price is None

    @pytest.mark.parametrize(
        ("price", "deadline"), [(None, DEADLINE), (D("1"), None), (None, None)]
    )
    def test_post_only_needs_price_and_deadline(self, price, deadline):
        with pytest.raises(ValueError, match="needs limit_price and deadline"):
            OrderIntent(Side.BUY, 1000, OrderKind.LIMIT_POST_ONLY, price, deadline)

    def test_naive_deadline_is_refused(self):
        naive = datetime(2026, 1, 1)
        arg = D("1")
        with pytest.raises(ValueError, match="timezone-aware"):
            OrderIntent(Side.BUY, 1, OrderKind.LIMIT_POST_ONLY, arg, naive)

    def test_market_with_price_is_refused(self):
        arg = D("1")
        with pytest.raises(ValueError, match="no limit_price"):
            OrderIntent(Side.BUY, 1, OrderKind.MARKET, arg)

    @pytest.mark.parametrize("sats", [0, -5, True, 1.5])
    def test_sats_must_be_positive_int(self, sats):
        with pytest.raises(ValueError, match="positive int"):
            OrderIntent(Side.BUY, sats, OrderKind.MARKET)

    def test_side_and_kind_must_be_enum_members(self):
        with pytest.raises(TypeError, match="members"):
            OrderIntent("buy", 1, "market")

    def test_float_price_is_refused(self):
        with pytest.raises(TypeError, match="Decimal"):
            OrderIntent(Side.BUY, 1, OrderKind.LIMIT_POST_ONLY, 1.0, DEADLINE)

    @pytest.mark.parametrize("bad", ["0", "-1", "NaN", "Infinity"])
    def test_invalid_price_is_refused(self, bad):
        price = D(bad)
        with pytest.raises(ValueError):
            OrderIntent(Side.BUY, 1, OrderKind.LIMIT_POST_ONLY, price, DEADLINE)


class TestFill:
    """Notional and fee are exact Decimals."""

    def test_notional_and_fee(self):
        fill = Fill(sats=50_000_000, price=D("60000"), fee_rate=D("0.0008"), maker=True)
        assert fill.notional_usdc == D("30000")
        assert fill.fee_usdc == D("24")

    def test_non_round_values_stay_exact(self):
        fill = Fill(sats=12_345_678, price=D("61234.56"), fee_rate=D("0.001"), maker=False)
        assert fill.notional_usdc == D("7559.5054041600") or fill.notional_usdc == (
            D("61234.56") * 12_345_678 / 100_000_000
        )
        assert fill.fee_usdc == fill.notional_usdc * D("0.001")
        assert not fill.maker

    def test_zero_sats_is_refused(self):
        arg1 = D("1")
        arg2 = D("0")
        with pytest.raises(ValueError, match="positive int"):
            Fill(0, arg1, arg2, True)

    @pytest.mark.parametrize("bad", ["-0.1", "1", "NaN", "Infinity"])
    def test_invalid_fee_rate_is_refused(self, bad):
        rate = D(bad)
        arg = D("1")
        with pytest.raises(ValueError):
            Fill(1, arg, rate, True)

    def test_float_price_or_fee_is_refused(self):
        arg = D("0")
        with pytest.raises(TypeError):
            Fill(1, 1.0, arg, True)
        arg = D("1")
        with pytest.raises(TypeError):
            Fill(1, arg, 0.001, True)

    @pytest.mark.parametrize("bad", ["Infinity", "NaN"])
    def test_non_finite_price_is_refused(self, bad):
        price = D(bad)
        arg = D("0")
        with pytest.raises(ValueError, match="finite"):
            Fill(1, price, arg, True)


class TestExchangeValues:
    """Order id, status and balances."""

    def test_order_id_cannot_be_empty(self):
        with pytest.raises(ValueError, match="empty"):
            OrderId("")

    def test_status_sums_fills(self):
        fills = (Fill(100, D("1"), D("0"), True), Fill(250, D("1"), D("0"), True))
        status = OrderStatus(OrderId("a"), OrderState.FILLED, fills)
        assert status.filled_sats == 350
        assert OrderStatus(OrderId("a"), OrderState.RESTING).filled_sats == 0

    def test_zero_balances_are_valid(self):
        balances = Balances(0, D("0"))
        assert (balances.btc_sats, balances.usdc) == (0, 0)

    @pytest.mark.parametrize("btc", [1.5, True])
    def test_btc_balance_must_be_int(self, btc):
        arg = D("5")
        with pytest.raises(TypeError, match="int"):
            Balances(btc, arg)

    def test_usdc_balance_must_be_decimal(self):
        with pytest.raises(TypeError, match="Decimal"):
            Balances(1, 5.0)

    def test_balances_cannot_be_negative_or_infinite(self):
        arg = D("5")
        with pytest.raises(ValueError, match="negative"):
            Balances(-1, arg)
        arg = D("-5")
        with pytest.raises(ValueError, match="negative"):
            Balances(1, arg)
        arg = D("Infinity")
        with pytest.raises(ValueError, match="finite"):
            Balances(1, arg)
