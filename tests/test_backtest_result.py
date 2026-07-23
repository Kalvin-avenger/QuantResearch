from quantresearch.backtest import BacktestResult


def test_backtest_result_creation():

    result = BacktestResult(
        equity_curve=[100000, 101000],
        trades=[]
    )


    assert result.equity_curve == [
        100000,
        101000
    ]

    assert result.trades == []