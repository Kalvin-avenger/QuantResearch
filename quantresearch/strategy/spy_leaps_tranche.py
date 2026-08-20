from dataclasses import dataclass


@dataclass
class SpyLeapsTranche:

    level: int

    equity_deployed: bool = False
    option_deployed: bool = False
    option_closed: bool = False

    option_contract: object | None = None

    def deploy_equity(
        self,
    ):
        self.equity_deployed = True

    def deploy_option(
        self,
        contract=None,
    ):
        self.option_deployed = True
        self.option_closed = False

        if contract is not None:
            self.option_contract = contract

    def close_option(
        self,
    ):
        self.option_deployed = False
        self.option_closed = True