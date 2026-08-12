from dataclasses import dataclass

import pandas as pd

from quantresearch.instruments.options import OptionContract


@dataclass(frozen=True)
class HistoricalOptionQuote:
    contract: OptionContract
    timestamp: pd.Timestamp
    bid: float
    ask: float

    def __post_init__(self):
        if self.bid < 0:
            raise ValueError(
                "bid cannot be negative"
            )

        if self.ask < 0:
            raise ValueError(
                "ask cannot be negative"
            )