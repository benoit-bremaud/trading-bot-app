# Data-flow diagram — btc-accumulation — data and sensitive fields

> **Feature**: BTC sats-accumulation bot (issue #15)
> **Source specs**: requirements R20, R24, R25, R29, R36
> **Related ADRs**: none yet
> **Decisions captured**: keys never reach the language model, external text is untrusted

## Context

What data moves where. No personal data of third parties is processed. Sensitive categories here are
`SECRET` (API keys), `FINANCIAL` (balances, orders) and `UNTRUSTED` (external text), each edge is annotated.

## Diagram

```mermaid
flowchart LR
  Exchange(["OKX Europe"])
  News(["News and status sources"])
  LLM(["Language-model API"])
  Operator(("Operator"))

  EnvFile[("Environment secrets")]
  Engine["Engine: DailyCycle and ProtectionWatcher"]
  Journal[("Journal")]
  Opinions[("OpinionStore")]
  Supervisor["Supervisor process"]
  Candles[("Candle store")]
  Reports["Sats reports"]

  Exchange -->|"candles, balances, fees"| Engine
  Engine -->|"FINANCIAL: orders and cancels"| Exchange
  EnvFile -->|"SECRET: trade-only API key, subaccount"| Engine
  Exchange -->|"public candles"| Candles
  Candles --> Engine
  Engine -->|"FINANCIAL: decisions, fills, fees, model versions"| Journal
  News -->|"UNTRUSTED: raw text"| Supervisor
  Supervisor -->|"sanitised typed fields, no keys, no balances"| LLM
  LLM -->|"typed opinion"| Supervisor
  Supervisor -->|"typed opinion, sources, cost"| Opinions
  Opinions --> Engine
  Journal --> Reports
  Reports --> Operator
  Operator -->|"approvals, phase and limit settings"| Engine
```

## Notes

- No edge carries `SECRET` toward `Supervisor` or `LLM` (R20, R25).
- The supervisor prompt contains no balances: it needs only market and incident context.
- The journal holds financial data, so it stays local and out of git (R29, repository rules).
- Open: where the journal and candle data are stored (files or SQLite) is an implementation choice, not modelled here.
