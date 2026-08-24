# Development Progress

**Latest checkpoint:** 2026-08-24  
**Regression status:** 314 passed, 0 failed

## Completed Foundation

### Equity Backtesting

- Price-series ingestion and validation.
- Signal enum and moving-average crossover strategy.
- Equity orders and execution.
- Position and portfolio accounting.
- Trade log.
- Performance metrics including return, CAGR, volatility, Sharpe ratio, and maximum drawdown.
- Trade analytics.
- Slippage infrastructure.

### Options Domain

- `OptionContract` and option type modeling.
- Historical option quotes and quote stores.
- Option positions with weighted-average cost.
- Unrealized and realized option PnL.
- Partial and full exits.
- ATM / nearest-strike and LEAPS-oriented selection infrastructure.
- Yahoo option-chain ingestion/normalization.
- Massive historical option-data provider.
- HTTP pagination behavior.
- Option order, intent, builder, resolver, execution result, and executor.

## Sprint 13 — Option Order & Execution

**Status: COMPLETE**

Established the option execution pipeline:

`OptionOrder / OptionOrderIntent -> resolver/builder -> OptionExecutor -> Portfolio / OptionPosition`

Important behaviors:

- Buy at ask.
- Sell at bid.
- Apply multiplier-aware cash accounting.
- Preserve realized PnL at portfolio level.
- Remove option positions after complete exit.

## Sprint 14.1 — SPY + LEAPS Initial Allocation

**Status: COMPLETE**

Implemented the infrastructure required to execute a combined SPY + LEAPS allocation on the same bar.

Key work:

- `EquityOrderIntent`.
- Multiple explicit instructions per trading day.
- Same-day cash snapshot so sibling allocations use the same pre-trade cash base.
- Fixed optional `allocation_base`.
- Initial SPY + LEAPS end-to-end backtest.
- Combined equity/option NAV validation.

Example research configuration:

- 25% initial capital SPY.
- 25% initial capital LEAPS.

## Sprint 14.2 — Drawdown Ladder

**Status: COMPLETE**

Implemented stateful SPY drawdown tracking.

Key work:

- Running peak.
- Drawdown calculation.
- Configurable drawdown step.
- Drawdown level mapping.
- Floating-point tolerance at exact thresholds.
- One-time trigger per drawdown level.
- Reset behavior after a new peak.
- Configurable `max_tranches`.
- Fixed initial-capital sizing for ladder tranches.

## Sprint 14.3 — Runtime Strategy + LEAPS Take-Profit

**Status: COMPLETE**

Added the runtime strategy path required for portfolio-aware decisions.

Key work:

- `StrategyContext`.
- `BacktestEngine` support for `on_bar(timestamp, price, context)`.
- Preservation of `generate()` and `generate_orders()` paths.
- Runtime access to cash, option positions, and current option quotes.
- Pandas `.iloc` compatibility fix for legacy signal Series.
- `SpyLeapsLadderStrategy.on_bar()`.
- LEAPS return calculation using current bid versus average cost.
- Configurable take-profit threshold.
- Generation of full-position option SELL orders.
- End-to-end take-profit execution.
- Full option-position cleanup after exit.
- Portfolio-level realized option PnL validation.

Example validated scenario:

- Buy 10 contracts at ask 25.
- Sell 10 contracts at bid 32.
- Proceeds: 32,000.
- Realized option PnL: 7,000.
- Closed contract removed from `option_positions`.

## Important Bugs / Lessons Captured

- Option position field naming must consistently use the current accounting API (`average_cost`).
- Massive provider fake HTTP responses must match the production client's expected response interface.
- Pagination tests should isolate network behavior with fake sessions.
- Test collection should be scoped to the repository (`pytest tests`) on Windows to avoid unrelated system directories.
- Historical quote timestamps and trading-date lookups must be normalized consistently.
- Multiple same-day allocations require a shared pre-trade snapshot.
- Fixed ladder allocations require an explicit capital base.
- Exact percentage thresholds require floating-point tolerance.
- A pandas `Series` with `DatetimeIndex` must use `.iloc` for positional access.
- After a full option exit, tests must not dereference the deleted position; realized PnL belongs to the portfolio ledger.

## Current Architectural Checkpoint

The framework now supports:

`Signal strategies + pre-generated order strategies + dynamic runtime strategies`

with both equity and option execution inside the same portfolio.

## Sprint 14.4 — Capital Recycling & Tranche State Model

Status: COMPLETE

Introduced independent equity and option lifecycle state.

Key work:

- `SpyLeapsTranche` lifecycle model.
- Independent equity and option deployment state.
- Option-leg closure without closing SPY exposure.
- Active equity and option tranche counts.
- Option-capacity recycling after take-profit.
- Repeated take-profit and recycling cycles.

The tranche ledger replaced the earlier assumption that one combined
`tranches_deployed` counter could represent the complete strategy
state.

## Sprint 15 — Dynamic LEAPS Contract Lifecycle

Status: COMPLETE

### 15.1–15.2 — Contract Resolution

Added fixed and dynamic LEAPS contract resolution.

The strategy can preserve legacy fixed-contract behavior or resolve a
contract dynamically from timestamp and underlying price.

### 15.3 — Historical Contract Universe

Added the option contract universe abstraction and Massive-backed
historical contract discovery.

Key work:

- `OptionContractUniverseProvider`
- `StaticOptionContractUniverseProvider`
- `MassiveOptionContractUniverseProvider`
- Massive option-contract reference requests
- pagination
- historical `as_of` queries
- vendor-to-domain contract normalization

### 15.3F — Contract Rotation

Validated that recycled option deployment can resolve to a different
LEAPS contract from the original deployment.

Each tranche stores the actual resolved contract.

### 15.4 — Multi-Contract Take-Profit

Take-profit decisions now use active tranche contracts rather than a
single legacy fixed contract.

Key work:

- active-contract discovery
- contract deduplication
- aggregated-position-aware SELL generation
- contract-specific tranche closure
- multiple simultaneous active LEAPS contracts
- multiple take-profit orders on the same bar

### 15.4C–15.4D — Multi-Order Runtime

Validated that runtime strategies can return multiple actions and that
`BacktestEngine` executes multiple option SELL orders on the same bar.

Portfolio position cleanup, cash accounting, and realized PnL were
validated through integration tests.

### 15.4E — Dynamic Lifecycle End-to-End

Validated the complete lifecycle using the real
`SpyLeapsLadderStrategy` and `BacktestEngine`:

    initial dynamic Contract A
              ↓
         drawdown
              ↓
      dynamic Contract B
              ↓
       A + B active
              ↓
    simultaneous take-profit
              ↓
       two SELL orders
              ↓
       engine execution
              ↓
    option positions closed
              ↓
      SPY exposure remains

Full regression suite GREEN at the Sprint 15 milestone.

## Current Architectural Checkpoint

The framework now supports:

    historical market state
            ↓
    runtime strategy
            ↓
    dynamic option universe
            ↓
    LEAPS contract resolution
            ↓
    multi-contract tranche lifecycle
            ↓
    multiple runtime orders
            ↓
    equity + option execution
            ↓
    unified portfolio accounting

## Next

Sprint 16 — Historical Dynamic LEAPS Validation

The next objective is to connect historical contract discovery and
historical option quotes in progressively more realistic backtests.

Initial target:

    historical timestamp
            ↓
    Massive contract universe
            ↓
    DynamicLeapsContractResolver
            ↓
    selected SPY LEAPS contract
            ↓
    Massive historical quote
            ↓
    executable bid / ask