import pandas as pd

from quantresearch.backtest import (
    BacktestEngine,
    BacktestResult,
)
from quantresearch.portfolio import Portfolio
from quantresearch.strategy import MovingAverageStrategy
from quantresearch.strategy import BaseStrategy
from quantresearch.signals import Signal

class StubStrategy(BaseStrategy):

    def __init__(
        self,
        signals,
    ):

        self.signals = signals

    def generate(
        self,
        prices: pd.Series,
    ):

        return self.signals


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


def test_backtest_equity_curve_reflects_open_position():

    prices = pd.Series(
        [100.0, 120.0],
        index=pd.to_datetime(
            [
                "2026-01-01",
                "2026-01-02",
            ]
        ),
    )

    strategy = StubStrategy(
        signals=[
            Signal.BUY,
            Signal.HOLD,
        ]
    )

    portfolio = Portfolio(
        initial_cash=10000,
    )

    engine = BacktestEngine()

    result = engine.run(
        prices=prices,
        strategy=strategy,
        portfolio=portfolio,
    )

    assert result.equity_curve[0] == 10000
    assert result.equity_curve[1] == 12000