# Architecture

**Checkpoint:** 2026-08-17

## System Overview

```mermaid
flowchart TD
    E[BacktestEngine] --> G1[generate prices]
    E --> G2[generate_orders prices]
    E --> OB[on_bar timestamp price context]

    G1 --> S[Signal]
    G2 --> I[Explicit Order / Intent]
    OB --> C[StrategyContext]
    C --> I

    S --> EO[Equity Order]
    I --> ER[EquityInstructionResolver]
    I --> OR[OptionInstructionResolver / Builder]

    ER --> EO
    OR --> OO[OptionOrder]

    EO --> EX[Executor]
    OO --> OEX[OptionExecutor]

    EX --> P[Portfolio]
    OEX --> P

    P --> EP[Equity Position]
    P --> OP[Option Positions]
    P --> RP[Realized PnL Ledger]

    OP --> MTM[Option Mark-to-Market]
    EP --> NAV[Portfolio NAV]
    MTM --> NAV
    P --> NAV

    NAV --> BR[BacktestResult]
```

## Strategy Interface Selection

```mermaid
flowchart TD
    A[BacktestEngine.run] --> B{strategy has on_bar?}
    B -- Yes --> C[Dynamic runtime strategy]
    B -- No --> D{strategy has generate_orders?}
    D -- Yes --> E[Pre-generated explicit instructions]
    D -- No --> F[Legacy generate signal path]

    C --> X[Common execution path]
    E --> X
    F --> Y[Legacy signal execution]
    X --> Z[Portfolio accounting and EOD NAV]
    Y --> Z
```

Dynamic `on_bar()` has precedence because a strategy implementing it needs current runtime state.

## Same-Day Multiple Instructions

```mermaid
sequenceDiagram
    participant Engine
    participant Strategy
    participant Resolver
    participant Portfolio

    Engine->>Engine: snapshot daily cash
    Engine->>Strategy: instruction(s)
    Strategy-->>Engine: [EquityIntent, OptionIntent]
    Engine->>Resolver: resolve EquityIntent using same snapshot
    Resolver-->>Engine: Equity Order
    Engine->>Portfolio: execute/apply equity
    Engine->>Resolver: resolve OptionIntent using same snapshot
    Resolver-->>Engine: Option Order
    Engine->>Portfolio: execute/apply option
```

The allocation snapshot prevents the second instruction from unintentionally shrinking simply because the first instruction executed first.

## Allocation Base

Sizing semantics:

```text
capital_base =
    intent.allocation_base
    if allocation_base is explicitly supplied
    else engine-provided cash snapshot

budget = capital_base * allocation_fraction
```

This keeps generic strategies cash-relative while allowing fixed-notional ladder tranches.

## Runtime StrategyContext

```mermaid
flowchart LR
    P[Portfolio] --> C[StrategyContext]
    Q[Current option quotes] --> C
    C --> S[Dynamic Strategy on_bar]
    S --> I[Order / Intent / None]
```

Current context surface:

- cash
- option positions
- option quotes

A copy of the option-position mapping is exposed rather than the portfolio's dictionary itself.

## SPY + LEAPS Runtime Flow

```mermaid
flowchart TD
    A[New SPY bar] --> B[Build StrategyContext]
    B --> C{First bar?}

    C -- Yes --> D[Set peak and initial capital]
    D --> E[Generate SPY + LEAPS initial tranche]

    C -- No --> F{Open LEAPS and current quote?}
    F -- Yes --> G{Bid return >= take-profit threshold?}
    G -- Yes --> H[Generate OptionOrder SELL full quantity]
    G -- No --> I[Update peak / drawdown state]
    F -- No --> I

    I --> J{New drawdown level?}
    J -- No --> K[No instruction]
    J -- Yes --> L{Below max_tranches?}
    L -- Yes --> M[Generate next SPY + LEAPS tranche]
    L -- No --> K
```

## Option Accounting Lifecycle

```mermaid
flowchart TD
    A[Option BUY at ask] --> B[Create/update OptionPosition]
    B --> C[Weighted average cost]
    C --> D[Daily mark using bid]
    D --> E{Take-profit?}
    E -- No --> D
    E -- Yes --> F[Option SELL at bid]
    F --> G[Calculate realized PnL]
    G --> H[Add proceeds to cash]
    G --> I[Add realized PnL to Portfolio]
    H --> J{Quantity == 0?}
    I --> J
    J -- Yes --> K[Remove contract from option_positions]
    J -- No --> B
```

## Missing Quote Semantics

Two behaviors are intentionally different:

1. **Strategy decision:** if the current option quote is missing, the runtime context does not invent one. Quote-dependent actions are skipped.
2. **Portfolio valuation:** if an open position lacks a current quote but has a previous valid mark, end-of-day valuation can use the last known option price.

## Current Design Limitation

A single `tranches_deployed` counter worked while SPY and LEAPS always entered and exited together. LEAPS take-profit now allows option exposure to disappear while SPY exposure remains.

Sprint 14.4 should replace or augment this combined state with a more expressive model before capital recycling is implemented.
