import pytest

from quantresearch.orders.equity_order_intent import (
    EquityOrderIntent,
)
from quantresearch.orders.equity_instruction_resolver import (
    EquityInstructionResolver,
)
from quantresearch.signals import Signal


def test_resolve_buy_allocation_into_share_quantity():

    resolver = EquityInstructionResolver()

    intent = EquityOrderIntent(
        action=Signal.BUY,
        allocation_fraction=0.25,
    )

    order = resolver.resolve(
        instruction=intent,
        price=500.0,
        cash=100000.0,
    )

    assert order.action == Signal.BUY
    assert order.quantity == 50