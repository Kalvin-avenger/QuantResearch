import pandas as pd

from quantresearch.instruments.options import (
    OptionContract,
    OptionType,
)
from quantresearch.strategy.leaps_selector import (
    select_leaps_call,
)


def test_select_leaps_call_returns_nearest_atm_contract():

    as_of = pd.Timestamp("2026-01-02")
    spot_price = 503.0

    contracts = [
        OptionContract(
            underlying="SPY",
            expiration=pd.Timestamp("2026-12-18"),
            strike=500.0,
            option_type=OptionType.CALL,
        ),
        OptionContract(
            underlying="SPY",
            expiration=pd.Timestamp("2027-03-19"),
            strike=500.0,
            option_type=OptionType.CALL,
        ),
        OptionContract(
            underlying="SPY",
            expiration=pd.Timestamp("2027-03-19"),
            strike=505.0,
            option_type=OptionType.CALL,
        ),
        OptionContract(
            underlying="SPY",
            expiration=pd.Timestamp("2027-03-19"),
            strike=510.0,
            option_type=OptionType.CALL,
        ),
    ]

    selected = select_leaps_call(
        contracts=contracts,
        as_of=as_of,
        spot_price=spot_price,
        min_months=12,
        max_months=18,
    )

    assert selected.expiration == pd.Timestamp(
        "2027-03-19"
    )

    assert selected.strike == 505.0

    assert selected.option_type == OptionType.CALL

def test_select_leaps_call_ignores_puts():

    as_of = pd.Timestamp("2026-01-02")
    spot_price = 503.0

    contracts = [
        OptionContract(
            underlying="SPY",
            expiration=pd.Timestamp("2027-03-19"),
            strike=503.0,
            option_type=OptionType.PUT,
        ),
        OptionContract(
            underlying="SPY",
            expiration=pd.Timestamp("2027-03-19"),
            strike=505.0,
            option_type=OptionType.CALL,
        ),
    ]

    selected = select_leaps_call(
        contracts=contracts,
        as_of=as_of,
        spot_price=spot_price,
        min_months=12,
        max_months=18,
    )

    assert selected.option_type == OptionType.CALL
    assert selected.strike == 505.0

import pytest


def test_select_leaps_call_raises_when_no_contract_is_eligible():

    as_of = pd.Timestamp("2026-01-02")
    spot_price = 503.0

    contracts = [
        OptionContract(
            underlying="SPY",
            expiration=pd.Timestamp("2026-06-19"),
            strike=500.0,
            option_type=OptionType.CALL,
        ),
        OptionContract(
            underlying="SPY",
            expiration=pd.Timestamp("2028-01-21"),
            strike=505.0,
            option_type=OptionType.CALL,
        ),
    ]

    with pytest.raises(
        ValueError,
        match="no eligible LEAPS call contracts found",
    ):
        select_leaps_call(
            contracts=contracts,
            as_of=as_of,
            spot_price=spot_price,
            min_months=12,
            max_months=18,
        )

def test_select_leaps_call_prefers_longest_eligible_expiration():

    as_of = pd.Timestamp("2026-01-02")
    spot_price = 503.0

    contracts = [
        OptionContract(
            underlying="SPY",
            expiration=pd.Timestamp("2027-01-15"),
            strike=503.0,
            option_type=OptionType.CALL,
        ),
        OptionContract(
            underlying="SPY",
            expiration=pd.Timestamp("2027-03-19"),
            strike=505.0,
            option_type=OptionType.CALL,
        ),
        OptionContract(
            underlying="SPY",
            expiration=pd.Timestamp("2027-06-18"),
            strike=500.0,
            option_type=OptionType.CALL,
        ),
    ]

    selected = select_leaps_call(
        contracts=contracts,
        as_of=as_of,
        spot_price=spot_price,
        min_months=12,
        max_months=18,
    )

    assert selected.expiration == pd.Timestamp(
        "2027-06-18"
    )

    assert selected.strike == 500.0