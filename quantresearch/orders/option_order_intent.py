from dataclasses import dataclass

from quantresearch.instruments.options import OptionContract
from quantresearch.signals import Signal


@dataclass(frozen=True)
class OptionOrderIntent:
    contract: OptionContract
    action: Signal
    allocation_fraction: float
    allocation_base: float | None = None