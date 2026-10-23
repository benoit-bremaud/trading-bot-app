# Class diagram — btc-accumulation — domain model

> **Feature**: BTC sats-accumulation bot (issue #15)
> **Source specs**: requirements R02, R04, R06, R13, R16, R22, R29, R35
> **Related ADRs**: none yet
> **Decisions captured**: results in integer sats, never fiat (R02)

## Context

The domain entities and the ports they cross. Quantities of BTC are integer sats, prices are decimals,
to avoid float error (the legacy code uses `float` everywhere, see the gap analysis). Does not detail
indicator computation nor the LLM client.

## Diagram

```mermaid
classDiagram
  class Candle {
    +datetime openTime
    +Decimal open
    +Decimal high
    +Decimal low
    +Decimal close
    +Decimal volume
  }
  class Pocket {
    +int btcSats
    +Decimal usdc
    +int pocketTargetBps
    +state PocketState
    +openTranches() Tranche[]
  }
  class Tranche {
    +UUID id
    +int exitedSats
    +Decimal exitVwap
    +stopPrice() Decimal
    +isStopReached(price) bool
  }
  class ExitCandidate {
    +date day
    +str rule
  }
  class SizedExit {
    +float fraction
    +str modelVersion
  }
  class OrderIntent {
    +Side side
    +int sats
    +Decimal limitPrice
    +OrderKind kind
    +datetime deadline
  }
  class Fill {
    +int sats
    +Decimal price
    +Decimal feeRate
    +bool maker
  }
  class FeeSchedule {
    +Decimal makerRate
    +Decimal takerRate
    +assertBelowCap(cap)
  }
  class SupervisorOpinion {
    +OpinionKind kind
    +datetime expiresAt
    +str[] sources
    +str promptVersion
  }
  class DecisionRecord {
    +date day
    +json inputs
    +str modelVersions
    +FeeSchedule fees
    +json outcome
  }
  class HardLimits {
    +int maxOrdersPerDay
    +int maxOrderSats
    +check(orderCount, sats) bool
  }
  class PhaseGate {
    +Phase phase
    +evaluate(evidence) GateResult
  }
  class SatsReport {
    +int satsEnd
    +int satsHodl
    +int satsTrendRule
    +CI confidenceInterval
  }

  Pocket "1" o-- "0..*" Tranche
  Pocket ..> HardLimits : checked by
  ExitCandidate --> SizedExit : filtered and sized into
  SizedExit --> OrderIntent : produces
  OrderIntent "1" --> "0..*" Fill : executed as
  Fill ..> FeeSchedule : charged with
  Tranche ..> Fill : exit vwap from
  DecisionRecord "1" o-- "0..1" SizedExit
  DecisionRecord "1" o-- "0..*" Fill
  DecisionRecord "1" o-- "0..1" SupervisorOpinion
  PhaseGate ..> SatsReport : reads
  SatsReport ..> Candle : computed from
```

## Notes

- `SupervisorOpinion.kind` has no "sell" value by construction: the worst effect is a return to HODL (R22).
- `Tranche.stopPrice()` = `exitVwap` × 1.05 (R16), one per exited tranche including partial exits.
- `SatsReport` holds the HODL and trend-rule baselines beside the result so no figure is shown without them (R02).
- Indicators (RSI, MACD, Bollinger) from the legacy code are inputs of the ML filter (R14), kept as value objects, not part of this model.
