import pandas as pd

from quantresearch.accounting.option_position import (
    OptionPosition,
)
from quantresearch.instruments.options import (
    OptionContract,
    OptionType,
)


def test_option_position_stores_contract_quantity_and_average_cost():

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp(
            "2027-12-17"
        ),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    position = OptionPosition(
        contract=contract,
        quantity=2,
        average_cost=25.50,
    )

    assert position.contract == contract
    assert position.quantity == 2
    assert position.average_cost == 25.50

import pytest


def test_option_position_rejects_negative_quantity():

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp(
            "2027-12-17"
        ),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    with pytest.raises(
        ValueError,
        match="quantity must not be negative",
    ):
        OptionPosition(
            contract=contract,
            quantity=-1,
            average_cost=25.50,
        )

def test_option_position_rejects_negative_average_cost():

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp(
            "2027-12-17"
        ),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    with pytest.raises(
        ValueError,
        match="average_cost must not be negative",
    ):
        OptionPosition(
            contract=contract,
            quantity=2,
            average_cost=-1.0,
        )

def test_option_position_requires_zero_cost_when_quantity_is_zero():

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp(
            "2027-12-17"
        ),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    with pytest.raises(
        ValueError,
        match="average_cost must be zero",
    ):
        OptionPosition(
            contract=contract,
            quantity=0,
            average_cost=25.50,
        )

def test_option_position_market_value():

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp(
            "2027-12-17"
        ),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    position = OptionPosition(
        contract=contract,
        quantity=2,
        average_cost=25.50,
    )

    value = position.market_value(
        current_price=30.0
    )

    assert value == pytest.approx(
        6000.0
    )

def test_option_position_market_value_rejects_negative_price():

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp(
            "2027-12-17"
        ),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    position = OptionPosition(
        contract=contract,
        quantity=2,
        average_cost=25.50,
    )

    with pytest.raises(
        ValueError,
        match="current_price must not be negative",
    ):
        position.market_value(
            current_price=-1.0
        )

def test_option_position_unrealized_pnl():

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp(
            "2027-12-17"
        ),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    position = OptionPosition(
        contract=contract,
        quantity=2,
        average_cost=25.50,
    )

    pnl = position.unrealized_pnl(
        current_price=30.0
    )

    assert pnl == pytest.approx(
        900.0
    )

def test_option_position_return_pct():

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp(
            "2027-12-17"
        ),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    position = OptionPosition(
        contract=contract,
        quantity=2,
        average_cost=25.50,
    )

    return_pct = position.return_pct(
        current_price=31.875
    )

    assert return_pct == pytest.approx(
        0.25
    )

def test_option_position_return_pct_is_zero_when_empty():

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    position = OptionPosition(
        contract=contract,
        quantity=0,
        average_cost=0.0,
    )

    assert position.return_pct(
        current_price=30.0
    ) == pytest.approx(0.0)

def test_option_position_buy_opens_position():

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    position = OptionPosition(
        contract=contract,
        quantity=0,
        average_cost=0.0,
    )

    position.buy(
        quantity=2,
        price=25.50,
    )

    assert position.quantity == 2
    assert position.average_cost == pytest.approx(
        25.50
    )

def test_option_position_buy_updates_weighted_average_cost():

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    position = OptionPosition(
        contract=contract,
        quantity=2,
        average_cost=20.0,
    )

    position.buy(
        quantity=1,
        price=30.0,
    )

    assert position.quantity == 3
    assert position.average_cost == pytest.approx(
        23.3333333333
    )

def test_option_position_buy_rejects_non_positive_quantity():

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    position = OptionPosition(
        contract=contract,
        quantity=0,
        average_cost=0.0,
    )

    with pytest.raises(
        ValueError,
        match="quantity must be positive",
    ):
        position.buy(
            quantity=0,
            price=25.0,
        )

def test_option_position_buy_rejects_non_positive_price():

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    position = OptionPosition(
        contract=contract,
        quantity=0,
        average_cost=0.0,
    )

    with pytest.raises(
        ValueError,
        match="price must be positive",
    ):
        position.buy(
            quantity=1,
            price=0.0,
        )

def test_option_position_partial_sell_returns_realized_pnl():

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    position = OptionPosition(
        contract=contract,
        quantity=3,
        average_cost=20.0,
    )

    realized_pnl = position.sell(
        quantity=1,
        price=30.0,
    )

    assert realized_pnl == pytest.approx(
        1000.0
    )

    assert position.quantity == 2

    assert position.average_cost == pytest.approx(
        20.0
    )

def test_option_position_full_sell_resets_position():

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    position = OptionPosition(
        contract=contract,
        quantity=2,
        average_cost=20.0,
    )

    realized_pnl = position.sell(
        quantity=2,
        price=30.0,
    )

    assert realized_pnl == pytest.approx(
        2000.0
    )

    assert position.quantity == 0

    assert position.average_cost == pytest.approx(
        0.0
    )

def test_option_position_sell_rejects_oversell():

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp(
            "2027-12-17"
        ),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    position = OptionPosition(
        contract=contract,
        quantity=2,
        average_cost=20.0,
    )

    with pytest.raises(
        ValueError,
        match="quantity exceeds current position",
    ):
        position.sell(
            quantity=3,
            price=30.0,
        )

def test_option_position_sell_rejects_oversell():

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    position = OptionPosition(
        contract=contract,
        quantity=2,
        average_cost=20.0,
    )

    with pytest.raises(
        ValueError,
        match="quantity exceeds current position",
    ):
        position.sell(
            quantity=3,
            price=30.0,
        )

def test_option_position_sell_rejects_non_positive_quantity():

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    position = OptionPosition(
        contract=contract,
        quantity=2,
        average_cost=20.0,
    )

    with pytest.raises(
        ValueError,
        match="quantity must be positive",
    ):
        position.sell(
            quantity=0,
            price=30.0,
        )

def test_option_position_sell_rejects_non_positive_price():

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    position = OptionPosition(
        contract=contract,
        quantity=2,
        average_cost=20.0,
    )

    with pytest.raises(
        ValueError,
        match="price must be positive",
    ):
        position.sell(
            quantity=1,
            price=0.0,
        )