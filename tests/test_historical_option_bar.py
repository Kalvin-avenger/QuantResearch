# tests/test_historical_option_bar.py

import pandas as pd

from quantresearch.data.historical_option_bar import (
    HistoricalOptionBar,
)
from quantresearch.instruments.options import (
    OptionContract,
    OptionType,
)


def test_historical_option_bar_stores_ohlcv():

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    bar = HistoricalOptionBar(
        contract=contract,
        timestamp=pd.Timestamp("2026-01-02"),
        open=50.0,
        high=53.0,
        low=49.0,
        close=52.0,
        volume=1234.0,
    )

    assert bar.contract == contract
    assert bar.timestamp == pd.Timestamp("2026-01-02")
    assert bar.open == 50.0
    assert bar.high == 53.0
    assert bar.low == 49.0
    assert bar.close == 52.0
    assert bar.volume == 1234.0