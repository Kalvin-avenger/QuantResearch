# QuantResearch

QuantResearch is a test-driven Python backtesting framework for
systematic equity and listed-option strategy research.

## Current Development Status

The framework supports equity and option backtesting, runtime
portfolio-aware strategies, historical option data, and dynamic
multi-contract LEAPS lifecycle management.

### Current capabilities

- Equity price data loading and validation
- Signal, explicit-order, and runtime strategy interfaces
- Equity and option order intents
- Slippage-aware execution
- Portfolio and position accounting
- Performance and trade analytics
- Historical option quote storage
- Yahoo option-chain ingestion and normalization
- Massive historical option-data integration
- Option contract universe discovery
- Dynamic LEAPS contract resolution
- DTE and nearest-ATM contract selection
- Option position accounting:
  - weighted-average cost
  - unrealized PnL
  - realized PnL
  - partial exits
  - full exits and position cleanup
- Multiple instructions and orders on the same trading day
- Same-day allocation cash snapshots
- Fixed allocation-base sizing

## Strategy Interfaces

The engine supports three strategy styles:

1. `generate(prices)` — legacy signal-based strategies.
2. `generate_orders(prices)` — pre-generated explicit orders/intents.
3. `on_bar(timestamp, price, context)` — runtime strategies that
   require current portfolio state or option quotes.

Runtime strategies may return no action, a single action, or multiple
actions on the same bar.

## SPY + LEAPS Ladder

The current research implementation supports:

- Initial SPY + LEAPS deployment
- Running SPY peak tracking
- Configurable drawdown ladder
- Independent equity and option tranche state
- LEAPS take-profit
- Option capital recycling
- Tranche lifecycle bookkeeping
- Historical dynamic LEAPS contract selection
- Configurable DTE targeting
- Nearest-ATM strike selection
- Massive-backed historical contract universes
- Contract rotation across recycling cycles
- Multiple simultaneous LEAPS contracts
- Contract-aware take-profit
- Same-bar multi-contract option exits

Dynamic option deployment follows:

    timestamp + SPY price
            ↓
    historical option universe
            ↓
    DTE filtering
            ↓
    target expiration
            ↓
    nearest ATM strike
            ↓
    OptionContract
            ↓
    tranche lifecycle

The current dynamic lifecycle has been validated end-to-end through
`SpyLeapsLadderStrategy`, `BacktestEngine`, option execution, portfolio
accounting, and multi-contract take-profit.

## Documentation

- `docs/DEVELOPMENT.md` — development model and component overview.
- `docs/DEVELOPMENT_PROGRESS.md` — sprint/checkpoint history.
- `docs/ARCHITECTURE.md` — current architecture and Mermaid diagrams.
- `docs/ROADMAP.md` — planned development work.

## Testing

Run the complete suite:

    pytest tests

Useful focused suites:

    pytest tests/test_spy_leaps_ladder.py -v
    pytest tests/test_spy_leaps_ladder_dynamic_contract.py -v
    pytest tests/test_spy_leaps_ladder_backtest.py -v
    pytest tests/test_backtest_engine_dynamic_strategy.py -v
    pytest tests/test_massive_option_contracts.py -v

## Development Principles

- TDD first.
- Preserve backward compatibility unless deliberately changing a contract.
- Keep strategy decisions separate from execution and accounting.
- Use executable option prices: ask for buys and bid for sells.
- Avoid hidden leverage.
- Keep realized PnL in the portfolio/accounting layer.
- Treat tranche lifecycle state and aggregated portfolio positions as
  separate concepts.

## Disclaimer

This repository is for research and educational purposes. It is not
investment advice and is not a production trading system.