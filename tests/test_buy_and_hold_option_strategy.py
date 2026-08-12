import pandas as pd

from quantresearch.instruments.options import (
    OptionContract,
    OptionType,
)
from quantresearch.orders.option_order import OptionOrder
from quantresearch.signals import Signal
from quantresearch.strategy.buy_and_hold_option import (
    BuyAndHoldOptionStrategy,
)


def test_buy_and_hold_option_strategy_buys_once():

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    strategy = BuyAndHoldOptionStrategy(
        contract=contract,
        quantity=1,
    )

    prices = pd.Series(
        [500.0, 510.0, 520.0],
        index=pd.to_datetime(
            [
                "2026-01-02",
                "2026-01-05",
                "2026-01-06",
            ]
        ),
    )

    orders = strategy.generate_orders(
        prices
    )

    assert len(orders) == len(prices)

    assert orders[0] == OptionOrder(
        contract=contract,
        action=Signal.BUY,
        quantity=1,
    )

    assert orders[1] is None
    assert orders[2] is None