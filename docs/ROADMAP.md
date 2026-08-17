# Roadmap

**Checkpoint:** 2026-08-17

## Sprint 14.4 — Capital Recycling & Tranche State Model

**Status: NEXT**

Goal: define correct state and capital semantics after a LEAPS take-profit while SPY remains invested.

Questions to answer before implementation:

- Should equity and option tranches be tracked independently?
- Does a LEAPS take-profit reopen only option capacity, or a complete SPY + LEAPS tranche?
- Should realized option proceeds be immediately reusable?
- How should a previously crossed drawdown level behave if capital becomes available later?
- Is re-entry tied to a new drawdown event, a new peak cycle, or another option-selection condition?
- Should a tranche ledger replace counters?

Likely first step: introduce tests for the desired state transitions before changing production code.

## Sprint 14.5 — Dynamic LEAPS Selection / Roll

Planned capabilities:

- Select a contract at entry time instead of holding a constructor-fixed contract.
- Target configurable DTE, e.g. 12–18 months.
- ATM / near-ATM strike selection.
- Handle expiration approach.
- Roll an existing LEAPS position when appropriate.
- Define behavior when historical quotes are unavailable.

## Sprint 14.6 — Historical SPY + Massive LEAPS Integration

Goal: run the strategy over real synchronized SPY and historical option data.

Work items:

- Robust trading-date/quote alignment.
- Contract-universe discovery.
- Quote availability diagnostics.
- Caching / rate-limit-aware retrieval.
- Reproducible stored datasets for tests and research runs.
- Clear distinction between provider integration tests and live-data experiments.

## Sprint 14.7 — Strategy Analytics & Benchmarking

Add research outputs tailored to the hybrid strategy:

- SPY benchmark comparison.
- Buy-and-hold comparison.
- Exposure over time.
- Equity versus option contribution.
- Realized versus unrealized PnL.
- Drawdown by portfolio and component.
- Tranche entry/exit log.
- Option win rate and holding period.
- Capital utilization.

## Sprint 15 — Research Experiments

Once execution semantics are stable:

- Parameter sweeps for drawdown step.
- Take-profit threshold experiments (e.g. 20%, 25%, 30%).
- Equity/option allocation combinations.
- DTE and strike-selection sensitivity.
- Maximum tranche sensitivity.
- Slippage and spread stress tests.
- Walk-forward / out-of-sample evaluation.
- Regime analysis.

## Later Engineering

Potential later work, after research behavior is stable:

- Commission model for options.
- More realistic liquidity / fill assumptions.
- Corporate actions and dividends.
- Multiple underlyings.
- Portfolio-level risk constraints.
- Persistent trade/event ledger.
- Experiment configuration objects.
- Result serialization.
- CI workflow.
- Packaging and public API cleanup.

## Non-Goals for the Current Phase

The project is not yet intended to be:

- a live trading system
- a broker integration
- a low-latency execution engine
- an investment recommendation system

The current priority is correctness, reproducibility, test coverage, and research usefulness.
