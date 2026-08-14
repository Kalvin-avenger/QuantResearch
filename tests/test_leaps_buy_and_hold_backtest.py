import pandas as pd

from quantresearch.backtest.engine import BacktestEngine
from quantresearch.data.historical_options import (
    HistoricalOptionDataProvider,
    HistoricalOptionQuote,
)
from quantresearch.instruments.options import (
    OptionContract,
    OptionType,
)
from quantresearch.portfolio.portfolio import Portfolio
from quantresearch.strategy.leaps_buy_and_hold import (
    LeapsBuyAndHoldStrategy,
)


class FakeHistoricalOptionDataProvider(
    HistoricalOptionDataProvider
):

    def __init__(
        self,
        quotes,
    ):
        self.quotes = quotes

    def get_quote(
        self,
        timestamp,
        contract,
    ):
        key = (
            pd.Timestamp(timestamp),
            contract,
        )

        return self.quotes[key]


def test_leaps_strategy_runs_end_to_end_backtest():

    contract_1 = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-01-15"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    contract_2 = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-06-18"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    contract_3 = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-06-18"),
        strike=505.0,
        option_type=OptionType.CALL,
    )

    contracts = [
        contract_1,
        contract_2,
        contract_3,
    ]

    prices = pd.Series(
        [503.0, 510.0, 515.0],
        index=pd.to_datetime(
            [
                "2026-01-02",
                "2026-01-05",
                "2026-01-06",
            ]
        ),
    )

    quotes = {
            (
                pd.Timestamp("2026-01-02"),
                contract_3,
            ): HistoricalOptionQuote(
                contract=contract_3,
                timestamp=pd.Timestamp(
                    "2026-01-02 15:59:00"
                ),
                bid=49.0,
                ask=51.0,
            ),

            (
                pd.Timestamp("2026-01-05"),
                contract_3,
            ): HistoricalOptionQuote(
                contract=contract_3,
                timestamp=pd.Timestamp(
                    "2026-01-05 15:59:00"
                ),
                bid=55.0,
                ask=57.0,
            ),

            (
                pd.Timestamp("2026-01-06"),
                contract_3,
            ): HistoricalOptionQuote(
                contract=contract_3,
                timestamp=pd.Timestamp(
                    "2026-01-06 15:59:00"
                ),
                bid=59.0,
                ask=61.0,
            ),
        }

    provider = FakeHistoricalOptionDataProvider(
        quotes=quotes
    )

    strategy = LeapsBuyAndHoldStrategy(
        contracts=contracts,
        allocation_fraction=0.25,
        min_months=12,
        max_months=18,
    )

    portfolio = Portfolio(
        initial_cash=100_000
    )

    engine = BacktestEngine()

    result = engine.run(
        prices=prices,
        strategy=strategy,
        portfolio=portfolio,
        option_data_provider=provider,
    )

    assert contract_3 in result.portfolio.option_positions

    position = result.portfolio.option_positions[
        contract_3
    ]

    assert position.quantity == 4
    assert position.average_cost == 51.0
    assert result.portfolio.cash == 79_600

def test_leaps_strategy_uses_allocation_fraction_end_to_end():

    contract_1 = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-01-15"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    contract_2 = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-06-18"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    contract_3 = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-06-18"),
        strike=505.0,
        option_type=OptionType.CALL,
    )

    contracts = [
        contract_1,
        contract_2,
        contract_3,
    ]

    prices = pd.Series(
        [503.0],
        index=pd.to_datetime(
            [
                "2026-01-02",
            ]
        ),
    )

    quotes = {
        (
            pd.Timestamp("2026-01-02"),
            contract_3,
        ): HistoricalOptionQuote(
            contract=contract_3,
            timestamp=pd.Timestamp(
                "2026-01-02 15:59:00"
            ),
            bid=49.0,
            ask=51.0,
        ),
    }

    provider = FakeHistoricalOptionDataProvider(
        quotes=quotes
    )

    strategy = LeapsBuyAndHoldStrategy(
        contracts=contracts,
        allocation_fraction=0.25,
        min_months=12,
        max_months=18,
    )

    portfolio = Portfolio(
        initial_cash=100_000
    )

    engine = BacktestEngine()

    result = engine.run(
        prices=prices,
        strategy=strategy,
        portfolio=portfolio,
        option_data_provider=provider,
    )

    position = result.portfolio.option_positions[
        contract_3
    ]

    assert position.quantity == 4
    assert position.average_cost == 51.0

    assert result.portfolio.cash == 79_600