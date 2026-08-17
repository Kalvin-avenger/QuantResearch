# tests/test_option_instruction_resolver.py

import pandas as pd

from quantresearch.data.historical_options import (
    HistoricalOptionQuote,
)
from quantresearch.instruments.options import (
    OptionContract,
    OptionType,
)
from quantresearch.orders.option_instruction_resolver import (
    OptionInstructionResolver,
)
from quantresearch.orders.option_order import OptionOrder
from quantresearch.orders.option_order_intent import (
    OptionOrderIntent,
)
from quantresearch.signals import Signal


def test_resolver_converts_option_intent_to_order():

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

    resolver = OptionInstructionResolver()

    order = resolver.resolve(
        instruction=intent,
        quote=quote,
        cash=100_000,
    )

    assert order == OptionOrder(
        contract=contract,
        action=Signal.BUY,
        quantity=4,
    )

def test_resolver_returns_existing_option_order():

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-06-18"),
        strike=505.0,
        option_type=OptionType.CALL,
    )

    existing_order = OptionOrder(
        contract=contract,
        action=Signal.BUY,
        quantity=2,
    )

    resolver = OptionInstructionResolver()

    result = resolver.resolve(
        instruction=existing_order,
        quote=None,
        cash=100_000,
    )

    assert result is existing_order

def test_option_intent_can_use_fixed_allocation_base():

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    quote = HistoricalOptionQuote(
        contract=contract,
        timestamp=pd.Timestamp("2026-01-02 15:59:00"),
        bid=24.0,
        ask=25.0,
    )

    resolver = OptionInstructionResolver()

    intent = OptionOrderIntent(
        contract=contract,
        action=Signal.BUY,
        allocation_fraction=0.25,
        allocation_base=100000.0,
    )

    order = resolver.resolve(
        instruction=intent,
        quote=quote,
        cash=50000.0,
    )

    assert order is not None
    assert order.contract == contract
    assert order.action == Signal.BUY
    assert order.quantity == 10