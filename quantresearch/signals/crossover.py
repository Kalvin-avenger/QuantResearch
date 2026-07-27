import pandas as pd

from .signal import Signal


def generate_crossover_signal(
    short_ma: pd.Series,
    long_ma: pd.Series,
) -> pd.Series:
    """
    Generate trading signals based on moving average crossover.

    Args:
        short_ma:
            Short-term moving average.

        long_ma:
            Long-term moving average.

    Returns:
        A Series of Signal values.

    Raises:
        ValueError:
            If the two input series have different lengths.
    """

    if len(short_ma) != len(long_ma):
        raise ValueError("short_ma and long_ma must have the same length.")

    signals = []

    for i in range(len(short_ma)):

        # 第一根K线没有前一天可以比较
        if i == 0:
            signals.append(Signal.NONE)
            continue

        # 任意均线为 NaN
        if (
            pd.isna(short_ma.iloc[i])
            or pd.isna(long_ma.iloc[i])
            or pd.isna(short_ma.iloc[i - 1])
            or pd.isna(long_ma.iloc[i - 1])
        ):
            signals.append(Signal.NONE)
            continue

        # Golden Cross
        if (
            short_ma.iloc[i - 1] <= long_ma.iloc[i - 1]
            and short_ma.iloc[i] > long_ma.iloc[i]
        ):
            signals.append(Signal.BUY)

        # Death Cross
        elif (
            short_ma.iloc[i - 1] >= long_ma.iloc[i - 1]
            and short_ma.iloc[i] < long_ma.iloc[i]
        ):
            signals.append(Signal.SELL)

        else:
            signals.append(Signal.HOLD)

    return pd.Series(signals, index=short_ma.index)