import pytest

from trading_bot.infrastructure.paper_order_executor import PaperOrderExecutor


def _price_getter_factory(price_by_symbol: dict[str, float]):
    def _getter(symbol: str) -> float:
        return price_by_symbol[symbol]

    return _getter


def test_buy_order_reduces_cash_and_increases_position():
    prices = {"BTC-USDT": 10.0}
    executor = PaperOrderExecutor(initial_cash=1000.0, price_getter=_price_getter_factory(prices))

    executor.place_market_order("BTC-USDT", 5.0)

    assert executor.cash == pytest.approx(950.0)
    assert executor.positions["BTC-USDT"] == pytest.approx(5.0)
    assert len(executor.trades) == 1
    trade = executor.trades[0]
    assert trade.symbol == "BTC-USDT"
    assert trade.size == pytest.approx(5.0)
    assert trade.price == pytest.approx(10.0)


def test_sell_order_increases_cash_and_reduces_position():
    call_count = {"BTC-USDT": 0}

    def price_getter(symbol: str) -> float:
        # First call: buy at 10, subsequent calls: sell at 12
        call_count[symbol] += 1
        if call_count[symbol] == 1:
            return 10.0
        return 12.0

    executor = PaperOrderExecutor(initial_cash=1000.0, price_getter=price_getter)

    executor.place_market_order("BTC-USDT", 5.0)
    executor.place_market_order("BTC-USDT", -2.0)

    assert executor.positions["BTC-USDT"] == pytest.approx(3.0)
    # 5 * 10 spent on buy, 2 * 12 received on sell
    assert executor.cash == pytest.approx(1000.0 - 5 * 10.0 + 2 * 12.0)


def test_insufficient_cash_raises_and_does_not_change_state():
    prices = {"BTC-USDT": 100.0}
    executor = PaperOrderExecutor(initial_cash=50.0, price_getter=_price_getter_factory(prices))

    with pytest.raises(ValueError):
        executor.place_market_order("BTC-USDT", 1.0)

    assert executor.cash == pytest.approx(50.0)
    assert executor.positions == {}
    assert len(executor.trades) == 0


def test_insufficient_position_raises_and_does_not_change_state():
    prices = {"BTC-USDT": 10.0}
    executor = PaperOrderExecutor(initial_cash=100.0, price_getter=_price_getter_factory(prices))

    executor.place_market_order("BTC-USDT", 5.0)
    cash_after_buy = executor.cash
    positions_after_buy = dict(executor.positions)

    with pytest.raises(ValueError):
        executor.place_market_order("BTC-USDT", -10.0)

    assert executor.cash == pytest.approx(cash_after_buy)
    assert executor.positions == positions_after_buy


def test_zero_size_order_is_noop():
    prices = {"BTC-USDT": 10.0}
    executor = PaperOrderExecutor(initial_cash=100.0, price_getter=_price_getter_factory(prices))

    executor.place_market_order("BTC-USDT", 0.0)

    assert executor.cash == pytest.approx(100.0)
    assert executor.positions == {}
    assert len(executor.trades) == 0


def test_initial_cash_validation():
    prices = {"BTC-USDT": 10.0}
    with pytest.raises(ValueError):
        PaperOrderExecutor(initial_cash=-1.0, price_getter=_price_getter_factory(prices))
