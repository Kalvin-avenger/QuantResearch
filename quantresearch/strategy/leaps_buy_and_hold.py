from quantresearch.orders.option_order import OptionOrder
from quantresearch.signals import Signal
from quantresearch.strategy.leaps_selector import (
    select_leaps_call,
)
from quantresearch.orders.option_order_intent import (
    OptionOrderIntent,
)


class LeapsBuyAndHoldStrategy:

    def __init__(
        self,
        contracts,
        allocation_fraction: float = 0.25,
        min_months: int = 12,
        max_months: int = 18,
    ):
        self.contracts = contracts
        self.allocation_fraction = allocation_fraction
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

        first_intent = OptionOrderIntent(
            contract=selected_contract,
            action=Signal.BUY,
            allocation_fraction=self.allocation_fraction,
        )

        return [
            first_intent,
            *([None] * (len(prices) - 1)),
        ]