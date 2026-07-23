from quantresearch.orders import order
from quantresearch.signals import Signal


class Portfolio:
    """
    Simple long-only portfolio.

    Uses all available cash when buying.
    """

    from quantresearch.signals import Signal

    def __init__(
        self,
        initial_cash: float,
    ):

        self.cash = initial_cash
        self.shares = 0


    def buy(
        self,
        price: float,
    ):

        if self.cash <= 0:
            return


        self.shares = int(
            self.cash // price
        )


        self.cash -= (
            self.shares * price
        )


    def sell(
        self,
        price: float,
    ):

        if self.shares <= 0:
            return


        self.cash += (
            self.shares * price
        )


        self.shares = 0

    def apply_execution(
        self,
        execution
    ):
        order = execution.order

        price = execution.execution_price

        if order.action == Signal.BUY:

            cost = (
                order.quantity * price
            )

            if cost > self.cash:
                raise ValueError(
                    "Insufficient cash."
                )

            self.shares += order.quantity
            self.cash -= cost


        elif order.action == Signal.SELL:

            if order.quantity > self.shares:
                raise ValueError(
                    "Insufficient shares."
                )

            self.shares -= order.quantity
            self.cash += (
                order.quantity * price
            )