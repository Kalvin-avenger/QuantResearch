import os
import pandas as pd

from quantresearch.instruments.options import (
    OptionContract,
    OptionType,
)
from quantresearch.data.providers.massive_options import (
    MassiveHttpClient,
    MassiveHistoricalOptionDataProvider,
)


api_key = "2uXc459WB6k7D0vjwP7FiSCCpLHAUEKH"

client = MassiveHttpClient(
    api_key=api_key,
)

provider = MassiveHistoricalOptionDataProvider(
    client=client,
)

contract = OptionContract(
    underlying="SPY",
    expiration=pd.Timestamp("2027-12-17"),
    strike=500.0,
    option_type=OptionType.CALL,
)

quotes = provider.get_quotes(
    contract=contract,
    start_date=pd.Timestamp("2026-01-02"),
    end_date=pd.Timestamp("2026-01-02"),
)

print("number of quotes:", len(quotes))

if quotes:
    print("first quote:")
    print(quotes[0])

    print()
    print("last quote:")
    print(quotes[-1])

    print()
    print("last bid:", quotes[-1].bid)
    print("last ask:", quotes[-1].ask)
    print("last timestamp:", quotes[-1].timestamp)
else:
    print("No quotes returned.")