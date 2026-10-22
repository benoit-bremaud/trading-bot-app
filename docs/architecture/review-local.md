# Local review — trading-bot-app (branch docs/btc-accumulation-requirements)

- Date: 2026-10-22
- Commit: 5017782 (+ review fixes, same branch)
- Scope: branch diff main...HEAD (docs only: requirements, PROJECT_LOG.md, VISION.md), issue #1
- Checks run: docs (doc-auditor) · security (diff read + gitleaks) · correctness (consistency review). Design and tests: not applicable, no code in the diff.
- Mode: `--push` (QA pass not run; no runtime change)
- Verdict: Must Have resolved, push authorised · Must 2 · Should 8 · Nice 5

## Pre-merge gate (head SHA 5017782 + fixes)
| Step | Result |
|---|---|
| 1 Tests | ✅ 107 passed, 1 skipped (pytest; fresh Python 3.14 venv with `setuptools<81`. The repo `venv/` is broken: no pip, no pytest) |
| 2 Coverage | tests 89 % statements (floor 80) · docs: not measured, no doc counter in the project |
| 3 SonarQube | ⚠️ not run: no SonarQube project for this repo (tracked in #3) |
| 4 Secrets | ✅ gitleaks clean on full history · only `.env.example` tracked · diff read: nothing sensitive |
| 5 QA pass | not run (`--push` mode, docs-only diff) |
- Gate: **push OK; SonarQube waived by the owner on 2026-10-22 for this Markdown-only diff (MCDA 425 vs 300); SonarQube arrives with #3**

## 🔴 Must Have
- `docs/requirements/btc-accumulation.md:83,100,101,107` `[docs]` · numeric rationale given without a source · **fixed**: tagged as own simulation, or as unverified prior-art research
- `docs/requirements/btc-accumulation.md:63` `[docs|correctness]` · R17's authorisation date and fee tier were not backed by the cited sources · **fixed**: the 2025-01-27 date is dropped; the fee schedule (since 2026-09-25) and the 2026-10-14 check date are stated

## 🟡 Should Have
- `:3` `[docs]` · stale status line · **fixed**: now gives the status of R01–R30, R31–R39 and R40
- `:56 vs :84` `[correctness]` · R16b looked like it conflicted with R28 · **fixed**: R28's stop criteria are now described as safety criteria
- `:110` `[correctness]` · R39 looked like it conflicted with R16c · **fixed**: R39 is scoped to the supervisor
- `:82,101,145` `[correctness]` · the word "trade" was ambiguous · **fixed**: defined as one filled order (168 fills over about 8.7 years is about 20 per year)
- `:137` `[docs]` · evidence was measured on BTC/USDT · **fixed**: caveat added for the USDC pair
- `:38,63` `[correctness]` · derivatives access vs spot-only · **fixed**: R08 and R20 clarified
- `:4` `[docs]` · unlinked `ai-paper-trading-bot` reference · **fixed**: now named as a separate repository
- `PROJECT_LOG.md:9` `[docs]` · no source for "KuCoin no longer serves French users" · open, to source during #2

## 🔵 Nice to Have
- `:55-57` · R16b and R16c sub-IDs · kept on purpose (stable IDs)
- `:73` · level 1 not defined · **fixed**
- `:46` · R12 re-entry rule not stated · deferred to UML conception
- `README.md`, `ROADMAP.md`, `GUIDE_TEST_LOCAL.md`, `AUDIT_REPORT.md` · stale KuCoin content · tracked in #2
- `PROJECT_LOG.md:7` · repository is private, against the rule · tracked in #5

## ⚪ Disagree / Intentional
_None._

## Per-dimension summary
- Design: N/A · Docs: 2 Must and 7 Should fixed, 1 Should open · Tests: suite green, coverage 89 % · Security: clean · Correctness: internal conflicts resolved
