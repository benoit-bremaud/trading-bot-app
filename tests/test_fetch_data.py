import pytest
from kucoin.client import Market
import os
from dotenv import load_dotenv
import time

load_dotenv()


def test_fetch_kline_data():
    api_url = os.getenv('KUCOIN_API_URL', 'https://api.kucoin.com')
    client = Market(url=api_url)
    symbol = 'BTC-USDT'
    interval = '1hour'
    now = int(time.time())
    start = now - 24 * 60 * 60  # 24h en arrière

    data = client.get_kline(symbol=symbol, kline_type=interval, startAt=start, endAt=now)

    assert data is not None
    assert isinstance(data, list)
    assert len(data) > 0

    # Optionnel : vérifier la structure du premier élément
    first = data[0]
    assert len(first) == 7  # time, open, close, high, low, volume, turnover
