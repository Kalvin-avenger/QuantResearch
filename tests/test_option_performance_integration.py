import pandas as pd
import pytest

from quantresearch.backtest.engine import BacktestEngine
from quantresearch.data.historical_option_quote import HistoricalOptionQuote
from quantresearch.data.historical_options import HistoricalOptionQuoteStore
from quantresearch.instruments.options import OptionContract, OptionType
from quantresearch.portfolio.portfolio import Portfolio
from quantresearch.strategy.buy_and_hold_option import BuyAndHoldOptionStrategy
from quantresearch.analytics import PerformanceAnalyzer


def test_option_mark_to_market_changes_equity_curve():

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    quotes = [
        HistoricalOptionQuote(
            contract=contract,
            timestamp=pd.Timestamp("2026-01-02 15:59:00"),
            bid=24.5,
            ask=25.5,
        ),
        HistoricalOptionQuote(
            contract=contract,
            timestamp=pd.Timestamp("2026-01-05 15:59:00"),
            bid=30.0,
            ask=31.0,
        ),
        HistoricalOptionQuote(
            contract=contract,
            timestamp=pd.Timestamp("2026-01-06 15:59:00"),
            bid=20.0,
            ask=21.0,
        ),
    ]

    store = HistoricalOptionQuoteStore.from_historical_quotes(
        quotes
    )

    prices = pd.Series(
        [500.0, 505.0, 495.0],
        index=[
            pd.Timestamp("2026-01-02"),
            pd.Timestamp("2026-01-05"),
            pd.Timestamp("2026-01-06"),
        ],
    )

    portfolio = Portfolio(
        initial_cash=100000,
    )

    strategy = BuyAndHoldOptionStrategy(
        contract=contract,
        quantity=1,
    )

    engine = BacktestEngine()

    result = engine.run(
        prices=prices,
        strategy=strategy,
        portfolio=portfolio,
        option_data_provider=store,
    )

    assert result.equity_curve[0] == pytest.approx(99900.0)
    assert result.equity_curve[1] == pytest.approx(100450.0)
    assert result.equity_curve[2] == pytest.approx(99450.0)

    assert result.equity_curve[1] > result.equity_curve[0]
    assert result.equity_curve[2] < result.equity_curve[1]

def test_option_mark_to_market_flows_into_performance_metrics():

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    quotes = [
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
        HistoricalOptionQuote(
            contract=contract,
            timestamp=pd.Timestamp(
                "2026-01-06 15:59:00"
            ),
            bid=20.0,
            ask=21.0,
        ),
    ]

    store = (
        HistoricalOptionQuoteStore
        .from_historical_quotes(
            quotes
        )
    )

    prices = pd.Series(
        [
            500.0,
            505.0,
            495.0,
        ],
        index=[
            pd.Timestamp("2026-01-02"),
            pd.Timestamp("2026-01-05"),
            pd.Timestamp("2026-01-06"),
        ],
    )

    portfolio = Portfolio(
        initial_cash=100000,
    )

    strategy = BuyAndHoldOptionStrategy(
        contract=contract,
        quantity=1,
    )

    engine = BacktestEngine()

    result = engine.run(
        prices=prices,
        strategy=strategy,
        portfolio=portfolio,
        option_data_provider=store,
    )

    analyzer = PerformanceAnalyzer()

    metrics = analyzer.calculate(
        result.equity_curve
    )

    expected_total_return = (
        99450.0 / 99900.0
    ) - 1.0

    expected_max_drawdown = (
        99450.0 / 100450.0
    ) - 1.0

    assert metrics.total_return == pytest.approx(
        expected_total_return
    )

    assert metrics.max_drawdown == pytest.approx(
        expected_max_drawdown
    )