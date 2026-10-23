# Local review — trading-bot-app (branch ci/3-security-baseline)

- Date: 2026-10-23
- Commit: 29b00d7
- Scope: branch diff origin/main...HEAD, issue #3 (CI security baseline, local gate, SonarQube; three files reformatted by ruff only — confirmed AST-identical)
- Checks run: design · docs · tests · security · correctness
- Verdict: fix Must Have first · Must 1 · Should 7 · Nice 7
- **Follow-up (same day, after fixes):** Must 1/1 fixed, Should 7/7 fixed, Nice: 5 fixed (S4502 accepted in SonarQube with justification, unused `PY`, Makefile wording, `retention-days`, gitleaks comment), 2 left (`csv_candle_repository.py` timeframe allowlist → tied to the gap analysis; `DASHBOARD_DEBUG` strictness kept on purpose). Local gate green again: 118 passed, 68 % coverage on 1186 lines (`scripts` now discovered via `scripts/__init__.py`), Semgrep 0, gitleaks clean. SonarQube: 0 bugs, 0 open vulnerabilities, gate still ERROR on `new_coverage` 55.6 % — only the 15 ruff-reformatted lines of `scripts/run.py` and the PyYAML import fallback; **owner waiver A (MCDA 420) covers it**, debt tracked in #10.

## Pre-merge gate (head SHA 29b00d7)
| Step | Result |
|---|---|
| 1 Tests | ✅ 107 passed, 1 skipped (integration marker, network) · no E2E suite exists |
| 2 Coverage | ❌ tests **69 %** lines on `trading_bot` + `scripts` (floor 80); `dashboard` not in the report · ❌ docs **≈22 %** of public symbols (27/121, AST estimate; floor 90). Both pre-existing: the diff adds 2 documented functions |
| 3 SonarQube | ✅ PASSED (quality gate `new_violations` = 0) · project auto-provisioned on first scan · 1 open vulnerability S4502 (CSRF, pre-existing, see Nice) |
| 4 Secrets | ✅ gitleaks clean (60 commits, full history) · no tracked `.env*` · diff read: nothing sensitive |
| 5 QA pass | ✅ full: `scripts/start_dashboard.py` binds `127.0.0.1:5000`, debug off; `/`, `/health` 200; `POST /api/backtest` → 404 "No candles found" (no data file, expected); console clean; network 3/3 200; screenshot `docs/architecture/qa/2026-10-23-dashboard-local-bind.jpg` |
- Gate: **RED — step 2 (coverage 69 % < 80 %, docs 22 % < 90 %)**, pre-existing debt, owner decision pending (waiver + tracking issue, or fill before merge).

## 🔴 Must Have
- `dashboard/app.py:47` `[tests][security][design]` · `run_dashboard()` has no test: the safe defaults (loopback, debugger off, `DASHBOARD_DEBUG` must be exactly `"1"`) could regress silently; `dashboard` is also outside `--cov` in `Makefile:26` and `ci.yml` · add `tests/test_dashboard_run.py` (patch `app.run`, `monkeypatch` the three variables: defaults, overrides, non-"1" values, bad port) and `--cov=dashboard` in both places.

## 🟡 Should Have
- `dashboard/app.py:55` `[correctness][security][docs]` · bare `int()` on `DASHBOARD_PORT` crashes with an unhelpful traceback · raise `SystemExit("DASHBOARD_PORT must be an integer, got …")` and state it in the docstring.
- `dashboard/app.py:56` `[security]` · `DASHBOARD_DEBUG=1` with a non-loopback host exposes the Werkzeug debugger (remote code execution) · refuse to start when debug is on and host is not loopback.
- `trading_bot/infrastructure/paper_order_executor.py:49,81,86` `[design]` · the dust tolerance `1e-12` appears three times, written three ways · module constant `_DUST_EPSILON`, `abs(size) < _DUST_EPSILON`, drop `import math`.
- `tests/test_paper_order_executor.py:73` `[tests]` · `test_zero_size_order_is_noop` only passes `0.0`, so the tolerance branch is unexercised · parametrize `0.0, 1e-13, -1e-13` (no-op, price getter not called) and `1e-9` (trades).
- `Makefile:16`, `.github/workflows/ci.yml:29`, `CLAUDE.md` `[design]` · `setuptools<81` pin written three times · put it once in `requirements-dev.txt` with its reason.
- `README.md:17-20`, `CLAUDE.md` "Running the tests" `[docs]` · neither mentions the Makefile gate · document `make venv`, `make check-local`, `make test`, `make sonar-scan`; keep the manual commands as fallback.
- `Makefile:5`, `dashboard/app.py:10-14`, `scripts/start_dashboard.py:7` `[docs]` · prerequisites (Docker, gitleaks, sonar-scanner, `SONAR_TOKEN`) and the new local-only default are not stated · one comment line and one sentence in each `Usage:` block.

## 🔵 Nice to Have
- `dashboard/api/backtest.py:17` `[security]` · SonarQube S4502 "CSRF protection disabled": JSON-only endpoint, no cookies or session, no state change, no CORS headers → a cross-site request cannot reach it; residual risk DNS rebinding · mark the issue "Accept" in SonarQube with this justification; revisit if auth or cookies ever appear.
- `trading_bot/infrastructure/csv_candle_repository.py:78-81` `[security]` · pre-existing, outside the diff: `timeframe` joined into a path unsanitised (`../` read of `.csv` files, localhost only) · allowlist timeframes; file as an issue, fate tied to the dashboard gap analysis.
- `Makefile:3` `[correctness]` · unused `PY` variable · delete.
- `Makefile:1` `[docs]` · "CI replays the same checks" overstates it (CI has no Semgrep/gitleaks job, Makefile has no HTML report) · "mirrors".
- `.github/workflows/ci.yml` upload-artifact `[security]` · no `retention-days` · set 7.
- `.github/workflows/gitleaks.yml:25` `[docs]` · licence comment sits inside `env:` · move above the step.
- `dashboard/app.py:56` `[design]` · `DASHBOARD_DEBUG` accepts only `"1"` while `logging.py:66` accepts `1/true/yes` · keep strict for the debugger (intentional), no helper needed for two cases.

## ⚪ Disagree / Intentional
- `dashboard/app.py:47` reading the environment at the entry point without a settings object `[design]` · proportional for this size, same style as `logging.py:63-66`; precedent: `architecture` skill "flat: pure helpers + thin entry points".
- `.github/workflows/dependency-review.yml:15` `if: !private` `[security][design]` · valid expression, documented, ties to #5.
- `trading_bot/shared/config.py:70` removed `type: ignore` `[correctness]` · required by `warn_unused_ignores` with `ignore_missing_imports`.
- `Makefile` `scan-secrets` without `--log-opts` `[security]` · full-history scan is the intent.

## Per-dimension summary
- Design: no over-engineering, two DRY smells (dust epsilon ×3, setuptools pin ×3) · Docs: diff well documented, README/CLAUDE.md omit the Makefile; repository-wide doc coverage ≈22 % (pre-existing) · Tests: pyramid healthy, `run_dashboard()` untested and outside coverage; repository coverage 69 % (pre-existing) · Security: SHA pins verified against tags, least-privilege tokens, Semgrep sandboxed, no secret in the diff; two hardening items on the dashboard entry point · Correctness: bare `int()` on the port, unused Makefile variable.
