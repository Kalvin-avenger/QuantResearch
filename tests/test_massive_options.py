# import pandas as pd

# from quantresearch.instruments.options import (
#     OptionContract,
#     OptionType,
# )

# from quantresearch.data.providers.massive_options import (
#     normalize_massive_option_bar,
# )


# def test_normalize_massive_option_bar():

#     contract = OptionContract(
#         underlying="SPY",
#         expiration=pd.Timestamp("2027-12-17"),
#         strike=500.0,
#         option_type=OptionType.CALL,
#     )

#     raw_bar = {
#         "o": 50.0,
#         "h": 53.0,
#         "l": 49.0,
#         "c": 52.0,
#         "v": 1234.0,
#         "t": 1767312000000,
#     }

#     bar = normalize_massive_option_bar(
#         raw_bar=raw_bar,
#         contract=contract,
#     )

#     assert bar.contract == contract
#     assert bar.open == 50.0
#     assert bar.high == 53.0
#     assert bar.low == 49.0
#     assert bar.close == 52.0
#     assert bar.volume == 1234.0