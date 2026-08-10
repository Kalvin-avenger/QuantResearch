from quantresearch.analytics.trade_analyzer import TradeAnalyzer
from quantresearch.execution import Trade
from quantresearch.signals import Signal
import pandas as pd


def test_trade_count():

    trades = [
        Trade(
            timestamp=pd.Timestamp("2023-01-01"),
            action=Signal.BUY,
            quantity=10,
            price=100,
        ),
        Trade(
            timestamp=pd.Timestamp("2023-02-01"),
            action=Signal.SELL,
            quantity=10,
            price=110,
        ),
    ]

    analyzer = TradeAnalyzer()

    result = analyzer.analyze(trades)

    assert result.total_trades == 2


import pandas as pd

from quantresearch.analytics import TradeAnalyzer
from quantresearch.execution import Trade
from quantresearch.signals import Signal


def test_trade_analyzer_calculates_win_rate():

    trades = [
        Trade(
            timestamp=pd.Timestamp("2026-01-01"),
            action=Signal.BUY,
            quantity=100,
            price=100,
        ),
        Trade(
            timestamp=pd.Timestamp("2026-01-02"),
            action=Signal.SELL,
            quantity=100,
            price=120,
        ),
        Trade(
            timestamp=pd.Timestamp("2026-01-03"),
            action=Signal.BUY,
            quantity=100,
            price=130,
        ),
        Trade(
            timestamp=pd.Timestamp("2026-01-04"),
            action=Signal.SELL,
            quantity=100,
            price=110,
        ),
    ]

    analyzer = TradeAnalyzer()

    statistics = analyzer.analyze(
        trades
    )

    assert statistics.winning_trades == 1
    assert statistics.losing_trades == 1
    assert statistics.win_rate == 0.5

def test_trade_analyzer_win_rate_is_zero_without_completed_trades():

    trades = [
        Trade(
            timestamp=pd.Timestamp("2026-01-01"),
            action=Signal.BUY,
            quantity=100,
            price=100,
        ),
    ]

    analyzer = TradeAnalyzer()

    statistics = analyzer.analyze(
        trades
    )

    assert statistics.winning_trades == 0
    assert statistics.losing_trades == 0
    assert statistics.win_rate == 0.0

def test_trade_analyzer_average_win_and_loss():

    trades = [
        Trade(
            timestamp=pd.Timestamp("2026-01-01"),
            action=Signal.BUY,
            quantity=1,
            price=100,
        ),
        Trade(
            timestamp=pd.Timestamp("2026-01-02"),
            action=Signal.SELL,
            quantity=1,
            price=120,
        ),
        Trade(
            timestamp=pd.Timestamp("2026-01-03"),
            action=Signal.BUY,
            quantity=1,
            price=100,
        ),
        Trade(
            timestamp=pd.Timestamp("2026-01-04"),
            action=Signal.SELL,
            quantity=1,
            price=110,
        ),
        Trade(
            timestamp=pd.Timestamp("2026-01-05"),
            action=Signal.BUY,
            quantity=1,
            price=100,
        ),
        Trade(
            timestamp=pd.Timestamp("2026-01-06"),
            action=Signal.SELL,
            quantity=1,
            price=80,
        ),
    ]

    analyzer = TradeAnalyzer()

    statistics = analyzer.analyze(trades)

    assert statistics.average_win == 15.0
    assert statistics.average_loss == -20.0


def test_trade_analyzer_profit_factor():

    trades = [
        Trade(
            timestamp=pd.Timestamp("2026-01-01"),
            action=Signal.BUY,
            quantity=1,
            price=100,
        ),
        Trade(
            timestamp=pd.Timestamp("2026-01-02"),
            action=Signal.SELL,
            quantity=1,
            price=120,
        ),
        Trade(
            timestamp=pd.Timestamp("2026-01-03"),
            action=Signal.BUY,
            quantity=1,
            price=100,
        ),
        Trade(
            timestamp=pd.Timestamp("2026-01-04"),
            action=Signal.SELL,
            quantity=1,
            price=110,
        ),
        Trade(
            timestamp=pd.Timestamp("2026-01-05"),
            action=Signal.BUY,
            quantity=1,
            price=100,
        ),
        Trade(
            timestamp=pd.Timestamp("2026-01-06"),
            action=Signal.SELL,
            quantity=1,
            price=80,
        ),
    ]

    analyzer = TradeAnalyzer()

    statistics = analyzer.analyze(trades)

    assert statistics.profit_factor == 1.5

import pytest


def test_trade_analyzer_calculates_expectancy():

    trades = [
        Trade(
            timestamp=pd.Timestamp("2026-01-01"),
            action=Signal.BUY,
            quantity=1,
            price=100,
        ),
        Trade(
            timestamp=pd.Timestamp("2026-01-02"),
            action=Signal.SELL,
            quantity=1,
            price=120,
        ),
        Trade(
            timestamp=pd.Timestamp("2026-01-03"),
            action=Signal.BUY,
            quantity=1,
            price=100,
        ),
        Trade(
            timestamp=pd.Timestamp("2026-01-04"),
            action=Signal.SELL,
            quantity=1,
            price=110,
        ),
        Trade(
            timestamp=pd.Timestamp("2026-01-05"),
            action=Signal.BUY,
            quantity=1,
            price=100,
        ),
        Trade(
            timestamp=pd.Timestamp("2026-01-06"),
            action=Signal.SELL,
            quantity=1,
            price=80,
        ),
    ]

    analyzer = TradeAnalyzer()

    statistics = analyzer.analyze(
        trades
    )

    assert statistics.expectancy == pytest.approx(
        10 / 3
    )

    def test_trade_analyzer_expectancy_is_zero_without_completed_trades():

        trades = []

        analyzer = TradeAnalyzer()

        statistics = analyzer.analyze(
            trades
        )

        assert statistics.expectancy == 0.0

def test_trade_analyzer_expectancy_with_only_winning_trades():

    trades = [
        Trade(
            timestamp=pd.Timestamp("2026-01-01"),
            action=Signal.BUY,
            quantity=1,
            price=100,
        ),
        Trade(
            timestamp=pd.Timestamp("2026-01-02"),
            action=Signal.SELL,
            quantity=1,
            price=120,
        ),
    ]

    statistics = TradeAnalyzer().analyze(
        trades
    )

    assert statistics.expectancy == 20.0

def test_trade_analyzer_expectancy_with_only_losing_trades():

    trades = [
        Trade(
            timestamp=pd.Timestamp("2026-01-01"),
            action=Signal.BUY,
            quantity=1,
            price=100,
        ),
        Trade(
            timestamp=pd.Timestamp("2026-01-02"),
            action=Signal.SELL,
            quantity=1,
            price=80,
        ),
    ]

    statistics = TradeAnalyzer().analyze(
        trades
    )

    assert statistics.expectancy == -20.0

def test_trade_analyzer_counts_breakeven_trade():

    trades = [
        Trade(
            timestamp=pd.Timestamp("2026-01-01"),
            action=Signal.BUY,
            quantity=1,
            price=100,
        ),
        Trade(
            timestamp=pd.Timestamp("2026-01-02"),
            action=Signal.SELL,
            quantity=1,
            price=100,
        ),
    ]

    statistics = TradeAnalyzer().analyze(
        trades
    )

    assert statistics.completed_trades == 1
    assert statistics.winning_trades == 0
    assert statistics.losing_trades == 0
    assert statistics.breakeven_trades == 1
    assert statistics.win_rate == 0.0
    assert statistics.expectancy == 0.0

def test_trade_analyzer_includes_breakeven_in_completed_trades():

    trades = [
        Trade(
            timestamp=pd.Timestamp("2026-01-01"),
            action=Signal.BUY,
            quantity=1,
            price=100,
        ),
        Trade(
            timestamp=pd.Timestamp("2026-01-02"),
            action=Signal.SELL,
            quantity=1,
            price=120,
        ),
        Trade(
            timestamp=pd.Timestamp("2026-01-03"),
            action=Signal.BUY,
            quantity=1,
            price=100,
        ),
        Trade(
            timestamp=pd.Timestamp("2026-01-04"),
            action=Signal.SELL,
            quantity=1,
            price=100,
        ),
        Trade(
            timestamp=pd.Timestamp("2026-01-05"),
            action=Signal.BUY,
            quantity=1,
            price=100,
        ),
        Trade(
            timestamp=pd.Timestamp("2026-01-06"),
            action=Signal.SELL,
            quantity=1,
            price=80,
        ),
    ]

    statistics = TradeAnalyzer().analyze(
        trades
    )

    assert statistics.completed_trades == 3
    assert statistics.winning_trades == 1
    assert statistics.losing_trades == 1
    assert statistics.breakeven_trades == 1

    assert statistics.win_rate == pytest.approx(
        1 / 3
    )

    assert statistics.expectancy == pytest.approx(
        0.0
    )

def test_trade_analyzer_calculates_average_holding_period():

    trades = [
        Trade(
            timestamp=pd.Timestamp("2026-01-01"),
            action=Signal.BUY,
            quantity=1,
            price=100,
        ),
        Trade(
            timestamp=pd.Timestamp("2026-01-03"),
            action=Signal.SELL,
            quantity=1,
            price=120,
        ),
        Trade(
            timestamp=pd.Timestamp("2026-01-05"),
            action=Signal.BUY,
            quantity=1,
            price=100,
        ),
        Trade(
            timestamp=pd.Timestamp("2026-01-11"),
            action=Signal.SELL,
            quantity=1,
            price=80,
        ),
    ]

    statistics = TradeAnalyzer().analyze(
        trades
    )

    assert statistics.average_holding_period == pd.Timedelta(
        days=4
    )

def test_trade_analyzer_average_holding_period_is_none_without_completed_trades():

    trades = [
        Trade(
            timestamp=pd.Timestamp("2026-01-01"),
            action=Signal.BUY,
            quantity=1,
            price=100,
        ),
    ]

    statistics = TradeAnalyzer().analyze(
        trades
    )

    assert statistics.average_holding_period is None

def test_trade_analyzer_rejects_negative_holding_period():

    trades = [
        Trade(
            timestamp=pd.Timestamp("2026-01-05"),
            action=Signal.BUY,
            quantity=1,
            price=100,
        ),
        Trade(
            timestamp=pd.Timestamp("2026-01-03"),
            action=Signal.SELL,
            quantity=1,
            price=120,
        ),
    ]

    with pytest.raises(
        ValueError,
        match="SELL timestamp must not precede BUY timestamp.",
    ):

        TradeAnalyzer().analyze(
            trades
        )

def test_analyze_returns_largest_win():
    trades = [
        Trade(
            timestamp=pd.Timestamp("2024-01-01"),
            action=Signal.BUY,
            quantity=10,
            price=100.0,
        ),
        Trade(
            timestamp=pd.Timestamp("2024-01-02"),
            action=Signal.SELL,
            quantity=10,
            price=110.0,
        ),
        Trade(
            timestamp=pd.Timestamp("2024-01-03"),
            action=Signal.BUY,
            quantity=5,
            price=200.0,
        ),
        Trade(
            timestamp=pd.Timestamp("2024-01-04"),
            action=Signal.SELL,
            quantity=5,
            price=250.0,
        ),
    ]

    statistics = TradeAnalyzer().analyze(trades)

    assert statistics.largest_win == pytest.approx(250.0)