# CLAUDE.md — trading-bot-app

Project rules for AI coding agents. Global rules (`~/.claude/CLAUDE.md`, `~/.agent-rules/common.md`) still apply; this file adds what is specific to this repository.

## Goal

A spot bot that **accumulates more BTC (measured in sats) than simply holding (HODL)**, on OKX Europe BTC/USDC. Success is never measured in fiat profit.

## Source of truth

- Requirements: [`docs/requirements/btc-accumulation.md`](docs/requirements/btc-accumulation.md) (R01–R40). Any change in behaviour must trace back to a requirement; a new need means a new requirement first.
- Proof before real money, in phases: R26 (historical walk-forward), R27 (forward paper trading), R28 (real-money ramp-up).
- Plan: [`ROADMAP.md`](ROADMAP.md). Log: [`PROJECT_LOG.md`](PROJECT_LOG.md).
- Tracking: GitHub Project #68; one issue per brick, the PR closes it (`Closes #N`).

## Stack

- Python 3.11+, `ruff` (lint + format), `mypy`, `pytest` (+ `pytest-cov`).
- Build decision R40: own engine with `ccxt` in production, NautilusTrader as a CI execution oracle.

## Running the tests

The local `venv/` (untracked) is broken under Python 3.14 (no pip, no pytest). Use the Makefile, which creates `.venv`:

```bash
make venv
make check-local
```

`check-local` runs ruff, mypy, pytest with coverage, Semgrep (needs Docker) and gitleaks; `make test` and `make sonar-scan` (needs `SONAR_TOKEN`) are also available. Without `make`: `python3 -m venv .venv && .venv/bin/pip install -e . -r requirements-dev.txt`, then `.venv/bin/pytest tests/`.

`requirements-dev.txt` pins `setuptools<81`: `kucoin-python` (legacy) still imports `pkg_resources`, removed in setuptools 81; drop the pin once the KuCoin code is gone.

## Conception first

UML before code: model each feature under `docs/architecture/diagrams/<feature>/` (Mermaid, skill `uml-diagram-new`) and get it validated before implementing.

## Forbidden

- No real-money trading before phase 3 (R28) is reached and approved. Until then: backtest and paper only.
- No exchange API key with withdrawal permission, ever. Trade-only keys, IP-restricted where possible.
- No secrets in the repository: no `.env`, keys, tokens or account IDs in tracked files, logs or tests. `.env.example` holds placeholders only.
- No investment-advice framing in docs or code comments: this is a personal experiment.
