import pandas as pd

from quantresearch.execution import Trade
from .metrics import TradeStatistics
from quantresearch.signals import Signal


class TradeAnalyzer:


    def calculate(
        self,
        trades: list[Trade],
    ) -> TradeStatistics:


        if len(trades) == 0:
            return TradeStatistics(
                total_trades=0,
                buy_trades=0,
                sell_trades=0,
                first_trade=None,
                last_trade=None,
            )


        buy_trades = sum(
            1
            for t in trades
            if t.action == Signal.BUY
        )


        sell_trades = sum(
            1
            for t in trades
            if t.action == Signal.SELL
        )


        return TradeStatistics(
            total_trades=len(trades),
            buy_trades=buy_trades,
            sell_trades=sell_trades,
            first_trade=trades[0].timestamp,
            last_trade=trades[-1].timestamp,
        )