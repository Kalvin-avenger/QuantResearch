import pandas as pd

from quantresearch.data.historical_options import (
    HistoricalOptionQuote,
)
from quantresearch.instruments.options import (
    OptionContract,
    OptionType,
)
from quantresearch.orders.option_order import OptionOrder
from quantresearch.orders.option_order_intent import (
    OptionOrderIntent,
)
from quantresearch.orders.option_order_builder import (
    OptionOrderBuilder,
)
from quantresearch.signals import Signal
import pytest

def test_option_order_builder_builds_buy_order_from_allocation():

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-06-18"),
        strike=505.0,
        option_type=OptionType.CALL,
    )

    intent = OptionOrderIntent(
        contract=contract,
        action=Signal.BUY,
        allocation_fraction=0.25,
    )

    quote = HistoricalOptionQuote(
        contract=contract,
        timestamp=pd.Timestamp(
            "2026-01-02 15:59:00"
        ),
        bid=49.0,
        ask=51.0,
    )

    builder = OptionOrderBuilder()

    order = builder.build(
        intent=intent,
        quote=quote,
        cash=100_000,
    )

    assert order == OptionOrder(
        contract=contract,
        action=Signal.BUY,
        quantity=4,
    )

def test_option_order_builder_returns_none_when_budget_is_insufficient():

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-06-18"),
        strike=505.0,
        option_type=OptionType.CALL,
    )

    intent = OptionOrderIntent(
        contract=contract,
        action=Signal.BUY,
        allocation_fraction=0.25,
    )

    quote = HistoricalOptionQuote(
        contract=contract,
        timestamp=pd.Timestamp(
            "2026-01-02 15:59:00"
        ),
        bid=49.0,
        ask=51.0,
    )

    builder = OptionOrderBuilder()

    order = builder.build(
        intent=intent,
        quote=quote,
        cash=10_000,
    )

    assert order is None

def test_option_order_builder_rejects_quote_for_different_contract():

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-06-18"),
        strike=505.0,
        option_type=OptionType.CALL,
    )

    different_contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-06-18"),
        strike=510.0,
        option_type=OptionType.CALL,
    )

    intent = OptionOrderIntent(
        contract=contract,
        action=Signal.BUY,
        allocation_fraction=0.25,
    )

    quote = HistoricalOptionQuote(
        contract=different_contract,
        timestamp=pd.Timestamp(
            "2026-01-02 15:59:00"
        ),
        bid=47.0,
        ask=49.0,
    )

    builder = OptionOrderBuilder()

    with pytest.raises(
        ValueError,
        match="intent and quote contracts must match",
    ):
        builder.build(
            intent=intent,
            quote=quote,
            cash=100_000,
        )