from quantresearch.backtest import BacktestResult
from quantresearch.portfolio import Portfolio


def test_backtest_result_creation():

    portfolio = Portfolio(
        initial_cash=100000,
    )

    result = BacktestResult(
        equity_curve=[
            100000,
            101000,
        ],
        trades=[],
        portfolio=portfolio,
    )

    assert result.equity_curve == [
        100000,
        101000,
    ]

    assert result.trades == []

    assert result.portfolio == portfolio