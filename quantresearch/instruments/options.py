from dataclasses import dataclass
from enum import Enum

import pandas as pd


class OptionType(Enum):
    CALL = "CALL"
    PUT = "PUT"


@dataclass(frozen=True)
class OptionContract:
    underlying: str
    expiration: pd.Timestamp
    strike: float
    option_type: OptionType
    multiplier: int = 100

    def __post_init__(self):

        if self.strike <= 0:
            raise ValueError(
                "strike must be positive"
            )

        if self.multiplier <= 0:
            raise ValueError(
                "multiplier must be positive"
            )

        if not self.underlying.strip():
            raise ValueError(
                "underlying must not be empty"
            )

def parse_option_contract_symbol(
    contract_symbol: str,
) -> OptionContract:

    if len(contract_symbol) <= 15:
        raise ValueError(
            "Invalid option contract symbol."
        )

    underlying = contract_symbol[:-15]

    expiration_text = contract_symbol[-15:-9]
    option_type_text = contract_symbol[-9]
    strike_text = contract_symbol[-8:]

    try:
        expiration = pd.Timestamp(
            "20"
            + expiration_text[:2]
            + "-"
            + expiration_text[2:4]
            + "-"
            + expiration_text[4:6]
        )

    except ValueError as exc:
        raise ValueError(
            "Invalid option expiration."
        ) from exc

    if option_type_text == "C":
        option_type = OptionType.CALL

    elif option_type_text == "P":
        option_type = OptionType.PUT

    else:
        raise ValueError(
            f"Invalid option type: {option_type_text}"
        )

    try:
        strike = int(
            strike_text
        ) / 1000

    except ValueError as exc:
        raise ValueError(
            "Invalid option strike."
        ) from exc

    return OptionContract(
        underlying=underlying,
        expiration=expiration,
        strike=strike,
        option_type=option_type,
    )