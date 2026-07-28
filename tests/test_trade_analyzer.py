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

    result = analyzer.calculate(trades)

    assert result.total_trades == 2