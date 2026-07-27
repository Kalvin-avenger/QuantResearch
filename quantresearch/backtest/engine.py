from turtle import pd

from quantresearch.execution import Executor
from quantresearch.orders import Order
from quantresearch.portfolio import Portfolio
from quantresearch.signals import Signal
from quantresearch.backtest import BacktestResult


class BacktestEngine:
    """
    Simple backtest engine.

    Assumptions
    -----------
    - Single asset
    - Long only
    - Market execution
    - No commission
    - No slippage
    """

    def __init__(self):

        self.executor = Executor()

    

    import pandas as pd

    from quantresearch.strategy import BaseStrategy
    from quantresearch.portfolio import Portfolio


    def run(
        self,
        prices: pd.Series,
        strategy: BaseStrategy,
        portfolio: Portfolio,
    ) -> BacktestResult:

        # if not isinstance(prices, pd.Series):
        #     prices = pd.Series(prices)

        equity_curve = []

        signals = strategy.generate(
            prices
        )

        for signal, price in zip(
            signals,
            prices,
        ):

            if signal == Signal.BUY:

                quantity = int(
                    portfolio.cash // price
                )

                if quantity > 0:

                    order = Order(
                        action=Signal.BUY,
                        quantity=quantity,
                    )

                    execution = self.executor.execute(
                        order,
                        price,
                    )

                    portfolio.apply_execution(
                        execution
                    )

            elif signal == Signal.SELL:

                if portfolio.shares > 0:

                    order = Order(
                        action=Signal.SELL,
                        quantity=portfolio.shares,
                    )

                    execution = self.executor.execute(
                        order,
                        price,
                    )

                    portfolio.apply_execution(
                        execution
                    )
            equity = (
                portfolio.cash
                + portfolio.shares * price
            )

            equity_curve.append(equity)

        return BacktestResult(
            equity_curve=equity_curve,
            trades=[],
            portfolio=portfolio,
        )