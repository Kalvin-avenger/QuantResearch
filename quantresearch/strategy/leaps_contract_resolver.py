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
        tradability_provider=None,
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

        self.tradability_provider = (
            tradability_provider
        )

    def _ranking_key(
        self,
        item,
        underlying_price: float,
    ):
        contract, days_to_expiration = item

        return (
            abs(
                days_to_expiration
                - self.target_days_to_expiration
            ),
            abs(
                contract.strike
                - underlying_price
            ),
            pd.Timestamp(
                contract.expiration
            ),
            contract.strike,
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

        ranked = sorted(
            eligible,
            key=lambda item: (
                self._ranking_key(
                    item=item,
                    underlying_price=(
                        underlying_price
                    ),
                )
            ),
        )

        # -------------------------------------------------
        # Legacy behavior
        #
        # If no tradability provider is configured,
        # preserve the existing selection semantics.
        # -------------------------------------------------

        if self.tradability_provider is None:
            return ranked[0][0]

        # -------------------------------------------------
        # Historical tradability filtering
        #
        # Candidates remain ordered using exactly the same
        # DTE / ATM ranking logic as before.
        #
        # We simply skip candidates that do not have a
        # market bar on the requested entry date.
        # -------------------------------------------------

        for (
            contract,
            _,
        ) in ranked:

            if self.tradability_provider.has_bar(
                timestamp=timestamp,
                contract=contract,
            ):
                return contract

        raise ValueError(
            "No tradable LEAPS contracts found"
        )