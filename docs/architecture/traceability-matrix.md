# Traceability matrix — requirements ↔ diagrams

Diagrams live in [`diagrams/btc-accumulation/`](diagrams/btc-accumulation/). Legend: UC = use case, SD = sequence,
CMP = component, CD = class, STM = state, DFD = data flow. A requirement with no diagram is either an
acceptance criterion (measured, not modelled) or a process rule, noted in the last column.

| Requirement | UC | SD | CMP | CD | STM | DFD | Note |
| --- | --- | --- | --- | --- | --- | --- | --- |
| R01 Bitcoin only | — | — | — | Pocket (BTC/USDC only) | 05a | — | constraint |
| R02 Results in BTC vs HODL | UC2 | — | WF, METRICS | SatsReport | — | Reports | |
| R03 Net of fees | UC2 | 02a | SIM | FeeSchedule, Fill | — | — | |
| R04 Active pocket 10–20 % | UC13, UC15 | — | — | Pocket | 05c | — | |
| R05 Phase-limited deposit | UC6, UC13 | — | — | — | 05c | — | |
| R06 Hard limits | UC15 | 02a | SAFE | HardLimits | 05b | — | |
| R07 BTC/USDC spot | — | — | OKX | Pocket | — | — | constraint |
| R08 Spot only | UC7 | 02b | OKX | — | — | — | |
| R09 Long BTC or flat | — | — | — | Pocket | 05a | — | |
| R10 Daily decisions | — | 02a | CYCLE | Candle | — | — | |
| R11 Deterministic rules | — | 02a | STRAT | ExitCandidate | — | — | |
| R12 Trend reference | UC2 | — | STRAT | SatsReport | — | — | |
| R13 ML filters and sizes | — | 02a | MLF | SizedExit | — | — | |
| R14 ML inputs one at a time | UC4 | — | WF | — | — | — | |
| R15 Simple models | — | — | MLF | — | — | — | process |
| R16 5 % buy-back stop | — | 02b | PROT | Tranche | 05a, 05b | — | polling frequency open |
| R16b No performance pause | UC14 | — | GATE | — | 05c | — | |
| R16c Fail closed | UC10, UC11 | 02b | PROT | — | 05a | — | |
| R16d Depeg controller | — | 02b | PROT | — | 05a | — | |
| R17 OKX venue and fee cap | UC7 | — | OKX | FeeSchedule | — | Exchange | |
| R18 Maker with fallback | — | 02a | CYCLE | OrderIntent | 05b | — | |
| R19 Exchange port, Bybit paper | — | — | PEX, BYB | — | — | — | |
| R20 Keys, subaccount | UC7, UC11 | 02b | OKX | — | — | EnvFile | |
| R21 Observation first | UC16 | 02c | SUP | SupervisorOpinion | — | — | |
| R22 Delay, reduce, pause only | UC17 | 02c | SUP | SupervisorOpinion | 05a | — | |
| R23 Haiku triage, Opus synthesis | — | 02c | SUP | — | — | — | |
| R24 10 € budget | UC18 | 02c | SUP | — | — | Opinions | |
| R25 Untrusted text | — | 02c | SUP | — | — | News | |
| R26 Phase 1 | UC1, UC12 | — | WF, GATE | PhaseGate | 05c | — | |
| R27 Phase 2 | UC12, UC9 | — | GATE | PhaseGate | 05c | — | |
| R28 Phase 3 | UC13, UC14 | — | GATE | PhaseGate | 05c | — | |
| R29 Journal and replay | UC8, UC9 | 02a | PJR | DecisionRecord | — | Journal | |
| R30 Clean architecture, tests, UML | — | — | all | — | — | — | process |
| R31 Lookahead and warm-up gates | UC3 | — | WF | — | — | — | CI gate |
| R32 One code path | — | 02a | PEX, SIM | — | — | — | |
| R33 Pessimistic maker fills | — | — | SIM | Fill | 05b | — | |
| R34 Purged walk-forward | UC1 | — | WF | — | — | — | |
| R35 ML target, bootstrap CI | UC1, UC4 | — | WF, MLF | SatsReport | — | — | |
| R36 Read/decide separation | UC16 | 02c | SUP | — | — | LLM | |
| R37 Confirmation, caps, expiry | UC17 | 02c | SUP | SupervisorOpinion | 05a | — | |
| R38 Frozen versions, counterfactual | UC16, UC17 | 02c | SUP | DecisionRecord | — | — | |
| R39 Fallback is no opinion | — | 02c | SUP | — | — | — | |
| R40 Own engine plus oracle | UC5 | — | ORACLE | — | — | — | |

Checks: every use case UC1–UC18 appears above; every diagram file is referenced; no orphan class
(`Candle`, `Pocket`, `Tranche`, `ExitCandidate`, `SizedExit`, `OrderIntent`, `Fill`, `FeeSchedule`,
`SupervisorOpinion`, `DecisionRecord`, `HardLimits`, `PhaseGate`, `SatsReport` all realise a requirement).
