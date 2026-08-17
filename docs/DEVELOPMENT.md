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

The current strategy is a runtime stateful strategy.

Implemented state includes:

- `peak_price`
- `last_triggered_level`
- `tranches_deployed`
- `initial_capital`
- configurable drawdown step
- configurable maximum tranches
- configurable LEAPS take-profit threshold

Drawdown thresholds include a small floating-point tolerance so exact boundaries such as -10% are not accidentally classified as -9.999...%.

## Known Design Boundary

`tranches_deployed` currently describes combined SPY + LEAPS deployment. Once LEAPS are independently sold for profit while SPY remains open, this single counter is no longer expressive enough.

Sprint 14.4 should therefore design capital recycling before adding more behavior. Likely candidates include separate equity and option tranche state, explicit available strategy capital, or a tranche ledger.

## Backward Compatibility Notes

The dynamic engine work preserved old strategy behavior. One compatibility issue discovered during the migration was pandas positional indexing: a signal `Series` with a `DatetimeIndex` must be accessed with `.iloc[index]`, not `series[index]`.

This is now covered by the full regression suite.
