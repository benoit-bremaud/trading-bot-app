import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os
import sys


def plot_kline(csv_filepath):
    if not os.path.exists(csv_filepath):
        print(f"Fichier {csv_filepath} non trouvé.")
        sys.exit(1)

    df = pd.read_csv(csv_filepath)
    df['time'] = pd.to_datetime(df['time'])
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    for idx, row in df.iterrows():
        color = 'green' if row['close'] >= row['open'] else 'red'
        ax.plot([row['time'], row['time']], [row['low'], row['high']], color='black')
        ax.plot([row['time'], row['time']], [row['open'], row['close']], color=color, linewidth=6)

    ax.xaxis.set_major_locator(mdates.HourLocator(interval=2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
    plt.xticks(rotation=45)
    plt.title('Graphique chandelier BTC-USDT')
    plt.xlabel('Temps')
    plt.ylabel('Prix')
    plt.grid(True)
    plt.tight_layout()

    output_file = 'kline_plot.png'
    plt.savefig(output_file)
    print(f"Graphique sauvegardé sous {output_file}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage : python scripts/plot_kline.py chemin/vers/fichier.csv")
        sys.exit(1)

    csv_file = sys.argv[1]
    plot_kline(csv_file)
