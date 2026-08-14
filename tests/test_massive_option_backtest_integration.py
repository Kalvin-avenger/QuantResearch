import pandas as pd

from quantresearch.backtest.engine import BacktestEngine
from quantresearch.data.providers.massive_options import (
    MassiveHistoricalOptionDataProvider,
)
from quantresearch.instruments.options import (
    OptionContract,
    OptionType,
)
from quantresearch.portfolio.portfolio import Portfolio
from quantresearch.strategy.buy_and_hold_option import (
    BuyAndHoldOptionStrategy,
)
import pytest
from quantresearch.data.historical_options import (
    HistoricalOptionQuoteStore,
)

from quantresearch.data.historical_option_quote import (
    HistoricalOptionQuote,
)

def test_massive_option_store_can_drive_backtest_engine():

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    class FakeMassiveClient:

        def get_quotes(
            self,
            ticker,
            start_date,
            end_date,
        ):
            return [
                {
                    "bid_price": 24.5,
                    "ask_price": 25.5,
                    "sip_timestamp": pd.Timestamp(
                        "2026-01-02 15:59:00"
                    ).value,
                }
            ]

    provider = MassiveHistoricalOptionDataProvider(
        client=FakeMassiveClient()
    )

    store = provider.load_store(
        contract=contract,
        start_date=pd.Timestamp("2026-01-02"),
        end_date=pd.Timestamp("2026-01-02"),
    )

    prices = pd.Series(
        [500.0],
        index=[
            pd.Timestamp("2026-01-02"),
        ],
    )

    strategy = BuyAndHoldOptionStrategy(
        contract=contract,
        quantity=1,
    )

    portfolio = Portfolio(
        initial_cash=100000,
    )

    engine = BacktestEngine()

    result = engine.run(
        prices=prices,
        strategy=strategy,
        portfolio=portfolio,
        option_data_provider=store,
    )

    assert portfolio.cash == pytest.approx(97450.0)

    assert contract in portfolio.option_positions

    position = portfolio.option_positions[
        contract
    ]

    assert position.quantity == 1
    assert position.average_cost == pytest.approx(25.5)

def test_backtest_marks_option_position_to_market():

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    historical_quotes = [
        HistoricalOptionQuote(
            contract=contract,
            timestamp=pd.Timestamp(
                "2026-01-02 15:59:00"
            ),
            bid=24.5,
            ask=25.5,
        ),
        HistoricalOptionQuote(
            contract=contract,
            timestamp=pd.Timestamp(
                "2026-01-05 15:59:00"
            ),
            bid=30.0,
            ask=31.0,
        ),
    ]

    store = HistoricalOptionQuoteStore.from_historical_quotes(
        historical_quotes
    )

    prices = pd.Series(
        [
            500.0,
            505.0,
        ],
        index=[
            pd.Timestamp("2026-01-02"),
            pd.Timestamp("2026-01-05"),
        ],
    )

    strategy = BuyAndHoldOptionStrategy(
        contract=contract,
        quantity=1,
    )

    portfolio = Portfolio(
        initial_cash=100000,
    )

    engine = BacktestEngine()

    result = engine.run(
        prices=prices,
        strategy=strategy,
        portfolio=portfolio,
        option_data_provider=store,
    )

    assert result.equity_curve[0] == pytest.approx(
        99900.0
    )

    assert result.equity_curve[1] == pytest.approx(
        100450.0
    )

def test_backtest_forward_fills_missing_option_mark():

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    historical_quotes = [
        HistoricalOptionQuote(
            contract=contract,
            timestamp=pd.Timestamp(
                "2026-01-02 15:59:00"
            ),
            bid=24.5,
            ask=25.5,
        ),

        # intentionally no quote on 2026-01-05

        HistoricalOptionQuote(
            contract=contract,
            timestamp=pd.Timestamp(
                "2026-01-06 15:59:00"
            ),
            bid=30.0,
            ask=31.0,
        ),
    ]

    store = HistoricalOptionQuoteStore.from_historical_quotes(
        historical_quotes
    )

    prices = pd.Series(
        [
            500.0,
            505.0,
            510.0,
        ],
        index=[
            pd.Timestamp("2026-01-02"),
            pd.Timestamp("2026-01-05"),
            pd.Timestamp("2026-01-06"),
        ],
    )

    strategy = BuyAndHoldOptionStrategy(
        contract=contract,
        quantity=1,
    )

    portfolio = Portfolio(
        initial_cash=100000,
    )

    engine = BacktestEngine()

    result = engine.run(
        prices=prices,
        strategy=strategy,
        portfolio=portfolio,
        option_data_provider=store,
    )

    assert result.equity_curve[0] == pytest.approx(
        99900.0
    )

    assert result.equity_curve[1] == pytest.approx(
        99900.0
    )

    assert result.equity_curve[2] == pytest.approx(
        100450.0
    )