# PROJECT_LOG

Chronological operational log, complementing `git log`.

## 2026-10-14

- Original GitHub repository `benoit-bremaud/trading-bot-app` found deleted; recreated as a private repository and all local branches pushed (including `feature/dashboard-web`, restored from the stale remote-tracking ref). Old PRs, issues and comments are lost. Gitleaks scan of 58 commits: no leaks.
- Archived the separate `btc-usdt-ratio-rebalancer` project to `~/Documents/02_personal/_archives/btc-usdt-ratio-rebalancer-2026-10-14.tar.gz` (dependencies excluded).
- Requirements drift review: February MVP exit criteria partly unmet (no drawdown metric, no metrics in paper run), dashboard added despite being a non-goal, KuCoin no longer serves French users (deposits halted 2025-08-04, full closure 2025-08-25, no MiCA/PSAN licence, on the AMF blacklist since 2024-04-15; [Cryptoast](https://cryptoast.fr/plateforme-crypto-kucoin-quitte-france-explique-pourquoi/)).
- Requirements reset with the owner: BTC accumulation measured in sats against HODL, OKX Europe BTC/USDC spot, ML filter plus observational LLM supervisor, phased proof before real money. See `docs/requirements/btc-accumulation.md`.

## 2026-10-15

- Prior-art research (open-source bots, Kaggle competitions, LLM trading agents) confirmed the design; added R31–R39 (backtest/ML rigour, LLM guardrails). Freqtrade eliminated: its spot mode treats selling BTC as a short.
- Throwaway comparative prototype (naive SMA50 rule, 5 % buy-back stop, daily BTC 2018–2026): own engine 3.6828 BTC vs NautilusTrader 3.6761 BTC, same 168 fills. NautilusTrader caught a post-only-at-last-price rejection bug. Maker fill ratio of 93 % on daily bars judged optimistic.
- Decision R40 (MCDA 420/500): own engine with ccxt in production, NautilusTrader as CI execution oracle.

## 2026-10-22

- Workflow conformance audit: created GitHub Project #68 and issues #1–#5 (requirements PR, project CLAUDE.md and root cleanup, CI security baseline, stale branches, public switch). Owner decision: repository goes public after the release checklist (MCDA 370 vs 330).
- Local review of the requirements branch: 2 Must and 7 Should fixed. Tests 107 passed, coverage 89 %, gitleaks clean on full history. The repository `venv/` is broken under Python 3.14. SonarQube waived for this Markdown-only PR (MCDA 425 vs 300); SonarQube comes with #3.
- Codex review on #6: 4 findings fixed (per-tranche buy-back stop, deterministic depeg handler R16d, subaccount isolation, warm-up bias test).
- GitHub Actions never ran on the recreated repository (workflow active, no run recorded; billing not checkable). Owner waived CI for the Markdown-only #6 (MCDA 420 vs 285); investigation moved to #3.
- #2: added a project `CLAUDE.md`, rewrote `README.md` (English, new goal) and `ROADMAP.md` (conformance #3–#5, UML conception, phases 1–3), deleted the stale `AUDIT_REPORT.md` and `GUIDE_TEST_LOCAL.md` (MCDA 475 vs archive 400; recoverable from git history), sourced the KuCoin France exit.
- Local review of #2: 0 Must, 3 of 4 Should fixed (mypy target version deferred to #3). Tests 107 passed, coverage 89 % on `trading_bot`. SonarQube waived by the owner for this Markdown-only PR (MCDA 500 vs wait 410 vs local scan 340).
- Owner approved merging #7 without CI (GitHub Actions still not running, fixed in #3) and with the SonarQube waiver; no Copilot/Codex review was delivered.

## 2026-10-23

- Resumed work. Debrief of the "survive or die" bot idea: issue #9 (survival budget, self-funded costs, documented research; reject per-trade reward and die-or-survive pressure on the LLM; MCDA 440 vs sandbox 335 vs copy 190). Model research (pre-trained time-series and sentiment models, Kaggle winners, local LLMs via Ollama, X field reports) posted on #8: gradient boosting on hand features for the ML filter (MCDA 420), Claude Haiku Batch for the supervisor (430) with a local model as offline fallback; the viral "$50 survive-or-die" post carries a Community Note calling its dashboard fabricated.
- GitHub Actions mystery solved: the account's private-repository Actions minutes are exhausted for the month; the repository and workflow were fine. Order kept (MCDA 420): #3 merged on the local gate, CI validated once the repository is public (#5).
- #3: SAST decision Semgrep locally now, CodeQL in #5 when public (MCDA 430 vs 370). Added `gitleaks.yml` (push, PR, weekly, full history), `dependency-review.yml` (self-activates when public; needs Advanced Security on private repositories), Dependabot (pip, github-actions), `Makefile` (`check-local` = ruff, mypy, pytest, Semgrep, gitleaks; `sonar-scan`), `.semgrepignore`, `sonar-project.properties` (key `trading-bot-app`, auto-provisioned on the first scan with the global token). `ci.yml`: actions pinned by SHA, read-only token, Codecov step removed (no account), `setuptools<81` pin. mypy target aligned to 3.11 (one unused `type: ignore` removed).
- First Semgrep run: 3 blocking findings, all in the dashboard (`debug=True`, `host=0.0.0.0`): fixed with a single `run_dashboard()` reading `DASHBOARD_HOST` (default `127.0.0.1`), `DASHBOARD_PORT`, `DASHBOARD_DEBUG`. Semgrep rules follow the registry at run time; only the engine is pinned (accepted trade-off).
- First SonarQube scan: project auto-provisioned; 1 bug fixed (float equality in `paper_order_executor.py`, now a `_DUST_EPSILON` constant); vulnerability S4502 (no CSRF protection on `POST /api/backtest`) **accepted** in SonarQube with justification: JSON-only endpoint, no session, cookie or auth, no state change, no CORS, server local-only; revisit if auth or cookies appear. ruff 0.17.1 reformatted 3 files (pure formatting, AST-identical).
- Local review (`review-local`, report in `docs/architecture/review-local.md`): 1 Must and 7 Should fixed — tests for `run_dashboard()` (loopback default, debugger only with `DASHBOARD_DEBUG=1` and refused on a non-loopback host, clear error on a bad port), dust-size executor tests, `setuptools<81` pinned once in `requirements-dev.txt`, README and CLAUDE.md point to `make check-local`, artifact retention 7 days. `scripts/__init__.py` added so coverage sees the scripts (they were imported as a package but not discovered); `--cov=.` with `relative_files` gives SonarQube one source root.
- **Pre-merge gate waiver (owner, 2026-10-23, MCDA 420 vs block-#3 375 vs fill-in-PR 255):** test coverage 68 % (floor 80) and docstring coverage ≈22 % (floor 90) are debt predating #3, tracked in #10 and decided after the UML gap analysis. The SonarQube `new_coverage` condition (55.6 %) fails only on the 15 ruff-reformatted lines of `scripts/run.py` and the PyYAML import fallback; every line actually added in #3 is covered. QA pass on the running dashboard green (screenshot in `docs/architecture/qa/`).
- PR #11 opened. The three workflows were triggered for the first time and failed in 2 s without running a step; GitHub's annotation: "The job was not started because recent account payments have failed or your spending limit needs to be increased". Confirms the billing diagnosis; the red checks are not a code failure. Copilot reviewer request again silently not applied (private repository, no Copilot plan).
- #4: deleted stale branches after owner confirmation (MCDA 450 vs tag-archive 430 vs locals-only 350); none merged, tips recoverable from the SHAs below until git garbage-collects them:
  - `chore/tooling-makefile` (local + origin, 891c481): abandoned, Makefile superseded by #11.
  - `feat/exchange-constraints` (local + origin, 63087dd): abandoned KuCoin-era adapter.
  - `feat/specs-regression-foundation` (local + origin, 78a2df5): abandoned KuCoin-era specs (replaced by R26).
  - `refactor/code-optimization-clean-solid` (local + origin, 7f36dea): abandoned KuCoin-era refactor.
  - `origin/feature/dashboard-web` (1343eb5): abandoned duplicate, dashboard shipped via PR #20.
  - `ci/3-security-baseline` (a1f1d47, local, worktree `reprise-travail-c11138` removed): merged, squashed as f99218a (PR #11).
  - `claude/reprise-travail-c11138` (91019fb, local): merged, 0 commits ahead.
  - `origin/dependabot/pip/setuptools-lt-85` kept (active Dependabot PR).
- #4 merged as PR #13 (squash 73aa7e4) under the same billing waiver (Actions could not run on the private repository).
- #5: Public Release Checklist run before the switch (MCDA 465 vs merge-first 335 vs no-CI 285): gitleaks on full history (55 commits) clean, no sensitive tracked files, no tags, no development secret to rotate (no OKX key exists yet), `.env.example` holds placeholders only (still KuCoin-named, to be rewritten for OKX with the engine work), gitleaks CI job present. Repository switched to **public** on 2026-10-23. Added `codeql.yml` (Python, push/PR/weekly, SHA-pinned, `contents: read` plus `security-events: write` on the job only). `dependency-review.yml` self-activates now that the repository is public.
