"""Data Quality Checker - Validate Polars DataFrames and log results to SQLite."""

__version__ = "0.1.0"

from .main import DataQualityChecker
from .connector.output_log import DBConnector

__all__ = [
    "DataQualityChecker",
    "DBConnector",
]
