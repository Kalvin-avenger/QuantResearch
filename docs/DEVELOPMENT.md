# Development Guide

**Checkpoint:** 2026-08-17

## Purpose

QuantResearch is being developed as a modular, test-driven research framework for equity and listed-option strategies. The current architecture separates strategy decisions, order intent resolution, execution, portfolio accounting, historical data access, and analytics.

## Core Development Contract

A feature should normally progress through:

1. Define the desired behavioral contract.
2. Add or update a focused unit/integration test.
3. Confirm the expected red failure.
4. Implement the smallest production change.
5. Run the focused test.
6. Run the full test suite.
7. Update documentation when behavior or architecture changes.

At this checkpoint the full suite is **257 passed, 0 failed**.

## Major Components

### Backtest Engine

`BacktestEngine` orchestrates the bar-by-bar simulation and supports three strategy contracts:

- `generate(prices)` for legacy signal strategies.
- `generate_orders(prices)` for pre-generated explicit orders/intents.
- `on_bar(timestamp, price, context)` for dynamic runtime strategies.

The engine owns execution orchestration, same-day allocation snapshots, option mark-to-market, and equity-curve construction. It should not contain strategy-specific rules.

### Strategy Context

`StrategyContext` exposes a deliberately small runtime view to dynamic strategies:

- current cash
- current option positions
- current option quotes

This permits state-aware strategies without passing the entire engine into the strategy.

### Intent Layer

Equity and option intents describe desired allocations without performing execution themselves.

`allocation_base` allows a strategy to specify a fixed capital base. If it is absent, the resolver/builder uses the cash supplied by the engine.

This distinction is essential for ladder strategies: repeated 25% tranches can be sized from initial capital rather than shrinking automatically with remaining cash.

### Execution Layer

Equity orders flow through `Executor`.

Option orders flow through `OptionInstructionResolver` / `OptionOrderBuilder` and then `OptionExecutor`.

Current option execution convention:

- BUY: executable ask
- SELL: executable bid

### Portfolio Accounting

The portfolio maintains equity and option positions, cash, and realized PnL.

A fully exited option position is removed from `option_positions`. Realized PnL therefore must remain at the portfolio/accounting level and must not depend on retaining a zero-quantity `OptionPosition`.

### Option Valuation

Open option positions are marked using the current bid. If a quote is unavailable for valuation but a previous valid mark exists, the engine can use the last known option price. Runtime strategy context does not fabricate a missing quote; a strategy simply cannot make a quote-dependent decision on that bar.

## SPY + LEAPS Ladder

`SpyLeapsLadderStrategy` is a stateful runtime strategy built on
`on_bar(timestamp, price, context)`.

The strategy separates equity and option lifecycle state through
`SpyLeapsTranche`.

Each tranche records:

- drawdown level
- equity deployment state
- option deployment state
- option closed state
- the actual `OptionContract` associated with the option leg

This allows SPY exposure to remain deployed after a LEAPS position is
closed.

### Dynamic LEAPS Resolution

Option deployment is no longer restricted to a single fixed contract.

The strategy supports a `LeapsContractResolver`.

A fixed resolver preserves the legacy fixed-contract behavior.

A dynamic resolver obtains the historical option universe for the
current timestamp and selects a contract according to the configured
LEAPS policy.

Current selection criteria include:

- CALL contracts
- minimum DTE
- maximum DTE
- target DTE
- nearest strike to the current underlying price

Contract universes are supplied through
`OptionContractUniverseProvider`.

Implementations currently include:

- `StaticOptionContractUniverseProvider`
- `MassiveOptionContractUniverseProvider`

### Capital Recycling

Equity and option capacity are tracked independently.

Closing a LEAPS position does not close the associated SPY exposure.
Released option capacity may therefore be redeployed on a later
drawdown trigger.

A recycled option deployment may resolve to a different LEAPS
contract.

### Multi-Contract Take-Profit

The tranche ledger is the strategy-level source of truth for active
option contracts.

Multiple tranches may reference the same contract, while the portfolio
aggregates those holdings into one `OptionPosition`.

Therefore:

- active contracts are deduplicated before exit decisions;
- one aggregated position generates one SELL order;
- different active contracts may independently generate SELL orders;
- multiple option SELL orders may be returned on the same bar.

`BacktestEngine` normalizes single and multiple runtime actions and
executes them independently.

### Current Lifecycle

    initial deployment
          ↓
    SPY + Contract A
          ↓
      drawdown
          ↓
    SPY + Contract B
          ↓
    A and B active
          ↓
    take-profit evaluation
          ↓
    SELL A / SELL B
          ↓
    option positions close
          ↓
    SPY legs remain deployed
          ↓
    option capacity can recycle

## Current Design Boundary

The dynamic contract lifecycle is operational and covered by
end-to-end tests.

The next development boundary is no longer tranche-state modeling.
The next problem is validating the architecture against real
historical contract universes and quotes over progressively longer
backtest windows.

## Backward Compatibility Notes

The dynamic engine work preserved old strategy behavior. One compatibility issue discovered during the migration was pandas positional indexing: a signal `Series` with a `DatetimeIndex` must be accessed with `.iloc[index]`, not `series[index]`.

This is now covered by the full regression suite.
