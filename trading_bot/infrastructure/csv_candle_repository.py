from __future__ import annotations

import csv
import os
from collections.abc import Sequence
from datetime import UTC, datetime

from trading_bot.application.ports import CandleRepository
from trading_bot.domain.entities import Candle


class CsvCandleRepository(CandleRepository):
    def __init__(self, base_dir: str = "data/candles") -> None:
        self._base_dir = base_dir

    def save(self, symbol: str, timeframe: str, candles: Sequence[Candle]) -> None:
        path = self._file_path(symbol, timeframe)
        os.makedirs(self._base_dir, exist_ok=True)

        existing = self.load(symbol, timeframe)
        deduped: dict[datetime, Candle] = {candle.timestamp: candle for candle in existing}
        for candle in candles:
            normalized = _normalize_candle(candle)
            deduped[normalized.timestamp] = normalized

        ordered = [deduped[key] for key in sorted(deduped)]
        with open(path, "w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["timestamp", "open", "high", "low", "close", "volume"])
            for candle in ordered:
                writer.writerow(
                    [
                        int(candle.timestamp.timestamp()),
                        candle.open,
                        candle.high,
                        candle.low,
                        candle.close,
                        candle.volume,
                    ]
                )

    def load(
        self,
        symbol: str,
        timeframe: str,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> Sequence[Candle]:
        path = self._file_path(symbol, timeframe)
        if not os.path.exists(path):
            return []

        start_dt = _ensure_utc(start) if start else None
        end_dt = _ensure_utc(end) if end else None
        candles: list[Candle] = []

        with open(path, encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                timestamp = datetime.fromtimestamp(int(row["timestamp"]), tz=UTC)
                if start_dt and timestamp < start_dt:
                    continue
                if end_dt and timestamp > end_dt:
                    continue
                candles.append(
                    Candle(
                        timestamp=timestamp,
                        open=float(row["open"]),
                        high=float(row["high"]),
                        low=float(row["low"]),
                        close=float(row["close"]),
                        volume=float(row["volume"]),
                    )
                )

        return candles

    def _file_path(self, symbol: str, timeframe: str) -> str:
        safe_symbol = symbol.replace("/", "-")
        filename = f"{safe_symbol}_{timeframe}.csv"
        return os.path.join(self._base_dir, filename)


def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _normalize_candle(candle: Candle) -> Candle:
    timestamp = _ensure_utc(candle.timestamp)
    if timestamp is candle.timestamp:
        return candle
    return Candle(
        timestamp=timestamp,
        open=candle.open,
        high=candle.high,
        low=candle.low,
        close=candle.close,
        volume=candle.volume,
    )
