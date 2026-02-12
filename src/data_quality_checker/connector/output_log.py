import json
import sqlite3
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path


class DBConnector:
    """Manages SQLite database connection and logging of validation results."""

    def __init__(self, db_path: Path) -> None:
        """
        Initialize database connector.

        Args:
            db_path: Path to SQLite database file.
        """
        self.db_path = Path(db_path)
        self._initialize_db()

    def _initialize_db(self) -> None:
        """Create the validation_log table if it doesn't exist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS validation_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    check_type TEXT NOT NULL,
                    result INTEGER NOT NULL,
                    additional_params TEXT
                )
                """
            )

    def log(
        self,
        check_type: str,
        result: bool,
        additional_params: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Log a validation result to the database.

        Args:
            check_type: Type of validation (e.g., 'unique', 'not_null').
            result: True if validation passed, False otherwise.
            additional_params: Additional context (column name, values, etc.).
        """
        params_json = json.dumps(additional_params) if additional_params else None
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO validation_log (timestamp, check_type, result, additional_params)
                VALUES (?, ?, ?, ?)
                """,
                (
                    datetime.now().isoformat(),
                    check_type,
                    int(result),
                    params_json,
                ),
            )

    def print_all_logs(self) -> None:
        """Print all logged validation results."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT id, timestamp, check_type, result, additional_params "
                "FROM validation_log ORDER BY id"
            )
            rows = cursor.fetchall()

        for row in rows:
            log_id, timestamp, check_type, result, params = row
            status = "PASS" if result else "FAIL"
            print(
                f"[{log_id}] {timestamp} | {check_type} | {status} | {params or ''}"
            )
