# Development Progress

**Latest checkpoint:** 2026-08-25  
**Status:** GREEN  
**Current milestone:** Real Historical Dynamic LEAPS Backtesting Complete

The repository now contains more than 350 regression and live integration
tests. Use `pytest -m "not integration"` and `pytest -m integration -v -s`
for exact local counts.

## Foundation — Complete

### Equity backtesting

- Historical price ingestion
- Signal-based strategies
- Moving-average strategy
- Equity orders and execution
- Position and portfolio accounting
- Trade log
- Performance metrics
- Trade analytics
- Slippage infrastructure

### Options domain

- `OptionContract`
- Option types
- Historical option quotes
- Historical quote store
- Historical daily option bars
- Option position accounting
- Weighted-average cost
- Unrealized / realized PnL
- Partial and full exits
- Option order / intent / resolver / builder / executor
- Yahoo option-chain normalization
- Massive option reference / historical data integration

## Sprint 13 — Option Order & Execution

**Status: COMPLETE**

Established:

```text
OptionOrder / OptionOrderIntent
        ↓
resolver / builder
        ↓
OptionExecutor
        ↓
Portfolio / OptionPosition
```

Validated multiplier-aware cash accounting, weighted-average cost, realized
PnL, full exits, and position cleanup.

## Sprint 14 — SPY + LEAPS Ladder State Model

**Status: COMPLETE**

### 14.1 — Initial SPY + LEAPS allocation

Completed:

- `EquityOrderIntent`
- multiple same-bar actions
- same-day cash snapshot
- fixed `allocation_base`
- combined equity / option NAV validation

### 14.2 — Drawdown ladder

Completed:

- running SPY peak
- drawdown calculation
- configurable step
- drawdown levels
- exact-threshold tolerance
- one-time level triggers
- configurable active capacity

### 14.3 — Runtime strategy and take-profit

Completed:

- `StrategyContext`
- `BacktestEngine.on_bar(...)` runtime path
- quote-aware LEAPS take-profit
- full-position option exits
- realized PnL validation

### 14.4 — Independent tranche lifecycle

Completed:

- independent equity and option leg state
- `SpyLeapsTranche`
- separate active equity / option capacities
- option-capacity recycling
- lifecycle ledger
- removal of the old combined deployment counter as the primary state source

Important semantic:

```text
lifecycle ledger count != active capacity
```

## Sprint 15 — Dynamic LEAPS Contract Lifecycle

**Status: COMPLETE**

Completed:

- `LeapsContractResolver`
- fixed resolver
- dynamic resolver
- `OptionContractUniverseProvider`
- static provider
- Massive-backed provider
- historical `as_of` contract discovery
- min / max / target DTE
- nearest-ATM ranking
- resolved contract stored in tranche state
- contract rotation
- simultaneous active option contracts
- contract-aware take-profit
- same-contract exit deduplication
- multiple option SELL orders on the same bar
- engine-level multiple runtime actions

## Sprint 16 — Daily Historical Option Integration

**Status: COMPLETE**

The research direction changed from historical intraday quote dependency to
daily option aggregate bars after live quote retrieval exposed vendor
entitlement constraints.

### 16.1 — Daily option domain and pricing

Completed:

- `HistoricalOptionBar`
- Massive option-bar normalization
- `MassiveHistoricalOptionBarProvider`
- `DailyOptionPricing`
- `DailyCloseOptionPricingPolicy`
- `DailyOptionExecutionQuoteAdapter`

Explicit research assumption:

```text
BUY  = daily close
SELL = daily close
MARK = daily close
```

No daily close is labeled as a real historical bid or ask.

### 16.2 — BacktestEngine daily market-data path

Completed:

- unified option market-state resolver
- daily bars in StrategyContext
- daily bars in option execution
- explicit `mark_price`
- daily bars in EOD option MTM
- top-level `BacktestEngine.run(...)` integration
- last-known option mark fallback
- missing-current-bar semantics

### 16.3 — Massive reliability and caching

Completed:

- aggregate endpoint routed through 429 retry / backoff
- same-day contract cache
- explicit `preload(...)`
- automatic range loading
- `set_backtest_range(...)`
- range-cache correctness
- contract-universe query cache
- integration-test marker

### 16.4 — Real short-window validation

Validated:

- one-day real Massive dynamic LEAPS execution
- five-day continuous historical backtest
- one-month real historical backtest
- automatic contract-range loading without test-side preselection
- real two-tranche drawdown deployment
- simultaneous distinct LEAPS positions
- multi-contract NAV reconciliation

Example two-tranche real window:

```text
Tranche 1: SPY 2026-06-18 610C
Tranche 2: SPY 2026-06-18 575C
```

Both option positions were valued simultaneously and final NAV reconciled
exactly to:

```text
cash + SPY market value + all option market values
```

## Sprint 17 — Real Take-Profit & Recycling Validation

**Status: COMPLETE**

### 17.1 — Real TP discovery

A dynamically selected:

```text
SPY 2026-06-18 560C
```

entered on 2025-04-01 at a daily close of 56.25 and first exceeded the 25%
take-profit threshold on 2025-05-13 at 72.94.

Observed option return:

```text
+29.67%
```

### 17.2 — Real TP and capacity release

Validated:

- real option SELL
- `option_closed=True`
- `option_deployed=False`
- equity leg remains active
- active option capacity released
- realized PnL persisted at portfolio level

Observed realized option PnL in the focused scenario:

```text
$6,676
```

### 17.3 — Real later drawdown and redeployment

A post-TP drawdown discovery identified:

```text
SPY peak date:                 2025-10-29
SPY peak:                      687.39
first subsequent 5% drawdown: 2025-11-20
SPY price:                     652.53
drawdown:                      -5.07%
```

The longer live test validated:

- TP of prior option positions
- released option capacity
- later drawdown-triggered option redeployment
- option-only lifecycle tranche when equity capacity was already full
- contract rotation
- automatic new-contract range loading

Observed lifecycle example:

```text
Tranche 1:
level 0
SPY 2026-06-18 560C
equity open
option closed

Tranche 2:
level 2
SPY 2026-06-18 505C
equity open
option closed

Tranche 3:
level 1
SPY 2027-03-19 655C
equity not deployed
option open
```

This established an important invariant:

```text
tranches are ordered by lifecycle creation,
not by drawdown level
```

## Sprint 18 — Historical Tradability & Full-Year Validation

**Status: COMPLETE**

### 18.1 — Entry-date tradability

A full-year backtest exposed a historically valid contract with no option bar
on the intended entry date.

Diagnostic example:

```text
SPY 2026-03-20 585C

2025-01-02:
no daily aggregate bar

first available bar:
2025-01-03
close = 58.82
volume = 2
```

This proved:

```text
contract exists
    !=
contract tradable on entry date
```

Completed:

- `MassiveHistoricalOptionBarProvider.has_bar(...)`
- resolver `tradability_provider`
- candidate checking in existing DTE / ATM ranking order
- skip unavailable entry-date contracts
- preserve legacy behavior when no tradability provider is supplied
- no look-ahead substitution with future bars

### 18.2 — Full-year 2025 historical backtest

Validated a full calendar-year dynamic SPY + LEAPS backtest using:

- real Yahoo SPY data
- real Massive historical contract universes
- real Massive daily option aggregate bars
- tradability-aware dynamic resolver
- automatic contract range loading
- take-profit
- option recycling
- multi-tranche lifecycle
- contract rotation
- continuous NAV

Observed result:

```text
Initial NAV:            $100,000.00
Ending NAV:             $143,226.34
Total return:           +43.23%
Maximum drawdown:       -21.68%
Minimum NAV:            $86,120.94
Maximum NAV:            $143,945.44
Ending cash:            $58,494.14
Realized option PnL:    $29,304.00
```

This is a research-validation result, not a future-performance claim.

## Important Engineering Lessons

- Daily bars are not quotes.
- Contract existence is not tradability.
- Entry executions must not use future bars.
- Missing current strategy data should not create synthetic signals.
- MTM may use a prior valid mark.
- `get_bar()` and `get_bars()` serve different responsibilities.
- Range fetches must return the requested date from cache, not `bars[0]`.
- API retry is a reliability mechanism; range loading is the performance
  architecture.
- Provider-level caches should hide HTTP concerns from strategies and engine.
- Active equity and option capacities are independent.
- Lifecycle ledger order is not drawdown-level order.
- Same-contract strategy tranches may aggregate into one portfolio option
  position.
- Different contracts must be valued independently.
- Offline regression and live integration tests should be run separately.

## Current Checkpoint

The historical daily-option architecture is mature enough to support
explainable research.

The next milestone is visualization and diagnostics rather than another
market-data architecture change.

## Next

**Sprint 19 — Visualization & Research Diagnostics**

Initial targets:

- NAV visualization
- SPY benchmark overlay
- portfolio drawdown chart
- tranche deployment markers
- option TP / exit markers
- option contract rotation timeline
- active equity / option capacity over time
- realized option PnL timeline
- portfolio component attribution

After the visualization milestone, the next strategy research direction will
be defined separately.
