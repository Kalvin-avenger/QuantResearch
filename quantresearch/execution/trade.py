from dataclasses import dataclass
import pandas as pd

from quantresearch.signals import Signal


@dataclass(frozen=True)
class Trade:
    timestamp: pd.Timestamp

    action: Signal

    quantity: int

    price: float

    