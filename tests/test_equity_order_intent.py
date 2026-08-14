import pytest

from quantresearch.orders.equity_order_intent import (
    EquityOrderIntent,
)
from quantresearch.signals import Signal


def test_equity_order_intent_stores_allocation():

    intent = EquityOrderIntent(
        action=Signal.BUY,
        allocation_fraction=0.25,
    )

    assert intent.action == Signal.BUY
    assert intent.allocation_fraction == pytest.approx(
        0.25
    )