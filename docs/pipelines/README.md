# Pipeline Patterns & Orchestration

## Table of Contents
- [ETL vs ELT](#etl-vs-elt)
- [Airflow DAG Patterns](#airflow-dag-patterns)
- [dbt Patterns](#dbt-patterns)
- [Idempotency Patterns](#idempotency-patterns)
- [Incremental Processing](#incremental-processing)
- [Error Handling & Retries](#error-handling--retries)
- [Pipeline Testing](#pipeline-testing)

---

## ETL vs ELT

### ETL (Extract, Transform, Load)

Transform data before loading into the warehouse. Use when:
- Data needs cleaning before storage
- Warehouse compute is expensive
- Sensitive data must be masked before landing

```
Source → Extract → Transform (Python/Spark) → Load → Warehouse
```

### ELT (Extract, Load, Transform)

Load raw data first, transform inside the warehouse. Use when:
- Warehouse compute is cheap (Snowflake, BigQuery)
- You want a raw data layer for auditability
- Transformations are SQL-heavy

```
Source → Extract → Load → Warehouse → Transform (dbt/SQL)
```

### Hybrid Pattern (Most Common)

```
Source → Extract → Light Clean (Python) → Load → Raw Layer
Raw Layer → Transform (dbt) → Staging → Marts
```

---

## Airflow DAG Patterns

### Basic DAG Structure

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
from datetime import timedelta

default_args = {
    "owner": "data-team",
    "retries": 3,
    "retry_delay": timedelta(minutes=5),
    "email_on_failure": True,
    "email": ["data-team@company.com"],
}

with DAG(
    dag_id="user_events_pipeline",
    default_args=default_args,
    schedule_interval="@daily",
    start_date=days_ago(1),
    catchup=False,
    tags=["production", "events"],
) as dag:

    extract = PythonOperator(
        task_id="extract_events",
        python_callable=extract_events,
        op_kwargs={"date": "{{ ds }}"},
    )

    validate = PythonOperator(
        task_id="validate_data",
        python_callable=validate_data,
    )

    load = PythonOperator(
        task_id="load_to_warehouse",
        python_callable=load_to_warehouse,
    )

    extract >> validate >> load
```

### Branching Pattern

```python
from airflow.operators.python import BranchPythonOperator

def choose_path(**context):
    row_count = context["ti"].xcom_pull(task_ids="count_rows")
    if row_count > 0:
        return "process_data"
    return "send_empty_alert"

branch = BranchPythonOperator(
    task_id="check_data",
    python_callable=choose_path,
)

branch >> [process_data, send_empty_alert]
```

### Sensor Pattern (Wait for Data)

```python
from airflow.sensors.filesystem import FileSensor
from airflow.sensors.external_task import ExternalTaskSensor

# Wait for file to appear
wait_for_file = FileSensor(
    task_id="wait_for_export",
    filepath="/data/exports/{{ ds }}/users.csv",
    poke_interval=300,  # Check every 5 minutes
    timeout=3600,       # Timeout after 1 hour
    mode="reschedule",  # Free up worker slot while waiting
)

# Wait for upstream DAG
wait_for_upstream = ExternalTaskSensor(
    task_id="wait_for_ingestion",
    external_dag_id="raw_ingestion",
    external_task_id="load_complete",
    timeout=7200,
)
```

### TaskGroup for Organization

```python
from airflow.utils.task_group import TaskGroup

with TaskGroup("quality_checks") as quality_group:
    check_nulls = PythonOperator(task_id="check_nulls", ...)
    check_dupes = PythonOperator(task_id="check_dupes", ...)
    check_freshness = PythonOperator(task_id="check_freshness", ...)

extract >> quality_group >> load
```

---

## dbt Patterns

### Model Layers

```
models/
├── staging/          # 1:1 with source tables, light cleaning
│   ├── stg_users.sql
│   └── stg_orders.sql
├── intermediate/     # Business logic joins
│   └── int_user_orders.sql
└── marts/            # Final tables for consumers
    ├── dim_users.sql
    └── fct_orders.sql
```

### Staging Model

```sql
-- models/staging/stg_orders.sql
WITH source AS (
    SELECT * FROM {{ source('raw', 'orders') }}
),

renamed AS (
    SELECT
        id AS order_id,
        customer_id,
        CAST(order_date AS DATE) AS order_date,
        CAST(amount AS DECIMAL(10,2)) AS amount,
        LOWER(status) AS status,
        _loaded_at
    FROM source
    WHERE id IS NOT NULL
)

SELECT * FROM renamed
```

### Incremental Model

```sql
-- models/marts/fct_orders.sql
{{
    config(
        materialized='incremental',
        unique_key='order_id',
        on_schema_change='sync_all_columns'
    )
}}

SELECT
    order_id,
    customer_id,
    order_date,
    amount,
    status,
    updated_at
FROM {{ ref('stg_orders') }}

{% if is_incremental() %}
WHERE updated_at > (SELECT MAX(updated_at) FROM {{ this }})
{% endif %}
```

### dbt Tests

```yaml
# models/schema.yml
version: 2

models:
  - name: fct_orders
    columns:
      - name: order_id
        tests:
          - unique
          - not_null
      - name: status
        tests:
          - accepted_values:
              values: ['pending', 'shipped', 'delivered', 'cancelled']
      - name: customer_id
        tests:
          - relationships:
              to: ref('dim_users')
              field: user_id
```

### Custom dbt Test

```sql
-- tests/assert_positive_revenue.sql
SELECT order_id, amount
FROM {{ ref('fct_orders') }}
WHERE amount < 0
```

### dbt Macros

```sql
-- macros/cents_to_dollars.sql
{% macro cents_to_dollars(column_name) %}
    ROUND({{ column_name }} / 100.0, 2)
{% endmacro %}

-- Usage in model
SELECT
    order_id,
    {{ cents_to_dollars('amount_cents') }} AS amount
FROM {{ ref('stg_orders') }}
```

---

## Idempotency Patterns

### Delete-Insert (Most Common)

```python
def load_partition(df, table_name, partition_date, conn):
    """Delete existing partition, then insert new data."""
    conn.execute(
        f"DELETE FROM {table_name} WHERE partition_date = ?",
        [partition_date]
    )
    df.write_database(table_name, conn, if_table_exists="append")
```

### Merge/Upsert

```sql
-- PostgreSQL
INSERT INTO target_table (id, name, updated_at)
VALUES (:id, :name, :updated_at)
ON CONFLICT (id)
DO UPDATE SET
    name = EXCLUDED.name,
    updated_at = EXCLUDED.updated_at;
```

### Atomic Table Swap

```sql
-- Write to temp table, then swap
CREATE TABLE target_table_new AS
SELECT * FROM staging_table;

-- Atomic rename
ALTER TABLE target_table RENAME TO target_table_old;
ALTER TABLE target_table_new RENAME TO target_table;
DROP TABLE target_table_old;
```

---

## Incremental Processing

### Watermark Pattern

```python
def get_watermark(conn, table_name: str) -> str:
    """Get the last processed timestamp."""
    result = conn.execute(
        f"SELECT MAX(updated_at) FROM {table_name}"
    ).fetchone()
    return result[0] or "1970-01-01"

def extract_incremental(conn, source_table: str, watermark: str):
    """Extract only records newer than watermark."""
    return conn.execute(
        f"SELECT * FROM {source_table} WHERE updated_at > ?",
        [watermark]
    ).pl()
```

### Change Data Capture (CDC) Processing

```python
def apply_cdc_changes(target_df, cdc_events):
    """Apply insert/update/delete events to target."""
    for event in cdc_events:
        if event["op"] == "INSERT":
            target_df = pl.concat([target_df, event["after"]])
        elif event["op"] == "UPDATE":
            target_df = target_df.filter(
                pl.col("id") != event["after"]["id"]
            )
            target_df = pl.concat([target_df, event["after"]])
        elif event["op"] == "DELETE":
            target_df = target_df.filter(
                pl.col("id") != event["before"]["id"]
            )
    return target_df
```

---

## Error Handling & Retries

### Retry with Exponential Backoff

```python
import time
import logging

logger = logging.getLogger(__name__)

def retry_with_backoff(func, max_retries=3, base_delay=1):
    """Retry a function with exponential backoff."""
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            delay = base_delay * (2 ** attempt)
            logger.warning(
                f"Attempt {attempt + 1} failed: {e}. "
                f"Retrying in {delay}s..."
            )
            time.sleep(delay)
```

### Dead Letter Queue Pattern

```python
def process_records(records, dlq_path):
    """Process records, send failures to dead letter queue."""
    success = []
    failures = []

    for record in records:
        try:
            result = transform(record)
            success.append(result)
        except Exception as e:
            failures.append({
                "record": record,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            })

    if failures:
        with open(dlq_path, "a") as f:
            for fail in failures:
                f.write(json.dumps(fail) + "\n")

    return success
```

### Circuit Breaker

```python
class CircuitBreaker:
    def __init__(self, failure_threshold=5, reset_timeout=60):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open

    def call(self, func):
        if self.state == "open":
            if time.time() - self.last_failure_time > self.reset_timeout:
                self.state = "half-open"
            else:
                raise Exception("Circuit breaker is open")

        try:
            result = func()
            self.failure_count = 0
            self.state = "closed"
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            if self.failure_count >= self.failure_threshold:
                self.state = "open"
            raise
```

---

## Pipeline Testing

### Unit Testing Transforms

```python
import polars as pl
import pytest

def test_revenue_calculation():
    input_df = pl.DataFrame({
        "quantity": [2, 3],
        "unit_price": [10.0, 20.0],
    })
    result = calculate_revenue(input_df)
    assert result["revenue"].to_list() == [20.0, 60.0]
```

### Contract Testing (Schema)

```python
def test_output_schema():
    """Verify pipeline output matches expected schema."""
    result = run_pipeline(sample_data)

    assert set(result.columns) == {
        "user_id", "event_date", "event_count", "total_revenue"
    }
    assert result["user_id"].dtype == pl.Utf8
    assert result["total_revenue"].dtype == pl.Float64
```

### Data Quality Gates

```python
def quality_gate(df: pl.DataFrame) -> None:
    """Fail pipeline if quality thresholds not met."""
    null_pct = df["user_id"].null_count() / len(df)
    if null_pct > 0.01:
        raise ValueError(f"Null rate {null_pct:.2%} exceeds 1% threshold")

    dupe_pct = df["event_id"].is_duplicated().sum() / len(df)
    if dupe_pct > 0.001:
        raise ValueError(f"Duplicate rate {dupe_pct:.3%} exceeds 0.1% threshold")
```

---

## Useful Snippets

### Pipeline Metadata Tracking

```python
from dataclasses import dataclass
from datetime import datetime

@dataclass
class PipelineRun:
    pipeline_name: str
    start_time: datetime
    end_time: datetime | None = None
    rows_processed: int = 0
    status: str = "running"
    error_message: str | None = None

    def complete(self, rows: int):
        self.end_time = datetime.now()
        self.rows_processed = rows
        self.status = "success"

    def fail(self, error: str):
        self.end_time = datetime.now()
        self.status = "failed"
        self.error_message = error
```

### Backfill Script

```python
from datetime import date, timedelta

def backfill(start_date: date, end_date: date, process_fn):
    """Run pipeline for each date in range."""
    current = start_date
    while current <= end_date:
        try:
            process_fn(current)
            print(f"Processed {current}")
        except Exception as e:
            print(f"Failed {current}: {e}")
        current += timedelta(days=1)

# Usage
backfill(date(2024, 1, 1), date(2024, 1, 31), daily_pipeline)
```
