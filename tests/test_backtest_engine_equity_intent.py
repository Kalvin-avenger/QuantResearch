import pandas as pd
import pytest

from quantresearch.backtest.engine import (
    BacktestEngine,
)
from quantresearch.orders.equity_order_intent import (
    EquityOrderIntent,
)
from quantresearch.portfolio import Portfolio
from quantresearch.signals import Signal


class EquityIntentStrategy:

    def generate_orders(
        self,
        prices,
    ):
        return [
            EquityOrderIntent(
                action=Signal.BUY,
                allocation_fraction=0.25,
            ),
            None,
        ]


def test_backtest_engine_executes_equity_order_intent():

    prices = pd.Series(
        [500.0, 510.0],
        index=[
            pd.Timestamp("2026-01-02"),
            pd.Timestamp("2026-01-05"),
        ],
    )

    portfolio = Portfolio(
        initial_cash=100000,
    )

    strategy = EquityIntentStrategy()

    engine = BacktestEngine()

    result = engine.run(
        prices=prices,
        strategy=strategy,
        portfolio=portfolio,
    )

    assert portfolio.position.quantity == 50

    assert portfolio.cash == pytest.approx(
        75000.0
    )

    assert len(result.trades) == 1

    assert result.trades[0].quantity == 50
    assert result.trades[0].price == pytest.approx(
        500.0
    )