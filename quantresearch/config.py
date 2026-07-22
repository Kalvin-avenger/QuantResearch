from pathlib import Path


# Project root directory
PROJECT_ROOT = Path(__file__).resolve().parents[1]


# Data directories
DATA_DIR = PROJECT_ROOT / "data"

RAW_DATA_DIR = DATA_DIR / "raw"

PROCESSED_DATA_DIR = DATA_DIR / "processed"


# Backtest settings

INITIAL_CAPITAL = 10000

COMMISSION_RATE = 0.001


# Trading settings

DEFAULT_START_DATE = "2015-01-01"

DEFAULT_END_DATE = None