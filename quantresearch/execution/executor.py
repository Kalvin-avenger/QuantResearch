from dataclasses import dataclass

from quantresearch.orders import Order


@dataclass
class ExecutionResult:

    order: Order
    execution_price: float



class Executor:
    """
    Simple market execution simulator.
    """


    def execute(
        self,
        order: Order,
        price: float,
    ) -> ExecutionResult:

        order.price = price


        return ExecutionResult(
            order=order,
            execution_price=price,
        )