import pandas as pd


def calculate_sma(
    series: pd.Series,
    window: int,
) -> pd.Series:
    """
    Calculate the simple moving average.

    Args:
        series:
            Input price series.

        window:
            Rolling window size.

    Returns:
        A pandas Series containing the SMA values.
    """

    if window <= 0:
        raise ValueError(
            "window must be greater than 0."
        )

    return series.rolling(window=window).mean()

