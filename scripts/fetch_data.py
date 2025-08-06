from kucoin.client import Market
import os
from dotenv import load_dotenv
import time
from trading_bot.data_handler import save_kline_to_csv

load_dotenv()

api_url = os.getenv('KUCOIN_API_URL', 'https://api.kucoin.com')
client = Market(url=api_url)

symbol = 'BTC-USDT'
interval = '1hour'

now = int(time.time())
start = now - 24 * 60 * 60  # 24 heures en arrière

kline = client.get_kline(symbol=symbol, kline_type=interval, startAt=start, endAt=now)

save_kline_to_csv(kline, symbol)
