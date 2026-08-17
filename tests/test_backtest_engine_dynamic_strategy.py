import pandas as pd
import pytest

from quantresearch.backtest.engine import BacktestEngine
from quantresearch.orders.equity_order_intent import EquityOrderIntent
from quantresearch.portfolio import Portfolio
from quantresearch.signals import Signal


class DynamicStrategy:

    def __init__(self):
        self.contexts = []

    def on_bar(
        self,
        timestamp,
        price,
        context,
    ):
        self.contexts.append(context)

        if len(self.contexts) == 1:
            return EquityOrderIntent(
                action=Signal.BUY,
                allocation_fraction=0.25,
            )

        return None


def test_engine_supports_dynamic_on_bar_strategy():

    prices = pd.Series(
        [500.0, 510.0],
        index=[
            pd.Timestamp("2026-01-02"),
            pd.Timestamp("2026-01-05"),
        ],
    )

    portfolio = Portfolio(
        initial_cash=100000.0,
    )

    strategy = DynamicStrategy()

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

    assert len(strategy.contexts) == 2

    assert strategy.contexts[0].cash == pytest.approx(
        100000.0
    )

    assert strategy.contexts[1].cash == pytest.approx(
        75000.0
    )

    assert len(result.trades) == 1