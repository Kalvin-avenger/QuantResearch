# Roadmap

**Checkpoint:** 2026-08-24

## Current Milestone

### Sprint 15 — Dynamic LEAPS Contract Lifecycle

**Status: COMPLETE**

Sprint 15 completed the transition from a fixed-contract SPY + LEAPS
ladder to a dynamic, tranche-aware, multi-contract lifecycle.

Completed capabilities include:

- independent equity and option tranche state;
- option capital recycling after take-profit;
- tranche lifecycle bookkeeping;
- fixed and dynamic LEAPS contract resolvers;
- historical option contract universe abstraction;
- static and Massive-backed contract universe providers;
- historical `as_of` contract discovery;
- configurable minimum, maximum, and target DTE;
- CALL filtering and nearest-ATM strike selection;
- contract rotation across recycling cycles;
- tranche-level resolved contract tracking;
- simultaneous active LEAPS contracts;
- contract-aware take-profit;
- same-contract exit deduplication;
- multiple runtime actions on the same bar;
- engine execution of multiple option SELL orders;
- end-to-end dynamic multi-contract lifecycle validation.

The major strategy-state questions originally planned for Sprint 14.4
and the dynamic-selection work originally planned for Sprint 14.5 have
therefore been resolved.

## Sprint 16 — Historical Dynamic LEAPS Validation

The next phase moves from architecture and lifecycle correctness toward
validation with real historical option universes and quotes.

The development sequence should remain incremental. A small historical
data smoke test should pass before attempting long backtests.

### Sprint 16.1 — Historical Data Smoke Test

**Status: NEXT**

Goal: connect historical contract discovery and historical quote
retrieval for one real historical SPY date.

Target pipeline:

```text
historical timestamp
        ↓
historical SPY price
        ↓
MassiveOptionContractUniverseProvider
        ↓
historical option universe
        ↓
DynamicLeapsContractResolver
        ↓
selected SPY LEAPS contract
        ↓
MassiveHistoricalOptionDataProvider
        ↓
historical bid / ask quote
        ↓
executable option market data
```

Success criteria:

- historical SPY price is available for the selected date;
- Massive returns a historical SPY option contract universe;
- the resolver selects an eligible CALL contract;
- selected DTE satisfies the configured LEAPS range;
- strike selection is consistent with the current SPY price;
- the selected internal `OptionContract` maps correctly to a Massive
  option ticker;
- historical quote retrieval succeeds for the selected contract;
- usable bid and ask values are available;
- timestamps are aligned without introducing look-ahead data;
- failures caused by unavailable vendor data are explicit rather than
  silently replaced with synthetic data.

The first implementation should be a focused smoke test or research
script rather than a long-running backtest.

### Sprint 16.2 — Short-Window Dynamic Backtest

Goal: run the real `SpyLeapsLadderStrategy` through a small historical
window using dynamic contract selection and historical option quotes.

Initial target window:

- several trading days to several weeks.

Validation targets:

- initial dynamic LEAPS deployment;
- historical quote retrieval for open option positions;
- SPY and option timestamp alignment;
- end-of-day option mark-to-market;
- portfolio NAV consistency;
- tranche lifecycle consistency;
- explicit handling of missing option quotes;
- reproducible results for the same stored inputs.

A short window should be used to expose integration problems before
adding caching, optimization, or long-horizon research complexity.

### Sprint 16.3 — Historical Data Robustness

Goal: make historical option retrieval reliable enough for repeated
research runs.

Work items may include:

- trading-date and quote alignment;
- quote availability diagnostics;
- contract-universe availability diagnostics;
- pagination validation;
- rate-limit-aware retrieval;
- request retry policy;
- deterministic caching;
- reproducible stored historical datasets;
- clear separation between provider integration tests and live-data
  experiments.

Missing-data behavior should remain explicit.

Strategy decisions should not silently use synthetic or forward-filled
current option quotes.

### Sprint 16.4 — Multi-Month Dynamic Backtest

Goal: extend the validated short-window pipeline to several months.

Focus areas:

- repeated contract resolution;
- multiple drawdown deployments;
- contract rotation;
- take-profit and capital recycling;
- simultaneous active contracts;
- option quote coverage through time;
- expiration transitions;
- missing-contract behavior;
- portfolio accounting over repeated option lifecycles.

Diagnostics should record enough information to explain every dynamic
contract selection and exit.

### Sprint 16.5 — Multi-Year Backtest

Goal: run the complete SPY + dynamic LEAPS strategy over a multi-year
historical period after data reliability has been established.

Core performance outputs:

- total return;
- CAGR;
- annualized volatility;
- Sharpe ratio;
- maximum drawdown;
- realized option PnL;
- unrealized option PnL;
- SPY contribution;
- option contribution;
- capital utilization.

Strategy-specific diagnostics:

- number of tranche deployments;
- number of option-only recycled deployments;
- number of LEAPS contract rotations;
- take-profit frequency;
- average option holding period;
- option win rate;
- average DTE at entry;
- average strike distance from spot at entry.

## Sprint 17 — Strategy Analytics and Benchmarking

After the historical dynamic pipeline is reliable, add research outputs
tailored to the hybrid SPY + LEAPS strategy.

Planned work:

- SPY benchmark comparison;
- buy-and-hold comparison;
- exposure over time;
- equity versus option contribution;
- realized versus unrealized PnL;
- portfolio and component drawdowns;
- tranche entry and exit history;
- option holding-period analysis;
- option win/loss distribution;
- capital utilization;
- dynamic contract-selection diagnostics.

The objective is to make strategy behavior explainable rather than
reporting only final performance statistics.

## Sprint 18 — Research Experiments

Once execution semantics and historical data quality are stable,
evaluate strategy sensitivity.

Potential experiments:

- drawdown-step sweeps;
- take-profit thresholds such as 20%, 25%, and 30%;
- equity/option allocation combinations;
- minimum, maximum, and target DTE sensitivity;
- ATM versus near-ATM strike-selection rules;
- maximum tranche sensitivity;
- option slippage and spread stress tests;
- transaction-cost sensitivity;
- walk-forward evaluation;
- out-of-sample evaluation;
- market-regime analysis.

Parameter research should follow, not precede, historical data and
execution validation.

## Later Strategy Extensions

Potential strategy work after the baseline dynamic LEAPS research
pipeline is validated:

- delta-based contract selection;
- liquidity-aware contract selection;
- open-interest and volume filters;
- volatility-aware option allocation;
- dynamic take-profit thresholds;
- expiration-management rules;
- explicit LEAPS roll logic;
- risk-budget-based tranche sizing;
- volatility-regime-dependent drawdown levels.

These extensions should be introduced individually with tests rather
than bundled into the baseline strategy.

## Later Engineering

Potential engineering work after research behavior is stable:

- option commission model;
- more realistic liquidity and fill assumptions;
- configurable option slippage models;
- corporate actions and dividends;
- multiple underlyings;
- portfolio-level risk constraints;
- persistent trade and event ledger;
- experiment configuration objects;
- result serialization;
- historical dataset management;
- CI workflow;
- packaging and public API cleanup.

## Non-Goals for the Current Phase

The project is not currently intended to be:

- a live trading system;
- a broker integration;
- a low-latency execution engine;
- an investment recommendation system.

The current priority remains:

- correctness;
- reproducibility;
- test coverage;
- explicit historical-data semantics;
- explainable strategy behavior;
- research usefulness.
