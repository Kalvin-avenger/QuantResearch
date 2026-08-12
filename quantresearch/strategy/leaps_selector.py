import pandas as pd

from quantresearch.instruments.options import (
    OptionContract,
    OptionType,
)


def select_leaps_call(
    contracts: list[OptionContract],
    as_of: pd.Timestamp,
    spot_price: float,
    min_months: int = 12,
    max_months: int = 18,
) -> OptionContract:

    min_expiration = as_of + pd.DateOffset(
        months=min_months
    )

    max_expiration = as_of + pd.DateOffset(
        months=max_months
    )

    eligible = [
        contract
        for contract in contracts
        if (
            contract.option_type == OptionType.CALL
            and min_expiration
            <= contract.expiration
            <= max_expiration
        )
    ]

    if not eligible:
        raise ValueError(
            "no eligible LEAPS call contracts found"
        )

    latest_expiration = max(
        contract.expiration
        for contract in eligible
    )

    expiration_candidates = [
        contract
        for contract in eligible
        if contract.expiration == latest_expiration
    ]

    return min(
        expiration_candidates,
        key=lambda contract: abs(
            contract.strike - spot_price
        ),
    )