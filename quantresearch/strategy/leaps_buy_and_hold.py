from quantresearch.orders.option_order import OptionOrder
from quantresearch.signals import Signal
from quantresearch.strategy.leaps_selector import (
    select_leaps_call,
)


class LeapsBuyAndHoldStrategy:

    def __init__(
        self,
        contracts,
        quantity: int = 1,
        min_months: int = 12,
        max_months: int = 18,
    ):
        self.contracts = contracts
        self.quantity = quantity
        self.min_months = min_months
        self.max_months = max_months

    def generate_orders(
        self,
        prices,
    ):
        if len(prices) == 0:
            return []

        selected_contract = select_leaps_call(
            contracts=self.contracts,
            as_of=prices.index[0],
            spot_price=prices.iloc[0],
            min_months=self.min_months,
            max_months=self.max_months,
        )

        first_order = OptionOrder(
            contract=selected_contract,
            action=Signal.BUY,
            quantity=self.quantity,
        )

        return [
            first_order,
            *([None] * (len(prices) - 1)),
        ]