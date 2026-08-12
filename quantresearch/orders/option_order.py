from dataclasses import dataclass

from quantresearch.instruments.options import OptionContract
from quantresearch.signals import Signal




@dataclass(frozen=True)
class OptionOrder:
    contract: OptionContract
    action: Signal
    quantity: int

    def __post_init__(self):
        if self.quantity <= 0:
            raise ValueError("quantity must be positive")

        if self.action not in (Signal.BUY, Signal.SELL):
            raise ValueError("action must be BUY or SELL")