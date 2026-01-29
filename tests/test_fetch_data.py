import os
from datetime import UTC, datetime, timedelta

import pytest
from dotenv import load_dotenv

from trading_bot.infrastructure.kucoin_market_data import KucoinMarketDataProvider

load_dotenv()

pytestmark = pytest.mark.integration


@pytest.mark.skipif(
    os.getenv("RUN_INTEGRATION") != "1",
    reason="Set RUN_INTEGRATION=1 to run KuCoin API tests.",
)
def test_fetch_kline_data():
    provider = KucoinMarketDataProvider()
    end = datetime.now(UTC)
    start = end - timedelta(hours=24)

    candles = provider.get_ohlcv("BTC-USDT", "1h", start, end)

    assert isinstance(candles, list)
    assert len(candles) > 0
