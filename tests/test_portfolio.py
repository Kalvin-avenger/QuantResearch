from quantresearch.portfolio import Portfolio
from quantresearch.orders import Order
from quantresearch.signals import Signal
from quantresearch.execution import (
    ExecutionResult,
)


def test_apply_execution():

    portfolio = Portfolio(
        initial_cash=100000
    )

    order = Order(
        action=Signal.BUY,
        quantity=100,
    )

    execution = ExecutionResult(
        order=order,
        execution_price=50,
    )


    portfolio.apply_execution(
        execution
    )


    assert portfolio.shares == 100
    assert portfolio.cash == 95000