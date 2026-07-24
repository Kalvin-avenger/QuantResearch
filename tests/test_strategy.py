# from quantresearch.strategy import BaseStrategy


# def test_strategy_base():

#     strategy = BaseStrategy()

#     try:
#         strategy.generate([])

#     except NotImplementedError:
#         pass

#     else:
#         assert False


import pandas as pd

from quantresearch.strategy import (
    MovingAverageStrategy,
)


def test_moving_average_strategy():

    prices = pd.Series(
        [1, 2, 3, 2, 1]
    )

    strategy = MovingAverageStrategy(
        short_window=2,
        long_window=3,
    )

    signals = strategy.generate(
        prices
    )

    assert len(signals) == len(prices)