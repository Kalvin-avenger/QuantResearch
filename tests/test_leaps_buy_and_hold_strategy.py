import pandas as pd

from quantresearch.instruments.options import (
    OptionContract,
    OptionType,
)
from quantresearch.orders.option_order import OptionOrder
from quantresearch.signals import Signal
from quantresearch.strategy.leaps_buy_and_hold import (
    LeapsBuyAndHoldStrategy,
)


def test_leaps_buy_and_hold_strategy_selects_and_buys_leaps():

    contracts = [
        OptionContract(
            underlying="SPY",
            expiration=pd.Timestamp("2027-01-15"),
            strike=500.0,
            option_type=OptionType.CALL,
        ),
        OptionContract(
            underlying="SPY",
            expiration=pd.Timestamp("2027-06-18"),
            strike=500.0,
            option_type=OptionType.CALL,
        ),
        OptionContract(
            underlying="SPY",
            expiration=pd.Timestamp("2027-06-18"),
            strike=505.0,
            option_type=OptionType.CALL,
        ),
        OptionContract(
            underlying="SPY",
            expiration=pd.Timestamp("2027-06-18"),
            strike=510.0,
            option_type=OptionType.CALL,
        ),
    ]

    prices = pd.Series(
        [503.0, 510.0, 515.0],
        index=pd.to_datetime(
            [
                "2026-01-02",
                "2026-01-05",
                "2026-01-06",
            ]
        ),
    )

    strategy = LeapsBuyAndHoldStrategy(
        contracts=contracts,
        quantity=1,
        min_months=12,
        max_months=18,
    )

    orders = strategy.generate_orders(
        prices
    )

    assert len(orders) == len(prices)

    assert isinstance(
        orders[0],
        OptionOrder,
    )

    assert orders[0].action == Signal.BUY
    assert orders[0].quantity == 1

    assert (
        orders[0].contract.expiration
        == pd.Timestamp("2027-06-18")
    )

    assert orders[0].contract.strike == 505.0

    assert orders[1] is None
    assert orders[2] is None