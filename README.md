## Current Development Status

QuantResearch is a test-driven Python backtesting framework for
systematic strategy research.

Current capabilities include:

- Equity price data loading and validation
- Moving-average strategy framework
- Order and execution modeling with slippage
- Portfolio and position accounting
- Performance and trade analytics
- Yahoo option-chain ingestion and normalization
- Option contract modeling and OCC/Yahoo symbol parsing
- ATM / DTE / LEAPS contract selection
- Option position accounting, including:
  - weighted-average cost
  - unrealized PnL
  - realized PnL
  - partial and full exits

### Current Development Phase

Completed through **Sprint 12**.

Next:

**Sprint 13 — Option Order & Execution**

Planned execution pipeline:

OptionOrder
→ OptionExecutor
→ OptionExecutionResult
→ OptionPosition / Portfolio