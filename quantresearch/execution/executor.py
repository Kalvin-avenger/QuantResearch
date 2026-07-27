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

        if price <= 0:
            raise ValueError(
                "Execution price must be positive."
            )

        if order.quantity <= 0:
            raise ValueError(
                "Order quantity must be positive."
            )

        return ExecutionResult(
            order=order,
            execution_price=price,
        )