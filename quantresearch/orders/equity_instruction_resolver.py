from quantresearch.orders.order import Order
from quantresearch.orders.equity_order_intent import (
    EquityOrderIntent,
)
from quantresearch.signals import Signal


class EquityInstructionResolver:

    def resolve(
        self,
        instruction: EquityOrderIntent,
        price: float,
        cash: float,
    ) -> Order | None:

        if instruction.action != Signal.BUY:
            raise ValueError(
                "only BUY equity intents are supported"
            )

        budget = (
            cash
            * instruction.allocation_fraction
        )

        quantity = int(
            budget // price
        )

        if quantity <= 0:
            return None

        return Order(
            action=instruction.action,
            quantity=quantity,
        )