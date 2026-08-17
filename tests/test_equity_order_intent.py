import pytest

from quantresearch.orders.equity_order_intent import (
    EquityOrderIntent,
)
from quantresearch.signals import Signal

from quantresearch.orders.equity_instruction_resolver import (
    EquityInstructionResolver
)


def test_equity_order_intent_stores_allocation():

    intent = EquityOrderIntent(
        action=Signal.BUY,
        allocation_fraction=0.25,
    )

    assert intent.action == Signal.BUY
    assert intent.allocation_fraction == pytest.approx(
        0.25
    )

def test_equity_intent_can_use_fixed_allocation_base():

    resolver = EquityInstructionResolver()

    intent = EquityOrderIntent(
        action=Signal.BUY,
        allocation_fraction=0.25,
        allocation_base=100000.0,
    )

    order = resolver.resolve(
        instruction=intent,
        price=500.0,
        cash=50000.0,
    )

    assert order.quantity == 50