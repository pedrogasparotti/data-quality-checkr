"""CLI entry point for data-quality-checker."""

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, List

import polars as pl
import yaml

from .connector.output_log import DBConnector
from .main import DataQualityChecker


def load_config(path: str) -> Dict[str, Any]:
    """Parse a YAML config file into a dict.

    Args:
        path: Path to the YAML config file.

    Returns:
        Parsed config dict with 'db' and 'checks' keys.

    Raises:
        FileNotFoundError: If the config file doesn't exist.
        ValueError: If the config is missing required keys.
    """
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with open(config_path) as f:
        config = yaml.safe_load(f)

    if not isinstance(config, dict):
        raise ValueError("Config file must contain a YAML mapping")
    if "checks" not in config:
        raise ValueError("Config file must contain a 'checks' key")

    return config


def _load_data(file_path: str) -> pl.DataFrame:
    """Load a data file into a Polars DataFrame.

    Args:
        file_path: Path to CSV or Parquet file.

    Returns:
        Polars DataFrame.

    Raises:
        FileNotFoundError: If the file doesn't exist.
        ValueError: If the file format is unsupported.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {file_path}")

    suffix = path.suffix.lower()
    if suffix == ".csv":
        return pl.read_csv(file_path)
    elif suffix == ".parquet":
        return pl.read_parquet(file_path)
    else:
        raise ValueError(f"Unsupported file format: {suffix}. Use .csv or .parquet")


def run_checks(file_path: str, config: Dict[str, Any]) -> bool:
    """Load data, run all checks from config, and return overall pass/fail.

    Args:
        file_path: Path to the data file.
        config: Parsed YAML config dict.

    Returns:
        True if all checks pass, False if any fail.
    """
    db_path = config.get("db", "validation_logs.db")
    checks: List[Dict[str, Any]] = config["checks"]

    df = _load_data(file_path)
    db = DBConnector(db_path)
    checker = DataQualityChecker(db)

    results = []
    for check in checks:
        check_type = check["type"]
        column = check.get("column", "")

        if check_type == "not_null":
            passed = checker.is_column_not_null(df, column)
        elif check_type == "unique":
            passed = checker.is_column_unique(df, column)
        elif check_type == "accepted_values":
            values = check.get("values", [])
            passed = checker.is_column_enum(df, column, values)
        else:
            print(f"  Unknown check type: {check_type}, skipping")
            continue

        status = "PASS" if passed else "FAIL"
        results.append((check_type, column, status))

    # Print summary table
    print(f"\nResults ({file_path}):")
    print(f"{'Check':<20} {'Column':<30} {'Result':<6}")
    print("-" * 56)
    for check_type, column, status in results:
        print(f"{check_type:<20} {column:<30} {status:<6}")

    all_passed = all(r[2] == "PASS" for r in results)
    total = len(results)
    passed_count = sum(1 for r in results if r[2] == "PASS")
    print(f"\n{passed_count}/{total} checks passed.")

    return all_passed


def main() -> None:
    """CLI entry point with check and logs subcommands."""
    parser = argparse.ArgumentParser(
        prog="dqc",
        description="Data Quality Checker - validate data files against quality rules",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # check subcommand
    check_parser = subparsers.add_parser(
        "check", help="Run data quality checks on a file"
    )
    check_parser.add_argument("file", help="Path to CSV or Parquet file")
    check_parser.add_argument(
        "--config", "-c", required=True, help="Path to YAML config file"
    )

    # logs subcommand
    logs_parser = subparsers.add_parser(
        "logs", help="Print all validation logs from a database"
    )
    logs_parser.add_argument("db", help="Path to SQLite database file")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    if args.command == "check":
        try:
            config = load_config(args.config)
            all_passed = run_checks(args.file, config)
            sys.exit(0 if all_passed else 1)
        except (FileNotFoundError, ValueError) as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.command == "logs":
        db_path = Path(args.db)
        if not db_path.exists():
            print(f"Error: Database file not found: {args.db}", file=sys.stderr)
            sys.exit(1)
        db = DBConnector(db_path)
        db.print_all_logs()
