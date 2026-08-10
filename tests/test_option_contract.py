import pandas as pd

from quantresearch.instruments.options import (
    OptionContract,
    OptionType,
)


def test_option_contract_stores_contract_terms():

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp(
            "2027-12-17"
        ),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    assert contract.underlying == "SPY"

    assert contract.expiration == pd.Timestamp(
        "2027-12-17"
    )

    assert contract.strike == 500.0

    assert contract.option_type == OptionType.CALL

    assert contract.multiplier == 100

import pytest


def test_option_contract_rejects_non_positive_strike():

    with pytest.raises(
        ValueError,
        match="strike must be positive",
    ):
        OptionContract(
            underlying="SPY",
            expiration=pd.Timestamp(
                "2027-12-17"
            ),
            strike=0.0,
            option_type=OptionType.CALL,
        )

def test_option_contract_rejects_non_positive_multiplier():

    with pytest.raises(
        ValueError,
        match="multiplier must be positive",
    ):
        OptionContract(
            underlying="SPY",
            expiration=pd.Timestamp(
                "2027-12-17"
            ),
            strike=500.0,
            option_type=OptionType.CALL,
            multiplier=0,
        )

def test_option_contract_rejects_empty_underlying():

    with pytest.raises(
        ValueError,
        match="underlying must not be empty",
    ):
        OptionContract(
            underlying="",
            expiration=pd.Timestamp(
                "2027-12-17"
            ),
            strike=500.0,
            option_type=OptionType.CALL,
        )

from quantresearch.instruments.options import (
    OptionContract,
    OptionType,
    parse_option_contract_symbol,
)


def test_parse_call_option_contract_symbol():

    contract = parse_option_contract_symbol(
        "SPY271217C00500000"
    )

    assert contract.underlying == "SPY"
    assert contract.expiration == pd.Timestamp(
        "2027-12-17"
    )
    assert contract.option_type == OptionType.CALL
    assert contract.strike == pytest.approx(
        500.0
    )
    assert contract.multiplier == 100

def test_parse_put_option_contract_symbol():

    contract = parse_option_contract_symbol(
        "SPY271217P00500000"
    )

    assert contract.underlying == "SPY"
    assert contract.expiration == pd.Timestamp(
        "2027-12-17"
    )
    assert contract.option_type == OptionType.PUT
    assert contract.strike == pytest.approx(
        500.0
    )

def test_parse_option_contract_symbol_rejects_invalid_option_type():

    with pytest.raises(
        ValueError,
        match="Invalid option type",
    ):
        parse_option_contract_symbol(
            "SPY271217X00500000"
        )

def test_parse_option_contract_symbol_rejects_too_short_symbol():

    with pytest.raises(
        ValueError,
        match="Invalid option contract symbol",
    ):
        parse_option_contract_symbol(
            "SPYC500"
        )

def test_parse_option_contract_symbol_rejects_invalid_expiration():

    with pytest.raises(
        ValueError,
        match="Invalid option expiration",
    ):
        parse_option_contract_symbol(
            "SPY271332C00500000"
        )

def test_parse_option_contract_symbol_rejects_invalid_strike():

    with pytest.raises(
        ValueError,
        match="Invalid option strike",
    ):
        parse_option_contract_symbol(
            "SPY271217C00ABC000"
        )

