from quantresearch.orders.option_order import OptionOrder
from quantresearch.signals import Signal


class BuyAndHoldOptionStrategy:

    def __init__(
        self,
        contract,
        quantity: int = 1,
    ):
        self.contract = contract
        self.quantity = quantity

    def generate_orders(
        self,
        prices,
    ):
        if len(prices) == 0:
            return []

        orders = [
            OptionOrder(
                contract=self.contract,
                action=Signal.BUY,
                quantity=self.quantity,
            )
        ]

        orders.extend(
            [None] * (len(prices) - 1)
        )

        return orders

class BuyThenSellOptionStrategy:

    def __init__(
        self,
        contract,
    ):
        self.contract = contract

    def generate_orders(
        self,
        prices,
    ):
        return [
            OptionOrder(
                contract=self.contract,
                action=Signal.BUY,
                quantity=1,
            ),
            OptionOrder(
                contract=self.contract,
                action=Signal.SELL,
                quantity=1,
            ),
        ]