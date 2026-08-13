from dataclasses import dataclass

import pandas as pd

from quantresearch.instruments.options import (
    OptionContract,
)


@dataclass(frozen=True)
class HistoricalOptionBar:
    contract: OptionContract
    timestamp: pd.Timestamp
    open: float
    high: float
    low: float
    close: float
    volume: float

    def __post_init__(self):

        if self.open < 0:
            raise ValueError(
                "open cannot be negative"
            )

        if self.high < 0:
            raise ValueError(
                "high cannot be negative"
            )

        if self.low < 0:
            raise ValueError(
                "low cannot be negative"
            )

        if self.close < 0:
            raise ValueError(
                "close cannot be negative"
            )

        if self.volume < 0:
            raise ValueError(
                "volume cannot be negative"
            )

        if self.high < self.low:
            raise ValueError(
                "high cannot be less than low"
            )