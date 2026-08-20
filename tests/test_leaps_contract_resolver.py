import pandas as pd
import pytest

from quantresearch.instruments.options import (
    OptionContract,
    OptionType,
)

from quantresearch.strategy.leaps_contract_resolver import (
    LeapsContractResolver,
    FixedLeapsContractResolver,
    DynamicLeapsContractResolver,
)


def test_leaps_contract_resolver_is_abstract():

    with pytest.raises(TypeError):
        LeapsContractResolver()


def test_fixed_leaps_contract_resolver_returns_configured_contract():

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    resolver = FixedLeapsContractResolver(
        contract=contract,
    )

    resolved = resolver.resolve(
        timestamp=pd.Timestamp("2026-01-02"),
        underlying_price=500.0,
    )

    assert resolved == contract


def test_fixed_resolver_returns_same_contract_for_different_dates():

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    resolver = FixedLeapsContractResolver(
        contract=contract,
    )

    first = resolver.resolve(
        timestamp=pd.Timestamp("2026-01-02"),
        underlying_price=500.0,
    )

    second = resolver.resolve(
        timestamp=pd.Timestamp("2027-01-02"),
        underlying_price=550.0,
    )

    assert first == contract
    assert second == contract

def test_dynamic_resolver_selects_call_contract():

    timestamp = pd.Timestamp(
        "2026-01-02"
    )

    call_contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp(
            "2027-04-16"
        ),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    put_contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp(
            "2027-04-16"
        ),
        strike=500.0,
        option_type=OptionType.PUT,
    )

    resolver = DynamicLeapsContractResolver(
        contracts=[
            put_contract,
            call_contract,
        ],
    )

    resolved = resolver.resolve(
        timestamp=timestamp,
        underlying_price=500.0,
    )

    assert resolved == call_contract

def test_dynamic_resolver_selects_call_contract():

    timestamp = pd.Timestamp(
        "2026-01-02"
    )

    call_contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp(
            "2027-04-16"
        ),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    put_contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp(
            "2027-04-16"
        ),
        strike=500.0,
        option_type=OptionType.PUT,
    )

    resolver = DynamicLeapsContractResolver(
        contracts=[
            put_contract,
            call_contract,
        ],
    )

    resolved = resolver.resolve(
        timestamp=timestamp,
        underlying_price=500.0,
    )

    assert resolved == call_contract

def test_dynamic_resolver_filters_contracts_by_dte():

    timestamp = pd.Timestamp(
        "2026-01-02"
    )

    too_short = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp(
            "2026-06-19"
        ),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    eligible = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp(
            "2027-04-16"
        ),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    too_long = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp(
            "2028-01-21"
        ),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    resolver = DynamicLeapsContractResolver(
        contracts=[
            too_short,
            too_long,
            eligible,
        ],
    )

    resolved = resolver.resolve(
        timestamp=timestamp,
        underlying_price=500.0,
    )

    assert resolved == eligible

def test_dynamic_resolver_prefers_expiration_nearest_target_dte():

    timestamp = pd.Timestamp(
        "2026-01-02"
    )

    shorter = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp(
            "2027-01-15"
        ),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    target = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp(
            "2027-04-16"
        ),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    longer = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp(
            "2027-06-18"
        ),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    resolver = DynamicLeapsContractResolver(
        contracts=[
            shorter,
            longer,
            target,
        ],
    )

    resolved = resolver.resolve(
        timestamp=timestamp,
        underlying_price=500.0,
    )

    assert resolved == target

def test_dynamic_resolver_selects_nearest_atm_strike():

    timestamp = pd.Timestamp(
        "2026-01-02"
    )

    contract_490 = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp(
            "2027-04-16"
        ),
        strike=490.0,
        option_type=OptionType.CALL,
    )

    contract_500 = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp(
            "2027-04-16"
        ),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    contract_510 = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp(
            "2027-04-16"
        ),
        strike=510.0,
        option_type=OptionType.CALL,
    )

    resolver = DynamicLeapsContractResolver(
        contracts=[
            contract_490,
            contract_500,
            contract_510,
        ],
    )

    resolved = resolver.resolve(
        timestamp=timestamp,
        underlying_price=503.0,
    )

    assert resolved == contract_500

def test_dynamic_resolver_raises_when_no_contract_is_eligible():

    timestamp = pd.Timestamp(
        "2026-01-02"
    )

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp(
            "2026-06-19"
        ),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    resolver = DynamicLeapsContractResolver(
        contracts=[
            contract,
        ],
    )

    with pytest.raises(
        ValueError,
        match="No eligible LEAPS contracts found",
    ):
        resolver.resolve(
            timestamp=timestamp,
            underlying_price=500.0,
        )