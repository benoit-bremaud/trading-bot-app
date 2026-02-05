# Trading Bot Dashboard

Interface web pour visualiser les données de marché, indicateurs techniques, signaux de trading et résultats de backtest.

## 🚀 Démarrage rapide

### 1. Installer les dépendances

```bash
pip install -e . -r requirements-prod.txt
```

### 2. Récupérer des données historiques

```bash
python scripts/ingest_candles.py --symbol BTC-USDT --timeframe 1h --days 30
```

### 3. Lancer le dashboard

```bash
python scripts/start_dashboard.py
```

Ou directement :

```bash
python dashboard/app.py
```

### 4. Ouvrir dans le navigateur

```
http://localhost:5000
```

## 📊 Fonctionnalités

### ✅ Implémenté (MVP)

- **Graphiques candlestick** : Visualisation OHLCV avec volume
- **Indicateurs techniques** : RSI, MACD, Bollinger Bands (overlay sur graphique)
- **Signaux de trading** : Marqueurs buy/sell sur le graphique
- **Backtest** : Exécution et affichage des résultats (PnL, trades, win rate)

### 🔜 À venir

- Comparaison de stratégies multiples
- Métriques avancées (Sharpe, drawdown, Sortino)
- Graphique d'équité (évolution du capital)
- Export des résultats en CSV
- Mode temps réel (WebSocket)

## 🎨 Interface

### Écran principal

1. **Sélecteurs** : Symbol et Timeframe
2. **Boutons** :
   - 📊 **Charger les données** : Affiche le graphique candlestick
   - 🎯 **Afficher les signaux** : Ajoute les signaux buy/sell
   - ⚡ **Lancer Backtest** : Exécute et affiche les résultats

3. **Graphique interactif** : Plotly.js avec zoom, pan, hover

4. **Résultats backtest** : Tableau de métriques

## 🛠️ API Endpoints

### GET /api/candles/{symbol}/{timeframe}

Récupère les données OHLCV pour un symbol/timeframe.

**Exemple** :
```bash
curl http://localhost:5000/api/candles/BTC-USDT/1h
```

**Réponse** :
```json
[
  {
    "timestamp": "2025-01-01T00:00:00+00:00",
    "open": 50000.0,
    "high": 50500.0,
    "low": 49800.0,
    "close": 50200.0,
    "volume": 1000.0
  }
]
```

### GET /api/signals/{symbol}/{timeframe}

Génère les signaux de trading pour un symbol/timeframe.

**Exemple** :
```bash
curl http://localhost:5000/api/signals/BTC-USDT/1h
```

**Réponse** :
```json
[
  {
    "timestamp": "2025-01-01T12:00:00+00:00",
    "type": "buy",
    "price": 50200.0,
    "confidence": 0.75,
    "reason": "Entry signal (score: 0.75)"
  }
]
```

### POST /api/backtest

Lance un backtest avec paramètres personnalisés.

**Exemple** :
```bash
curl -X POST http://localhost:5000/api/backtest \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "BTC-USDT",
    "timeframe": "1h",
    "initial_cash": 10000,
    "risk_per_trade": 0.02
  }'
```

**Réponse** :
```json
{
  "symbol": "BTC-USDT",
  "timeframe": "1h",
  "initial_cash": 10000.0,
  "final_equity": 10500.0,
  "pnl": 500.0,
  "pnl_pct": 5.0,
  "num_trades": 10,
  "winning_trades": 6,
  "losing_trades": 4,
  "win_rate": 60.0
}
```

### GET /health

Health check endpoint.

**Exemple** :
```bash
curl http://localhost:5000/health
```

**Réponse** :
```json
{"status": "ok"}
```

## 🏗️ Architecture

```
dashboard/
├── app.py                    # Flask application (point d'entrée)
├── api/                      # API endpoints (blueprints)
│   ├── candles.py           # GET /api/candles
│   ├── signals.py           # GET /api/signals
│   └── backtest.py          # POST /api/backtest
├── templates/
│   └── index.html           # Interface web principale
└── static/
    ├── css/
    │   └── style.css        # Styles CSS
    └── js/
        └── charts.js        # Logique Plotly.js
```

### Respect de l'architecture CLEAN

- **Dashboard** = Adaptateur (couche externe)
- **API endpoints** → Appellent `application/` (logique métier)
- **Pas de logique métier dans le dashboard** (lecture seule)
- **Dépendances** : Dashboard → Application → Domain ✅

## 🧪 Tests

```bash
# Tests unitaires du dashboard
pytest tests/test_dashboard_api.py -v

# Tous les tests
pytest tests/ -v
```

## 🔧 Configuration

Le dashboard utilise les mêmes composants que le reste du projet :

- **CsvCandleRepository** : Lecture des données depuis `data/candles/`
- **DefaultIndicatorPipeline** : Calcul RSI, MACD, Bollinger Bands
- **IndicatorBasedSignalModel** : Génération de signaux
- **BacktestEngine** : Exécution des backtests

Pas de configuration supplémentaire nécessaire.

## 📝 Notes

- Le dashboard est en **lecture seule** (pas d'exécution d'ordres réels)
- Les données doivent être ingérées via `scripts/ingest_candles.py`
- Le serveur est en mode **debug** par défaut (désactiver en production)
- Le dashboard est accessible sur **0.0.0.0** (toutes les interfaces réseau)

## 🚀 Prochaines étapes

Voir [ROADMAP.md](../ROADMAP.md) pour le plan complet :

- **Track A2** : Métriques avancées, comparaison stratégies
- **Track B** : Pipeline IA, feature engineering, modèles ML
