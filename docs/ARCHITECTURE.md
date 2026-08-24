# Architecture

**Checkpoint:** 2026-08-24  
**Milestone:** Sprint 15 — Dynamic LEAPS Contract Lifecycle

## System Overview

QuantResearch separates strategy decisions, instruction resolution,
execution, portfolio accounting, and market-data access.

The backtest engine supports three strategy interfaces:

1. `generate(prices)` for legacy signal-based strategies.
2. `generate_orders(prices)` for pre-generated explicit orders or intents.
3. `on_bar(timestamp, price, context)` for runtime strategies requiring current portfolio state or option quotes.

```mermaid
flowchart TD
    E[BacktestEngine] --> G1[generate prices]
    E --> G2[generate_orders prices]
    E --> OB[on_bar timestamp price context]
    G1 --> S[Signal]
    G2 --> I[Explicit Order or Intent]
    P[Portfolio] --> C[StrategyContext]
    Q[Current Option Quotes] --> C
    C --> OB
    OB --> I
    S --> EO[Equity Order]
    I --> ER[EquityInstructionResolver]
    I --> OR[OptionInstructionResolver]
    ER --> EO
    OR --> OO[OptionOrder]
    EO --> EX[Executor]
    OO --> OEX[OptionExecutor]
    EX --> P
    OEX --> P
    P --> EP[Equity Position]
    P --> OP[Option Positions]
    P --> RP[Realized PnL]
    OP --> MTM[Option Mark-to-Market]
    EP --> NAV[Portfolio NAV]
    MTM --> NAV
    P --> NAV
    NAV --> BR[BacktestResult]
```

## Strategy Interface Selection

`BacktestEngine` selects the most state-aware interface implemented by the strategy.

```mermaid
flowchart TD
    A[BacktestEngine.run] --> B{Strategy has on_bar?}
    B -- Yes --> C[Dynamic Runtime Strategy]
    B -- No --> D{Strategy has generate_orders?}
    D -- Yes --> E[Pre-generated Explicit Instructions]
    D -- No --> F[Legacy Signal Strategy]
    C --> X[Explicit Execution Path]
    E --> X
    F --> Y[Legacy Signal Execution]
    X --> Z[Portfolio Accounting and EOD NAV]
    Y --> Z
```

`on_bar()` has precedence because runtime strategies require current portfolio and market state before making each decision.

## Runtime Strategy Context

Before calling a dynamic strategy, the engine builds a `StrategyContext`.

The context exposes current cash, a copy of current option positions, and current quotes for option contracts held by the portfolio.

Missing current option quotes are allowed. A quote-dependent strategy decision can therefore choose not to act rather than inventing market data.

## Runtime Action Contract

A runtime strategy may return:

- `None`;
- one order or intent;
- a `list` or `tuple` containing multiple orders or intents.

`BacktestEngine` normalizes single and multiple actions and executes each action independently. This allows a strategy to enter multiple legs or exit multiple option contracts on the same trading day.

## Same-Day Allocation Semantics

Before executing the current day's instructions, `BacktestEngine` captures a cash snapshot. Allocation-based intents generated for that bar use the same snapshot unless the intent explicitly supplies its own `allocation_base`.

```text
capital_base =
    intent.allocation_base
    if allocation_base is explicitly supplied
    else engine-provided daily cash snapshot

budget =
    capital_base * allocation_fraction
```

This prevents a second same-day allocation from becoming smaller only because an earlier instruction already consumed cash. It also allows fixed-notional ladder tranches to size from the strategy's initial capital.

## SPY + LEAPS Ladder Strategy

`SpyLeapsLadderStrategy` is a stateful runtime strategy.

Its responsibilities include:

- maintaining the running SPY peak;
- calculating drawdown levels;
- deploying equity and option legs;
- tracking tranche lifecycle state;
- resolving LEAPS contracts at deployment time;
- evaluating contract-specific take-profit conditions;
- recycling released option capacity.

The strategy supports both fixed and dynamic LEAPS contract resolution.

## Tranche Lifecycle Model

Strategy lifecycle state is represented by `SpyLeapsTranche`.

Each tranche stores:

```text
level
equity_deployed
option_deployed
option_closed
option_contract
```

Equity and option state are deliberately independent. Closing a LEAPS position does not automatically close the SPY leg, making option capital recycling possible.

## LEAPS Contract Resolution

Contract selection is delegated to `LeapsContractResolver`.

```mermaid
flowchart TD
    A[SpyLeapsLadderStrategy] --> B[LeapsContractResolver]
    B --> C[FixedLeapsContractResolver]
    B --> D[DynamicLeapsContractResolver]
    C --> E[Configured OptionContract]
    D --> F[OptionContractUniverseProvider]
    F --> G[Historical Contract Universe]
    G --> H[CALL Filter]
    H --> I[DTE Range Filter]
    I --> J[Target DTE Ranking]
    J --> K[Nearest ATM Ranking]
    K --> L[Resolved OptionContract]
    E --> L
```

### Fixed Resolver

`FixedLeapsContractResolver` preserves legacy fixed-contract behavior by always returning the configured contract.

### Dynamic Resolver

`DynamicLeapsContractResolver` obtains contracts from an `OptionContractUniverseProvider`.

Current default LEAPS parameters are:

```text
minimum DTE = 365 days
maximum DTE = 548 days
target DTE  = 456 days
```

Eligible contracts must be CALL options within the configured DTE range. Selection prioritizes distance from target DTE, distance between strike and current underlying price, expiration date, and strike.

## Option Contract Universe

Contract discovery is separated from contract selection.

`OptionContractUniverseProvider` defines the abstraction used by the dynamic resolver. Current implementations include:

- `StaticOptionContractUniverseProvider`
- `MassiveOptionContractUniverseProvider`

The Massive-backed provider retrieves historical contract reference data and normalizes vendor records into internal `OptionContract` objects. The strategy itself remains vendor-independent.

## Massive Option Data Boundary

Massive-specific HTTP access and normalization live in the data provider layer.

```text
Historical contract discovery
    → MassiveOptionContractUniverseProvider
    → OptionContract

Historical quote retrieval
    → MassiveHistoricalOptionDataProvider
    → HistoricalOptionQuote
```

This separation allows strategy and execution layers to operate on internal domain objects rather than vendor response dictionaries.

## Dynamic LEAPS Deployment Flow

```mermaid
flowchart TD
    A[SPY Market Bar] --> B[SpyLeapsLadderStrategy]
    B --> C{Option Capacity Available?}
    C -- No --> D[Continue Without New Option Deployment]
    C -- Yes --> E[Resolve LEAPS Contract]
    E --> F[OptionContractUniverseProvider]
    F --> G[Historical Option Universe]
    G --> H[DynamicLeapsContractResolver]
    H --> I[CALL and DTE Filtering]
    I --> J[Target DTE and ATM Ranking]
    J --> K[Resolved OptionContract]
    K --> L[OptionOrderIntent]
    K --> M[SpyLeapsTranche.option_contract]
    L --> N[BacktestEngine]
    N --> O[OptionInstructionResolver]
    O --> P[OptionOrder]
    P --> Q[OptionExecutor]
    Q --> R[Portfolio]
```

The exact contract selected at deployment time is stored in the tranche lifecycle ledger. Later exit decisions therefore do not need to depend on the original legacy `self.leaps_contract`.

## Drawdown and Capital Recycling

The ladder tracks the running SPY peak and converts drawdown depth into trigger levels. When a new drawdown level is reached, equity and option capacity are evaluated independently.

A previous option take-profit can release option capacity while its corresponding equity exposure remains active. A later drawdown may therefore deploy an option without requiring a new equity leg, and the new option may resolve to a different contract.

```text
Earlier lifecycle:

Tranche 0
    SPY        OPEN
    Contract A CLOSED

Later drawdown:

Tranche 2
    SPY        NONE
    Contract B OPEN
```

## Multi-Contract Take-Profit

Take-profit decisions are based on active contracts recorded in the tranche ledger.

Identical contracts are deduplicated because several strategy tranches may correspond to one aggregated portfolio `OptionPosition`.

```mermaid
flowchart TD
    A[Tranche Lifecycle Ledger] --> B[Collect Active Option Contracts]
    B --> C[Deduplicate Contracts]
    C --> D[Lookup Portfolio OptionPosition]
    D --> E[Lookup Current Historical Quote]
    E --> F{Position and Quote Available?}
    F -- No --> G[Skip Contract]
    F -- Yes --> H[Calculate Bid Return]
    H --> I{Return >= Take-Profit Threshold?}
    I -- No --> J[Keep Contract Active]
    I -- Yes --> K[Generate OptionOrder SELL]
    K --> L[Close Matching Tranche Option Legs]
    L --> M[Return SELL Order Collection]
```

Multiple different contracts may reach the take-profit threshold on the same bar. In that case, `SpyLeapsLadderStrategy.on_bar()` returns multiple `OptionOrder` objects and `BacktestEngine` executes them sequentially.

## Tranche State vs Portfolio State

The tranche ledger and portfolio positions serve different purposes.

```text
Strategy layer
    SpyLeapsTranche
        → lifecycle history
        → deployment capacity
        → contract ownership

Portfolio layer
    OptionPosition
        → aggregated quantity
        → average cost
        → realized/unrealized PnL
```

Multiple active tranches may reference the same `OptionContract`, while the portfolio aggregates those holdings into one `OptionPosition`. Therefore the same contract produces one aggregated exit order, while different contracts can produce independent exits.

## Option Execution Lifecycle

Option execution uses executable market sides:

- BUY at ask;
- SELL at bid.

```mermaid
flowchart TD
    A[OptionOrderIntent BUY] --> B[Resolve Quantity]
    B --> C[OptionOrder BUY]
    C --> D[Execute at Ask]
    D --> E[Create or Update OptionPosition]
    E --> F[Weighted Average Cost]
    F --> G[Daily Mark-to-Market at Bid]
    G --> H{Take-Profit Triggered?}
    H -- No --> G
    H -- Yes --> I[OptionOrder SELL]
    I --> J[Execute at Bid]
    J --> K[Calculate Realized PnL]
    K --> L[Add Sale Proceeds to Cash]
    K --> M[Update Portfolio Realized PnL]
    L --> N{Position Quantity Zero?}
    M --> N
    N -- Yes --> O[Remove OptionPosition]
    N -- No --> E
```

## Missing Quote Semantics

Strategy decision-making and portfolio valuation intentionally use different missing-data behavior.

For runtime strategy decisions, missing current quotes are not invented or forward-filled. Quote-dependent decisions such as take-profit are skipped for that contract.

For end-of-day valuation, if an open position does not have a current quote but a previous valid mark exists, the engine may use the last known option mark.

This prevents a stale quote from silently triggering a strategy decision while still allowing portfolio NAV calculation when historical quote data is sparse.

## SPY + Dynamic LEAPS End-to-End Lifecycle

```mermaid
flowchart TD
    A[Initial SPY Bar] --> B[Resolve Contract A]
    B --> C[Deploy Initial SPY + Contract A]
    C --> D[Record Contract A in Tranche]
    D --> E[SPY Drawdown]
    E --> F[Evaluate Independent Capacity]
    F --> G[Resolve Contract B]
    G --> H[Deploy New Tranche with Contract B]
    H --> I[Contract A and Contract B Active]
    I --> J[Read Current Quotes]
    J --> K[Evaluate Take-Profit per Unique Contract]
    K --> L{Multiple Contracts Trigger?}
    L -- No --> M[Generate Matching SELL Order]
    L -- Yes --> N[Generate Multiple SELL Orders]
    M --> O[BacktestEngine]
    N --> O
    O --> P[Execute Each Option SELL]
    P --> Q[Update Cash and Realized PnL]
    Q --> R[Remove Closed Option Positions]
    R --> S[Close Matching Tranche Option Legs]
    S --> T[SPY Legs Remain Active]
    T --> U[Option Capacity Available for Recycling]
```

This lifecycle has been validated through integration tests using the real `SpyLeapsLadderStrategy`, `BacktestEngine`, option execution, and portfolio accounting.

## Architectural Invariants

### Strategy and execution remain separate

Strategies generate decisions. Resolvers translate allocation intents into executable orders. Executors determine execution prices. Portfolio objects own accounting state.

### Vendor data does not enter strategy logic directly

Massive-specific response structures are normalized in the data layer. Strategies and resolvers operate on internal domain objects.

### Tranche state is not portfolio accounting

Tranches represent strategy lifecycle state. `OptionPosition` represents financial position state.

### Same contract means one aggregated exit

If multiple tranches reference the same active option contract, the strategy generates one exit for the aggregated portfolio position.

### Different contracts may exit together

If multiple distinct active contracts independently reach take-profit, they may generate multiple SELL orders on the same bar.

### Strategy decisions do not use synthetic current quotes

Missing current quotes cause quote-dependent decisions to be skipped. Portfolio valuation may separately use a previous valid mark.

### Legacy interfaces remain supported

The framework continues to support signal strategies, pre-generated-order strategies, and fixed-contract LEAPS behavior alongside the dynamic runtime architecture.

## Current Architectural Boundary

Sprint 15 resolves the earlier tranche-state limitation.

The framework now supports:

- independent equity and option lifecycle state;
- option capital recycling;
- dynamic historical LEAPS contract selection;
- contract rotation across recycling cycles;
- simultaneous active option contracts;
- contract-aware take-profit;
- same-contract exit deduplication;
- multiple option exits on the same bar;
- engine-level multi-order execution;
- portfolio accounting for those executions.

The next architectural boundary is historical data validation rather than strategy-state representation.

Sprint 16 should progressively validate:

```text
historical timestamp
        ↓
historical SPY price
        ↓
Massive historical option universe
        ↓
DynamicLeapsContractResolver
        ↓
selected OptionContract
        ↓
Massive historical option quote
        ↓
executable bid / ask
        ↓
SpyLeapsLadderStrategy
        ↓
BacktestEngine
        ↓
Portfolio and performance results
```

The first objective should be a small historical smoke test before attempting multi-month or multi-year dynamic LEAPS backtests.
