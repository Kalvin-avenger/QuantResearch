def calculate_option_quantity(
    cash: float,
    option_price: float,
    multiplier: int,
    allocation_fraction: float,
) -> int:

    if option_price <= 0:
        raise ValueError(
            "option_price must be positive"
        )

    if multiplier <= 0:
        raise ValueError(
            "multiplier must be positive"
        )

    if not 0 < allocation_fraction <= 1:
        raise ValueError(
            "allocation_fraction must be greater than 0 and at most 1"
        )

    budget = (
        cash
        * allocation_fraction
    )

    contract_cost = (
        option_price
        * multiplier
    )

    return int(
        budget // contract_cost
    )