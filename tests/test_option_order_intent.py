import pandas as pd

from quantresearch.instruments.options import (
    OptionContract,
    OptionType,
)
from quantresearch.orders.option_order_intent import (
    OptionOrderIntent,
)
from quantresearch.signals import Signal


def test_option_order_intent_stores_allocation_fraction():

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

    assert intent.contract == contract
    assert intent.action == Signal.BUY
    assert intent.allocation_fraction == 0.25