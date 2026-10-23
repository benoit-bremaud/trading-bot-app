# Sequence diagram — btc-accumulation — supervisor advice pipeline

> **Feature**: BTC sats-accumulation bot (issue #15)
> **Source specs**: requirements R21–R25, R36–R39
> **Related ADRs**: none yet
> **Decisions captured**: reading and deciding are separated (R36)

## Context

How an opinion is produced from untrusted text and reaches the decision cycle. The pipeline runs
beside the engine and communicates only through a stored, typed opinion. At level 1 (observation, R21)
the cycle logs the opinion and ignores it.

## Diagram

```mermaid
sequenceDiagram
  participant NS as NewsAndStatusSources
  participant RD as ReaderModel (small, no power)
  participant DC as DeciderModel (large)
  participant CF as Confirmer
  participant BG as BudgetGuard
  participant OS as OpinionStore
  participant CY as DailyCycle
  participant JR as Journal

  loop hourly triage
    NS-->>RD: raw text (untrusted)
    RD->>RD: sanitise (strip HTML, normalise Unicode, reject homoglyphs)
    RD-->>DC: typed fields only
  end
  DC->>BG: request budget for call
  alt budget exhausted or API error
    BG-->>OS: no opinion
  else budget available
    DC-->>CF: proposed pause or delay
    CF->>CF: two independent sources or measurable confirmation
    alt confirmed
      CF-->>OS: opinion (delay up to 72 h or pause with expiry)
    else not confirmed
      CF-->>OS: no opinion
    end
  end
  OS-->>CY: current opinion
  CY->>JR: log opinion, exact inputs, prompt and model versions
  CY->>JR: log counterfactual portfolio and whether advice was ignored
```

## Notes

- The deciding model never sees raw text, and no model holds API keys (R20, R25, R36).
- Budget exhaustion and API errors always mean "no opinion", never "pause" (R39).
- Any change of prompt, model ID, threshold or source restarts the forward evaluation (R38).
- Model sizes (Haiku 5.5 triage, Opus 5.5 on alerts and daily synthesis) are in the component diagram and R23.
