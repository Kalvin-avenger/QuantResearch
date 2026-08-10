from quantresearch.portfolio import Portfolio, portfolio
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

def test_portfolio_initial_realized_pnl_is_zero():

    portfolio = Portfolio(
        initial_cash=10000,
    )

    assert portfolio.realized_pnl == 0

def test_apply_execution_updates_realized_pnl():

    portfolio = Portfolio(
        initial_cash=10000,
    )

    buy_execution = ExecutionResult(
        order=Order(
            action=Signal.BUY,
            quantity=50,
        ),
        execution_price=100,
    )

    portfolio.apply_execution(
        buy_execution,
    )

    sell_execution = ExecutionResult(
        order=Order(
            action=Signal.SELL,
            quantity=20,
        ),
        execution_price=120,
    )

    portfolio.apply_execution(
        sell_execution,
    )

    assert portfolio.realized_pnl == 400

def test_multiple_sells_accumulate_realized_pnl():

    portfolio = Portfolio(
        initial_cash=20000,
    )

    buy_execution = ExecutionResult(
        order=Order(
            action=Signal.BUY,
            quantity=100,
        ),
        execution_price=100,
    )

    portfolio.apply_execution(
        buy_execution,
    )

    first_sell = ExecutionResult(
        order=Order(
            action=Signal.SELL,
            quantity=40,
        ),
        execution_price=120,
    )

    portfolio.apply_execution(
        first_sell,
    )

    second_sell = ExecutionResult(
        order=Order(
            action=Signal.SELL,
            quantity=20,
        ),
        execution_price=90,
    )

    portfolio.apply_execution(
        second_sell,
    )

    assert portfolio.realized_pnl == 600
    assert portfolio.position.quantity == 40
    assert portfolio.position.avg_price == 100


def test_market_value_with_no_position():

    portfolio = Portfolio(
        initial_cash=10000,
    )

    assert portfolio.market_value(
        price=120,
    ) == 0

def test_market_value_with_position():

    portfolio = Portfolio(
        initial_cash=10000,
    )

    buy_execution = ExecutionResult(
        order=Order(
            action=Signal.BUY,
            quantity=50,
        ),
        execution_price=100,
    )

    portfolio.apply_execution(
        buy_execution,
    )

    assert portfolio.market_value(
        price=120,
    ) == 6000

def test_unrealized_pnl_with_profit():

    portfolio = Portfolio(
        initial_cash=10000,
    )

    buy_execution = ExecutionResult(
        order=Order(
            action=Signal.BUY,
            quantity=50,
        ),
        execution_price=100,
    )

    portfolio.apply_execution(
        buy_execution,
    )

    assert portfolio.unrealized_pnl(
        price=120,
    ) == 1000

def test_unrealized_pnl_with_loss():

    portfolio = Portfolio(
        initial_cash=10000,
    )

    buy_execution = ExecutionResult(
        order=Order(
            action=Signal.BUY,
            quantity=50,
        ),
        execution_price=100,
    )

    portfolio.apply_execution(
        buy_execution,
    )

    assert portfolio.unrealized_pnl(
        price=80,
    ) == -1000

def test_total_equity():

    portfolio = Portfolio(
        initial_cash=10000,
    )

    buy_execution = ExecutionResult(
        order=Order(
            action=Signal.BUY,
            quantity=50,
        ),
        execution_price=100,
    )

    portfolio.apply_execution(
        buy_execution,
    )

    assert portfolio.total_equity(
        price=120,
    ) == 11000