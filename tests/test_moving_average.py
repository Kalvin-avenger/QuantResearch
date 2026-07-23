import pandas as pd

from quantresearch.indicators.moving_average import calculate_sma


def test_calculate_sma():

    data = pd.Series([1, 2, 3, 4, 5])

    sma = calculate_sma(data, window=3)

    expected = [None, None, 2.0, 3.0, 4.0]

    for actual, exp in zip(sma.tolist(), expected):

        if exp is None:
            assert pd.isna(actual)
        else:
            assert actual == exp