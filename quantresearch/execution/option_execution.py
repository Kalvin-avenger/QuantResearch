from dataclasses import dataclass

from quantresearch.orders.option_order import OptionOrder
from quantresearch.data.options import OptionQuote
from quantresearch.signals import Signal
from quantresearch.execution.slippage import FixedSlippageModel
from quantresearch.execution.option_quote_protocol import (
    ExecutableOptionQuote,
)


@dataclass(frozen=True)
class OptionExecutionResult:
    order: OptionOrder
    execution_price: float

    def __post_init__(self):
        if self.execution_price < 0:
            raise ValueError("execution_price cannot be negative")


class OptionExecutor:

    def __init__(
        self,
        slippage_model: FixedSlippageModel | None = None,
    ):
        self.slippage_model = (
            slippage_model
            if slippage_model is not None
            else FixedSlippageModel()
        )

    def execute(
        self,
        order: OptionOrder,
        quote: ExecutableOptionQuote,
    ) -> OptionExecutionResult:

        if order.contract != quote.contract:
            raise ValueError("order and quote contracts must match")

        if order.action == Signal.BUY:
            base_price = quote.ask
        else:
            base_price = quote.bid

        execution_price = self.slippage_model.apply(
            price=base_price,
            side=order.action.name,
        )

        return OptionExecutionResult(
            order=order,
            execution_price=execution_price,
        )