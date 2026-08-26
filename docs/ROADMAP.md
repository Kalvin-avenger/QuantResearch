# Roadmap

**Checkpoint:** 2026-08-25

## Current Milestone

### Sprint 18 — Real Historical Dynamic LEAPS Validation

**Status: COMPLETE**

QuantResearch now supports and has live-tested:

- real Yahoo SPY history
- real Massive historical option universes
- daily historical option aggregate bars
- explicit daily option pricing
- automatic option range loading
- provider caching
- 429 retry / backoff
- dynamic DTE / ATM LEAPS selection
- entry-date tradability filtering
- multiple active option contracts
- independent equity / option tranche capacity
- take-profit
- option-capacity recycling
- contract rotation
- full-year historical execution

Full-year 2025 validation snapshot:

```text
Initial NAV:            $100,000.00
Ending NAV:             $143,226.34
Total return:           +43.23%
Maximum drawdown:       -21.68%
Realized option PnL:    $29,304.00
```

This is a historical research result, not a forecast or investment claim.

## Completed Development Sequence

### Sprints 1–13 — Core Backtesting Foundation

Completed:

- equity data
- strategy interfaces
- signals
- orders
- execution
- portfolio accounting
- performance analytics
- trade analytics
- option domain
- option execution
- historical option infrastructure

### Sprint 14 — Stateful SPY + LEAPS Ladder

Completed:

- initial combined allocation
- drawdown ladder
- runtime strategy context
- take-profit
- independent equity / option tranche state
- option-capacity recycling

### Sprint 15 — Dynamic LEAPS Lifecycle

Completed:

- dynamic contract resolver
- historical universe provider
- DTE / ATM selection
- contract rotation
- multi-contract state
- multiple same-bar option exits

### Sprint 16 — Daily Historical Option Pipeline

Completed:

- `HistoricalOptionBar`
- Massive daily aggregates
- daily pricing policy
- execution compatibility adapter
- BacktestEngine daily path
- mark-price separation
- missing-bar semantics
- provider cache
- range preload
- automatic range loading
- contract-universe cache
- 429 resilience

### Sprint 17 — Real TP & Recycling Validation

Completed:

- real TP event discovery
- real TP execution
- option capacity release
- later drawdown discovery
- option redeployment
- option-only lifecycle tranche
- real contract rotation

### Sprint 18 — Tradability & Long-Horizon Validation

Completed:

- entry-date `has_bar(...)`
- tradability-aware dynamic resolver
- no-look-ahead entry semantics
- full-year 2025 backtest
- long-horizon lifecycle / accounting validation

# Sprint 19 — Visualization & Research Diagnostics

**Status: NEXT**

Goal: make the strategy visually explainable before changing strategy logic.

## 19.1 — Core Backtest Visualization

Build reusable plotting functions for:

- portfolio NAV
- SPY price
- normalized SPY benchmark
- strategy vs SPY cumulative return
- portfolio drawdown

Target inputs should be stable research objects such as:

```text
BacktestResult
price Series
timestamps
```

Avoid embedding plotting logic inside `BacktestEngine`.

## 19.2 — Strategy Event Visualization

Visualize lifecycle events:

- initial tranche deployment
- drawdown-triggered deployments
- equity-only deployment
- option-only recycled deployment
- option take-profit
- contract close
- contract rotation

Potential representation:

```text
SPY price chart
    + vertical event markers
    + lifecycle labels
```

## 19.3 — Option Lifecycle Visualization

Add views for:

- contract entry / exit dates
- entry strike
- underlying price at entry
- DTE at entry
- option holding period
- realized PnL
- open / closed status
- contract rotation timeline

## 19.4 — Capacity Visualization

Plot:

```text
active equity tranches over time
active option tranches over time
cash utilization
equity exposure
option notional / market value
```

This should make the independent-capacity design observable.

## 19.5 — Performance Dashboard

Combine research diagnostics into a compact summary:

- total return
- CAGR
- annualized volatility
- Sharpe ratio
- maximum drawdown
- realized option PnL
- SPY benchmark return
- lifecycle event count
- take-profit count
- contract rotation count
- capital utilization

The first implementation can remain matplotlib / Python based. A web UI is
not required for this milestone.

# Sprint 20 — Strategy Research Definition

**Status: PLANNED**

After visualization is usable, define the next strategy hypothesis.

The next strategy should be discussed and specified before implementation.

Before coding, document:

```text
economic / behavioral hypothesis
entry logic
exit logic
capital allocation
risk constraints
required market data
benchmark
success criteria
failure criteria
```

Do not combine several new ideas into one first experiment.

# Sprint 21 — Performance & Benchmark Analytics

**Status: PLANNED**

Integrate existing analytics directly with real historical dynamic LEAPS
results.

Targets:

- total return
- CAGR
- volatility
- Sharpe
- maximum drawdown
- SPY benchmark comparison
- excess return
- component attribution
- realized vs unrealized option PnL
- capital utilization

Visualization and analytics should share common result structures rather than
duplicate metric calculations.

# Sprint 22 — Research Experiment Framework

**Status: PLANNED**

Once visualization and analytics are stable, support structured parameter
experiments.

Potential experiments:

- drawdown step
- take-profit threshold
- equity / option allocation mix
- min / max / target DTE
- ATM vs near-ATM
- max active tranches
- slippage assumptions
- transaction-cost assumptions

Research methodology:

- explicit hypothesis first
- fixed benchmark
- in-sample / out-of-sample separation
- avoid selecting a strategy only from the best historical result
- record all tested parameter combinations

# Sprint 23 — Robustness & Realism

**Status: LATER**

Potential additions:

- option commissions
- option slippage / spread stress
- liquidity thresholds
- minimum volume / open-interest filters
- expiration-management rules
- explicit roll logic
- dividend / corporate-action handling
- alternative daily execution policies
- sensitivity to missing option bars

# Later Strategy Extensions

Potential ideas to evaluate individually:

- delta-based contract selection
- liquidity-aware contract selection
- volatility-aware option allocation
- dynamic take-profit thresholds
- risk-budget-based tranche sizing
- volatility-regime-dependent drawdown levels
- defensive option overlays
- alternative underlying / LEAPS combinations

These should be introduced one hypothesis at a time.

# Later Engineering

Potential work:

- persistent historical dataset cache
- serialized backtest results
- experiment configuration objects
- event ledger
- reproducible research run manifests
- CI
- packaging / public API cleanup
- multiple underlyings
- portfolio-level risk constraints

# Non-Goals

QuantResearch is not currently intended to be:

- a live trading system
- a broker integration
- a low-latency engine
- an investment recommendation system

Current priorities remain:

- correctness
- reproducibility
- explicit historical-data semantics
- explainability
- test coverage
- research usefulness
