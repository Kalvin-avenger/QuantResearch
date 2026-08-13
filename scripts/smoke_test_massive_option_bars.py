import os
import pandas as pd

from quantresearch.instruments.options import (
    OptionContract,
    OptionType,
)
from quantresearch.data.providers.massive_options import (
    MassiveHttpClient,
    format_massive_option_ticker,
)


api_key = "2uXc459WB6k7D0vjwP7FiSCCpLHAUEKH"

client = MassiveHttpClient(
    api_key=api_key,
)

contract = OptionContract(
    underlying="SPY",
    expiration=pd.Timestamp("2027-12-17"),
    strike=500.0,
    option_type=OptionType.CALL,
)

ticker = format_massive_option_ticker(
    contract
)

print("ticker:", ticker)

bars = client.get_aggregate_bars(
    ticker=ticker,
    start_date="2026-01-02",
    end_date="2026-01-09",
    multiplier=1,
    timespan="day",
)

print("number of bars:", len(bars))

for bar in bars[:5]:
    print(bar)