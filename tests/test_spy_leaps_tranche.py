from quantresearch.strategy.spy_leaps_tranche import (
    SpyLeapsTranche,
)


def test_spy_leaps_tranche_initial_state():
    tranche = SpyLeapsTranche(level=0)

    assert tranche.level == 0
    assert tranche.equity_deployed is False
    assert tranche.option_deployed is False
    assert tranche.option_closed is False


def test_spy_leaps_tranche_can_mark_both_legs_deployed():
    tranche = SpyLeapsTranche(level=1)

    tranche.deploy_equity()
    tranche.deploy_option()

    assert tranche.equity_deployed is True
    assert tranche.option_deployed is True


def test_spy_leaps_tranche_option_can_close_independently():
    tranche = SpyLeapsTranche(level=1)

    tranche.deploy_equity()
    tranche.deploy_option()

    tranche.close_option()

    assert tranche.equity_deployed is True
    assert tranche.option_deployed is False
    assert tranche.option_closed is True

import pandas as pd

from quantresearch.instruments.options import (
    OptionContract,
    OptionType,
)


def test_tranche_stores_deployed_option_contract():

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2028-01-21"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    tranche = SpyLeapsTranche(
        level=1,
    )

    tranche.deploy_option(
        contract=contract,
    )

    assert tranche.option_deployed is True
    assert tranche.option_closed is False
    assert tranche.option_contract == contract

def test_closing_option_preserves_contract_history():

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2028-01-21"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    tranche = SpyLeapsTranche(
        level=1,
    )

    tranche.deploy_option(
        contract=contract,
    )

    tranche.close_option()

    assert tranche.option_deployed is False
    assert tranche.option_closed is True

    # Keep the contract for lifecycle/history.
    assert tranche.option_contract == contract