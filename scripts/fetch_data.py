import os

from kucoin.client import Market
from dotenv import load_dotenv

load_dotenv()

api_url = os.getenv('KUCOIN_API_URL', 'https://api.kucoin.com')

client = Market(url=api_url)

symbol = 'BTC-USDT'
kline = client.get_kline(symbol=symbol, kline_type='1hour', startAt=None, endAt=None)
print(kline[:5])
