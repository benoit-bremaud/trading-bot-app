# Local review — trading-bot-app (branch chore/project-claude-md-cleanup)

- Date: 2026-10-22
- Commit: 9ea3282 (+ review fixes, same branch)
- Scope: branch diff main...HEAD (docs only: CLAUDE.md, README.md, ROADMAP.md, PROJECT_LOG.md, .gitignore, deleted AUDIT_REPORT.md and GUIDE_TEST_LOCAL.md), issue #2
- Checks run: docs + correctness (doc-auditor) · security (diff read + gitleaks). Design and tests: not applicable, no code in the diff.
- Mode: `--push` (QA pass not run; no runtime change)
- Verdict: ship · Must 0 · Should 4 (3 fixed, 1 deferred) · Nice 2

## Pre-merge gate (head SHA 9ea3282 + fixes)
| Step | Result |
|---|---|
| 1 Tests | ✅ 107 passed, 1 skipped (pytest, fresh Python 3.14 venv with `setuptools<81`) |
| 2 Coverage | tests 89 % statements on `trading_bot` (floor 80); 68 % with `scripts` included (pre-existing, unchanged by this diff) · docs: not measured, no doc counter in the project |
| 3 SonarQube | ⚠️ not run: no SonarQube project for this repo (tracked in #3) |
| 4 Secrets | ✅ gitleaks clean on main..HEAD · only `.env.example` tracked · diff read: nothing sensitive |
| 5 QA pass | not run (`--push` mode, docs-only diff) |
- Gate: **push OK; SonarQube needs an owner waiver for this Markdown-only diff, as for #6**

## 🔴 Must Have
_None._

## 🟡 Should Have
- `docs/architecture/review-local.md:38` `[docs]` · previous report still listed the deleted files and the unsourced KuCoin claim as open · **fixed**: report replaced (prior version in git history)
- `CLAUDE.md:32` `[docs]` · `setuptools<81` rationale too vague · **fixed**: names `kucoin-python` and when to drop the pin
- `CLAUDE.md` / `README.md` `[docs]` · two venv names (`.venv-test`, `.venv`) · **fixed**: `.venv` everywhere, ignored in `.gitignore`
- `pyproject.toml:41` `[docs]` · mypy `python_version = "3.12"` vs `requires-python >=3.11` · deferred: config change, belongs with #3

## 🔵 Nice to Have
- `README.md:23` · could say the dashboard is a non-goal under the new requirements · left to the UML gap analysis
- `PROJECT_LOG.md:7` · repository private, against the rule · tracked in #5

## ⚪ Disagree / Intentional
_None._

## Per-dimension summary
- Design: N/A · Docs: requirement IDs, phase criteria and links verified against R01–R40 · Tests: suite green, unchanged · Security: clean · Correctness: no stale reference to deleted files
