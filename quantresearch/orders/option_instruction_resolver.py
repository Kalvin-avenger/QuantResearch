from quantresearch.orders.option_order import (
    OptionOrder,
)
from quantresearch.orders.option_order_intent import (
    OptionOrderIntent,
)
from quantresearch.orders.option_order_builder import (
    OptionOrderBuilder,
)


class OptionInstructionResolver:

    def __init__(self):
        self.order_builder = OptionOrderBuilder()

    def resolve(
        self,
        instruction,
        quote,
        cash: float,
    ) -> OptionOrder | None:

        if isinstance(
            instruction,
            OptionOrder,
        ):
            return instruction

        if isinstance(
            instruction,
            OptionOrderIntent,
        ):
            return self.order_builder.build(
                intent=instruction,
                quote=quote,
                cash=cash,
            )

        raise TypeError(
            "unsupported option instruction type"
        )