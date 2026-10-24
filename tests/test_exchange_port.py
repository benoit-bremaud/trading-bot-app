"""The ExchangePort contract, exercised through an in-memory fake exchange."""

from datetime import UTC, datetime
from decimal import Decimal

from trading_bot.application.ports import ExchangePort
from trading_bot.domain.fees import FeeSchedule
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


class FakeExchange:
    """In-memory venue: fills every order at once, remembers orders for cancel/fetch."""

    def __init__(self) -> None:
        self.orders: dict[str, OrderStatus] = {}

    def fetch_fee_schedule(self) -> FeeSchedule:
        return FeeSchedule(Decimal("0.0008"), Decimal("0.0010"))

    def fetch_balances(self) -> Balances:
        return Balances(1_000, Decimal("500"))

    def place_order(self, intent: OrderIntent) -> OrderId:
        order_id = OrderId(f"o{len(self.orders)}")
        maker = intent.kind is OrderKind.LIMIT_POST_ONLY
        price = intent.limit_price or Decimal("60000")
        fill = Fill(intent.sats, price, Decimal("0.0008" if maker else "0.0010"), maker)
        self.orders[order_id.value] = OrderStatus(order_id, OrderState.FILLED, (fill,))
        return order_id

    def cancel_order(self, order_id: OrderId) -> OrderStatus:
        return self.orders[order_id.value]

    def fetch_order(self, order_id: OrderId) -> OrderStatus:
        return self.orders[order_id.value]


def test_fake_exchange_satisfies_the_port_and_round_trips_an_order() -> None:
    exchange: ExchangePort = FakeExchange()
    intent = OrderIntent(
        Side.SELL,
        500,
        OrderKind.LIMIT_POST_ONLY,
        Decimal("61000"),
        datetime(2026, 1, 1, tzinfo=UTC),
    )

    order_id = exchange.place_order(intent)
    status = exchange.fetch_order(order_id)

    exchange.fetch_fee_schedule().assert_below_cap()
    assert status.state is OrderState.FILLED
    assert status.filled_sats == 500
    assert status.fills[0].maker
    assert exchange.cancel_order(order_id) == status
    assert exchange.fetch_balances().btc_sats == 1_000
