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

import pandas as pd

from quantresearch.accounting.option_position import OptionPosition
from quantresearch.instruments.options import OptionContract, OptionType
from quantresearch.portfolio import Portfolio


def test_portfolio_can_hold_option_position():
    portfolio = Portfolio(
        initial_cash=100000,
    )

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    position = OptionPosition(
        contract=contract,
        quantity=2,
        average_cost=25.0,
    )

    portfolio.option_positions[contract] = position

    assert portfolio.option_positions[contract] == position


def test_portfolio_can_add_option_position():
    portfolio = Portfolio(
        initial_cash=100000,
    )

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    position = OptionPosition(
        contract=contract,
        quantity=2,
        average_cost=25.0,
    )

    portfolio.add_option_position(position)

    assert portfolio.option_positions[contract] == position

def test_portfolio_rejects_duplicate_option_position():
    portfolio = Portfolio(
        initial_cash=100000,
    )

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    first_position = OptionPosition(
        contract=contract,
        quantity=1,
        average_cost=20.0,
    )

    second_position = OptionPosition(
        contract=contract,
        quantity=2,
        average_cost=25.0,
    )

    portfolio.add_option_position(first_position)

    with pytest.raises(ValueError):
        portfolio.add_option_position(second_position)

from quantresearch.orders.option_order import OptionOrder
from quantresearch.execution.option_execution import OptionExecutionResult

def test_portfolio_applies_option_buy_execution():
    portfolio = Portfolio(
        initial_cash=100000,
    )

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    order = OptionOrder(
        contract=contract,
        action=Signal.BUY,
        quantity=2,
    )

    execution = OptionExecutionResult(
        order=order,
        execution_price=25.0,
    )

    portfolio.apply_option_execution(execution)

    position = portfolio.option_positions[contract]

    assert position.quantity == 2
    assert position.average_cost == 25.0
    assert portfolio.cash == 95000.0

def test_portfolio_rejects_option_buy_when_cash_is_insufficient():
    portfolio = Portfolio(
        initial_cash=1000,
    )

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    order = OptionOrder(
        contract=contract,
        action=Signal.BUY,
        quantity=1,
    )

    execution = OptionExecutionResult(
        order=order,
        execution_price=25.0,
    )

    with pytest.raises(ValueError):
        portfolio.apply_option_execution(execution)

    assert portfolio.cash == 1000
    assert contract not in portfolio.option_positions

def test_portfolio_adds_to_existing_option_position():
    portfolio = Portfolio(
        initial_cash=100000,
    )

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    existing_position = OptionPosition(
        contract=contract,
        quantity=1,
        average_cost=20.0,
    )

    portfolio.add_option_position(existing_position)

    order = OptionOrder(
        contract=contract,
        action=Signal.BUY,
        quantity=1,
    )

    execution = OptionExecutionResult(
        order=order,
        execution_price=30.0,
    )

    portfolio.apply_option_execution(execution)

    position = portfolio.option_positions[contract]

    assert position.quantity == 2
    assert position.average_cost == pytest.approx(25.0)
    assert portfolio.cash == 97000.0


def test_portfolio_applies_option_sell_execution():
    portfolio = Portfolio(
        initial_cash=100000,
    )

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    position = OptionPosition(
        contract=contract,
        quantity=2,
        average_cost=20.0,
    )

    portfolio.add_option_position(position)

    order = OptionOrder(
        contract=contract,
        action=Signal.SELL,
        quantity=1,
    )

    execution = OptionExecutionResult(
        order=order,
        execution_price=30.0,
    )

    portfolio.apply_option_execution(execution)

    remaining_position = portfolio.option_positions[contract]

    assert remaining_position.quantity == 1
    assert remaining_position.average_cost == 20.0
    assert portfolio.cash == 103000.0

def test_portfolio_rejects_option_sell_when_position_does_not_exist():
    portfolio = Portfolio(
        initial_cash=100000,
    )

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    order = OptionOrder(
        contract=contract,
        action=Signal.SELL,
        quantity=1,
    )

    execution = OptionExecutionResult(
        order=order,
        execution_price=30.0,
    )

    with pytest.raises(ValueError):
        portfolio.apply_option_execution(execution)

    assert portfolio.cash == 100000

def test_portfolio_rejects_option_oversell_without_changing_state():
    portfolio = Portfolio(
        initial_cash=100000,
    )

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    position = OptionPosition(
        contract=contract,
        quantity=1,
        average_cost=20.0,
    )

    portfolio.add_option_position(position)

    order = OptionOrder(
        contract=contract,
        action=Signal.SELL,
        quantity=2,
    )

    execution = OptionExecutionResult(
        order=order,
        execution_price=30.0,
    )

    with pytest.raises(ValueError):
        portfolio.apply_option_execution(execution)

    remaining_position = portfolio.option_positions[contract]

    assert remaining_position.quantity == 1
    assert remaining_position.average_cost == 20.0
    assert portfolio.cash == 100000

def test_portfolio_removes_option_position_after_full_close():
    portfolio = Portfolio(
        initial_cash=100000,
    )

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    position = OptionPosition(
        contract=contract,
        quantity=1,
        average_cost=20.0,
    )

    portfolio.add_option_position(position)

    order = OptionOrder(
        contract=contract,
        action=Signal.SELL,
        quantity=1,
    )

    execution = OptionExecutionResult(
        order=order,
        execution_price=30.0,
    )

    portfolio.apply_option_execution(execution)

    assert contract not in portfolio.option_positions
    assert portfolio.cash == 103000.0

def test_portfolio_calculates_option_market_value():
    portfolio = Portfolio(
        initial_cash=100000,
    )

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    position = OptionPosition(
        contract=contract,
        quantity=2,
        average_cost=20.0,
    )

    portfolio.add_option_position(position)

    option_prices = {
        contract: 30.0,
    }

    value = portfolio.option_market_value(option_prices)

    assert value == 6000.0


def test_portfolio_calculates_market_value_for_multiple_option_positions():
    portfolio = Portfolio(
        initial_cash=100000,
    )

    call_contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    put_contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=450.0,
        option_type=OptionType.PUT,
    )

    call_position = OptionPosition(
        contract=call_contract,
        quantity=2,
        average_cost=20.0,
    )

    put_position = OptionPosition(
        contract=put_contract,
        quantity=1,
        average_cost=15.0,
    )

    portfolio.add_option_position(call_position)
    portfolio.add_option_position(put_position)

    option_prices = {
        call_contract: 30.0,
        put_contract: 10.0,
    }

    value = portfolio.option_market_value(option_prices)

    assert value == pytest.approx(7000.0)

def test_portfolio_total_equity_includes_option_market_value():
    portfolio = Portfolio(
        initial_cash=100000,
    )

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    position = OptionPosition(
        contract=contract,
        quantity=2,
        average_cost=20.0,
    )

    portfolio.add_option_position(position)

    option_prices = {
        contract: 30.0,
    }

    total = portfolio.total_equity(
        price=500.0,
        option_prices=option_prices,
    )

    assert total == pytest.approx(106000.0)

def test_portfolio_total_equity_includes_equity_and_options():
    portfolio = Portfolio(
        initial_cash=100000,
    )

    # Buy equity: uses all available cash according to current Portfolio.buy()
    portfolio.buy(price=500.0)

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    option_position = OptionPosition(
        contract=contract,
        quantity=2,
        average_cost=20.0,
    )

    portfolio.add_option_position(option_position)

    option_prices = {
        contract: 30.0,
    }

    total = portfolio.total_equity(
        price=550.0,
        option_prices=option_prices,
    )

    assert total == pytest.approx(116000.0)