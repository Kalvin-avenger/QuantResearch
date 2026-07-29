from quantresearch.signals import Signal
from quantresearch.accounting import Position


class Portfolio:
    """
    Simple long-only portfolio.

    Uses all available cash when buying.
    """

    def __init__(
        self,
        initial_cash: float,
    ):

        if initial_cash < 0:
            raise ValueError(
                "Initial cash cannot be negative."
            )

        self.cash = initial_cash
        self.position = Position()

    def buy(
        self,
        price: float,
    ) -> None:

        if price <= 0:
            raise ValueError(
                "Price must be positive."
            )

        if self.cash <= 0:
            return

        quantity = int(
            self.cash // price
        )

        if quantity <= 0:
            return

        cost = quantity * price

        self.cash -= cost

        self.position.buy(
            quantity=quantity,
            price=price,
        )

    def sell(
        self,
        price: float,
    ) -> None:

        if price <= 0:
            raise ValueError(
                "Price must be positive."
            )

        quantity = self.position.quantity

        if quantity <= 0:
            return

        self.position.sell(
            quantity=quantity,
            price=price,
        )

        self.cash += quantity * price

    def apply_execution(
        self,
        execution,
    ) -> None:

        quantity = execution.order.quantity
        price = execution.execution_price
        action = execution.order.action

        if action == Signal.BUY:

            cost = quantity * price

            if cost > self.cash:
                raise ValueError(
                    "Insufficient cash."
                )

            self.cash -= cost

            self.position.buy(
                quantity=quantity,
                price=price,
            )

        elif action == Signal.SELL:

            self.position.sell(
                quantity=quantity,
                price=price,
            )

            self.cash += quantity * price