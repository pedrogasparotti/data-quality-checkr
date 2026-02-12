import json
import sqlite3
from pathlib import Path
from unittest.mock import patch

import polars as pl
import pytest
import yaml

from data_quality_checker.cli import load_config, run_checks, main, _load_data


class TestLoadConfig:
    def test_loads_valid_yaml(self, tmp_path: Path) -> None:
        config_file = tmp_path / "checks.yml"
        config_file.write_text(
            yaml.dump({"db": "test.db", "checks": [{"type": "not_null", "column": "id"}]})
        )
        config = load_config(str(config_file))
        assert config["db"] == "test.db"
        assert len(config["checks"]) == 1
        assert config["checks"][0]["type"] == "not_null"

    def test_missing_file_raises_error(self) -> None:
        with pytest.raises(FileNotFoundError, match="Config file not found"):
            load_config("/nonexistent/checks.yml")

    def test_missing_checks_key_raises_error(self, tmp_path: Path) -> None:
        config_file = tmp_path / "bad.yml"
        config_file.write_text(yaml.dump({"db": "test.db"}))
        with pytest.raises(ValueError, match="must contain a 'checks' key"):
            load_config(str(config_file))

    def test_invalid_yaml_structure_raises_error(self, tmp_path: Path) -> None:
        config_file = tmp_path / "bad.yml"
        config_file.write_text("just a string")
        with pytest.raises(ValueError, match="must contain a YAML mapping"):
            load_config(str(config_file))


class TestLoadData:
    def test_load_csv(self, tmp_path: Path) -> None:
        csv_file = tmp_path / "data.csv"
        df = pl.DataFrame({"id": [1, 2, 3], "name": ["a", "b", "c"]})
        df.write_csv(str(csv_file))
        loaded = _load_data(str(csv_file))
        assert loaded.shape == (3, 2)

    def test_load_parquet(self, tmp_path: Path) -> None:
        parquet_file = tmp_path / "data.parquet"
        df = pl.DataFrame({"id": [1, 2, 3]})
        df.write_parquet(str(parquet_file))
        loaded = _load_data(str(parquet_file))
        assert loaded.shape == (3, 1)

    def test_missing_file_raises_error(self) -> None:
        with pytest.raises(FileNotFoundError, match="Data file not found"):
            _load_data("/nonexistent/data.csv")

    def test_unsupported_format_raises_error(self, tmp_path: Path) -> None:
        txt_file = tmp_path / "data.txt"
        txt_file.write_text("hello")
        with pytest.raises(ValueError, match="Unsupported file format"):
            _load_data(str(txt_file))


class TestRunChecks:
    def test_all_checks_pass(self, tmp_path: Path) -> None:
        csv_file = tmp_path / "data.csv"
        df = pl.DataFrame({"id": [1, 2, 3], "status": ["a", "b", "a"]})
        df.write_csv(str(csv_file))

        config = {
            "db": str(tmp_path / "test.db"),
            "checks": [
                {"type": "not_null", "column": "id"},
                {"type": "unique", "column": "id"},
                {"type": "accepted_values", "column": "status", "values": ["a", "b"]},
            ],
        }

        result = run_checks(str(csv_file), config)
        assert result is True

    def test_failing_check_returns_false(self, tmp_path: Path) -> None:
        csv_file = tmp_path / "data.csv"
        df = pl.DataFrame({"id": [1, 1, 3]})
        df.write_csv(str(csv_file))

        config = {
            "db": str(tmp_path / "test.db"),
            "checks": [{"type": "unique", "column": "id"}],
        }

        result = run_checks(str(csv_file), config)
        assert result is False

    def test_uses_default_db_path(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        csv_file = tmp_path / "data.csv"
        df = pl.DataFrame({"id": [1, 2]})
        df.write_csv(str(csv_file))

        config = {"checks": [{"type": "not_null", "column": "id"}]}
        run_checks(str(csv_file), config)
        assert (tmp_path / "validation_logs.db").exists()

    def test_unknown_check_type_skipped(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        csv_file = tmp_path / "data.csv"
        df = pl.DataFrame({"id": [1, 2]})
        df.write_csv(str(csv_file))

        config = {
            "db": str(tmp_path / "test.db"),
            "checks": [{"type": "unknown_check", "column": "id"}],
        }

        result = run_checks(str(csv_file), config)
        captured = capsys.readouterr()
        assert "Unknown check type" in captured.out
        assert result is True  # No valid checks failed

    def test_results_logged_to_db(self, tmp_path: Path) -> None:
        csv_file = tmp_path / "data.csv"
        df = pl.DataFrame({"id": [1, 2, 3]})
        df.write_csv(str(csv_file))

        db_path = tmp_path / "test.db"
        config = {
            "db": str(db_path),
            "checks": [
                {"type": "not_null", "column": "id"},
                {"type": "unique", "column": "id"},
            ],
        }

        run_checks(str(csv_file), config)

        with sqlite3.connect(db_path) as conn:
            count = conn.execute("SELECT COUNT(*) FROM validation_log").fetchone()[0]
        assert count == 2

    def test_prints_summary_table(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        csv_file = tmp_path / "data.csv"
        df = pl.DataFrame({"id": [1, 2, 3]})
        df.write_csv(str(csv_file))

        config = {
            "db": str(tmp_path / "test.db"),
            "checks": [{"type": "not_null", "column": "id"}],
        }

        run_checks(str(csv_file), config)
        captured = capsys.readouterr()
        assert "not_null" in captured.out
        assert "id" in captured.out
        assert "PASS" in captured.out
        assert "1/1 checks passed" in captured.out


class TestMainCLI:
    def test_check_command_success(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        csv_file = tmp_path / "data.csv"
        df = pl.DataFrame({"id": [1, 2, 3]})
        df.write_csv(str(csv_file))

        config_file = tmp_path / "checks.yml"
        config_file.write_text(yaml.dump({
            "db": str(tmp_path / "test.db"),
            "checks": [{"type": "not_null", "column": "id"}],
        }))

        monkeypatch.setattr(
            "sys.argv", ["dqc", "check", str(csv_file), "--config", str(config_file)]
        )

        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0

    def test_check_command_failure(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        csv_file = tmp_path / "data.csv"
        df = pl.DataFrame({"id": [1, 1, 3]})
        df.write_csv(str(csv_file))

        config_file = tmp_path / "checks.yml"
        config_file.write_text(yaml.dump({
            "db": str(tmp_path / "test.db"),
            "checks": [{"type": "unique", "column": "id"}],
        }))

        monkeypatch.setattr(
            "sys.argv", ["dqc", "check", str(csv_file), "--config", str(config_file)]
        )

        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1

    def test_check_command_missing_config(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        csv_file = tmp_path / "data.csv"
        pl.DataFrame({"id": [1]}).write_csv(str(csv_file))

        monkeypatch.setattr(
            "sys.argv", ["dqc", "check", str(csv_file), "--config", "/nonexistent.yml"]
        )

        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1

    def test_logs_command(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
        from data_quality_checker.connector.output_log import DBConnector
        db_path = tmp_path / "test.db"
        db = DBConnector(db_path)
        db.log("unique", True, {"column": "id"})

        monkeypatch.setattr("sys.argv", ["dqc", "logs", str(db_path)])
        main()

        captured = capsys.readouterr()
        assert "unique" in captured.out
        assert "PASS" in captured.out

    def test_logs_command_missing_db(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("sys.argv", ["dqc", "logs", "/nonexistent.db"])

        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1

    def test_no_command_shows_help(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("sys.argv", ["dqc"])

        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1

    def test_check_command_short_config_flag(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        csv_file = tmp_path / "data.csv"
        pl.DataFrame({"id": [1, 2]}).write_csv(str(csv_file))

        config_file = tmp_path / "checks.yml"
        config_file.write_text(yaml.dump({
            "db": str(tmp_path / "test.db"),
            "checks": [{"type": "not_null", "column": "id"}],
        }))

        monkeypatch.setattr(
            "sys.argv", ["dqc", "check", str(csv_file), "-c", str(config_file)]
        )

        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0
