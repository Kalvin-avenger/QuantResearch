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


    assert portfolio.position.quantity == 100
    assert portfolio.cash == 95000

def test_apply_execution_sell():

    portfolio = Portfolio(
        initial_cash=10000,
    )

    buy_execution = ExecutionResult(
        order=Order(
            action=Signal.BUY,
            quantity=100,
        ),
        execution_price=20,
    )

    portfolio.apply_execution(
        buy_execution,
    )

    sell_execution = ExecutionResult(
        order=Order(
            action=Signal.SELL,
            quantity=50,
        ),
        execution_price=40,
    )

    portfolio.apply_execution(
        sell_execution,
    )

    assert portfolio.cash == 10000
    assert portfolio.position.quantity == 50
    assert portfolio.position.quantity == 50
    assert portfolio.position.avg_price == 20

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

    portfolio.position.buy(
        quantity=5,
        price=100,
    )
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


from quantresearch.portfolio import Portfolio
from quantresearch.accounting import Position


def test_portfolio_contains_position():

    portfolio = Portfolio(
        initial_cash=10000,
    )

    assert isinstance(
        portfolio.position,
        Position,
    )

def test_portfolio_does_not_expose_legacy_shares():

    portfolio = Portfolio(
        initial_cash=10000,
    )

    assert not hasattr(
        portfolio,
        "shares",
    )