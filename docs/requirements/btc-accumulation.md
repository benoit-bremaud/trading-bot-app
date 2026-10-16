# Requirements — BTC accumulation bot

Status: requirements reset validated by the owner on 2026-10-14. Supersedes `VISION.md` (February 2026)
and the `ai-paper-trading-bot` paper-trading specification (2026-10-05) wherever they conflict.
This document authorizes no real-money trading. It is the contract that UML conception and
implementation must satisfy.

## Purpose

Grow the owner's bitcoin holdings. Success is measured in BTC (sats), against holding (HODL),
after all costs. The owner already accumulates through recurring purchases elsewhere, so this bot
does active trading, not dollar-cost averaging.

## Accepted requirements

### Goal and measurement

| ID | Requirement | Rationale |
| --- | --- | --- |
| R01 | Bitcoin only. No other asset is traded. | Focus; matches the goal. |
| R02 | Every result is expressed in BTC. The mandatory baseline is HODL (the pocket never trading). A secondary baseline is the naive trend rule (R12). | A gain in fiat while holding fewer sats is a failure. |
| R03 | All comparisons are net of fees, using the venue's real fee schedule (R17). | Fees decide viability (see Evidence). |

### Scope of capital

| ID | Requirement | Rationale |
| --- | --- | --- |
| R04 | The bot only trades an **active pocket**, a fixed fraction of the stack. Target pocket: 10–20 % of the stack. The rest never moves and stays in self-custody. | Pocket sats drawdown of 34–51 % is structural; the pocket size is the real protection. |
| R05 | Only the pocket allowed by the current phase (R28) is deposited on the exchange. | Bounds operational and counterparty risk. |
| R06 | Hard-coded limits independent of strategy: maximum orders per day and maximum order size in sats. | Bounds damage from software defects. |

### Market and instruments

| ID | Requirement | Rationale |
| --- | --- | --- |
| R07 | Pair: BTC/USDC spot. | USDT pairs are unavailable to EEA clients of MiCA-licensed venues since 2026-07-01. Exchanges between crypto-assets are assumed tax-neutral in France until the owner confirms with an advisor. |
| R08 | Spot only. Futures are a distinct later experiment with its own conception and approval. | Leverage and liquidation risk are out of scope until proven need. |
| R09 | Long BTC or flat in USDC, nothing else. The sats risk only exists while the pocket is out of BTC. | Defines where risk can arise. |

### Decisions and strategy

| ID | Requirement | Rationale |
| --- | --- | --- |
| R10 | Decisions are made once per day on completed daily candles. | Hourly or 4-hour decisions destroyed sats in simulations once fees reach 0.4 %. |
| R11 | Deterministic rules generate exit candidates (leaving BTC) and re-entry signals. | Transparent, testable baseline. |
| R12 | The naive trend rule (exit when the close is below its 50-day moving average) is kept as a permanent reference strategy. | Any added complexity must beat it. |
| R13 | A machine-learning model **filters and sizes** the exit candidates proposed by R11. It never invents trades on its own. | Its measurable job is to remove false signals. |
| R14 | ML inputs start with price, volume, technical indicators and futures data (funding rate, open interest). Other sources (sentiment, macro, spot ETF flows, stablecoin supply, on-chain) are added **one at a time** and kept only if they add sats in walk-forward validation. | Limits overfitting on ~3,000 daily observations. |
| R15 | Models start simple (for example logistic regression or shallow gradient boosting). | Same reason. |

### Protection

| ID | Requirement | Rationale |
| --- | --- | --- |
| R16 | 5 % buy-back stop: when the pocket is out of BTC and the price rises 5 % above the exit price, the bot buys back. | Only form of per-trade sats loss; improved results in simulation at no cost. |
| R16b | No pause based on performance. | A 90-day underperformance pause cut the 2018-start result from 3.57 to 0.66 BTC. |
| R16c | Technical incidents fail closed: missing data, exchange errors or inconsistent state pause new exits, with the pocket returning to or staying in BTC only when it can be done safely. Recovery requires operator approval. | Safety. |

### Venue and execution

| ID | Requirement | Rationale |
| --- | --- | --- |
| R17 | Primary venue: OKX Europe Limited (MiCA, MFSA, authorised 2025-01-27, France covered per ESMA register), account with derivatives access for the 0.08 % maker / 0.10 % taker spot tier. The bot reads the real fee for BTC/USDC at start-up and refuses to trade above 0.10 %. | Only verified venue meeting the fee cap without order-type conditions. |
| R18 | Orders are maker post-only limit orders, with a fallback to a market order after a configured deadline. The R16 stop is a market order. | Lowest fees with guaranteed execution. |
| R19 | The engine is venue-agnostic behind an exchange port. Bybit EU GmbH (MiCA, FMA, France covered) is implemented and tested on public data in paper mode, with no account or funds. | Cheap fallback without operational overhead. |
| R20 | Exchange API keys have trade permission only, never withdrawal permission, and are never exposed to the language model. | Security. |

### Language-model supervisor

| ID | Requirement | Rationale |
| --- | --- | --- |
| R21 | The supervisor starts in **observation**: its opinions are logged with their exact inputs and never applied. | It cannot be backtested: the model already knows past events. Its only valid evaluation is forward. |
| R22 | After proving value forward, it may (level 2) delay or reduce an exit from BTC, and (level 3) pause on incidents such as an exchange hack, stablecoin depeg or regulatory event. It can never sell BTC or initiate a trade. | Its worst possible effect is a return to HODL. |
| R23 | Architecture: a small model (Claude Haiku 5.5) triages news hourly; a large model (Claude Opus 5.5) runs on alerts and for the daily synthesis. | Incident detection must be fast; quality where it matters. |
| R24 | Hard budget cap of 10 € per month enforced in code, falling back to daily synthesis only. Cost is logged per call and reviewed after one month. | Budget control. |
| R25 | External text read by the supervisor is untrusted data. It can only produce a structured opinion within the R22 powers. | Prompt-injection resistance. |

### Proof before real money

| ID | Requirement | Rationale |
| --- | --- | --- |
| R26 | **Phase 1 — historical walk-forward.** To pass: more sats than HODL in at least 70 % of rolling one-year windows; better than R12; results hold with fees doubled to 0.2 %; a final untouched period confirms it, with a single attempt. Criteria are fixed before results are seen. | The only phase with enough trades (~170 since 2018) to measure an edge. |
| R27 | **Phase 2 — forward paper trading.** To pass: at least 6 months, at least 8 trades, at least one real price drawdown of 20 %, all fault-injection tests passed (stop, incident pause, API outage, stablecoin depeg), small gap with the same period replayed in backtest, fees as modelled. Review point at 12 months if not met. | Three months miss the stop in 72 % of historical windows and any 20 % drawdown in 41 %. |
| R28 | **Phase 3 — real money ramp-up.** 2 % of the stack for 3 months, then 5 % for 3 months, then the target pocket (R04). Each step requires no unhandled incident and a small gap with the replayed backtest. Pre-defined stop criteria send the bot back to paper. | Bugs, not strategy statistics, are the unbounded early risk. |

### Engineering

| ID | Requirement | Rationale |
| --- | --- | --- |
| R29 | Every decision is journaled with its inputs, model versions, fees and outcome, so any day can be replayed. | Auditability and R27 replay comparison. |
| R30 | Clean architecture proportional to need, tests mandatory, UML conception validated before implementation, CI green (ruff, mypy, pytest). | Owner's standing rules. |

### Backtest and ML rigour (added 2026-10-15 after prior-art research)

| ID | Requirement | Rationale |
| --- | --- | --- |
| R31 | CI gates against lookahead and indicator warm-up bias: the strategy is re-run on truncated data and signals/indicators must be identical. | Freqtrade `lookahead-analysis` / `recursive-analysis` pattern. |
| R32 | One code path for backtest, paper and live trading. | Strongest defence against backtest/live divergence (NautilusTrader design). |
| R33 | Backtests assume pessimistic maker fills: post-only orders may not fill, and the taker fallback is charged. | Maker orders without queue modelling overstate results. |
| R34 | Purged walk-forward validation with an embargo at least as long as a trade's horizon; samples grouped by date. | Validation used by G-Research and DRW winners. |
| R35 | ML target: binary "this exit ends with more sats after re-entry, net of fees", each sample weighted by the sats gained or lost. Results reported with confidence intervals (block bootstrap). | Low-sample setting (~20 trades/year); winners' correlations were only 0.05–0.13. |

### Supervisor guardrails (added 2026-10-15)

| ID | Requirement | Rationale |
| --- | --- | --- |
| R36 | Reading and deciding are separated: the model reading raw text has no power and outputs typed fields only; the deciding step never sees raw text. Inputs are sanitised (HTML stripped, Unicode normalised, homoglyphs rejected). | One day of manipulated headlines cut annual returns by up to 17.7 points in a 2026 study. |
| R37 | Any pause or delay requires two independent sources or a measurable confirmation (for example a stablecoin price below 0.98, or the exchange status API). Delays are capped at 72 hours and pauses expire automatically. | A fake "exchange hacked" headline is the obvious attack. |
| R38 | Prompts, model IDs, thresholds and input sources are frozen and versioned; any change restarts the forward evaluation. A counterfactual "followed the supervisor" portfolio is tracked alongside the real one, and ignored advice is logged too. | Fair forward evaluation. |
| R39 | Budget exhaustion or API errors fall back to "no opinion", never to "pause". | An outage must not freeze the bot. |

### Build approach (decided 2026-10-15)

| ID | Requirement | Rationale |
| --- | --- | --- |
| R40 | Own domain and engine in production, with ccxt (`myokx` class for OKX Europe) as the exchange layer. NautilusTrader is used only in development and CI as an execution oracle: the reference strategy (R12) is replayed in it and the gap with our simulator must stay within a fixed tolerance. The ML filter and the supervisor are never duplicated in the oracle. | MCDA after a comparative prototype: own engine + oracle 420/500, own engine alone 410, NautilusTrader 400, Freqtrade 310. Both engines agreed within 0.18 %, and NautilusTrader caught a post-only rejection bug the own engine had missed. |

## Out of scope

- Other assets, including ETH.
- Leverage and futures trading (until a separate approved experiment).
- Dollar-cost averaging.
- Any language-model power to sell or initiate trades.

## Open points

- Tax treatment of BTC/USDC exchanges in France: to confirm with an advisor.
- Exact BTC/USDC fee on the owner's account: read at start-up (R17).
- Thresholds for "small gap" (R27, R28) and the phase-3 stop criteria: to fix before phase 2 starts.
- Reuse of code from `trading-bot-app` and from the archived BTC/USDT rebalancer: to decide during conception.
- R33 fill realism: on daily bars both prototypes filled 93 % of post-only orders as maker, which is likely optimistic. Maker fills should be simulated on intraday data (for example hourly bars) or with a trade-through margin.
- Post-only orders must rest at least one tick on the passive side of the book; an order at the last price is rejected as taker (found by the 2026-10-15 prototype).
- Oracle tolerance for R40: to fix during conception (the prototype gap was 0.18 %).

## Evidence (2026-10-14)

Simulations on public BTC/USDT daily, 4-hour and hourly data since 2018, using the naive trend rule.
They ignore slippage and taxes and only set orders of magnitude.

- Fees: with a 50-day average from January 2023, daily decisions ended at 1.041 BTC with 0.1 % fees and 0.818 BTC with 0.4 %.
- Frequency: hourly decisions with 0.4 % fees kept 0.031 BTC of 1 BTC since 2018.
- Start-date dependence: 3.568 BTC from January 2018, 1.041 BTC from January 2023.
- Pocket drawdown in sats: 34–51 % from its peak, even in winning runs.
- Pauses: a 90-day 10 % underperformance pause reduced the 2018-start result from 3.568 to 0.664 BTC; a 5 % buy-back stop slightly improved results.
- Trade frequency: about 20 trades per year; a 6-month window has a median of 9 trades.

## Sources

- [ESMA interim MiCA CASP register](https://www.esma.europa.eu/sites/default/files/2024-12/CASPS.csv)
- [OKX EU spot fees for EEA users](https://www.okx.com/en-eu/help/what-are-the-new-trading-fees-for-eea-users)
- [OKX EU spot fee adjustment, 2026-09-25](https://www.okx.com/en-eu/help/important-notice-upcoming-spot-fee-adjustment-eea)
- [Bybit EU spot fees](https://www.bybit.eu/en-EU/help-center/article/Bybit-Spot-Fees-Explained)
- [CoinDesk: Binance stops serving EU users](https://www.coindesk.com/policy/2026/06/26/binance-tells-eu-users-it-will-no-longer-provide-services-after-failing-to-secure-mica-license)
- [Crypto Briefing: USDT delisted in Europe](https://cryptobriefing.com/usdt-delisted-from-european-exchanges-as-mica-takes-effect/)
