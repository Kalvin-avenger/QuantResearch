from typing import Protocol

from quantresearch.instruments.options import OptionContract


class ExecutableOptionQuote(Protocol):
    contract: OptionContract
    bid: float
    ask: float