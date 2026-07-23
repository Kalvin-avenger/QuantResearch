from quantresearch.analytics import PerformanceMetrics


def test_metrics_creation():

    metrics = PerformanceMetrics(
        total_return=0.20,
        cagr=0.10,
        volatility=0.15,
        sharpe=0.67,
        max_drawdown=-0.25,
    )


    assert metrics.total_return == 0.20
    assert metrics.cagr == 0.10
    assert metrics.volatility == 0.15
    assert metrics.sharpe == 0.67
    assert metrics.max_drawdown == -0.25