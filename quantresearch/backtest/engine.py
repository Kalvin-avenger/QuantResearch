from quantresearch.portfolio import Portfolio
from quantresearch.orders import Order
from quantresearch.execution import Executor
from quantresearch.backtest import BacktestResult
from quantresearch.signals import Signal


class BacktestEngine:


    def __init__(
        self,
        prices,
        signals,
        initial_cash=100000,
    ):

        self.prices = prices
        self.signals = signals

        self.portfolio = Portfolio(
            initial_cash
        )

        self.executor = Executor()



    def run(self):

        equity_curve = []


        for price, signal in zip(
            self.prices,
            self.signals
        ):


            if signal == Signal.BUY:

                quantity = int(
                    self.portfolio.cash
                    // price
                )


                order = Order(
                    action=Signal.BUY,
                    quantity=quantity,
                )


                execution = self.executor.execute(
                    order,
                    price,
                )


                self.portfolio.apply_execution(
                    execution
                )


            elif signal == Signal.SELL:


                order = Order(
                    action=Signal.SELL,
                    quantity=self.portfolio.shares,
                )


                execution = self.executor.execute(
                    order,
                    price,
                )


                self.portfolio.apply_execution(
                    execution
                )


            value = (
                self.portfolio.cash
                +
                self.portfolio.shares * price
            )


            equity_curve.append(value)


        return BacktestResult(
            equity_curve=equity_curve,
            trades=[]
        )