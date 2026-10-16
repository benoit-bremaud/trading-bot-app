# PROJECT_LOG

Chronological operational log, complementing `git log`.

## 2026-10-14

- Original GitHub repository `benoit-bremaud/trading-bot-app` found deleted; recreated as a private repository and all local branches pushed (including `feature/dashboard-web`, restored from the stale remote-tracking ref). Old PRs, issues and comments are lost. Gitleaks scan of 58 commits: no leaks.
- Archived the separate `btc-usdt-ratio-rebalancer` project to `~/Documents/02_personal/_archives/btc-usdt-ratio-rebalancer-2026-10-14.tar.gz` (dependencies excluded).
- Requirements drift review: February MVP exit criteria partly unmet (no drawdown metric, no metrics in paper run), dashboard added despite being a non-goal, KuCoin no longer serves French users.
- Requirements reset with the owner: BTC accumulation measured in sats against HODL, OKX Europe BTC/USDC spot, ML filter plus observational LLM supervisor, phased proof before real money. See `docs/requirements/btc-accumulation.md`.

## 2026-10-15

- Prior-art research (open-source bots, Kaggle competitions, LLM trading agents) confirmed the design; added R31–R39 (backtest/ML rigour, LLM guardrails). Freqtrade eliminated: its spot mode treats selling BTC as a short.
- Throwaway comparative prototype (naive SMA50 rule, 5 % buy-back stop, daily BTC 2018–2026): own engine 3.6828 BTC vs NautilusTrader 3.6761 BTC, same 168 fills. NautilusTrader caught a post-only-at-last-price rejection bug. Maker fill ratio of 93 % on daily bars judged optimistic.
- Decision R40 (MCDA 420/500): own engine with ccxt in production, NautilusTrader as CI execution oracle.
