import pandas as pd
import pytest

from quantresearch.instruments.options import (
    OptionContract,
    OptionType,
)

from quantresearch.data.option_contract_universe_provider import (
    OptionContractUniverseProvider,
    StaticOptionContractUniverseProvider,
)

from quantresearch.strategy.leaps_contract_resolver import (
    DynamicLeapsContractResolver
)


def test_option_contract_universe_provider_is_abstract():

    with pytest.raises(TypeError):
        OptionContractUniverseProvider()


def test_static_option_contract_universe_provider_returns_contracts():

    contract_1 = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-04-16"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    contract_2 = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-04-16"),
        strike=510.0,
        option_type=OptionType.CALL,
    )

    provider = StaticOptionContractUniverseProvider(
        contracts=[
            contract_1,
            contract_2,
        ],
    )

    contracts = provider.get_contracts(
        timestamp=pd.Timestamp("2026-01-02"),
    )

    assert contracts == [
        contract_1,
        contract_2,
    ]

def test_static_provider_returns_copy():

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-04-16"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    provider = StaticOptionContractUniverseProvider(
        contracts=[contract],
    )

    first = provider.get_contracts(
        timestamp=pd.Timestamp("2026-01-02"),
    )

    first.clear()

    second = provider.get_contracts(
        timestamp=pd.Timestamp("2026-01-03"),
    )

    assert second == [contract]

def test_dynamic_resolver_requests_contracts_for_timestamp():

    calls = []

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-04-16"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    class RecordingProvider:

        def get_contracts(
            self,
            timestamp,
        ):

            calls.append(
                timestamp
            )

            return [contract]

    resolver = DynamicLeapsContractResolver(
        universe_provider=RecordingProvider(),
    )

    timestamp = pd.Timestamp(
        "2026-01-02"
    )

    resolved = resolver.resolve(
        timestamp=timestamp,
        underlying_price=500.0,
    )

    assert resolved == contract

    assert calls == [
        timestamp
    ]

def test_dynamic_resolver_can_select_different_contracts_on_different_dates():

    first_contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-04-16"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    second_contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2028-04-21"),
        strike=550.0,
        option_type=OptionType.CALL,
    )

    class DateAwareProvider:

        def get_contracts(
            self,
            timestamp,
        ):

            timestamp = pd.Timestamp(
                timestamp
            )

            if timestamp.year == 2026:
                return [
                    first_contract
                ]

            return [
                second_contract
            ]

    resolver = DynamicLeapsContractResolver(
        universe_provider=DateAwareProvider(),
    )

    first = resolver.resolve(
        timestamp=pd.Timestamp(
            "2026-01-02"
        ),
        underlying_price=500.0,
    )

    second = resolver.resolve(
        timestamp=pd.Timestamp(
            "2027-01-04"
        ),
        underlying_price=550.0,
    )

    assert first == first_contract
    assert second == second_contract

def test_static_option_contract_universe_provider_filters_expiration_range():

    early = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2026-12-18"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    middle = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-04-16"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    late = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-08-20"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    provider = StaticOptionContractUniverseProvider(
        contracts=[
            early,
            middle,
            late,
        ],
    )

    contracts = provider.get_contracts(
        timestamp=pd.Timestamp("2026-01-02"),
        expiration_date_gte=pd.Timestamp(
            "2027-01-02"
        ),
        expiration_date_lte=pd.Timestamp(
            "2027-07-04"
        ),
    )

    assert contracts == [
        middle
    ]