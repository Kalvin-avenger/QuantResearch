import pandas as pd

from quantresearch.strategy import BaseStrategy

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

    def run(
        self,
        prices: pd.Series,
        strategy: BaseStrategy,
        portfolio: Portfolio,
    ) -> BacktestResult:

        # if not isinstance(prices, pd.Series):
        #     prices = pd.Series(prices)

        equity_curve = []
        trades = []

        signals = strategy.generate(
            prices
        )

        for timestamp, signal, price in zip(
            prices.index,
            signals,
            prices,
        ):

            if signal == Signal.BUY:

                if portfolio.position.quantity == 0:

                    quantity = int(
                        portfolio.cash / price
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

                    from quantresearch.execution.trade import Trade

                    trades.append(
                        Trade(
                            timestamp=pd.Timestamp(timestamp),
                            action=execution.order.action,
                            quantity=execution.order.quantity,
                            price=execution.execution_price,
                        )
                    )

            elif signal == Signal.SELL:

                if portfolio.position.quantity > 0:

                    quantity = portfolio.position.quantity

                    execution = self.executor.execute(
                        order,
                        price,
                    )

                    portfolio.apply_execution(
                        execution
                    )

                    trades.append(
                        Trade(
                            timestamp=pd.Timestamp(timestamp),
                            action=execution.order.action,
                            quantity=execution.order.quantity,
                            price=execution.execution_price,
                        )
                    )
            equity = (
                portfolio.cash
                + portfolio.position.quantity * price
            )

            equity_curve.append(equity)

        return BacktestResult(
            equity_curve=equity_curve,
            trades=trades,
            portfolio=portfolio,
        )