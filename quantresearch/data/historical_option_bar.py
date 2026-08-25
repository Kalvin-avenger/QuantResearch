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

    volume: float | None = None
    vwap: float | None = None

    def __post_init__(
        self,
    ):

        if self.open < 0:
            raise ValueError(
                "open must be non-negative"
            )

        if self.high < 0:
            raise ValueError(
                "high must be non-negative"
            )

        if self.low < 0:
            raise ValueError(
                "low must be non-negative"
            )

        if self.close < 0:
            raise ValueError(
                "close must be non-negative"
            )