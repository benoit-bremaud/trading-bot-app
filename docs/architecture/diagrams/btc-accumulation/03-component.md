# Component diagram — btc-accumulation — engine, ports and adapters

> **Feature**: BTC sats-accumulation bot (issue #15)
> **Source specs**: requirements R19, R20, R30, R32, R40
> **Related ADRs**: none yet (R40 acts as the decision record)
> **Decisions captured**: R40 own engine with ccxt, NautilusTrader as dev/CI oracle only

## Context

Structure only, layered with the dependency rule (domain never imports infrastructure). One decision
cycle serves backtest, paper and live through interchangeable ports (R32). Layers stay proportional:
the supervisor is a separate process behind a stored opinion, not a new layer.

## Diagram

```mermaid
flowchart LR
  subgraph Adapters ["Adapters (entry points)"]
    CLI["CLI: backtest, paper, live, replay"]
    DASH["Read-only dashboard"]
  end
  subgraph Application ["Application"]
    CYCLE["DailyCycle"]
    PROT["ProtectionWatcher"]
    GATE["PhaseGate"]
    WF["WalkForwardRunner"]
    SAFE["SafetyLimits"]
  end
  subgraph Domain ["Domain"]
    STRAT["Strategy rules and trend reference"]
    MLF["MLFilter"]
    POCKET["Pocket, Tranche, Sats"]
    METRICS["Sats metrics vs HODL"]
  end
  subgraph Ports ["Ports (interfaces)"]
    PEX(["ExchangePort"])
    PMD(["MarketDataPort"])
    PJR(["JournalPort"])
    POP(["OpinionPort"])
    PCL(["ClockPort"])
  end
  subgraph Infra ["Infrastructure"]
    OKX["CcxtOkxAdapter"]
    BYB["CcxtBybitAdapter (public data only)"]
    SIM["SimulatedExchange (pessimistic maker fills)"]
    CSV["CsvCandleRepository"]
    JSTORE["JournalStore"]
    OSTORE["OpinionStore"]
  end
  subgraph Supervisor ["Supervisor process (separate)"]
    SUP["Reader, Decider, Confirmer, BudgetGuard"]
  end
  subgraph DevCI ["Development and CI only"]
    ORACLE["NautilusTrader oracle for R12"]
  end

  CLI --> CYCLE
  CLI --> WF
  CLI --> GATE
  DASH --> PJR
  CYCLE --> STRAT
  CYCLE --> MLF
  CYCLE --> SAFE
  CYCLE --> POCKET
  PROT --> POCKET
  WF --> CYCLE
  WF --> METRICS
  GATE --> METRICS
  CYCLE --> PEX
  CYCLE --> PMD
  CYCLE --> PJR
  CYCLE --> POP
  PROT --> PEX
  PROT --> PMD
  CYCLE --> PCL
  OKX -. implements .-> PEX
  BYB -. implements .-> PEX
  SIM -. implements .-> PEX
  CSV -. implements .-> PMD
  OKX -. implements .-> PMD
  JSTORE -. implements .-> PJR
  OSTORE -. implements .-> POP
  SUP --> OSTORE
  ORACLE -. "gap tolerance check" .-> SIM
```

## Notes

- Everything above `Ports` depends only on ports and the domain: backtest, paper and live differ by the adapter wired in (R32).
- API keys are read only by `CcxtOkxAdapter`, never by `SUP` (R20, R25).
- `SUP` writes only typed opinions to `OpinionStore`, so the engine keeps working if it is down (R39).
- The oracle is replayed in CI only, never imported by production code (R40).
- The legacy `KucoinMarketDataProvider`, `PaperOrderExecutor` and Flask dashboard map to `OKX`/`SIM`/`DASH`, see `docs/architecture/gap-analysis.md`.
