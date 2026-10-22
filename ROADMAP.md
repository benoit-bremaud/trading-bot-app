# ROADMAP

Plan derived from [`docs/requirements/btc-accumulation.md`](docs/requirements/btc-accumulation.md) (R01–R40). Tracking: GitHub Project #68. Update this file after each merge.

Status: ✅ done · 🔄 in progress · ⏳ next · 💤 later

## 0. Requirements reset — ✅

- ✅ #1 Requirements R01–R40 for BTC accumulation in sats vs HODL (PR #6).

## 1. Workflow conformance — 🔄

- 🔄 #2 Project `CLAUDE.md`, root docs cleanup, this roadmap.
- ⏳ #3 CI security baseline (Gitleaks, CodeQL, dependency review), SonarQube, and fix GitHub Actions that never run.
- ⏳ #4 Delete stale KuCoin-era branches.
- ⏳ #5 Switch the repository to public after the release checklist.

## 2. UML conception — 💤

Model before code, under `docs/architecture/diagrams/` and validated by the owner:

- Use cases (operator goals: run a walk-forward, review a supervisor report, promote a phase).
- Components: own engine + `ccxt` venue adapter, NautilusTrader CI oracle (R40), ML filter, observational LLM supervisor.
- Sequences and states for the decision loop, the incident pause and the phase gates.
- Gap analysis of the existing KuCoin-era code: what is kept, adapted or removed.

## 3. Phase 1 — historical walk-forward (R26) — 💤

- Data: daily and intraday BTC/USDC history from 2018, fees modelled (R31–R39 rigour).
- Measurement in sats against HODL; drawdown and trade metrics.
- Pass criteria fixed before results: more sats than HODL in ≥ 70 % of rolling one-year windows, better than R12, holds with fees doubled to 0.2 %, single attempt on the untouched final period.

## 4. Phase 2 — forward paper trading (R27) — 💤

At least 6 months and 8 trades, a real 20 % drawdown, fault-injection tests passed, small gap with the replayed backtest.

## 5. Phase 3 — real-money ramp-up (R28) — 💤

2 % of the stack for 3 months, then 5 % for 3 months, then the target pocket (R04). Trade-only keys; pre-defined stop criteria send the bot back to paper.
