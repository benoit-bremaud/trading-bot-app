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
