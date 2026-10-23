# ROADMAP

Plan derived from [`docs/requirements/btc-accumulation.md`](docs/requirements/btc-accumulation.md) (R01–R40). Tracking: GitHub Project #68. Update this file after each merge.

Status: ✅ done · 🔄 in progress · ⏳ next · 💤 later

## 0. Requirements reset — ✅

- ✅ #1 Requirements R01–R40 for BTC accumulation in sats vs HODL (PR #6).

## 1. Workflow conformance — ✅

- ✅ #2 Project `CLAUDE.md`, root docs cleanup, this roadmap (PR #7).
- ✅ #3 CI security baseline (Gitleaks, dependency review, Semgrep locally), SonarQube, Dependabot. CodeQL comes with #5 (free on public repositories). GitHub Actions never ran because the private-repository minutes were exhausted; #5 removes the limit. Merged as PR #11 (f99218a).
- ✅ #4 Delete stale KuCoin-era branches.
- ✅ #5 Repository switched to public after the release checklist (gitleaks clean on full history), CodeQL workflow added, GitHub Actions running again.

## 2. UML conception — ✅

- ✅ #15 UML conception validated by the owner on 2026-10-23: [`docs/architecture/diagrams/btc-accumulation/`](docs/architecture/diagrams/btc-accumulation/) (use case, 3 sequences, component, class, 3 states, data flow), [traceability matrix](docs/architecture/traceability-matrix.md) and [gap analysis](docs/architecture/gap-analysis.md). Decisions: R16 stop polled intraday, halt returns to BTC when safe, legacy daily-loss limit dropped.

## 2b. Build bricks (from the gap analysis) — ⏳

One issue per brick, created when it starts. Legacy modules are deleted inside the brick that replaces them; #10 (coverage and docstring debt) is re-scoped to the survivors and closes when `make test` ≥ 80 % and `make doc-coverage` ≥ 90 % on `main`.

1. ⏳ Domain and ports: sats and `Decimal` model (Pocket, Tranche, Fill, FeeSchedule), `ExchangePort`; the matching tests and docstrings.
2. 💤 Data: `ccxt` OKX market-data adapter (daily and hourly BTC/USDC history), ingest script moved off KuCoin, KuCoin code removed; OKX variables added to `.env.example`.
3. 💤 Simulator and baselines: pessimistic maker fills (R33), HODL and trend rule R12 baselines, sats report (R02, R03).
4. 💤 Walk-forward and bias gates (R26, R31, R34, R35): ends phase 1 evidence.
5. 💤 Daily cycle, journal and replay (R10, R11, R18, R29, R32), `SafetyLimits` (R06), kill switch.
6. 💤 Protections: tranche stop, depeg controller, fail-closed incidents (R16, R16c, R16d).
7. 💤 CI oracle (R40) and its tolerance.
8. 💤 ML filter (R13–R15), one input at a time.
9. 💤 Supervisor in observation (R21–R25, R36–R39).
10. 💤 Phase gate and paper-trading runner (R27).

## 3. Phase 1 — historical walk-forward (R26) — 💤

- Data: daily and intraday BTC/USDC history from 2018, fees modelled (R31–R39 rigour).
- Measurement in sats against HODL; drawdown and trade metrics.
- Pass criteria fixed before results: more sats than HODL in ≥ 70 % of rolling one-year windows, better than R12, holds with fees doubled to 0.2 %, single attempt on the untouched final period.

## 4. Phase 2 — forward paper trading (R27) — 💤

At least 6 months and 8 trades, a real 20 % drawdown, fault-injection tests passed, small gap with the replayed backtest.

## 5. Phase 3 — real-money ramp-up (R28) — 💤

2 % of the stack for 3 months, then 5 % for 3 months, then the target pocket (R04). Trade-only keys; pre-defined stop criteria send the bot back to paper.

## Backlog — long-term ideas

- 💤 #8 Prepare the option of training a self-hosted model at home (model interface, reproducible datasets, hardware study).
