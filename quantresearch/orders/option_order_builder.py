from quantresearch.orders.option_order import (
    OptionOrder,
)
from quantresearch.signals import Signal
from quantresearch.strategy.position_sizing import (
    calculate_option_quantity,
)


class OptionOrderBuilder:

    def build(
        self,
        intent,
        quote,
        cash: float,
    ) -> OptionOrder | None:

        if intent.contract != quote.contract:
            raise ValueError(
                "intent and quote contracts must match"
            )

        if intent.action == Signal.BUY:
            option_price = quote.ask
        else:
            option_price = quote.bid

        quantity = calculate_option_quantity(
            cash=cash,
            option_price=option_price,
            multiplier=intent.contract.multiplier,
            allocation_fraction=intent.allocation_fraction,
        )

        if quantity == 0:
            return None

        return OptionOrder(
            contract=intent.contract,
            action=intent.action,
            quantity=quantity,
        )