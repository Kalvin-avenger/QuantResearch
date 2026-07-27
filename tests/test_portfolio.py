from quantresearch.portfolio import Portfolio
from quantresearch.orders import Order
from quantresearch.signals import Signal
from quantresearch.execution import (
    ExecutionResult,
)

import pytest


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

def test_apply_execution_sell():

    portfolio = Portfolio(
        initial_cash=0
    )

    portfolio.shares = 100

    order = Order(
        action=Signal.SELL,
        quantity=50,
    )

    execution = ExecutionResult(
        order=order,
        execution_price=40,
    )

    portfolio.apply_execution(
        execution
    )

    assert portfolio.shares == 50
    assert portfolio.cash == 2000

def test_apply_execution_insufficient_cash():

    portfolio = Portfolio(
        initial_cash=100
    )

    order = Order(
        action=Signal.BUY,
        quantity=10,
    )

    execution = ExecutionResult(
        order=order,
        execution_price=20,
    )

    with pytest.raises(ValueError):
        portfolio.apply_execution(
            execution
        )

def test_apply_execution_insufficient_shares():

    portfolio = Portfolio(
        initial_cash=1000
    )

    portfolio.shares = 5

    order = Order(
        action=Signal.SELL,
        quantity=10,
    )

    execution = ExecutionResult(
        order=order,
        execution_price=20,
    )

    with pytest.raises(ValueError):
        portfolio.apply_execution(
            execution
        )
