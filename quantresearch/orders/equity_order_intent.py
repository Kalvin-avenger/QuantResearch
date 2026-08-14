from dataclasses import dataclass

from quantresearch.signals import Signal


@dataclass(frozen=True)
class EquityOrderIntent:
    action: Signal
    allocation_fraction: float