import pandas as pd
import pytest

from quantresearch.data.yahoo import (
    download_price_data,
)


@pytest.mark.integration
def test_spy_real_drawdown_window_discovery():
    spy_data = download_price_data(
        ticker="SPY",
        start_date="2025-01-01",
        end_date="2026-08-01",
    )

    assert not spy_data.empty

    prices = pd.Series(
        data=spy_data["close"].astype(float).to_numpy(),
        index=pd.to_datetime(
            spy_data["date"]
        ),
        dtype=float,
    )

    assert not prices.empty
    assert not prices.isna().any()

    running_peak = prices.cummax()

    drawdown = (
        prices
        / running_peak
        - 1.0
    )

    triggered = drawdown[
        drawdown <= -0.05
    ]

    assert not triggered.empty

    first_trigger_date = (
        triggered.index[0]
    )

    first_trigger_drawdown = float(
        triggered.iloc[0]
    )

    trigger_price = float(
        prices.loc[
            first_trigger_date
        ]
    )

    peak_price = float(
        running_peak.loc[
            first_trigger_date
        ]
    )

    # Find the date of the peak that generated
    # this first >= 5% drawdown.
    history_to_trigger = prices.loc[
        :first_trigger_date
    ]

    peak_date = (
        history_to_trigger.idxmax()
    )

    print(
        "\nSPY drawdown discovery"
    )

    print(
        "Data window:",
        prices.index[0],
        "->",
        prices.index[-1],
    )

    print(
        "Peak date:",
        peak_date,
    )

    print(
        "Peak price:",
        peak_price,
    )

    print(
        "First 5% drawdown date:",
        first_trigger_date,
    )

    print(
        "Trigger price:",
        trigger_price,
    )

    print(
        "Drawdown:",
        first_trigger_drawdown,
    )

    assert first_trigger_drawdown <= -0.05

    assert trigger_price <= (
        peak_price * 0.95
    )

@pytest.mark.integration
def test_spy_post_tp_drawdown_window_discovery():
    spy_data = download_price_data(
        ticker="SPY",
        start_date="2025-05-13",
        end_date="2025-12-31",
    )

    assert not spy_data.empty

    prices = pd.Series(
        data=spy_data["close"].astype(float).to_numpy(),
        index=pd.to_datetime(spy_data["date"]),
        dtype=float,
    )

    running_peak = prices.cummax()

    drawdown = (
        prices / running_peak - 1.0
    )

    triggered = drawdown[
        drawdown <= -0.05
    ]

    assert not triggered.empty

    trigger_date = triggered.index[0]
    trigger_drawdown = float(
        triggered.iloc[0]
    )

    trigger_price = float(
        prices.loc[trigger_date]
    )

    peak_price = float(
        running_peak.loc[trigger_date]
    )

    peak_date = (
        prices.loc[:trigger_date]
        .idxmax()
    )

    print(
        "\nPost-TP drawdown discovery"
    )

    print(
        "Peak date:",
        peak_date,
    )

    print(
        "Peak price:",
        peak_price,
    )

    print(
        "First post-TP 5% drawdown date:",
        trigger_date,
    )

    print(
        "Trigger price:",
        trigger_price,
    )

    print(
        "Drawdown:",
        trigger_drawdown,
    )

    assert trigger_drawdown <= -0.05