import json
import sqlite3
from pathlib import Path

import pytest

from data_quality_checker.connector.output_log import DBConnector


class TestDBConnectorInit:
    def test_creates_database_file(self, temp_db: Path) -> None:
        DBConnector(temp_db)
        assert temp_db.exists()

    def test_creates_validation_log_table(self, db_connector: DBConnector) -> None:
        with sqlite3.connect(db_connector.db_path) as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='validation_log'"
            )
            assert cursor.fetchone() is not None

    def test_idempotent_initialization(self, temp_db: Path) -> None:
        DBConnector(temp_db)
        DBConnector(temp_db)  # Should not raise


class TestDBConnectorLog:
    def test_log_passing_result(self, db_connector: DBConnector) -> None:
        db_connector.log("unique", True, {"column": "user_id"})

        with sqlite3.connect(db_connector.db_path) as conn:
            row = conn.execute("SELECT * FROM validation_log").fetchone()

        assert row is not None
        assert row[2] == "unique"  # check_type
        assert row[3] == 1  # result (True)
        assert json.loads(row[4]) == {"column": "user_id"}

    def test_log_failing_result(self, db_connector: DBConnector) -> None:
        db_connector.log("not_null", False, {"column": "email"})

        with sqlite3.connect(db_connector.db_path) as conn:
            row = conn.execute("SELECT * FROM validation_log").fetchone()

        assert row[3] == 0  # result (False)

    def test_log_without_additional_params(self, db_connector: DBConnector) -> None:
        db_connector.log("unique", True)

        with sqlite3.connect(db_connector.db_path) as conn:
            row = conn.execute("SELECT * FROM validation_log").fetchone()

        assert row[4] is None  # additional_params

    def test_log_multiple_entries(self, db_connector: DBConnector) -> None:
        db_connector.log("unique", True)
        db_connector.log("not_null", False)
        db_connector.log("enum", True)

        with sqlite3.connect(db_connector.db_path) as conn:
            count = conn.execute("SELECT COUNT(*) FROM validation_log").fetchone()[0]

        assert count == 3

    def test_log_records_timestamp(self, db_connector: DBConnector) -> None:
        db_connector.log("unique", True)

        with sqlite3.connect(db_connector.db_path) as conn:
            row = conn.execute("SELECT timestamp FROM validation_log").fetchone()

        assert row[0] is not None
        assert "T" in row[0]  # ISO format contains T


class TestDBConnectorPrintAllLogs:
    def test_print_all_logs_empty(
        self, db_connector: DBConnector, capsys: pytest.CaptureFixture[str]
    ) -> None:
        db_connector.print_all_logs()
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_print_all_logs_with_entries(
        self, db_connector: DBConnector, capsys: pytest.CaptureFixture[str]
    ) -> None:
        db_connector.log("unique", True, {"column": "id"})
        db_connector.log("not_null", False, {"column": "email"})

        db_connector.print_all_logs()
        captured = capsys.readouterr()

        assert "unique" in captured.out
        assert "PASS" in captured.out
        assert "not_null" in captured.out
        assert "FAIL" in captured.out
