import pandas as pd

from quantresearch.data.daily_option_pricing import (
    DailyOptionExecutionQuoteAdapter,
    DailyOptionPricing,
)
from quantresearch.execution.option_execution import OptionExecutor
from quantresearch.instruments.options import (
    OptionContract,
    OptionType,
)
from quantresearch.orders.option_order import OptionOrder
from quantresearch.signals import Signal


def test_option_executor_accepts_daily_pricing_adapter_for_buy():

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-03-19"),
        strike=505.0,
        option_type=OptionType.CALL,
    )

    pricing = DailyOptionPricing(
        contract=contract,
        timestamp=pd.Timestamp("2026-01-02"),
        buy_price=30.0,
        sell_price=29.5,
        mark_price=29.75,
    )

    quote = DailyOptionExecutionQuoteAdapter(
        pricing=pricing,
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

    assert result.contract == contract
    assert result.quantity == 2
    assert result.price == 30.0


def test_option_executor_accepts_daily_pricing_adapter_for_buy():
    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-03-19"),
        strike=505.0,
        option_type=OptionType.CALL,
    )

    pricing = DailyOptionPricing(
        contract=contract,
        timestamp=pd.Timestamp("2026-01-02"),
        buy_price=30.0,
        sell_price=29.5,
        mark_price=29.75,
    )

    quote = DailyOptionExecutionQuoteAdapter(
        pricing=pricing,
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
    assert result.execution_price == 30.0


def test_option_executor_accepts_daily_pricing_adapter_for_sell():
    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-03-19"),
        strike=505.0,
        option_type=OptionType.CALL,
    )

    pricing = DailyOptionPricing(
        contract=contract,
        timestamp=pd.Timestamp("2026-01-02"),
        buy_price=30.0,
        sell_price=29.5,
        mark_price=29.75,
    )

    quote = DailyOptionExecutionQuoteAdapter(
        pricing=pricing,
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

    assert result.order == order
    assert result.execution_price == 29.5