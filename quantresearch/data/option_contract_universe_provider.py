from abc import ABC, abstractmethod


class OptionContractUniverseProvider(ABC):

    @abstractmethod
    def get_contracts(
        self,
        timestamp,
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
    ):
        return list(
            self.contracts
        )