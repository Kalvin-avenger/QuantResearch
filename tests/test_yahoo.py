from quantresearch.data.yahoo import download_price_data


def test_download_price_data():
    df = download_price_data(
        ticker="AAPL",
        start_date="2024-01-01",
    )

    assert not df.empty
    assert "Close" in df.columns
    assert "Volume" in df.columns