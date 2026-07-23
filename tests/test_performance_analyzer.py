from quantresearch.analytics import (
    PerformanceAnalyzer
)
import pytest


def test_total_return():

    analyzer = PerformanceAnalyzer()


    equity_curve = [
        100,
        110,
        121,
    ]


    metrics = analyzer.calculate(
        equity_curve
    )


    assert metrics.total_return == pytest.approx(
        0.21
    )