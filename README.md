# QuantResearch

QuantResearch is a test-driven Python research and backtesting framework for
systematic equity and listed-option strategies.

The current research focus is a stateful SPY + LEAPS ladder strategy using
real historical SPY prices, historical option contract discovery, dynamic
LEAPS selection, daily option aggregate bars, tranche lifecycle accounting,
take-profit exits, option-capital recycling, and multi-contract valuation.

## Current Development Status

**Checkpoint:** 2026-08-25  
**Milestone:** Real Historical Dynamic LEAPS Backtesting

The framework has progressed from a quote-oriented option prototype to a
daily historical research pipeline validated with real Yahoo Finance equity
data and real Massive option reference/aggregate data.

### Current capabilities

- Equity price ingestion and validation
- Legacy signal strategies
- Pre-generated explicit order / intent strategies
- Runtime portfolio-aware strategies through `on_bar(...)`
- Equity and option order intents
- Equity and option execution
- Portfolio and position accounting
- Realized and unrealized option PnL
- Performance and trade analytics
- Historical option quote infrastructure
- Daily historical option bar domain model
- Explicit daily option pricing policies
- Daily execution-price compatibility adapters
- Yahoo Finance historical SPY data
- Massive historical option contract discovery
- Massive historical option daily aggregates
- HTTP pagination
- HTTP 429 retry / backoff
- Same-day option-bar cache
- Automatic option-bar range loading
- Historical contract-universe cache
- Entry-date option tradability filtering
- Dynamic LEAPS contract resolution
- Configurable min / max / target DTE
- Nearest-ATM strike selection
- Multi-contract option positions
- Multiple same-bar runtime actions
- Same-day allocation cash snapshots
- Fixed allocation-base sizing
- Independent equity and option tranche lifecycle
- Take-profit exits
- Option-capacity recycling
- Dynamic contract rotation
- Missing-bar last-mark fallback for valuation

## Strategy Interfaces

`BacktestEngine` supports three strategy styles:

1. `generate(prices)` — legacy signal-based strategies.
2. `generate_orders(prices)` — pre-generated explicit orders or intents.
3. `on_bar(timestamp, price, context)` — runtime strategies using current
   portfolio and option market state.

Runtime strategies may return:

- `None`
- one order / intent
- a list or tuple of multiple actions on the same bar

## SPY + LEAPS Ladder

The current research implementation supports:

- Initial SPY + LEAPS deployment
- Running SPY peak tracking
- Configurable drawdown ladder
- Independent equity and option capacity
- Historical tranche lifecycle ledger
- LEAPS take-profit
- Option-capital recycling
- Dynamic contract selection at each deployment
- Multiple simultaneous LEAPS contracts
- Contract-aware exits
- Option-only recycled deployments when equity capacity is already full

A tranche records:

```text
level
equity_deployed
option_deployed
option_closed
option_contract
```

The tranche ledger represents strategy lifecycle history. It is intentionally
separate from aggregated portfolio positions.

## Daily Historical Option Pipeline

The primary historical research path is now:

```text
historical SPY price
        ↓
DynamicLeapsContractResolver
        ↓
Massive historical contract universe
        ↓
DTE / ATM ranking
        ↓
entry-date tradability filtering
        ↓
selected OptionContract
        ↓
Massive daily option aggregate bars
        ↓
HistoricalOptionBar
        ↓
DailyOptionPricingPolicy
        ↓
DailyOptionExecutionQuoteAdapter
        ↓
BacktestEngine
        ↓
execution / StrategyContext / MTM
        ↓
Portfolio NAV
```

Important semantics:

- A contract existing in a reference universe does **not** imply it traded on
  the intended entry date.
- Daily option bars are **not** historical bid/ask quotes.
- The default daily research proxy currently uses daily close for BUY, SELL,
  and mark-to-market.
- Missing current bars do not create synthetic strategy signals.
- Open-position valuation may use the last known valid mark when a current
  daily bar is missing.
- A new option contract automatically loads the remaining configured
  backtest range into the provider cache.

## Real Historical Validation

The pipeline has been validated with real market data across progressively
larger scenarios:

- One-day real Massive dynamic LEAPS smoke test
- Five-day real historical SPY + LEAPS backtest
- One-month real historical backtest
- Real two-tranche drawdown deployment
- Multi-contract NAV reconciliation
- Real take-profit and option-capacity release
- Real take-profit followed by later drawdown and option redeployment
- Full-year 2025 historical backtest

### 2025 Full-Year Validation Snapshot

Research configuration:

```text
Initial capital:        $100,000
Equity allocation:      25% per active tranche
Option allocation:      25% per active tranche
Max active tranches:    2
LEAPS take-profit:      25%
Dynamic LEAPS DTE:      365–548 days
Target DTE:             456 days
```

Observed integration result:

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

This result is an engineering and research-validation snapshot. It is not a
claim of future performance and should not be interpreted as investment
advice.

## Testing

Offline regression tests:

```powershell
pytest -m "not integration"
```

Live integration tests:

```powershell
pytest -m integration -v -s
```

Focused suites include:

```powershell
pytest tests/test_leaps_contract_resolver.py -v
pytest tests/test_massive_option_bar_provider.py -v
pytest tests/test_spy_leaps_ladder_dynamic_contract.py -v
pytest tests/test_backtest_engine_dynamic_strategy.py -v
pytest tests/test_massive_daily_leaps_smoke.py -m integration -v -s
```

The latest development checkpoint is fully GREEN. The repository now contains
more than 350 regression and integration tests; use the commands above for the
exact local count.

## Development Principles

- TDD first.
- Preserve backward compatibility unless a contract is deliberately changed.
- Keep strategy decisions separate from execution and accounting.
- Keep vendor response structures outside strategy logic.
- Treat daily-bar pricing as an explicit research assumption.
- Never silently fabricate historical market data.
- Contract existence and entry-date tradability are separate concepts.
- Execution price and mark price are separate concepts.
- Tranche lifecycle and portfolio accounting are separate concepts.
- `max_tranches` represents active capacity, not lifetime deployment count.
- Prefer provider-level caching over strategy or engine knowledge of HTTP I/O.
- Run focused tests before the full regression suite.

## Documentation

- `docs/DEVELOPMENT.md` — development model and current component semantics.
- `docs/DEVELOPMENT_PROGRESS.md` — sprint and milestone history.
- `docs/ARCHITECTURE.md` — current system architecture.
- `docs/ROADMAP.md` — planned work and research direction.

## Next Development Direction

The next engineering milestone is **Visualization & Research Diagnostics**.

Planned first outputs include:

- portfolio NAV chart
- SPY benchmark overlay
- drawdown chart
- tranche entry / exit markers
- option contract lifecycle visualization
- active equity / option capacity over time
- realized option PnL timeline
- contract-rotation timeline

After the visualization layer is established, the next strategy research
direction will be defined separately.

## Disclaimer

This repository is for research and educational purposes. It is not
investment advice and is not a production trading system.
