# ROADMAP

## Project summary
- Goal: MVP KuCoin spot trading bot with AI, backtesting, and dynamic money management.
- Scope: data ingestion, signals/AI, backtesting, risk, execution, monitoring, and operator UX.
- Constraints: CLEAN/SOLID architecture, patterns only when justified, tests are mandatory.
- Process: commit + push + PR after each feature; PR body in Markdown with Summary/Testing/Notes.
- Roadmap maintenance: update this file after each merge and when new feature ideas appear.

## Status legend
- [DONE] merged to main
- [IN PROGRESS] active work, not merged yet
- [PLANNED] not started

## Roadmap by domain

### Architecture and foundations
- [DONE] CLEAN/SOLID layers with domain/application/infrastructure/adapters/shared.
- [DONE] Ports and entities defined, ARCHITECTURE.md documented.
- [DONE] Base test suite for architecture/imports.

### Configuration
- [DONE] Dynamic config merge (default -> timeframe -> pair -> pair+timeframe) + example + tests.
- [PLANNED] Runtime config validation of required keys per feature.

### Observability
- [DONE] Context logger + JSON formatter + metrics (in-memory/noop) + tests.
- [PLANNED] Metrics export integration (Prometheus or similar) and tracing.

### CI/Quality
- [DONE] CI with Python 3.11/3.12 + ruff/mypy/pytest.
- [PLANNED] Cache pip and optimize dependency install time.

### Data ingestion (KuCoin spot)
- [PLANNED] KuCoin REST client wrapper with retries and rate-limit handling.
- [PLANNED] OHLCV normalization to domain Candle.
- [PLANNED] Market data provider port implementation + tests.
- [PLANNED] Optional local persistence (raw + normalized).

### Data processing and features
- [PLANNED] Indicator pipeline (RSI, MACD, Bollinger).
- [PLANNED] Feature engineering for AI models.

### Strategy and AI
- [PLANNED] Signal model interface + baseline heuristic model.
- [PLANNED] Pattern recognition (head-shoulders, double bottom).
- [PLANNED] Model training and evaluation workflow.

### Backtesting
- [PLANNED] Backtest engine for candle replay.
- [PLANNED] Performance metrics (PnL, drawdown, sharpe, win rate).
- [PLANNED] Walk-forward / out-of-sample evaluation.

### Risk and money management
- [PLANNED] Position sizing (risk % per trade, dynamic based on volatility/ATR).
- [PLANNED] Portfolio constraints and max exposure rules.

### Execution (spot)
- [PLANNED] Paper trading mode.
- [PLANNED] Live order execution (market orders first).
- [PLANNED] Safety checks (min size, slippage, cooldowns).

### UX / Ops
- [PLANNED] CLI entrypoints for ingestion, backtests, and live.
- [PLANNED] Minimal dashboard (signals, positions, PnL).

## History (chronological)

- 2026-01-29: ROADMAP.md created; state captured.
- Prior to 2026-01-29 (merged):
  - Architecture: CLEAN layout, ports, entities, ARCHITECTURE.md, tests.
  - Config: dynamic merge + example + tests (PR #2).
  - Cleanup: removed IDE files and updated .gitignore (PR #3).
  - Logging + metrics scaffolding + tests (PR #4).
- 2026-01-29 (merged, PR #5):
  - CI quality gates: ruff + mypy + pytest on Python 3.11/3.12.
  - Formatting and typing cleanup to satisfy ruff/mypy.
  - CI test fix: set PYTHONPATH for pytest.
  - Added requirements-dev.txt and pyproject.toml tooling config.

## Current focus
- Start P1: data-ingestion-kucoin (client, normalization, tests).
