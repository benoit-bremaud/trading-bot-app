from datetime import UTC, datetime, timedelta

from trading_bot.domain.entities import Candle
from trading_bot.infrastructure.csv_candle_repository import CsvCandleRepository


def test_csv_repository_roundtrip(tmp_path):
    repo = CsvCandleRepository(base_dir=str(tmp_path))
    base_time = datetime(2024, 1, 1, tzinfo=UTC)
    candles = [
        Candle(base_time, 1.0, 1.5, 0.9, 1.2, 100.0),
        Candle(base_time + timedelta(hours=1), 1.2, 1.6, 1.1, 1.3, 120.0),
    ]

    repo.save("BTC-USDT", "1h", candles)
    loaded = repo.load("BTC-USDT", "1h")

    assert loaded == candles


def test_csv_repository_upserts_on_timestamp(tmp_path):
    repo = CsvCandleRepository(base_dir=str(tmp_path))
    timestamp = datetime(2024, 1, 1, tzinfo=UTC)
    first = Candle(timestamp, 1.0, 1.5, 0.9, 1.2, 100.0)
    updated = Candle(timestamp, 1.0, 1.5, 0.9, 1.4, 100.0)

    repo.save("BTC-USDT", "1h", [first])
    repo.save("BTC-USDT", "1h", [updated])

    loaded = repo.load("BTC-USDT", "1h")
    assert loaded == [updated]


def test_csv_repository_filters_by_range(tmp_path):
    repo = CsvCandleRepository(base_dir=str(tmp_path))
    base_time = datetime(2024, 1, 1, tzinfo=UTC)
    candles = [
        Candle(base_time, 1.0, 1.5, 0.9, 1.2, 100.0),
        Candle(base_time + timedelta(hours=1), 1.2, 1.6, 1.1, 1.3, 120.0),
        Candle(base_time + timedelta(hours=2), 1.3, 1.7, 1.2, 1.4, 130.0),
    ]

    repo.save("BTC-USDT", "1h", candles)

    start = base_time + timedelta(hours=1)
    end = base_time + timedelta(hours=2)
    loaded = repo.load("BTC-USDT", "1h", start=start, end=end)

    assert loaded == candles[1:]
