# Python for Data Engineering

## Table of Contents
- [Core Data Processing](#core-data-processing)
- [File I/O Patterns](#file-io-patterns)
- [Data Validation](#data-validation)
- [Performance Optimization](#performance-optimization)
- [Testing Patterns](#testing-patterns)
- [Common Utilities](#common-utilities)

---

## Core Data Processing

### Polars: Modern DataFrame Library

```python
import polars as pl

# Read and transform
df = (
    pl.read_parquet("events.parquet")
    .filter(pl.col("event_time") >= "2024-01-01")
    .with_columns([
        pl.col("user_id").cast(pl.Utf8),
        pl.col("revenue").round(2),
    ])
    .group_by("user_id")
    .agg([
        pl.count().alias("event_count"),
        pl.col("revenue").sum().alias("total_revenue"),
    ])
)
```

### DuckDB: SQL on Local Files

```python
import duckdb

con = duckdb.connect("warehouse.db")

# Query parquet files directly with SQL
result = con.execute("""
    SELECT
        user_id,
        DATE_TRUNC('day', event_time) AS event_date,
        COUNT(*) AS event_count
    FROM read_parquet('events/*.parquet')
    WHERE event_time >= '2024-01-01'
    GROUP BY 1, 2
""").pl()  # Returns Polars DataFrame
```

### When to Use What

| Data Size | Processing | Tool Choice |
|-----------|------------|-------------|
| < 1GB | In-memory | Polars, pandas |
| 1-100GB | Single machine | DuckDB, Polars lazy |
| > 100GB | Distributed | Spark, Snowflake, BigQuery |

---

## File I/O Patterns

### Reading Data

**Parquet (preferred for analytics)**
```python
import polars as pl

# Single file
df = pl.read_parquet("data.parquet")

# Partitioned directory
df = pl.scan_parquet("data/**/*.parquet").collect()

# Specific columns only
df = pl.read_parquet("data.parquet", columns=["user_id", "revenue"])
```

**CSV with messy data**
```python
df = pl.read_csv(
    "messy_data.csv",
    has_header=True,
    skip_rows=2,
    ignore_errors=True,
    null_values=["NA", "NULL", ""],
    encoding="utf8-lossy",
)
```

**JSON Lines (event streams, logs)**
```python
# Polars native
df = pl.read_ndjson("events.jsonl")

# Standard library (streaming)
import json
from pathlib import Path

def read_jsonl(filepath: Path):
    with open(filepath) as f:
        for line in f:
            yield json.loads(line)
```

### Writing Data

```python
# Parquet with compression
df.write_parquet("output.parquet", compression="snappy")

# CSV with custom separator
df.write_csv("output.csv", separator="|")

# JSON Lines
df.write_ndjson("output.jsonl")
```

### Streaming Large Files

```python
# Lazy evaluation: only loads what's needed
result = (
    pl.scan_parquet("huge_file.parquet")
    .filter(pl.col("year") == 2024)
    .select(["user_id", "revenue"])
    .collect()
)

# Process CSV in batches
reader = pl.read_csv_batched("large.csv", batch_size=100_000)
for chunk in reader:
    process(chunk)
```

---

## Data Validation

### Schema Validation

```python
import polars as pl
from typing import Dict, Any

def validate_schema(df: pl.DataFrame, expected: Dict[str, Any]) -> None:
    """Validate DataFrame matches expected schema."""
    for col_name, expected_type in expected.items():
        if col_name not in df.columns:
            raise ValueError(f"Missing column: {col_name}")
        if df[col_name].dtype != expected_type:
            raise TypeError(
                f"Column {col_name}: expected {expected_type}, "
                f"got {df[col_name].dtype}"
            )

# Usage
validate_schema(df, {
    "user_id": pl.Utf8,
    "event_time": pl.Datetime,
    "revenue": pl.Float64,
})
```

### Quality Check Pattern

```python
from dataclasses import dataclass

@dataclass
class QualityReport:
    total_rows: int
    null_counts: dict
    duplicate_count: int
    passed: bool

def quality_check(df: pl.DataFrame, unique_cols: list[str]) -> QualityReport:
    null_counts = {col: df[col].null_count() for col in df.columns}
    duplicate_count = df.select(unique_cols).is_duplicated().sum()
    has_critical_nulls = any(
        count > 0 for col, count in null_counts.items()
        if col in unique_cols
    )

    return QualityReport(
        total_rows=len(df),
        null_counts=null_counts,
        duplicate_count=duplicate_count,
        passed=not has_critical_nulls and duplicate_count == 0,
    )
```

---

## Performance Optimization

### Lazy Evaluation

```python
# BAD: loads everything into memory
df = pl.read_parquet("huge.parquet")
filtered = df.filter(pl.col("year") == 2024)
result = filtered.select(["user_id", "revenue"])

# GOOD: query plan optimized, only loads needed data
result = (
    pl.scan_parquet("huge.parquet")
    .filter(pl.col("year") == 2024)
    .select(["user_id", "revenue"])
    .collect()
)
```

### Vectorized Operations

```python
# BAD: row-by-row iteration
total = 0
for row in df.iter_rows():
    if row[1] > 100:
        total += row[1]

# GOOD: vectorized
total = df.filter(pl.col("revenue") > 100)["revenue"].sum()
```

### Parallel File Processing

```python
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
import polars as pl

def process_file(filepath: Path) -> pl.DataFrame:
    return pl.read_parquet(filepath).filter(pl.col("year") == 2024)

def process_directory(dir_path: Path) -> pl.DataFrame:
    files = list(dir_path.glob("*.parquet"))
    with ProcessPoolExecutor() as executor:
        results = executor.map(process_file, files)
    return pl.concat(list(results))
```

---

## Testing Patterns

### Unit Testing with Pytest

```python
import polars as pl
import pytest

@pytest.fixture
def sample_events():
    return pl.DataFrame({
        "event_id": [1, 2, 3],
        "user_id": ["u1", "u2", "u3"],
        "revenue": [10.0, 20.0, 30.0],
    })

def test_clean_removes_duplicates(sample_events):
    result = clean_user_events(sample_events)
    assert result["event_id"].is_duplicated().sum() == 0

def test_aggregate_sums_revenue(sample_events):
    result = aggregate_metrics(sample_events, ["user_id"])
    assert result["total_revenue"].sum() == 60.0
```

### Integration Testing

```python
import tempfile
from pathlib import Path

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_full_pipeline(temp_dir):
    # Setup
    input_file = temp_dir / "input.csv"
    test_data = pl.DataFrame({"id": [1, 2], "value": [10, 20]})
    test_data.write_csv(input_file)

    # Execute
    df = pl.read_csv(input_file)
    output_file = temp_dir / "output.parquet"
    df.write_parquet(output_file)

    # Verify
    result = pl.read_parquet(output_file)
    assert len(result) == 2
```

---

## Common Utilities

### Logging Setup

```python
import logging
from pathlib import Path

def setup_logging(
    name: str = "my_data_lib",
    level: int = logging.INFO,
    log_file: Path | None = None,
) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    console = logging.StreamHandler()
    console.setFormatter(formatter)
    logger.addHandler(console)

    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
```

### Configuration with Dataclasses

```python
from dataclasses import dataclass
from pathlib import Path
import os

@dataclass
class Config:
    db_connection_string: str
    data_dir: Path
    output_dir: Path
    chunk_size: int = 100_000

    @classmethod
    def from_env(cls) -> "Config":
        return cls(
            db_connection_string=os.getenv("DB_CONN", "duckdb://warehouse.db"),
            data_dir=Path(os.getenv("DATA_DIR", "./data")),
            output_dir=Path(os.getenv("OUTPUT_DIR", "./output")),
            chunk_size=int(os.getenv("CHUNK_SIZE", "100000")),
        )
```

### Type Hints for DataFrames

```python
from typing import Protocol
import polars as pl

class DataFrameTransformer(Protocol):
    def __call__(self, df: pl.DataFrame) -> pl.DataFrame: ...

def apply_transformations(
    df: pl.DataFrame,
    transformations: list[DataFrameTransformer],
) -> pl.DataFrame:
    result = df
    for transform in transformations:
        result = transform(result)
    return result

# Usage
cleaned = apply_transformations(df, [remove_nulls, deduplicate])
```

---

## Modern Python Packaging

### pyproject.toml (the only config file you need)

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "my_data_lib"
version = "0.1.0"
requires-python = ">=3.9"
dependencies = ["polars>=0.20.0"]

[project.optional-dependencies]
dev = ["pytest>=7.0", "ruff>=0.1.0"]
```

### Building and Installing

```bash
# Editable install for development
pip install -e ".[dev]"

# Build distribution
python -m build

# With uv
uv sync --all-extras
uv build
```

---

## Best Practices Summary

1. **Package your code** - Use `pyproject.toml`, not loose scripts
2. **Test everything** - Unit, integration, and edge cases
3. **Use type hints** - Catch errors early
4. **Optimize lazily** - Profile first, optimize second
5. **Choose the right tool** - stdlib -> Polars -> DuckDB -> Spark
6. **Log, don't print** - Use the logging module
