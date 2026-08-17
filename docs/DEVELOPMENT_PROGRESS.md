# Development Progress

**Latest checkpoint:** 2026-08-17  
**Regression status:** 257 passed, 0 failed

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

## Next

**Sprint 14.4 — Capital Recycling & Tranche State Model**

Primary question:

How should the strategy represent state after LEAPS are sold for profit while the associated SPY tranche remains open?

Do not solve this by simply decrementing the existing combined `tranches_deployed` counter.
