from abc import ABC, abstractmethod

import pandas as pd

from quantresearch.instruments.options import (
    OptionType,
)

from quantresearch.data.option_contract_universe_provider import (
    StaticOptionContractUniverseProvider,
)


class LeapsContractResolver(ABC):

    @abstractmethod
    def resolve(
        self,
        timestamp,
        underlying_price: float,
    ):
        raise NotImplementedError


class FixedLeapsContractResolver(
    LeapsContractResolver
):

    def __init__(
        self,
        contract,
    ):
        self.contract = contract

    def resolve(
        self,
        timestamp,
        underlying_price: float,
    ):
        return self.contract


class DynamicLeapsContractResolver(
    LeapsContractResolver
):

    def __init__(
        self,
        contracts=None,
        universe_provider=None,
        min_days_to_expiration: int = 365,
        max_days_to_expiration: int = 548,
        target_days_to_expiration: int = 456,
    ):

        if universe_provider is None:

            if contracts is None:
                raise ValueError(
                    "Either contracts or universe_provider "
                    "must be provided"
                )

            universe_provider = (
                StaticOptionContractUniverseProvider(
                    contracts=contracts,
                )
            )

        self.universe_provider = (
            universe_provider
        )

        self.min_days_to_expiration = (
            min_days_to_expiration
        )

        self.max_days_to_expiration = (
            max_days_to_expiration
        )

        self.target_days_to_expiration = (
            target_days_to_expiration
        )

    def resolve(
        self,
        timestamp,
        underlying_price: float,
    ):

        timestamp = pd.Timestamp(
            timestamp
        )

        minimum_expiration = (
            timestamp
            + pd.Timedelta(
                days=self.min_days_to_expiration
            )
        )

        maximum_expiration = (
            timestamp
            + pd.Timedelta(
                days=self.max_days_to_expiration
            )
        )

        contracts = (
            self.universe_provider.get_contracts(
                timestamp=timestamp,
                expiration_date_gte=minimum_expiration,
                expiration_date_lte=maximum_expiration,
            )
        )

        eligible = []

        for contract in contracts:

            if (
                contract.option_type
                != OptionType.CALL
            ):
                continue

            expiration = pd.Timestamp(
                contract.expiration
            )

            days_to_expiration = (
                expiration - timestamp
            ).days

            if (
                days_to_expiration
                < self.min_days_to_expiration
            ):
                continue

            if (
                days_to_expiration
                > self.max_days_to_expiration
            ):
                continue

            eligible.append(
                (
                    contract,
                    days_to_expiration,
                )
            )

        if not eligible:
            raise ValueError(
                "No eligible LEAPS contracts found"
            )

        return min(
            eligible,
            key=lambda item: (
                abs(
                    item[1]
                    - self.target_days_to_expiration
                ),
                abs(
                    item[0].strike
                    - underlying_price
                ),
                pd.Timestamp(
                    item[0].expiration
                ),
                item[0].strike,
            ),
        )[0]