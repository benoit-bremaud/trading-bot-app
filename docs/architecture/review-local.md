# Local review — trading-bot-app (#17 domain model and ExchangePort)

- Date: 2026-10-23
- Commit: 0e73002 + review fixes (head of `feat/17-domain-model`)
- Scope: branch diff `origin/main...HEAD`
- Checks run: design · docs · tests · security · correctness (mode `--push`, no QA pass)
- Verdict: ship after fixes — all Must Have resolved · Must 0 open · Should 0 open · Nice 7 deferred

## Pre-merge gate (head SHA c56daf5, all run locally, 2026-10-24)
| Step | Result |
|---|---|
| 1 Tests | ✅ 239 passed, 1 skipped (unit); ruff, mypy, Semgrep 0 findings; no E2E suite in this project yet |
| 2 Coverage | tests **74 %** repo-wide (68 % before this PR, floor 80 → #10 waiver) and **100 %** on every new line · docs **100 %** on the new surface (53/53 symbols), **42.7 %** repo-wide (floor 90 → #10 debt, legacy files) |
| 3 SonarQube | ✅ PASSED (new_coverage 93.9 %, new violations 0, duplication 0 %) |
| 4 Secrets | ✅ gitleaks clean (full history and `origin/main..HEAD`) · only `.env.example` tracked (placeholders) · diff read: nothing sensitive |
| 5 QA pass | ✅ smoke only (no runtime path touched): dashboard started locally, `/` 200, static assets 200, console clean, network clean, `/api/backtest` GET 405 (POST-only, expected); screenshot `docs/architecture/qa/2026-10-24-dashboard-smoke-17.png` |
| Conception | ✅ amended 04-class and 05a-state-pocket render with `mmdc`; 9 of 15 UML classes of 04 implemented, the other 6 (`DecisionRecord`, `ExitCandidate`, `PhaseGate`, `SatsReport`, `SizedExit`, `SupervisorOpinion`) belong to bricks 3–10; code-only types are enums, errors and value types documented in the 04 notes |
- Gate: **GREEN on the PR's own code; repo-wide coverage floors (80 % tests, 90 % docs) remain under the #10 waiver** (coverage 74 %, docs 42.7 %).
- External reviewers: GitHub Actions and Copilot are not relied on; Codex answered "usage limit reached" (no review).

## 🔴 Must Have (all fixed)
- `pocket.py` `[design][correctness]` · one exit filled in several pieces made duplicate tranche ids and lost the VWAP → `record_exit(id, fills)` opens one tranche at the fills' VWAP, duplicate id refused (owner decision A1).
- `pocket.py` `[design][correctness]` · `halt()` accepted with an open tranche, stranding USDC → refused while a tranche is open.
- `pocket.py`, `orders.py`, `fees.py`, `sats.py` `[security][correctness]` · NaN/Infinity accepted or raising the wrong exception, `Pocket` unchecked types → shared `checks.py`, all money types validate.
- `05a-state-pocket.md` `[design]` · `resume()` went beyond the diagram → diagram amended (owner decision B1), **owner to validate in the PR**.
- tests `[tests]` · buy-back with fee, funds boundary, paused buy-back with open tranche, fee cap boundary untested; weak `pytest.raises` → added, `match=` on messages.

## 🟡 Should Have (all fixed)
- `[design]` `fetch_fee_schedule(symbol)` inconsistent with the rest of the port → no symbol (decision C1).
- `[design]` `Pocket` state/holdings could contradict, `_after` disabled type checks → invariant in `__post_init__`, no `replace`.
- `[correctness]` `HardLimits.check` accepted invalid arguments; market order with deadline; `Tranche` unvalidated → fixed.
- `[docs]` `Raises` clauses, `Fill.fee_rate` meaning, port failure contract, stale date reference → fixed.
- `[tests]` S5778 (SonarQube) in all test files → arguments built before `pytest.raises`.

## 🔵 Nice to Have (deferred)
- `OrderStatus` has no state/fills invariant (`FILLED` with no fills).
- Negative zero accepted for rates and balances (arithmetically harmless).
- `open_tranches()` duplicates the `tranches` field (kept: it is in diagram 04).
- Private-helper docstrings are borderline doc-noise.
- Round-trip property test with hypothesis; `FakeExchange` could move to a shared `tests/fakes.py` when the first adapter needs a contract suite.
- Pause reason (supervisor vs incident) not modelled: arrives with the supervisor and protection bricks (noted in 05a).

## ⚪ Disagree / Intentional
- Fee charged in USDC on the notional for both sides: conservative, to reconcile with OKX in the adapter brick (PROJECT_LOG #17).
- `OrderExecutor` and `ExchangePort` coexist until brick 3 (the legacy port is removed with `paper_order_executor`).
- `ExchangePort` has a test fake only: justified by R32 (one code path for backtest, paper and live).

## Per-dimension summary
- Design: aggregate invariants hardened, diagram 05a/04 synced. · Docs: new surface fully documented; legacy ports and repo-wide ≈ 37 % remain #10 debt. · Tests: behaviour-level, boundary cases added, only the exchange boundary doubled. · Security: money types refuse float, NaN, infinity. · Correctness: accounting conserves sats and USDC.
