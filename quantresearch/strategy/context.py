from dataclasses import dataclass, field

from quantresearch.instruments.options import (
    OptionContract,
)


@dataclass(frozen=True)
class StrategyContext:
    cash: float
    option_positions: dict
    option_quotes: dict[OptionContract, object] = field(
        default_factory=dict
    )