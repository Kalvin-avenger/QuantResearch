import pandas as pd

from quantresearch.instruments.options import (
    OptionContract,
    OptionType,
)
from quantresearch.orders.option_order import OptionOrder
from quantresearch.signals import Signal


def test_option_order_stores_contract_action_and_quantity():
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

    assert order.contract == contract
    assert order.action == Signal.BUY
    assert order.quantity == 2

import pytest


def test_option_order_rejects_non_positive_quantity():
    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    with pytest.raises(ValueError):
        OptionOrder(
            contract=contract,
            action=Signal.BUY,
            quantity=0,
        )

    with pytest.raises(ValueError):
        OptionOrder(
            contract=contract,
            action=Signal.BUY,
            quantity=-1,
        )

def test_option_order_rejects_non_trade_action():
    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    with pytest.raises(ValueError):
        OptionOrder(
            contract=contract,
            action=Signal.HOLD,
            quantity=1,
        )

    with pytest.raises(ValueError):
        OptionOrder(
            contract=contract,
            action=Signal.NONE,
            quantity=1,
        )

import pandas as pd

from quantresearch.instruments.options import (
    OptionContract,
    OptionType,
)
from quantresearch.orders.option_order import OptionOrder
from quantresearch.execution.option_execution import OptionExecutionResult
from quantresearch.signals import Signal


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

