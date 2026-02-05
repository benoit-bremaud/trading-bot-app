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

## Priority backlog (MVP)

### P0 — MUST HAVE
- [DONE] Data ingestion KuCoin (spot): robust client + retries/backoff + timeframe mapping.
- [DONE] OHLCV normalization to `Candle` + tests.
- [DONE] Market data provider port implementation + tests.
- [DONE] Simple historical storage (CSV) for replay + tests.
- [DONE] Minimal backtest loop with PnL + tests.
- [DONE] Risk manager baseline (max % per trade, optional ATR/vol) + tests.

### P1 — IMPORTANT
- [DONE] Baseline signal model (rules-based).
- [DONE] Paper trading execution adapter.
- [DONE] Minimal CLI entrypoints (ingest/backtest/run).

### Data ingestion (KuCoin spot)
- [DONE] KuCoin REST client wrapper with retries and rate-limit handling.
- [DONE] OHLCV normalization to domain Candle.
- [DONE] Market data provider port implementation + tests.
- [PLANNED] Optional local persistence (raw + normalized).

### Historical storage
- [DONE] CSV candle repository with upsert and range filtering + tests.

### Data processing and features
- [DONE] Indicator pipeline (RSI, MACD, Bollinger).
- [PLANNED] Feature engineering for AI models.

### Strategy and AI
- [DONE] Signal model interface + baseline heuristic model.
- [DONE] Indicator-based signal model (RSI, MACD, Bollinger Bands).
- [PLANNED] Pattern recognition (head-shoulders, double bottom).
- [PLANNED] Model training and evaluation workflow.

### Backtesting
- [DONE] Backtest engine for candle replay (minimal PnL) + tests.
- [PLANNED] Performance metrics (PnL, drawdown, sharpe, win rate).
- [PLANNED] Walk-forward / out-of-sample evaluation.

### Risk and money management
- [DONE] Position sizing (risk % per trade, dynamic based on volatility/ATR).
- [PLANNED] Portfolio constraints and max exposure rules.

### Execution (spot)
- [DONE] Paper trading mode.
- [PLANNED] Live order execution (market orders first).
- [PLANNED] Safety checks (min size, slippage, cooldowns).

### UX / Ops
- [DONE] CLI entrypoints for ingestion, backtests, and live.
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
- 2026-01-29: Prioritized MVP tasks (P0/P1) agreed.
- 2026-01-29 (merged, PR #7):
  - KuCoin market data provider with retries, timeframe mapping, and OHLCV normalization.
  - Unit tests for normalization, ordering, and retries.
  - Integration test for KuCoin fetch gated by RUN_INTEGRATION=1.
- 2026-01-29 (merged, PR #9):
  - CSV candle repository + tests.
- 2026-01-29 (merged, PR #10):
  - ROADMAP update after CSV storage.
- 2026-01-29 (merged, PR #11):
  - Minimal backtest engine (buy-and-hold) with BacktestResult + tests.
- 2026-01-29 (merged, PR #12):
  - Roadmap update after backtest merge.
- 2026-01-29 (merged, PR #13):
  - Roadmap update after PR #12.
- 2026-01-29 (merged, PR #14):
  - Baseline risk manager with position sizing + tests.
- 2026-01-29 (merged, PR #15):
  - Roadmap update after PR #14.
- 2026-01-29 (merged, PR #17):
  - Baseline signal model (moving-average crossover) + tests.
- 2026-01-29 (merged, PR #18):
  - Roadmap update after PR #17.
- 2026-01-29 (merged, PR #16):
  - Roadmap update after PR #15.
- 2026-02-05:
  - CLI entrypoints: backtest.py and run.py scripts.
  - Paper trading execution fully functional.
  - Tests for all CLI scripts.
  - README updated with usage examples.
- 2026-02-05 (merged, current):
  - Technical indicators pipeline: RSI, MACD, Bollinger Bands.
  - Indicator-based signal model with weighted scoring.
  - Clean architecture: ports in application, implementations in infrastructure.
  - 38 new tests for indicators and signal model (100% passing).

## Current focus
- Pattern recognition and model training workflow.
- Dashboard for visualization of signals and positions.
