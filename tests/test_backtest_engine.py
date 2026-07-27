# import pandas as pd

# from quantresearch.backtest import (
#     BacktestEngine,
#     BacktestResult,
# )
# from quantresearch.portfolio import Portfolio
# from quantresearch.strategy import MovingAverageStrategy
# from quantresearch.signals import Signal


# def test_backtest_engine_basic():


#     prices = pd.Series(
#             [
#                 100,
#                 120,
#             ]
#         )

#     signals = [
#         Signal.BUY,
#         Signal.SELL,
#     ]


#     portfolio = Portfolio(
#         initial_cash=100000,
#     )

#     strategy = MovingAverageStrategy(
#         short_window=2,
#         long_window=3,
#     )

#     engine = BacktestEngine()

#     result = engine.run(
#         prices=prices,
#         strategy=strategy,
#         portfolio=portfolio,
#     )

#     assert result.equity_curve[-1] == 120000