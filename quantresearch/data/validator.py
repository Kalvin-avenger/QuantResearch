import pandas as pd

from quantresearch.logger import get_logger


logger = get_logger(__name__)


def validate_price_data(
    df: pd.DataFrame
) -> bool:
    """
    Validate historical price dataframe.
    """

    logger.info(
        "Running data validation..."
    )


    # Check empty dataframe
    if df.empty:
        raise ValueError(
            "DataFrame is empty"
        )


    # Check required columns

    required_columns = [
        "Date",
        "Close",
        "Volume"
    ]

    missing_columns = [
        col
        for col in required_columns
        if col not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing columns: {missing_columns}"
        )


    # Check duplicate dates

    if df["Date"].duplicated().any():

        raise ValueError(
            "Duplicate dates found"
        )


    # Check sorting

    if not df["Date"].is_monotonic_increasing:

        raise ValueError(
            "Dates are not sorted"
        )


    # Check missing values

    if df.isnull().sum().sum() > 0:

        raise ValueError(
            "Missing values detected"
        )


    logger.info(
        "Data validation passed"
    )

    return True