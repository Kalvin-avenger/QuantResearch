import pandas as pd

from quantresearch.execution.trade import Trade
from quantresearch.signals import Signal


def test_create_trade():

    trade = Trade(
        timestamp=pd.Timestamp("2023-01-05"),
        action=Signal.BUY,
        quantity=10,
        price=100.0,
    )

    assert trade.action == Signal.BUY
    assert trade.quantity == 10
    assert trade.price == 100.0


def test_trade_equality():

    trade1 = Trade(
        timestamp=pd.Timestamp("2023-01-05"),
        action=Signal.BUY,
        quantity=10,
        price=100,
    )

    trade2 = Trade(
        timestamp=pd.Timestamp("2023-01-05"),
        action=Signal.BUY,
        quantity=10,
        price=100,
    )

    assert trade1 == trade2

import pytest
from dataclasses import FrozenInstanceError

from quantresearch.execution.trade import Trade
from quantresearch.signals import Signal


def test_trade_is_immutable():

    trade = Trade(
        timestamp=pd.Timestamp("2023-01-05"),
        action=Signal.BUY,
        quantity=10,
        price=100,
    )

    with pytest.raises(FrozenInstanceError):
        trade.price = 120

def test_trade_has_timestamp():

    timestamp = pd.Timestamp("2023-01-05")


    trade = Trade(
        timestamp=timestamp,
        action=Signal.BUY,
        quantity=10,
        price=100,
    )

    assert trade.timestamp == pd.Timestamp("2023-01-05")