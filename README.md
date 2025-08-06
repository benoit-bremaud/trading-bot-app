# Trading Bot App

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
pip install -r requirements.txt
```

4. **Configurez les variables d'environnement** :

Copiez le fichier `.env.example` en `.env` et remplissez vos clés API KuCoin.

## ▶️ Utilisation

Lancez un script de test pour vérifier la connexion à KuCoin :

```bash
python scripts/fetch_data.py
```

Ce script récupère les 5 dernières bougies 1H de la paire BTC/USDT.

## 📂 Arborescence du projet

```text
trading-bot-app/
├── trading_bot/         # Code source principal
│   └── __init__.py
├── scripts/             # Scripts d’exécution ponctuels
│   └── fetch_data.py
├── data/                # Données locales (ignorées par Git)
├── models/              # Modèles IA entraînés (fichiers .h5, .pt)
├── README.md
├── requirements.txt
├── .gitignore
└── .env.example
```

## 📈 Roadmap (MVP)

- [x] Configuration initiale du projet
- [ ] Récupération de données (API KuCoin)
- [ ] Affichage graphique (chandeliers, indicateurs)
- [ ] Backtesting de stratégies simples
- [ ] Implémentation IA (figure recognition)
- [ ] Bot exécutable et dashboard web

## 🤖 Fonctionnalités prévues

- Lecture temps réel du marché via WebSocket KuCoin
- Calcul d'indicateurs : RSI, MACD, bandes de Bollinger
- Reconnaissance de figures : tête-épaules, double creux
- Trading automatique sur signal validé
- Tableau de bord interactif (en développement)

## 📄 Licence

Projet personnel de Benoît Bremaud. Tous droits réservés.
Usage libre non commercial (sous réserve d'approbation).
