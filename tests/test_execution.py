from quantresearch.execution import Executor
from quantresearch.orders import Order
from quantresearch.signals import Signal

import pytest

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



def test_execute_invalid_price():

    executor = Executor()

    order = Order(
        action=Signal.BUY,
        quantity=100,
    )

    with pytest.raises(ValueError):
        executor.execute(
            order,
            price=0,
        )

def test_execute_invalid_quantity():

    executor = Executor()

    order = Order(
        action=Signal.BUY,
        quantity=0,
    )

    with pytest.raises(ValueError):
        executor.execute(
            order,
            price=50,
        )

def test_market_execution_sell():

    executor = Executor()

    order = Order(
        action=Signal.SELL,
        quantity=100,
    )

    result = executor.execute(
        order,
        price=50,
    )

    assert result.order == order
    assert result.execution_price == 50