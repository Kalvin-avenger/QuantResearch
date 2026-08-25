from abc import ABC, abstractmethod

import pandas as pd


class OptionContractUniverseProvider(ABC):

    @abstractmethod
    def get_contracts(
        self,
        timestamp,
        expiration_date_gte=None,
        expiration_date_lte=None,
    ):
        raise NotImplementedError


class StaticOptionContractUniverseProvider(
    OptionContractUniverseProvider
):

    def __init__(
        self,
        contracts,
    ):
        self.contracts = list(
            contracts
        )

    def get_contracts(
        self,
        timestamp,
        expiration_date_gte=None,
        expiration_date_lte=None,
    ):

        contracts = list(
            self.contracts
        )

        if expiration_date_gte is not None:

            minimum_expiration = pd.Timestamp(
                expiration_date_gte
            )

            contracts = [
                contract
                for contract in contracts
                if pd.Timestamp(
                    contract.expiration
                ) >= minimum_expiration
            ]

        if expiration_date_lte is not None:

            maximum_expiration = pd.Timestamp(
                expiration_date_lte
            )

            contracts = [
                contract
                for contract in contracts
                if pd.Timestamp(
                    contract.expiration
                ) <= maximum_expiration
            ]

        return contracts