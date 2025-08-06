import os
import pandas as pd
from datetime import datetime


def save_kline_to_csv(data, symbol):
    df = pd.DataFrame(data, columns=["time", "open", "close", "high", "low", "volume", "turnover"])
    # Conversion forcée en int avant pd.to_datetime pour éviter le FutureWarning
    df['time'] = pd.to_datetime(df['time'].astype(int), unit='s')
    
    folder = 'data/raw'
    os.makedirs(folder, exist_ok=True)
    
    date_str = datetime.now().strftime("%Y%m%d")
    filename = f"{folder}/{symbol}_{date_str}.csv"
    
    df.to_csv(filename, index=False)
    print(f"Saved data to {filename}")

