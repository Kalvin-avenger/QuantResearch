from quantresearch.analytics import (
    PerformanceAnalyzer
)
import pytest
import numpy as np


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

def test_max_drawdown():

    analyzer = PerformanceAnalyzer()


    equity_curve = [
        100,
        120,
        90,
        110,
    ]


    metrics = analyzer.calculate(
        equity_curve
    )


    assert metrics.max_drawdown == pytest.approx(
        -0.25
    )

def test_cagr():

    analyzer = PerformanceAnalyzer()


    equity_curve = [
        100,
        110,
        121,
    ]


    metrics = analyzer.calculate(
        equity_curve
    )


    assert metrics.cagr == pytest.approx(
        (121 / 100) ** (252 / 2) - 1
    )


def test_volatility():

    analyzer = PerformanceAnalyzer()


    equity_curve = [
        100,
        110,
        100,
    ]


    metrics = analyzer.calculate(
        equity_curve
    )


    returns = [
        0.1,
        -10/110
    ]

    expected = (
        np.std(
            returns,
            ddof=1
        )
        *
        np.sqrt(252)
    )


    assert metrics.volatility == pytest.approx(
        expected
    )

def test_sharpe():

    analyzer = PerformanceAnalyzer()


    equity_curve = [
        100,
        110,
        100,
    ]


    metrics = analyzer.calculate(
        equity_curve
    )


    returns = np.array(
        [
            0.1,
            -10/110
        ]
    )


    expected = (
        returns.mean()
        /
        returns.std(ddof=1)
        *
        np.sqrt(252)
    )


    assert metrics.sharpe == pytest.approx(
        expected
    )