# VISION

## Mission
Deliver a reliable MVP trading bot for KuCoin spot that can ingest market data, generate signals (rules + AI-ready), backtest, manage risk dynamically, and execute safely — all within a CLEAN/SOLID architecture.

## Scope (MVP)
- KuCoin spot market data ingestion (REST).
- OHLCV normalization to domain entities.
- Minimal backtest engine with core performance metrics.
- Baseline risk management (position sizing, max exposure).
- Baseline signal model (rules-based) with AI-ready interfaces.
- Paper trading execution path.
- Minimal CLI entrypoints (ingest/backtest/run).
- Logging/metrics for observability.

## Non-goals (MVP)
- Futures, margin, or leverage trading.
- High-frequency / low-latency execution.
- Full web dashboard (only minimal CLI).
- Live AI model training in production.

## Architecture principles
- CLEAN/SOLID boundaries are mandatory (domain, application, infrastructure, adapters, shared).
- Dependencies flow inward only; ports in application, implementations in infrastructure/adapters.
- Patterns only when justified (Strategy/Factory/Repository/Event bus).
- Tests are required for each feature (unit + focused integration where relevant).

## Definition of MVP (exit criteria)
- Can ingest candles for a pair/timeframe and normalize to `Candle`.
- Can run a backtest on historical data and report PnL + drawdown.
- Can compute a position size from risk constraints.
- Can generate an entry signal from a baseline strategy.
- Can paper-trade end-to-end with logs and metrics.

## Success criteria (initial)
- Deterministic backtest results on fixed data input.
- No architecture boundary violations (imports).
- CI green (ruff, mypy, pytest) on 3.11/3.12.
- Clear, reproducible steps to run ingest/backtest.

## Constraints & process
- Commit + push + PR for each feature.
- PR body in Markdown with Summary/Testing/Notes.
- Roadmap must be updated after each merge and when new ideas appear.
