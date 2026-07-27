import pandas as pd

from quantresearch.backtest import (
    BacktestEngine,
    BacktestResult,
)
from quantresearch.portfolio import Portfolio
from quantresearch.strategy import MovingAverageStrategy


def test_backtest_engine_basic():

    prices = pd.Series(
        [
            1,
            2,
            3,
            2,
            1,
            2,
            3,
            4,
            5,
        ]
    )

    strategy = MovingAverageStrategy(
        short_window=2,
        long_window=3,
    )

    portfolio = Portfolio(
        initial_cash=1000,
    )

    engine = BacktestEngine()

    result = engine.run(
        prices=prices,
        strategy=strategy,
        portfolio=portfolio,
    )

    assert isinstance(
        result,
        BacktestResult,
    )

    assert len(result.equity_curve) == len(prices)

    assert result.portfolio.cash >= 0