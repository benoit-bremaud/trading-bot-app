from datetime import UTC, datetime, timedelta

import pytest

from trading_bot.application.backtest import BuyAndHoldBacktestEngine
from trading_bot.domain.entities import Candle


class FakeCandleRepository:
    def __init__(self, candles):
        self._candles = list(candles)
        self.calls = []

    def save(self, symbol, timeframe, candles):
        raise NotImplementedError

    def load(self, symbol, timeframe, start=None, end=None):
        self.calls.append((symbol, timeframe, start, end))
        return list(self._candles)


def test_buy_and_hold_backtest_computes_pnl():
    base = datetime(2024, 1, 1, tzinfo=UTC)
    candles = [
        Candle(base, 10.0, 12.0, 9.0, 11.0, 100.0),
        Candle(base + timedelta(hours=1), 11.0, 15.0, 10.0, 15.0, 120.0),
    ]
    repo = FakeCandleRepository(candles)
    engine = BuyAndHoldBacktestEngine(repo, initial_cash=1000.0)

    result = engine.run("BTC-USDT", "1h", base, base + timedelta(hours=1))

    assert result.pnl == pytest.approx(500.0)
    assert result.return_pct == pytest.approx(0.5)
    assert result.final_cash == pytest.approx(1500.0)
    assert result.trades == 1


def test_buy_and_hold_backtest_requires_candles():
    base = datetime(2024, 1, 1, tzinfo=UTC)
    repo = FakeCandleRepository([])
    engine = BuyAndHoldBacktestEngine(repo, initial_cash=1000.0)

    with pytest.raises(ValueError):
        engine.run("BTC-USDT", "1h", base, base + timedelta(hours=1))
