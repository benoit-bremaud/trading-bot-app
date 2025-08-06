from kucoin.client import Market
import os
from dotenv import load_dotenv
import time
import datetime
import pandas as pd

# Charger les variables d'environnement
load_dotenv()

# Créer le client KuCoin
api_url = os.getenv('KUCOIN_API_URL', 'https://api.kucoin.com')
client = Market(url=api_url)

# Définir la paire et la période
symbol = 'BTC-USDT'
interval = '1hour'

# Définir startAt (24h en arrière) et endAt (maintenant)
now = int(time.time())
start = now - 24 * 60 * 60  # 24 heures en secondes

# Récupérer les données Kline
kline = client.get_kline(symbol=symbol, kline_type=interval, startAt=start, endAt=now)

# Afficher les 5 premières bougies sous forme DataFrame
df = pd.DataFrame(kline, columns=["time", "open", "close", "high", "low", "volume", "turnover"])
print(df.head())
