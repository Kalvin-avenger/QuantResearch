from dataclasses import dataclass

import pandas as pd

from quantresearch.instruments.options import (
    OptionContract,
)


@dataclass(frozen=True)
class OptionQuote:
    contract: OptionContract
    last_trade_date: pd.Timestamp
    last_price: float
    bid: float
    ask: float
    volume: float | None
    open_interest: float | None
    implied_volatility: float
    in_the_money: bool


@dataclass(frozen=True)
class OptionChain:
    calls: list[OptionQuote]
    puts: list[OptionQuote]