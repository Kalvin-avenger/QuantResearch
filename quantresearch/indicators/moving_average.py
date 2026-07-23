import pandas as pd


def calculate_sma(
    series: pd.Series,
    window: int,
) -> pd.Series:
    """
    Calculate Simple Moving Average.
    """

    return series.rolling(window=window).mean()