import pandas as pd

from quantresearch.data.providers.massive_options import (
    MassiveHistoricalOptionBarProvider,
)
from quantresearch.instruments.options import (
    OptionContract,
    OptionType,
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