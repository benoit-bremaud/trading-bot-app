# Trading Bot App

[![Python CI](https://github.com/benoit-bremaud/trading-bot-app/actions/workflows/ci.yml/badge.svg)](https://github.com/benoit-bremaud/trading-bot-app/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/benoit-bremaud/trading-bot-app/branch/main/graph/badge.svg)](https://codecov.io/gh/benoit-bremaud/trading-bot-app)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

Bot de trading algorithmique connecté à l'API KuCoin.

🎯 **Objectif** : Automatiser l'analyse de marchés financiers et la prise de décision d'achat/vente en s'appuyant sur des données historiques, des indicateurs techniques et de l'intelligence artificielle (IA).

## 🔧 Installation

1. **Clonez le dépôt** :

```bash
git clone git@github.com:benoit-bremaud/trading-bot-app.git
cd trading-bot-app
```

2. **Créez un environnement virtuel** :

```bash
python3 -m venv venv
source venv/bin/activate  # Windows : venv\Scripts\activate
```

3. **Installez les dépendances** :

```bash
# Pour le développement (inclut les outils de test et linting)
pip install -e . -r requirements-dev.txt

# Pour la production uniquement
pip install -e . -r requirements-prod.txt
```

4. **Configurez les variables d'environnement** :

Copiez le fichier `.env.example` en `.env` et remplissez vos clés API KuCoin.

## ▶️ Utilisation

### Ingestion de données

Récupérez des données historiques depuis KuCoin :

```bash
python scripts/ingest_candles.py --symbol BTC-USDT --timeframe 1h --days 30
```

### Backtest

Exécutez un backtest sur des données historiques :

```bash
python scripts/backtest.py --symbol BTC-USDT --timeframe 1h --days 30 --cash 10000
```

Les résultats affichent le PnL, le rendement en %, et le nombre de trades.

### Dashboard Web

Lancez le dashboard pour visualiser les données, indicateurs et signaux :

```bash
python scripts/start_dashboard.py
```

Ouvrez votre navigateur : [http://localhost:5000](http://localhost:5000)

Le dashboard permet de :
- Visualiser les graphiques candlestick avec volume
- Afficher les indicateurs techniques (RSI, MACD, Bollinger Bands)
- Voir les signaux de trading (buy/sell)
- Lancer des backtests et afficher les résultats

Voir [dashboard/README.md](dashboard/README.md) pour plus de détails.

### Paper Trading

Lancez le bot en mode paper trading (simulation en temps réel) :

```bash
# Mode normal (exécute les ordres simulés)
python scripts/run.py --symbol BTC-USDT --timeframe 1h --cash 10000

# Mode dry-run (affiche les signaux sans exécuter)
python scripts/run.py --symbol BTC-USDT --timeframe 1h --cash 10000 --dry-run
```

Le bot récupère les données en temps réel, génère des signaux, et exécute les trades en mémoire.
Utilisez `Ctrl+C` pour arrêter le bot proprement.

### Exécution des tests

```bash
# Tous les tests
pytest tests/

# Avec couverture de code
pytest tests/ --cov=trading_bot --cov=scripts --cov-report=html

# Tests spécifiques (sans les tests d'intégration)
pytest tests/ -m "not integration"
```

### Linting et formatage

```bash
# Vérifier le code
ruff check .

# Formater le code
ruff format .

# Vérification de types
mypy trading_bot tests
```

## 📂 Architecture du projet

Le projet suit une **architecture hexagonale (Clean Architecture)** :

```text
trading-bot-app/
├── trading_bot/
│   ├── domain/              # Entités métier (Candle, PairProfile, etc.)
│   ├── application/         # Logique métier (SignalModel, RiskManager, Backtest)
│   ├── infrastructure/      # Adaptateurs externes (KuCoin, CSV, PaperTrading)
│   ├── shared/              # Utilitaires partagés (config, logging, metrics)
│   └── adapters/            # Adaptateurs d'interface
├── scripts/                 # Scripts CLI (ingest_candles.py)
├── tests/                   # Tests unitaires et d'intégration
├── config/                  # Fichiers de configuration
├── data/                    # Données locales (ignorées par Git)
├── models/                  # Modèles IA entraînés
└── notebooks/               # Notebooks Jupyter pour exploration
```

Voir [ARCHITECTURE.md](trading_bot/ARCHITECTURE.md) pour plus de détails.

## 📈 Roadmap

Voir [ROADMAP.md](ROADMAP.md) pour la feuille de route détaillée.

### Statut actuel

- ✅ Architecture hexagonale mise en place
- ✅ Ingestion de données depuis KuCoin
- ✅ Repository CSV pour stockage local
- ✅ Moteur de backtest simple (Buy & Hold)
- ✅ Modèles de signal (Moving Average Crossover, Indicator-Based)
- ✅ Gestionnaire de risque (position sizing)
- ✅ **Pipeline d'indicateurs techniques (RSI, MACD, Bollinger Bands)**
- ✅ **Exécuteur d'ordres paper trading**
- ✅ **CLI entrypoints (ingest, backtest, run)**
- ✅ Suite de tests complète (90% de couverture)
- ✅ CI/CD avec GitHub Actions

## 🤖 Fonctionnalités

### Implémentées
- ✅ Indicateurs techniques : RSI, MACD, Bandes de Bollinger
- ✅ Pipeline d'enrichissement de données avec indicateurs
- ✅ Signal model basé sur les indicateurs techniques
- ✅ Architecture hexagonale pour indicateurs (ports + implémentations)
- ✅ **Dashboard web Flask avec Plotly.js**
- ✅ **API REST pour candles, signaux, backtest**

### Prévues
- Feature engineering et pipeline ML
- Reconnaissance de patterns (pas de prédiction!)
- Modèles ML (Random Forest, XGBoost, LSTM)
- Métriques avancées (Sharpe, drawdown, Sortino)
- WebSocket temps réel KuCoin

## 📄 Licence

Projet personnel de Benoît Bremaud. Tous droits réservés.
Usage libre non commercial (sous réserve d'approbation).
