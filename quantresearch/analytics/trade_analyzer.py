from collections.abc import Sequence

from quantresearch.analytics.metrics import TradeStatistics
from quantresearch.execution import Trade
from quantresearch.signals import Signal

import pandas as pd


class TradeAnalyzer:
    """
    Analyze completed round-trip trades.

    Current assumptions
    -------------------
    - Single asset
    - Long only
    - One BUY opens a position
    - One SELL fully closes the position
    - No partial entries or exits
    """

    def analyze(
        self,
        trades: Sequence[Trade],
    ) -> TradeStatistics:

        total_trades = len(trades)

        buy_trades = sum(
            trade.action == Signal.BUY
            for trade in trades
        )

        sell_trades = sum(
            trade.action == Signal.SELL
            for trade in trades
        )

        first_trade_time = (
            trades[0].timestamp
            if trades
            else None
        )

        last_trade_time = (
            trades[-1].timestamp
            if trades
            else None
        )

        winning_pnls: list[float] = []
        losing_pnls: list[float] = []

        breakeven_trades = 0
        holding_periods: list[pd.Timedelta] = []

        entry_trade: Trade | None = None

        expectancy: float

        for trade in trades:

            if trade.action == Signal.BUY:

                entry_trade = trade

            elif (
                trade.action == Signal.SELL
                and entry_trade is not None
            ):

                pnl = (
                    trade.price
                    - entry_trade.price
                ) * trade.quantity

                holding_period = (
                    trade.timestamp
                    - entry_trade.timestamp
                )

                if holding_period < pd.Timedelta(0):

                    raise ValueError(
                        "SELL timestamp must not precede BUY timestamp."
                    )

                holding_periods.append(
                    holding_period
                )


                if pnl > 0:

                    winning_pnls.append(
                        pnl
                    )

                elif pnl < 0:

                    losing_pnls.append(
                        pnl
                    )

                else:

                    breakeven_trades += 1

                entry_trade = None

        winning_trades = len(
            winning_pnls
        )

        losing_trades = len(
            losing_pnls
        )

        completed_trades = (
            winning_trades
            + losing_trades
            + breakeven_trades
        )

        win_rate = (
            winning_trades / completed_trades
            if completed_trades > 0
            else 0.0
        )

        average_win = (
            sum(winning_pnls)
            / winning_trades
            if winning_trades > 0
            else 0.0
        )

        average_loss = (
            sum(losing_pnls)
            / losing_trades
            if losing_trades > 0
            else 0.0
        )

        gross_profit = sum(
            winning_pnls
        )

        gross_loss = abs(
            sum(losing_pnls)
        )

        if gross_loss > 0:

            profit_factor = (
                gross_profit / gross_loss
            )

        elif gross_profit > 0:

            profit_factor = float("inf")

        else:

            profit_factor = 0.0

        total_pnl = (
            sum(winning_pnls)
            + sum(losing_pnls)
        )

        expectancy = (
            total_pnl / completed_trades
            if completed_trades > 0
            else 0.0
        )

        average_holding_period = (
            sum(
                holding_periods,
                start=pd.Timedelta(0),
            ) / len(holding_periods)
            if holding_periods
            else None
        )

        largest_win = max(winning_pnls) if winning_pnls else 0.0

        return TradeStatistics(
            total_trades=total_trades,
            buy_trades=buy_trades,
            sell_trades=sell_trades,
            first_trade_time=first_trade_time,
            last_trade_time=last_trade_time,
            completed_trades=completed_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            breakeven_trades=breakeven_trades,
            win_rate=win_rate,
            average_win=average_win,
            average_loss=average_loss,
            profit_factor=profit_factor,
            expectancy=expectancy,
            average_holding_period=average_holding_period,
            largest_win=largest_win,
        )