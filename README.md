# Trading Bot App

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

A personal experiment: a BTC/USDC spot bot whose only goal is to **end up with more BTC (in sats) than simply holding**. Not investment advice.

The project is being reset from an earlier KuCoin BTC-USDT MVP. Real money is only considered after two proof phases (historical walk-forward, then forward paper trading).

- Requirements (source of truth): [docs/requirements/btc-accumulation.md](docs/requirements/btc-accumulation.md)
- Plan: [ROADMAP.md](ROADMAP.md) · Log: [PROJECT_LOG.md](PROJECT_LOG.md)
- Rules for contributors and AI agents: [CLAUDE.md](CLAUDE.md)

## Development

```bash
python3 -m venv .venv
.venv/bin/pip install "setuptools<81" -e . -r requirements-dev.txt
.venv/bin/pytest tests/ --cov=trading_bot --cov=scripts
.venv/bin/ruff check . && .venv/bin/mypy trading_bot tests
```

The legacy code (KuCoin ingestion, backtest, paper trading, Flask dashboard) still lives in `trading_bot/`, `scripts/` and `dashboard/`; its future is decided during the UML conception step (see the roadmap). Architecture notes: [trading_bot/ARCHITECTURE.md](trading_bot/ARCHITECTURE.md).

## Licence

Personal project of Benoît Bremaud. All rights reserved.
