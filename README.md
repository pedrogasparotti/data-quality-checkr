# Data Quality Checker

Validate Polars DataFrames and log results to SQLite.

A lightweight Python library for data engineers who need to validate pipeline data without the overhead of heavyweight frameworks.

## Installation

```bash
pip install data-quality-checker
```

Or with [uv](https://github.com/astral-sh/uv):

```bash
uv add data-quality-checker
```

## Quick Start

```python
import polars as pl
from data_quality_checker import DataQualityChecker, DBConnector

# Setup
db = DBConnector("validation_logs.db")
checker = DataQualityChecker(db)

# Load data
df = pl.DataFrame({
    "user_id": [1, 2, 3],
    "email": ["a@test.com", "b@test.com", "c@test.com"],
    "status": ["active", "inactive", "active"],
})

# Run checks
checker.is_column_unique(df, "user_id")       # True
checker.is_column_not_null(df, "email")        # True
checker.is_column_enum(df, "status", ["active", "inactive", "pending"])  # True

# View results
db.print_all_logs()
```

## Features

| Check | Method | Description |
|-------|--------|-------------|
| Unique | `is_column_unique(df, column)` | All values are unique |
| Not Null | `is_column_not_null(df, column)` | No null values |
| Accepted Values | `is_column_enum(df, column, values)` | All values in accepted list |
| Referential Integrity | `are_tables_referential_integral(parent, child, pk, fk)` | All foreign keys exist in parent |

Each check:
- Returns `True` (pass) or `False` (fail)
- Logs the result to SQLite with timestamp and context
- Raises `ValueError` if the column doesn't exist

## API Reference

### `DBConnector(db_path)`

Manages SQLite connection and logging.

- `log(check_type, result, additional_params=None)` - Log a validation result
- `print_all_logs()` - Print all logged results

### `DataQualityChecker(db_connector)`

Validates Polars DataFrames.

- `is_column_unique(df, column)` - Check uniqueness
- `is_column_not_null(df, column)` - Check for nulls
- `is_column_enum(df, column, accepted_values)` - Check accepted values
- `are_tables_referential_integral(parent_df, child_df, parent_key, child_key)` - Check referential integrity

## Architecture

```
┌─────────────────┐
│  Data Engineer   │
│    [Person]      │
└────────┬─────────┘
         │ Uses
         ▼
┌─────────────────────────┐
│ DataQualityChecker      │
│                         │
│ - is_column_unique()    │
│ - is_column_not_null()  │
│ - is_column_enum()      │
│ - are_tables_           │
│   referential_integral()│
└────────┬────────────────┘
         │ Logs via
         ▼
┌─────────────────────────┐
│ DBConnector             │
│                         │
│ - log()                 │
│ - print_all_logs()      │
└────────┬────────────────┘
         │ Writes to
         ▼
┌─────────────────────────┐
│ SQLite (.db file)       │
│                         │
│ validation_log table    │
└─────────────────────────┘
```

## Development

```bash
# Clone and install
git clone <repo-url>
cd data-quality-checker
uv sync --all-extras

# Run tests
uv run pytest tests/

# Run with coverage
uv run pytest tests/ --cov=src/data_quality_checker
```

## Constraints

- **Dataset size**: < 100GB (single-machine processing)
- **Input type**: Polars DataFrames only
- **Result storage**: SQLite3
- **Python**: >= 3.9

## Reference Guides

| Topic | Description |
|-------|-------------|
| [SQL Guide](docs/sql/README.md) | Query patterns, optimization, window functions |
| [Python & PySpark](docs/python/README.md) | Data processing with Python ecosystem |
| [Pipeline Patterns](docs/pipelines/README.md) | ETL/ELT design and orchestration |
| [Data Quality](docs/data-quality/README.md) | Validation, testing, and monitoring |
| [CLI Tools](docs/cli/README.md) | Essential command-line references |
| [Architecture](docs/architecture/README.md) | Data platform design patterns |

## License

MIT
