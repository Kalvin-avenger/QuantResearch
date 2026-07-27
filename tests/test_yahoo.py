from quantresearch.data import download_price_data


def test_download_price_data():
    df = download_price_data(
        ticker="AAPL",
        start_date="2024-01-01",
    )

    assert not df.empty
    assert "close" in df.columns
    assert "volume" in df.columns

def test_download_price_data_public_api():

    from quantresearch.data import download_price_data

    assert callable(download_price_data)