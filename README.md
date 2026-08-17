# QuantResearch

QuantResearch is a test-driven Python backtesting framework for systematic equity and options strategy research.

## Current Development Status

**Checkpoint:** 2026-08-17  
**Current phase:** Sprint 14.3 complete  
**Test status:** 257 tests passed, 0 failed at this checkpoint.

### Current capabilities

- Equity price data loading and validation
- Moving-average and explicit-order strategy interfaces
- Dynamic runtime strategies via `on_bar(timestamp, price, context)`
- Equity order intents and position sizing
- Order/execution modeling with slippage support
- Portfolio and position accounting
- Performance and trade analytics
- Option contract modeling and option quote storage
- Yahoo option-chain ingestion and normalization
- Massive historical option-data provider integration
- Option order intents, builders, resolvers, and execution
- Option position accounting:
  - weighted-average cost
  - unrealized PnL
  - realized PnL
  - partial exits
  - full exits and position cleanup
- Option mark-to-market using bid prices with last-known-price fallback
- Multiple instructions on the same trading day
- Same-day allocation cash snapshots
- Fixed `allocation_base` sizing for strategy tranches
- SPY + LEAPS ladder strategy:
  - initial SPY + LEAPS allocation
  - peak tracking
  - configurable drawdown steps
  - one-time drawdown-level triggers
  - maximum tranche control
  - runtime `StrategyContext`
  - LEAPS take-profit based on current bid versus average cost
  - end-to-end take-profit execution and realized PnL

## Strategy Interfaces

The engine currently supports three strategy styles:

1. `generate(prices)` — legacy signal-based strategies.
2. `generate_orders(prices)` — pre-generated explicit orders/intents.
3. `on_bar(timestamp, price, context)` — runtime strategies that require current portfolio state or option quotes.

The runtime path is used by `SpyLeapsLadderStrategy`.

## SPY + LEAPS Strategy Status

The current research implementation supports:

- Initial tranche: configurable SPY allocation + LEAPS allocation.
- Fixed tranche sizing against `initial_capital` / `allocation_base`.
- Drawdown levels measured from the running SPY peak.
- Configurable drawdown interval (default research setting: 5%).
- Maximum number of deployed tranches.
- LEAPS take-profit threshold (default research setting: 25%).
- Option exits at the executable bid.
- Realized option PnL retained at the portfolio level after a fully closed option position is removed.

The next design problem is **capital recycling and independent equity/option tranche state** after a LEAPS take-profit.

## Documentation

- [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md) — development model and component overview.
- [`docs/DEVELOPMENT_PROGRESS.md`](docs/DEVELOPMENT_PROGRESS.md) — sprint/checkpoint history.
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — current architecture and Mermaid flow diagrams.
- [`docs/ROADMAP.md`](docs/ROADMAP.md) — planned work from Sprint 14.4 onward.

## Testing

Run the complete suite:

```bash
pytest tests
```

Useful focused suites:

```bash
pytest tests/test_spy_leaps_ladder.py -v
pytest tests/test_spy_leaps_ladder_backtest.py -v
pytest tests/test_backtest_engine_dynamic_strategy.py -v
pytest tests/test_option_instruction_resolver.py -v
```

## Development Principles

- TDD first: reproduce behavior with a failing test before changing production logic.
- Preserve backward compatibility unless a deliberate contract change is documented.
- Keep strategy decisions separate from execution/accounting.
- Use executable option prices: ask for buys, bid for sells/valuation where applicable.
- Avoid hidden leverage; capital constraints should be explicit.
- Keep historical realized PnL at the portfolio/accounting layer even when zero-quantity positions are removed.

## Disclaimer

This repository is for research and educational purposes. It is not investment advice and is not a production trading system.
