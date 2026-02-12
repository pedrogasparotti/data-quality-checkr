from typing import List
import polars as pl

from .connector.output_log import DBConnector


class DataQualityChecker:
    """Validates Polars DataFrames against data quality rules."""

    def __init__(self, db_connector: DBConnector) -> None:
        """
        Initialize the data quality checker.

        Args:
            db_connector: DBConnector instance for logging results.
        """
        self.db_connector = db_connector

    def _validate_column_exists(self, df: pl.DataFrame, column: str) -> None:
        """Raise ValueError if column is not in DataFrame."""
        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found in DataFrame")

    def is_column_unique(self, df: pl.DataFrame, column: str) -> bool:
        """
        Check if column values are unique.

        Args:
            df: Polars DataFrame to validate.
            column: Column name to check.

        Returns:
            True if all values are unique, False otherwise.

        Raises:
            ValueError: If column doesn't exist in DataFrame.
        """
        self._validate_column_exists(df, column)
        result = df[column].is_duplicated().sum() == 0
        self.db_connector.log(
            check_type="unique",
            result=result,
            additional_params={"column": column},
        )
        return result

    def is_column_not_null(self, df: pl.DataFrame, column: str) -> bool:
        """
        Check if column has no null values.

        Args:
            df: Polars DataFrame to validate.
            column: Column name to check.

        Returns:
            True if no nulls, False otherwise.

        Raises:
            ValueError: If column doesn't exist in DataFrame.
        """
        self._validate_column_exists(df, column)
        result = df[column].null_count() == 0
        self.db_connector.log(
            check_type="not_null",
            result=result,
            additional_params={"column": column},
        )
        return result

    def is_column_enum(
        self,
        df: pl.DataFrame,
        column: str,
        accepted_values: List[str],
    ) -> bool:
        """
        Check if column values are all in the accepted list.

        Args:
            df: Polars DataFrame to validate.
            column: Column name to check.
            accepted_values: List of valid values.

        Returns:
            True if all values are in accepted list, False otherwise.

        Raises:
            ValueError: If column doesn't exist in DataFrame.
        """
        self._validate_column_exists(df, column)
        result = df[column].is_in(accepted_values).all()
        self.db_connector.log(
            check_type="accepted_values",
            result=result,
            additional_params={
                "column": column,
                "accepted_values": accepted_values,
            },
        )
        return result

    def are_tables_referential_integral(
        self,
        parent_df: pl.DataFrame,
        child_df: pl.DataFrame,
        parent_key: str,
        child_key: str,
    ) -> bool:
        """
        Check referential integrity between parent and child tables.

        Args:
            parent_df: Parent table DataFrame.
            child_df: Child table DataFrame.
            parent_key: Primary key column in parent.
            child_key: Foreign key column in child.

        Returns:
            True if all child keys exist in parent, False otherwise.

        Raises:
            ValueError: If key column doesn't exist in respective DataFrame.
        """
        self._validate_column_exists(parent_df, parent_key)
        self._validate_column_exists(child_df, child_key)

        parent_keys = parent_df[parent_key].to_list()
        child_keys = child_df[child_key]
        result = child_keys.is_in(parent_keys).all()

        self.db_connector.log(
            check_type="referential_integrity",
            result=result,
            additional_params={
                "parent_key": parent_key,
                "child_key": child_key,
            },
        )
        return result
