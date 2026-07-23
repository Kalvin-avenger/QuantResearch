from quantresearch.data.yahoo import download_price_data
from quantresearch.data.validator import validate_price_data


def test_validate_price_data():
    df = download_price_data(
        ticker="AAPL",
        start_date="2024-01-01",
    )

    assert validate_price_data(df)