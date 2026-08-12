import pandas as pd

from quantresearch.instruments.options import (
    OptionContract,
    OptionType,
)
from quantresearch.orders.option_order import OptionOrder
from quantresearch.execution.option_execution import OptionExecutionResult
from quantresearch.signals import Signal
from quantresearch.data.options import OptionQuote
from quantresearch.instruments.options import OptionContract
from quantresearch.execution.option_execution import (
    OptionExecutionResult,
    OptionExecutor,
)


def test_option_execution_result_stores_order_and_execution_price():
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

    result = OptionExecutionResult(
        order=order,
        execution_price=25.50,
    )

    assert result.order == order
    assert result.execution_price == 25.50

import pytest


def test_option_execution_result_rejects_negative_execution_price():
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

    with pytest.raises(ValueError):
        OptionExecutionResult(
            order=order,
            execution_price=-1.0,
        )

def test_option_executor_executes_buy_at_ask():
    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    quote = OptionQuote(
        contract=contract,
        last_trade_date=pd.Timestamp("2026-08-10"),
        last_price=24.80,
        bid=24.50,
        ask=25.00,
        volume=100,
        open_interest=1000,
        implied_volatility=0.20,
        in_the_money=False,
    )

    order = OptionOrder(
        contract=contract,
        action=Signal.BUY,
        quantity=2,
    )

    executor = OptionExecutor()

    result = executor.execute(
        order=order,
        quote=quote,
    )

    assert result.order == order
    assert result.execution_price == 25.00

def test_option_executor_executes_sell_at_bid():
    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    quote = OptionQuote(
        contract=contract,
        last_trade_date=pd.Timestamp("2026-08-10"),
        last_price=24.80,
        bid=24.50,
        ask=25.00,
        volume=100,
        open_interest=1000,
        implied_volatility=0.20,
        in_the_money=False,
    )

    order = OptionOrder(
        contract=contract,
        action=Signal.SELL,
        quantity=2,
    )

    executor = OptionExecutor()

    result = executor.execute(
        order=order,
        quote=quote,
    )

    assert result.execution_price == 24.50


def test_option_executor_rejects_quote_for_different_contract():
    order_contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    quote_contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=510.0,
        option_type=OptionType.CALL,
    )

    order = OptionOrder(
        contract=order_contract,
        action=Signal.BUY,
        quantity=1,
    )

    quote = OptionQuote(
        contract=quote_contract,
        last_trade_date=pd.Timestamp("2026-08-10"),
        last_price=20.00,
        bid=19.50,
        ask=20.50,
        volume=100,
        open_interest=1000,
        implied_volatility=0.20,
        in_the_money=False,
    )

    executor = OptionExecutor()

    with pytest.raises(ValueError):
        executor.execute(
            order=order,
            quote=quote,
        )

from quantresearch.execution.slippage import FixedSlippageModel


def test_option_executor_applies_slippage_to_buy():
    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    quote = OptionQuote(
        contract=contract,
        last_trade_date=pd.Timestamp("2026-08-10"),
        last_price=24.80,
        bid=24.50,
        ask=25.00,
        volume=100,
        open_interest=1000,
        implied_volatility=0.20,
        in_the_money=False,
    )

    order = OptionOrder(
        contract=contract,
        action=Signal.BUY,
        quantity=2,
    )

    slippage_model = FixedSlippageModel(
        slippage=0.01,
    )

    executor = OptionExecutor(
        slippage_model=slippage_model,
    )

    result = executor.execute(
        order=order,
        quote=quote,
    )

    assert result.execution_price == pytest.approx(25.25)


def test_option_executor_applies_slippage_to_sell():
    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    quote = OptionQuote(
        contract=contract,
        last_trade_date=pd.Timestamp("2026-08-10"),
        last_price=24.80,
        bid=24.50,
        ask=25.00,
        volume=100,
        open_interest=1000,
        implied_volatility=0.20,
        in_the_money=False,
    )

    order = OptionOrder(
        contract=contract,
        action=Signal.SELL,
        quantity=2,
    )

    slippage_model = FixedSlippageModel(
        slippage=0.01,
    )

    executor = OptionExecutor(
        slippage_model=slippage_model,
    )

    result = executor.execute(
        order=order,
        quote=quote,
    )

    assert result.execution_price == pytest.approx(24.255)

from quantresearch.data.historical_option_quote import (
    HistoricalOptionQuote,
)

def test_option_executor_executes_historical_option_quote():
    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    quote = HistoricalOptionQuote(
        contract=contract,
        timestamp=pd.Timestamp("2026-01-02"),
        bid=24.5,
        ask=25.5,
    )

    order = OptionOrder(
        contract=contract,
        action=Signal.BUY,
        quantity=2,
    )

    executor = OptionExecutor()

    result = executor.execute(
        order=order,
        quote=quote,
    )

    assert result.execution_price == pytest.approx(25.5)