import yfinance as yf
import pandas as pd

from quantresearch.logger import get_logger


logger = get_logger(__name__)


def download_price_data(
    ticker: str,
    start_date: str,
    end_date: str | None = None,
) -> pd.DataFrame:
    """
    Download historical price data from Yahoo Finance.

    Parameters
    ----------
    ticker : str
        Stock ticker symbol, e.g. "AAPL"

    start_date : str
        Start date, format: YYYY-MM-DD

    end_date : str, optional
        End date, format: YYYY-MM-DD

    Returns
    -------
    pd.DataFrame
        Historical OHLCV data
    """

    logger.info(
        "Downloading %s data from Yahoo Finance",
        ticker,
    )

    data = yf.download(
        ticker,
        start=start_date,
        end=end_date,
        auto_adjust=False,
        progress=False,
    )

    if data.empty:
        raise ValueError(
            f"No data returned for ticker: {ticker}"
        )

    data.reset_index(inplace=True)

    return data