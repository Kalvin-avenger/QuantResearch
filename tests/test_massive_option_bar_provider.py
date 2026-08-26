import pandas as pd

from quantresearch.data.providers.massive_options import (
    MassiveHistoricalOptionBarProvider,
)
from quantresearch.instruments.options import (
    OptionContract,
    OptionType,
)

from quantresearch.strategy.leaps_contract_resolver import (
    DynamicLeapsContractResolver
)


def test_massive_option_bar_provider_returns_historical_bars():

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-03-19"),
        strike=505.0,
        option_type=OptionType.CALL,
    )

    class FakeClient:

        def __init__(self):
            self.calls = []

        def get_aggregate_bars(
            self,
            ticker,
            multiplier,
            timespan,
            start_date,
            end_date,
        ):

            self.calls.append(
                {
                    "ticker": ticker,
                    "multiplier": multiplier,
                    "timespan": timespan,
                    "start_date": start_date,
                    "end_date": end_date,
                }
            )

            return [
                {
                    "o": 28.0,
                    "h": 31.0,
                    "l": 27.5,
                    "c": 30.0,
                    "v": 1250,
                    "vw": 29.4,
                    "t": pd.Timestamp(
                        "2026-01-02"
                    ).value // 1_000_000,
                },
                {
                    "o": 30.5,
                    "h": 33.0,
                    "l": 29.0,
                    "c": 32.0,
                    "v": 1400,
                    "vw": 31.2,
                    "t": pd.Timestamp(
                        "2026-01-05"
                    ).value // 1_000_000,
                },
            ]

    client = FakeClient()

    provider = MassiveHistoricalOptionBarProvider(
        client=client,
    )

    bars = provider.get_bars(
        contract=contract,
        start_date=pd.Timestamp("2026-01-02"),
        end_date=pd.Timestamp("2026-01-05"),
    )

    assert len(bars) == 2

    assert bars[0].contract == contract
    assert bars[0].timestamp == pd.Timestamp("2026-01-02")
    assert bars[0].close == 30.0

    assert bars[1].contract == contract
    assert bars[1].timestamp == pd.Timestamp("2026-01-05")
    assert bars[1].close == 32.0

    assert client.calls == [
        {
            "ticker": "O:SPY270319C00505000",
            "multiplier": 1,
            "timespan": "day",
            "start_date": pd.Timestamp("2026-01-02"),
            "end_date": pd.Timestamp("2026-01-05"),
        }
    ]

def test_massive_option_bar_provider_caches_same_day_contract():
    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-03-19"),
        strike=680.0,
        option_type=OptionType.CALL,
    )

    raw_bar = {
        "o": 67.63,
        "h": 67.63,
        "l": 66.95,
        "c": 66.95,
        "v": 9,
        "vw": 67.4644,
        "t": int(
            pd.Timestamp(
                "2026-01-02",
                tz="UTC",
            ).timestamp()
            * 1000
        ),
    }

    class FakeClient:
        def __init__(self):
            self.calls = 0

        def get_aggregate_bars(
            self,
            ticker,
            start_date,
            end_date,
            multiplier,
            timespan,
        ):
            self.calls += 1

            return [raw_bar]

    client = FakeClient()

    provider = MassiveHistoricalOptionBarProvider(
        client=client,
    )

    timestamp = pd.Timestamp(
        "2026-01-02"
    )

    first = provider.get_bar(
        timestamp=timestamp,
        contract=contract,
    )

    second = provider.get_bar(
        timestamp=timestamp,
        contract=contract,
    )

    assert client.calls == 1
    assert first == second

def test_massive_option_bar_provider_preload_populates_cache():
    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-03-19"),
        strike=680.0,
        option_type=OptionType.CALL,
    )

    raw_bars = [
        {
            "o": 67.63,
            "h": 67.63,
            "l": 66.95,
            "c": 66.95,
            "v": 9,
            "vw": 67.4644,
            "t": int(
                pd.Timestamp(
                    "2026-01-02",
                    tz="UTC",
                ).timestamp()
                * 1000
            ),
        },
        {
            "o": 68.0,
            "h": 70.0,
            "l": 67.5,
            "c": 69.5,
            "v": 20,
            "vw": 69.0,
            "t": int(
                pd.Timestamp(
                    "2026-01-05",
                    tz="UTC",
                ).timestamp()
                * 1000
            ),
        },
    ]

    class FakeClient:
        def __init__(self):
            self.calls = 0

        def get_aggregate_bars(
            self,
            ticker,
            start_date,
            end_date,
            multiplier,
            timespan,
        ):
            self.calls += 1

            assert start_date == pd.Timestamp(
                "2026-01-02"
            )

            assert end_date == pd.Timestamp(
                "2026-01-05"
            )

            return raw_bars

    client = FakeClient()

    provider = MassiveHistoricalOptionBarProvider(
        client=client,
    )

    provider.preload(
        contract=contract,
        start_date=pd.Timestamp(
            "2026-01-02"
        ),
        end_date=pd.Timestamp(
            "2026-01-05"
        ),
    )

    first = provider.get_bar(
        timestamp=pd.Timestamp(
            "2026-01-02"
        ),
        contract=contract,
    )

    second = provider.get_bar(
        timestamp=pd.Timestamp(
            "2026-01-05"
        ),
        contract=contract,
    )

    assert client.calls == 1

    assert first.close == 66.95
    assert second.close == 69.5

def test_massive_option_bar_provider_auto_loads_configured_range():
    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-03-19"),
        strike=685.0,
        option_type=OptionType.CALL,
    )

    raw_bars = [
        {
            "o": 63.0,
            "h": 64.0,
            "l": 62.0,
            "c": 63.19,
            "t": int(
                pd.Timestamp(
                    "2026-01-02",
                    tz="UTC",
                ).timestamp()
                * 1000
            ),
        },
        {
            "o": 65.0,
            "h": 67.0,
            "l": 64.0,
            "c": 66.0,
            "t": int(
                pd.Timestamp(
                    "2026-01-05",
                    tz="UTC",
                ).timestamp()
                * 1000
            ),
        },
    ]

    class FakeClient:
        def __init__(self):
            self.calls = []

        def get_aggregate_bars(
            self,
            ticker,
            start_date,
            end_date,
            multiplier,
            timespan,
        ):
            self.calls.append(
                (
                    pd.Timestamp(start_date),
                    pd.Timestamp(end_date),
                )
            )

            return raw_bars

    client = FakeClient()

    provider = MassiveHistoricalOptionBarProvider(
        client=client,
    )

    provider.set_backtest_range(
        start_date=pd.Timestamp(
            "2026-01-02"
        ),
        end_date=pd.Timestamp(
            "2026-01-31"
        ),
    )

    # First request is a cache miss.
    first = provider.get_bar(
        timestamp=pd.Timestamp(
            "2026-01-02"
        ),
        contract=contract,
    )

    # This should already have been loaded
    # by the first range request.
    second = provider.get_bar(
        timestamp=pd.Timestamp(
            "2026-01-05"
        ),
        contract=contract,
    )

    assert len(client.calls) == 1

    assert client.calls[0] == (
        pd.Timestamp("2026-01-02"),
        pd.Timestamp("2026-01-31"),
    )

    assert first.close == 63.19
    assert second.close == 66.0

def test_massive_option_bar_provider_has_bar_returns_true():
    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2026-03-20"),
        strike=585.0,
        option_type=OptionType.CALL,
    )

    raw_bar = {
        "o": 58.0,
        "h": 60.0,
        "l": 57.0,
        "c": 59.0,
        "v": 2,
        "vw": 58.8,
        "t": int(
            pd.Timestamp(
                "2025-01-02",
                tz="UTC",
            ).timestamp()
            * 1000
        ),
    }

    class FakeClient:
        def __init__(self):
            self.calls = 0

        def get_aggregate_bars(
            self,
            ticker,
            start_date,
            end_date,
            multiplier,
            timespan,
        ):
            self.calls += 1

            assert start_date == pd.Timestamp(
                "2025-01-02"
            )

            assert end_date == pd.Timestamp(
                "2025-01-02"
            )

            return [raw_bar]

    client = FakeClient()

    provider = MassiveHistoricalOptionBarProvider(
        client=client,
    )

    result = provider.has_bar(
        timestamp=pd.Timestamp(
            "2025-01-02"
        ),
        contract=contract,
    )

    assert result is True
    assert client.calls == 1

def test_massive_option_bar_provider_has_bar_returns_false():
    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2026-03-20"),
        strike=585.0,
        option_type=OptionType.CALL,
    )

    class FakeClient:
        def __init__(self):
            self.calls = 0

        def get_aggregate_bars(
            self,
            ticker,
            start_date,
            end_date,
            multiplier,
            timespan,
        ):
            self.calls += 1
            return []

    client = FakeClient()

    provider = MassiveHistoricalOptionBarProvider(
        client=client,
    )

    result = provider.has_bar(
        timestamp=pd.Timestamp(
            "2025-01-02"
        ),
        contract=contract,
    )

    assert result is False
    assert client.calls == 1

def test_dynamic_resolver_skips_contract_without_entry_bar():
    timestamp = pd.Timestamp(
        "2025-01-02"
    )

    unavailable = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp(
            "2026-03-20"
        ),
        strike=585.0,
        option_type=OptionType.CALL,
    )

    available = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp(
            "2026-03-20"
        ),
        strike=580.0,
        option_type=OptionType.CALL,
    )

    class FakeUniverseProvider:
        def get_contracts(
            self,
            timestamp,
            expiration_date_gte=None,
            expiration_date_lte=None,
        ):
            return [
                unavailable,
                available,
            ]

    class FakeTradabilityProvider:
        def __init__(self):
            self.checked = []

        def has_bar(
            self,
            timestamp,
            contract,
        ):
            self.checked.append(
                contract
            )

            return (
                contract == available
            )

    tradability_provider = (
        FakeTradabilityProvider()
    )

    resolver = DynamicLeapsContractResolver(
        universe_provider=(
            FakeUniverseProvider()
        ),
        min_days_to_expiration=365,
        max_days_to_expiration=548,
        target_days_to_expiration=456,
        tradability_provider=(
            tradability_provider
        ),
    )

    resolved = resolver.resolve(
        timestamp=timestamp,
        underlying_price=585.0,
    )

    assert resolved == available

    assert tradability_provider.checked == [
        unavailable,
        available,
    ]

def test_dynamic_resolver_without_tradability_provider_preserves_ranking():
    timestamp = pd.Timestamp(
        "2025-01-02"
    )

    best = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp(
            "2026-03-20"
        ),
        strike=585.0,
        option_type=OptionType.CALL,
    )

    second_best = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp(
            "2026-03-20"
        ),
        strike=580.0,
        option_type=OptionType.CALL,
    )

    resolver = DynamicLeapsContractResolver(
        contracts=[
            second_best,
            best,
        ],
        min_days_to_expiration=365,
        max_days_to_expiration=548,
        target_days_to_expiration=456,
    )

    resolved = resolver.resolve(
        timestamp=timestamp,
        underlying_price=585.0,
    )

    assert resolved == best