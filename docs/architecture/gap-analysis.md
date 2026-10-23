# Gap analysis — diagrams vs requirements vs existing code

Date: 2026-10-23 (issue #15). Inputs: requirements R01–R40, the diagrams in
[`diagrams/btc-accumulation/`](diagrams/btc-accumulation/), and the legacy KuCoin-era code at `3de8bc0`.
Coverage measured locally: 68 % (375 of 1,186 statements missed), see #10.

## 1. Existing code against the diagrams

Decision legend: **Keep** (as is), **Adapt** (reuse with changes), **Replace** (new module, old one removed), **Remove**.

| Module (statements, coverage) | Maps to | Decision | Why |
| --- | --- | --- | --- |
| `domain/entities.py` Candle (39, 100 %) | CD Candle | Adapt | `float` prices, no sats or `Decimal`; `BacktestResult`, `PairProfile` are cash/volatility-based, replace by `SatsReport` and the pocket model |
| `application/ports.py` (11, 100 %) | Ports | Adapt | `MarketDataProvider`, `CandleRepository` stay. `OrderExecutor.place_market_order` is replaced by `ExchangePort` (post-only limit, cancel, fees) |
| `application/signal_model.py` (101, 93 %) | STRAT | Replace | Entry scores for a long-only scalper. R11/R12 need exit candidates and re-entry signals. The SMA helper is reusable for R12 |
| `application/risk_manager.py` (26, 96 %) | CYCLE sizing | Remove | Volatility-targeted position sizing has no place: sizing comes from the pocket (R04) and the ML filter (R13) |
| `application/trading_safety.py` (86, 88 %) | SAFE, 05a | Adapt | `IdempotencyGuard` and kill switch are kept (UC11). Position count, exposure % and the daily-loss limit do not match R06. The daily-loss limit is a performance stop and must be checked against R16b |
| `application/backtest.py` (22, 100 %) | HODL baseline | Adapt | Buy-and-hold engine becomes the HODL baseline of R02, not the engine |
| `application/indicators.py` (12, 0 %) | ML inputs | Keep | Port, unused by tests; real use arrives with R14 |
| `infrastructure/indicators.py` (149, 93 %) | ML inputs | Keep | RSI, MACD, Bollinger as ML features (R14) |
| `infrastructure/csv_candle_repository.py` (54, 94 %) | CSV store | Keep | Used by the walk-forward and the paper mode |
| `infrastructure/kucoin_market_data.py` (87, 89 %) | OKX adapter | Replace | KuCoin is out (R17). Replaced by `CcxtOkxAdapter` (data and orders) |
| `infrastructure/paper_order_executor.py` (55, 96 %) | SIM | Replace | Instant market fills, floats. Needs pessimistic maker fills and fee model (R33) |
| `shared/config.py`, `logging.py`, `metrics.py` (136, 71–100 %) | cross-cutting | Keep | Config keys are per-pair/timeframe, to be reshaped for pocket, limits and phase |
| `scripts/run.py` (181, 0 %) | CLI | Replace | KuCoin loop, intraday timeframes. Replaced by the CLI of the new cycle |
| `scripts/backtest.py` (48, 0 %) | CLI | Replace | Wraps the buy-and-hold engine |
| `scripts/ingest_candles.py` (35, 97 %) | CLI | Adapt | Swap the KuCoin provider for the ccxt data source |
| `scripts/start_dashboard.py` (11, 0 %) | DASH | Keep | Local bind verified in #3 |
| `dashboard/**` (133, 46–97 %) | DASH | Adapt | Read-only view stays in the target. `signals` and `backtest` endpoints show the legacy model and need rework when the engine exists |
| `.env.example`, `config/config.example.json` | — | Replace | KuCoin names and keys. Proposed: OKX placeholders when the OKX adapter lands |
| `VISION.md` | — | Remove | Superseded by the requirements (status line of the requirements file) |

## 2. Requirements with no code yet (new work)

Everything in the diagrams except the rows marked Keep/Adapt above. Main blocks: exchange port and OKX adapter
(R17–R20), the daily cycle and trend reference (R10–R12), tranche stop (R16), depeg and fail-closed protections (R16c, R16d),
pessimistic simulator (R33), walk-forward and bias gates (R26, R31, R34, R35), sats metrics (R02), journal and replay (R29), phase gate (R26–R28),
ML filter (R13–R15), supervisor (R21–R25, R36–R39), oracle (R40).

## 3. Requirement and diagram issues found (decided by the owner on 2026-10-23)

- **R16 vs R10**: the stop is a market order on a 5 % move, yet decisions are daily. The polling interval is undefined and backtest needs intraday data to model it (decided: intraday polling).
- **R16b vs legacy daily-loss limit**: `max_daily_loss_pct` pauses entries after a loss, a performance-based stop that R16b forbids. Decided: drop it.
- **R18**: the number of repricing attempts and the deadline are not specified (see `05b-state-order.md`).
- **Halt** (UC11): whether it returns the pocket to BTC is not in the requirements. Decided: yes, when safe (see `05a-state-pocket.md`).
- No ADR exists yet: R40 is recorded only in the requirements.

## 4. Treatment of the coverage debt (#10)

Measured: the 0 %-covered files (`scripts/run.py`, `scripts/backtest.py`, `scripts/start_dashboard.py`, `application/indicators.py`) hold 252 of the 375 missed statements, and the Replace rows above hold most of the rest.
If the modules marked Replace/Remove are deleted (498 statements, 249 missed), the survivors measure about 82 % line coverage (688 statements, 126 missed), just above the 80 % floor with no new test. The margin is thin: the dashboard `signals` endpoint still imports the replaced signal model and must be reworked in the same brick.
Docstring coverage also improves because the largest undocumented files disappear. The debt shrinks to documenting the survivors
(`ports.py`, `config`, `logging`, `metrics`, `csv_candle_repository`, `indicators`, dashboard).

| Option | Waste | Gate honesty | Reference value kept | Time to green | Total /500 |
| --- | --- | --- | --- | --- | --- |
| A. Delete-first, then test and document the survivors | 5 | 4 | 3 | 4 | **410** |
| B. Raise coverage on everything as-is | 1 | 5 | 5 | 1 | 300 |
| C. Keep the waiver until the new engine lands | 4 | 2 | 5 | 3 | 340 |

(Weights 30 / 30 / 20 / 20.) Decided (owner, 2026-10-23): A, executed as separate bricks after validation: removal is one brick per replaced area, each with the replacement.
The legacy remains in git history (`3de8bc0`).
