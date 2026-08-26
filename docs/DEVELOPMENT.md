# Development Guide

**Checkpoint:** 2026-08-25  
**Current milestone:** Real Historical Dynamic LEAPS Backtesting

## Purpose

QuantResearch is developed as a modular, test-driven research framework for
equity and listed-option strategies.

The architecture separates:

- strategy decisions
- instruction / sizing resolution
- execution
- portfolio accounting
- historical market-data access
- option contract selection
- analytics and visualization

The project currently focuses on daily historical research rather than
intraday option execution.

## Core Development Contract

A feature should normally progress through:

1. Define the desired behavioral contract.
2. Add or update a focused test.
3. Confirm the expected RED failure.
4. Implement the smallest production change.
5. Run the focused test.
6. Run the offline regression suite.
7. Run live integration tests only when external data behavior is involved.
8. Update documentation when behavior or architecture changes.

Recommended commands:

```powershell
pytest tests/test_some_file.py -v
pytest -m "not integration"
pytest -m integration -v -s
git diff --check
```

The latest checkpoint is GREEN with more than 350 regression / integration
tests in the repository.

## Backtest Engine

`BacktestEngine` supports three strategy contracts:

```text
generate(prices)
generate_orders(prices)
on_bar(timestamp, price, context)
```

The runtime `on_bar(...)` path is the primary interface for stateful
strategies such as the SPY + LEAPS ladder.

The engine owns:

- bar-by-bar orchestration
- same-day allocation cash snapshots
- instruction execution
- option market-state resolution
- option mark-to-market
- equity-curve construction

The engine should not contain strategy-specific rules.

## Strategy Context

`StrategyContext` exposes a deliberately narrow runtime view:

- current cash
- current option positions
- current option market-state adapters

A strategy does not receive direct access to vendor APIs or the full engine.

For missing current option data, the strategy context does not fabricate a
quote. Quote-dependent decisions can therefore skip the action.

## Instruction Layer

Equity and option intents describe desired allocation without performing
execution.

`allocation_base` can lock an intent to a fixed capital base. If absent, the
engine-provided daily cash snapshot is used.

This is important for ladder strategies because multiple 25% allocations can
be sized from initial capital rather than from progressively shrinking cash.

## Execution Layer

Equity orders flow through `Executor`.

Option orders flow through:

```text
OptionOrder / OptionOrderIntent
        ↓
OptionInstructionResolver
        ↓
OptionOrderBuilder
        ↓
OptionExecutor
        ↓
Portfolio
```

Legacy quote execution semantics remain:

- BUY at executable ask
- SELL at executable bid

For daily research, the engine can instead consume
`DailyOptionExecutionQuoteAdapter`, whose bid/ask-like attributes are explicit
execution proxies rather than historical market quotes.

## Daily Option Pricing

Daily option aggregates do not contain historical bid/ask.

The current default research policy is therefore explicit:

```text
BUY execution proxy  = daily close
SELL execution proxy = daily close
mark-to-market       = daily close
```

This is represented through:

```text
HistoricalOptionBar
        ↓
DailyOptionPricingPolicy
        ↓
DailyOptionPricing
        ↓
DailyOptionExecutionQuoteAdapter
```

This avoids labeling a daily close as a real bid or ask.

## Option Mark-to-Market

The engine resolves option market state through a unified path.

If an explicit `mark_price` exists, valuation uses it.

For legacy quote data, bid remains the fallback mark.

If a current bar / quote is unavailable but the position has a previously
valid mark, end-of-day valuation can use the last known mark.

Strategy decisions and valuation intentionally differ:

```text
missing current market data
    strategy decision → skip quote-dependent action
    portfolio MTM     → last known mark may be used
```

## Portfolio Accounting

The portfolio owns:

- cash
- equity position
- option positions
- realized PnL

Option positions support:

- weighted-average cost
- partial exits
- full exits
- realized PnL
- position cleanup

A fully exited option contract is removed from `option_positions`. Historical
realized PnL therefore lives at the portfolio level.

## SPY + LEAPS Ladder State

`SpyLeapsLadderStrategy` tracks:

- running SPY peak
- drawdown levels
- initial capital
- independent active equity capacity
- independent active option capacity
- tranche lifecycle ledger
- dynamic contract resolution
- take-profit state

`SpyLeapsTranche` records:

```text
level
equity_deployed
option_deployed
option_closed
option_contract
```

Important invariant:

```text
equity lifecycle != option lifecycle
```

An option can close for profit while the associated equity leg remains open.

Later drawdowns may therefore create an option-only lifecycle tranche when
equity capacity is already full but option capacity has been released.

## Active Capacity vs Lifetime Ledger

`max_tranches` represents active capacity.

It does not cap the lifetime number of `SpyLeapsTranche` objects.

For example:

```text
historical lifecycle count = 3
active equity tranches     = 2
active option tranches     = 1
max_tranches               = 2
```

This is valid.

The lifecycle ledger is stored in creation order, not sorted by drawdown
level.

## Dynamic LEAPS Contract Resolution

`DynamicLeapsContractResolver` obtains contracts from an
`OptionContractUniverseProvider`.

Current default range:

```text
min DTE    = 365
max DTE    = 548
target DTE = 456
```

Current ranking priority:

1. distance from target DTE
2. distance from current SPY price
3. expiration date
4. strike

CALL options outside the configured DTE range are rejected.

## Entry-Date Tradability

A reference contract existing on a historical date does not prove that it
actually traded on that date.

Real historical tests exposed examples where a contract existed in Massive's
reference universe but had no daily aggregate bar on the intended entry day.

The dynamic resolver can therefore receive a tradability provider.

Candidates remain ranked using the existing DTE / ATM rules and are checked in
that order:

```text
best candidate
    ↓
has_bar(entry_date)?
    ├─ yes → select
    └─ no  → next candidate
```

This prevents look-ahead execution using a future day's option price.

## Massive Option Data

Massive-specific functionality remains isolated in the provider layer.

### Contract discovery

```text
MassiveHttpClient.get_option_contracts
        ↓
MassiveOptionContractUniverseProvider
        ↓
OptionContract
```

Historical contract queries use:

```text
as_of = historical date
expired = false
expiration_date.gte / lte
```

The provider caches identical historical universe queries.

### Daily option aggregates

```text
MassiveHttpClient.get_aggregate_bars
        ↓
MassiveHistoricalOptionBarProvider
        ↓
HistoricalOptionBar
```

The aggregate endpoint uses the common 429 retry / backoff helper.

## Option-Bar Cache and Automatic Range Loading

`MassiveHistoricalOptionBarProvider` supports:

- `get_bars(...)` — explicit range retrieval
- `get_bar(...)` — engine-facing single-day lookup
- `has_bar(...)` — entry-date tradability probe
- `preload(...)` — explicit range preload
- `set_backtest_range(...)` — automatic remaining-window loading

Behavior:

```text
get_bar(timestamp, contract)
        ↓
cache hit?
    ├─ yes → return
    └─ no
        ↓
load timestamp → configured backtest end
        ↓
cache all returned bars
        ↓
return requested date
```

A newly resolved option contract therefore triggers at most one remaining
range load under normal backtest operation.

`has_bar(...)` is deliberately lighter: it only probes the requested day so
candidate screening does not download an entire backtest range.

## Missing Historical Bars

Historical option daily bars can be sparse, especially for long-dated LEAPS.

Rules:

- no entry-day bar → contract is not historically tradable for that entry
- no current strategy-decision bar → do not synthesize a decision price
- no current valuation bar + prior valid mark → last-known-mark fallback
- no current valuation bar + no historical mark → explicit failure

Do not substitute the next available future bar for an entry-day execution.

## Live Integration Testing

Tests requiring Yahoo or Massive are marked:

```python
@pytest.mark.integration
```

Use:

```powershell
pytest -m "not integration"
```

for normal development.

Use:

```powershell
pytest -m integration -v -s
```

for external-data validation.

This avoids making every local regression run dependent on API latency or rate
limits.

## Current Validated Scope

Real historical tests have validated:

- one-day dynamic LEAPS selection and execution
- five-day continuous MTM
- one-month dynamic backtest
- two-tranche drawdown deployment
- simultaneous distinct LEAPS positions
- exact NAV reconciliation
- real +25% take-profit
- option-capacity release
- later option redeployment after a new drawdown
- contract rotation
- automatic range loading
- entry-date tradability filtering
- full-year 2025 historical execution

## Current Research Boundary

Execution and historical-data semantics are now sufficiently mature for a
visual research layer.

The next milestone should focus on turning backtest state into explainable
visual diagnostics before adding new strategy logic.
