from datetime import UTC, datetime, timedelta

import pytest

from trading_bot.infrastructure.kucoin_market_data import (
    KucoinMarketDataProvider,
    MarketDataError,
    normalize_kucoin_kline,
    to_kucoin_timeframe,
)


class FakeMarket:
    def __init__(self, rows, error: Exception | None = None) -> None:
        self._rows = rows
        self._error = error
        self.calls: list[tuple[str, str, dict[str, int]]] = []

    def get_kline(self, symbol: str, kline_type: str, **kwargs):
        self.calls.append((symbol, kline_type, kwargs))
        if self._error is not None:
            raise self._error
        return list(self._rows)


class FlakyMarket:
    def __init__(self, rows, fail_times: int) -> None:
        self._rows = rows
        self._fail_times = fail_times
        self.calls = 0

    def get_kline(self, symbol: str, kline_type: str, **kwargs):
        self.calls += 1
        if self.calls <= self._fail_times:
            raise Exception("boom")
        return list(self._rows)


def test_to_kucoin_timeframe_accepts_aliases():
    assert to_kucoin_timeframe("1h") == "1hour"
    assert to_kucoin_timeframe("1hour") == "1hour"
    assert to_kucoin_timeframe("5m") == "5min"


def test_to_kucoin_timeframe_rejects_unknown():
    with pytest.raises(ValueError):
        to_kucoin_timeframe("7m")


def test_normalize_kucoin_kline_parses_values():
    row = ["1545904980", "0.058", "0.049", "0.058", "0.049", "0.018", "0.000945"]
    candle = normalize_kucoin_kline(row)

    assert candle.timestamp == datetime.fromtimestamp(1545904980, tz=UTC)
    assert candle.open == 0.058
    assert candle.close == 0.049
    assert candle.high == 0.058
    assert candle.low == 0.049
    assert candle.volume == 0.018


def test_normalize_kucoin_kline_handles_milliseconds():
    row = ["1545904980000", "1", "1", "1", "1", "1", "0"]
    candle = normalize_kucoin_kline(row)

    assert candle.timestamp == datetime.fromtimestamp(1545904980, tz=UTC)


def test_provider_sorts_and_filters_candles():
    start_ts = 1_700_000_000
    end_ts = start_ts + 2 * 60 * 60
    rows = [
        [str(start_ts + 60 * 60), "2", "2", "2", "2", "2", "0"],
        [str(start_ts - 60 * 60), "0", "0", "0", "0", "0", "0"],
        [str(start_ts), "1", "1", "1", "1", "1", "0"],
    ]
    market = FakeMarket(rows)
    provider = KucoinMarketDataProvider(
        client=market,
        max_retries=0,
        sleep=lambda _: None,
    )

    start = datetime.fromtimestamp(start_ts, tz=UTC)
    end = datetime.fromtimestamp(end_ts, tz=UTC)
    candles = provider.get_ohlcv("BTC-USDT", "1h", start, end)

    assert [candle.open for candle in candles] == [1.0, 2.0]
    symbol, kline_type, kwargs = market.calls[0]
    assert symbol == "BTC-USDT"
    assert kline_type == "1hour"
    assert kwargs["startAt"] == start_ts
    assert kwargs["endAt"] == end_ts


def test_provider_retries_on_failure():
    start = datetime(2024, 1, 1, tzinfo=UTC)
    end = start + timedelta(hours=1)
    rows = [[str(int(start.timestamp())), "1", "1", "1", "1", "1", "0"]]
    market = FlakyMarket(rows, fail_times=1)
    provider = KucoinMarketDataProvider(
        client=market,
        max_retries=1,
        sleep=lambda _: None,
    )

    candles = provider.get_ohlcv("BTC-USDT", "1h", start, end)

    assert len(candles) == 1
    assert market.calls == 2


def test_provider_raises_after_retries_exhausted():
    start = datetime(2024, 1, 1, tzinfo=UTC)
    end = start + timedelta(hours=1)
    rows: list[list[str]] = []
    market = FlakyMarket(rows, fail_times=2)
    provider = KucoinMarketDataProvider(
        client=market,
        max_retries=1,
        sleep=lambda _: None,
    )

    with pytest.raises(MarketDataError):
        provider.get_ohlcv("BTC-USDT", "1h", start, end)
