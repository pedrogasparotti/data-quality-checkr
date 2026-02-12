from unittest.mock import MagicMock

import polars as pl
import pytest

from data_quality_checker.main import DataQualityChecker


class TestIsColumnUnique:
    def test_unique_values_returns_true(self, mock_db_connector: MagicMock) -> None:
        df = pl.DataFrame({"id": [1, 2, 3]})
        checker = DataQualityChecker(mock_db_connector)
        assert checker.is_column_unique(df, "id") is True

    def test_duplicate_values_returns_false(self, mock_db_connector: MagicMock) -> None:
        df = pl.DataFrame({"id": [1, 2, 2]})
        checker = DataQualityChecker(mock_db_connector)
        assert checker.is_column_unique(df, "id") is False

    def test_logs_result(self, mock_db_connector: MagicMock) -> None:
        df = pl.DataFrame({"id": [1, 2, 3]})
        checker = DataQualityChecker(mock_db_connector)
        checker.is_column_unique(df, "id")
        mock_db_connector.log.assert_called_once_with(
            check_type="unique",
            result=True,
            additional_params={"column": "id"},
        )

    def test_missing_column_raises_value_error(self, mock_db_connector: MagicMock) -> None:
        df = pl.DataFrame({"id": [1, 2, 3]})
        checker = DataQualityChecker(mock_db_connector)
        with pytest.raises(ValueError, match="Column 'missing'"):
            checker.is_column_unique(df, "missing")

    def test_empty_dataframe(self, mock_db_connector: MagicMock) -> None:
        df = pl.DataFrame({"id": []})
        checker = DataQualityChecker(mock_db_connector)
        assert checker.is_column_unique(df, "id") is True


class TestIsColumnNotNull:
    def test_no_nulls_returns_true(self, mock_db_connector: MagicMock) -> None:
        df = pl.DataFrame({"name": ["a", "b", "c"]})
        checker = DataQualityChecker(mock_db_connector)
        assert checker.is_column_not_null(df, "name") is True

    def test_with_nulls_returns_false(self, mock_db_connector: MagicMock) -> None:
        df = pl.DataFrame({"name": ["a", None, "c"]})
        checker = DataQualityChecker(mock_db_connector)
        assert checker.is_column_not_null(df, "name") is False

    def test_logs_result(self, mock_db_connector: MagicMock) -> None:
        df = pl.DataFrame({"name": ["a", None]})
        checker = DataQualityChecker(mock_db_connector)
        checker.is_column_not_null(df, "name")
        mock_db_connector.log.assert_called_once_with(
            check_type="not_null",
            result=False,
            additional_params={"column": "name"},
        )

    def test_missing_column_raises_value_error(self, mock_db_connector: MagicMock) -> None:
        df = pl.DataFrame({"name": ["a"]})
        checker = DataQualityChecker(mock_db_connector)
        with pytest.raises(ValueError, match="Column 'missing'"):
            checker.is_column_not_null(df, "missing")

    def test_empty_dataframe(self, mock_db_connector: MagicMock) -> None:
        df = pl.DataFrame({"name": []})
        checker = DataQualityChecker(mock_db_connector)
        assert checker.is_column_not_null(df, "name") is True


class TestIsColumnEnum:
    def test_all_values_accepted_returns_true(self, mock_db_connector: MagicMock) -> None:
        df = pl.DataFrame({"status": ["active", "inactive"]})
        checker = DataQualityChecker(mock_db_connector)
        assert checker.is_column_enum(df, "status", ["active", "inactive", "pending"]) is True

    def test_unexpected_values_returns_false(self, mock_db_connector: MagicMock) -> None:
        df = pl.DataFrame({"status": ["active", "deleted"]})
        checker = DataQualityChecker(mock_db_connector)
        assert checker.is_column_enum(df, "status", ["active", "inactive"]) is False

    def test_logs_result_with_accepted_values(self, mock_db_connector: MagicMock) -> None:
        df = pl.DataFrame({"status": ["active"]})
        checker = DataQualityChecker(mock_db_connector)
        checker.is_column_enum(df, "status", ["active"])
        mock_db_connector.log.assert_called_once_with(
            check_type="accepted_values",
            result=True,
            additional_params={
                "column": "status",
                "accepted_values": ["active"],
            },
        )

    def test_missing_column_raises_value_error(self, mock_db_connector: MagicMock) -> None:
        df = pl.DataFrame({"status": ["active"]})
        checker = DataQualityChecker(mock_db_connector)
        with pytest.raises(ValueError, match="Column 'missing'"):
            checker.is_column_enum(df, "missing", ["active"])

    def test_empty_dataframe(self, mock_db_connector: MagicMock) -> None:
        df = pl.DataFrame({"status": []})
        checker = DataQualityChecker(mock_db_connector)
        assert checker.is_column_enum(df, "status", ["active"]) is True


class TestAreTablesReferentialIntegral:
    def test_all_child_keys_in_parent_returns_true(self, mock_db_connector: MagicMock) -> None:
        parent = pl.DataFrame({"id": [1, 2, 3]})
        child = pl.DataFrame({"parent_id": [1, 2]})
        checker = DataQualityChecker(mock_db_connector)
        assert checker.are_tables_referential_integral(parent, child, "id", "parent_id") is True

    def test_orphan_child_keys_returns_false(self, mock_db_connector: MagicMock) -> None:
        parent = pl.DataFrame({"id": [1, 2]})
        child = pl.DataFrame({"parent_id": [1, 3]})
        checker = DataQualityChecker(mock_db_connector)
        assert checker.are_tables_referential_integral(parent, child, "id", "parent_id") is False

    def test_logs_result(self, mock_db_connector: MagicMock) -> None:
        parent = pl.DataFrame({"id": [1, 2]})
        child = pl.DataFrame({"parent_id": [1]})
        checker = DataQualityChecker(mock_db_connector)
        checker.are_tables_referential_integral(parent, child, "id", "parent_id")
        mock_db_connector.log.assert_called_once_with(
            check_type="referential_integrity",
            result=True,
            additional_params={
                "parent_key": "id",
                "child_key": "parent_id",
            },
        )

    def test_missing_parent_key_raises_value_error(self, mock_db_connector: MagicMock) -> None:
        parent = pl.DataFrame({"id": [1]})
        child = pl.DataFrame({"parent_id": [1]})
        checker = DataQualityChecker(mock_db_connector)
        with pytest.raises(ValueError, match="Column 'missing'"):
            checker.are_tables_referential_integral(parent, child, "missing", "parent_id")

    def test_missing_child_key_raises_value_error(self, mock_db_connector: MagicMock) -> None:
        parent = pl.DataFrame({"id": [1]})
        child = pl.DataFrame({"parent_id": [1]})
        checker = DataQualityChecker(mock_db_connector)
        with pytest.raises(ValueError, match="Column 'missing'"):
            checker.are_tables_referential_integral(parent, child, "id", "missing")

    def test_empty_child_table(self, mock_db_connector: MagicMock) -> None:
        parent = pl.DataFrame({"id": [1, 2]})
        child = pl.DataFrame({"parent_id": []})
        checker = DataQualityChecker(mock_db_connector)
        assert checker.are_tables_referential_integral(parent, child, "id", "parent_id") is True
