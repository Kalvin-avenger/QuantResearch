from quantresearch.execution import Executor
from quantresearch.orders import Order
from quantresearch.signals import Signal


def test_market_execution():

    executor = Executor()

    order = Order(
        action=Signal.BUY,
        quantity=100,
    )


    result = executor.execute(
        order,
        price=50,
    )


    assert result.order == order
    assert result.execution_price == 50