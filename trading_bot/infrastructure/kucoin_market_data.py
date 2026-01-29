from __future__ import annotations

import os
import time
from collections.abc import Callable, Iterable, Sequence
from datetime import UTC, datetime
from typing import Any

from kucoin.client import Market

from trading_bot.application.ports import MarketDataProvider
from trading_bot.domain.entities import Candle
from trading_bot.shared.logging import ContextLogger, get_logger
from trading_bot.shared.metrics import MetricsRecorder, NoopMetrics


class MarketDataError(RuntimeError):
    pass


_TIMEFRAME_ALIASES: dict[str, str] = {
    "1m": "1min",
    "1min": "1min",
    "3m": "3min",
    "3min": "3min",
    "5m": "5min",
    "5min": "5min",
    "15m": "15min",
    "15min": "15min",
    "30m": "30min",
    "30min": "30min",
    "1h": "1hour",
    "1hour": "1hour",
    "2h": "2hour",
    "2hour": "2hour",
    "4h": "4hour",
    "4hour": "4hour",
    "6h": "6hour",
    "6hour": "6hour",
    "8h": "8hour",
    "8hour": "8hour",
    "12h": "12hour",
    "12hour": "12hour",
    "1d": "1day",
    "1day": "1day",
    "1w": "1week",
    "1week": "1week",
}

_TIMEFRAME_SECONDS: dict[str, int] = {
    "1min": 60,
    "3min": 3 * 60,
    "5min": 5 * 60,
    "15min": 15 * 60,
    "30min": 30 * 60,
    "1hour": 60 * 60,
    "2hour": 2 * 60 * 60,
    "4hour": 4 * 60 * 60,
    "6hour": 6 * 60 * 60,
    "8hour": 8 * 60 * 60,
    "12hour": 12 * 60 * 60,
    "1day": 24 * 60 * 60,
    "1week": 7 * 24 * 60 * 60,
}


def to_kucoin_timeframe(timeframe: str) -> str:
    key = timeframe.strip().lower()
    if key in _TIMEFRAME_ALIASES:
        return _TIMEFRAME_ALIASES[key]
    raise ValueError(f"Unsupported timeframe '{timeframe}' for KuCoin")


def timeframe_seconds(timeframe: str) -> int:
    kucoin_timeframe = to_kucoin_timeframe(timeframe)
    return _TIMEFRAME_SECONDS[kucoin_timeframe]


def normalize_kucoin_kline(row: Sequence[Any]) -> Candle:
    if len(row) < 6:
        raise MarketDataError(f"Unexpected kline row length: {len(row)}")

    timestamp = _parse_epoch_seconds(row[0])
    open_price = float(row[1])
    close_price = float(row[2])
    high_price = float(row[3])
    low_price = float(row[4])
    volume = float(row[5])

    return Candle(
        timestamp=datetime.fromtimestamp(timestamp, tz=UTC),
        open=open_price,
        high=high_price,
        low=low_price,
        close=close_price,
        volume=volume,
    )


def _parse_epoch_seconds(raw: Any) -> int:
    try:
        value = int(float(raw))
    except (TypeError, ValueError) as exc:
        raise MarketDataError(f"Invalid timestamp value: {raw!r}") from exc

    if value < 0:
        raise MarketDataError(f"Negative timestamp value: {raw!r}")

    if value > 1_000_000_000_000:
        value //= 1000

    return value


def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def _dedupe_sorted(candles: Iterable[Candle]) -> list[Candle]:
    deduped = {candle.timestamp: candle for candle in candles}
    return [deduped[key] for key in sorted(deduped)]


class KucoinMarketDataProvider(MarketDataProvider):
    def __init__(
        self,
        client: Market | None = None,
        *,
        api_url: str | None = None,
        max_retries: int = 2,
        retry_backoff: float = 0.5,
        metrics: MetricsRecorder | None = None,
        logger: ContextLogger | None = None,
        sleep: Callable[[float], None] | None = None,
    ) -> None:
        self._client = client or Market(url=api_url or _default_api_url())
        self._max_retries = max_retries
        self._retry_backoff = retry_backoff
        self._metrics = metrics or NoopMetrics()
        self._logger = logger or get_logger(__name__).bind(source="kucoin")
        self._sleep = sleep or time.sleep

    def get_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        start: datetime,
        end: datetime,
    ) -> Sequence[Candle]:
        start_dt = _ensure_utc(start)
        end_dt = _ensure_utc(end)
        if start_dt >= end_dt:
            raise ValueError("start must be before end")

        kucoin_timeframe = to_kucoin_timeframe(timeframe)
        start_at = int(start_dt.timestamp())
        end_at = int(end_dt.timestamp())

        self._logger.info(
            "kucoin_fetch_ohlcv",
            symbol=symbol,
            timeframe=kucoin_timeframe,
            start=start_at,
            end=end_at,
        )

        rows = self._fetch_with_retries(
            symbol=symbol,
            kline_type=kucoin_timeframe,
            start_at=start_at,
            end_at=end_at,
        )

        candles: list[Candle] = []
        for row in rows:
            candle = normalize_kucoin_kline(row)
            if start_dt <= candle.timestamp <= end_dt:
                candles.append(candle)

        result = _dedupe_sorted(candles)
        self._metrics.gauge(
            "market_data.candles",
            len(result),
            source="kucoin",
            symbol=symbol,
            timeframe=kucoin_timeframe,
        )
        return result

    def _fetch_with_retries(
        self,
        *,
        symbol: str,
        kline_type: str,
        start_at: int,
        end_at: int,
    ) -> list[list[Any]]:
        attempt = 0
        while True:
            try:
                self._metrics.increment("market_data.request", source="kucoin")
                data = self._client.get_kline(
                    symbol=symbol,
                    kline_type=kline_type,
                    startAt=start_at,
                    endAt=end_at,
                )
                if not isinstance(data, list):
                    raise MarketDataError("KuCoin response is not a list")
                return data
            except Exception as exc:  # pragma: no cover - defensive logging
                attempt += 1
                if attempt > self._max_retries:
                    raise MarketDataError("KuCoin request failed") from exc
                self._metrics.increment("market_data.retry", source="kucoin")
                self._logger.warning(
                    "kucoin_request_failed",
                    attempt=attempt,
                    error=str(exc),
                )
                self._sleep(self._retry_backoff * (2 ** (attempt - 1)))


def _default_api_url() -> str:
    return os.getenv("KUCOIN_API_URL", "https://api.kucoin.com")
