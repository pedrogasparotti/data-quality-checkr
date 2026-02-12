# Data Quality Patterns

## Table of Contents
- [Validation Strategies](#validation-strategies)
- [Great Expectations](#great-expectations)
- [dbt Testing](#dbt-testing)
- [Data Quality Metrics](#data-quality-metrics)
- [Anomaly Detection](#anomaly-detection)
- [Quality Monitoring & Alerting](#quality-monitoring--alerting)
- [Data Quality Framework Design](#data-quality-framework-design)

---

## Validation Strategies

### The Four Pillars

| Check | What It Catches | When to Run |
|-------|-----------------|-------------|
| **Schema** | Missing columns, wrong types | On ingestion |
| **Completeness** | Nulls, missing records | After extraction |
| **Uniqueness** | Duplicates, key violations | Before loading |
| **Business Rules** | Invalid values, broken logic | After transformation |

### Schema Validation

```python
import polars as pl

def validate_schema(df: pl.DataFrame, expected_columns: dict) -> list[str]:
    """Return list of schema violations."""
    errors = []

    for col, dtype in expected_columns.items():
        if col not in df.columns:
            errors.append(f"Missing column: {col}")
        elif df[col].dtype != dtype:
            errors.append(f"{col}: expected {dtype}, got {df[col].dtype}")

    unexpected = set(df.columns) - set(expected_columns.keys())
    for col in unexpected:
        errors.append(f"Unexpected column: {col}")

    return errors
```

### Completeness Checks

```python
def check_completeness(
    df: pl.DataFrame,
    required_columns: list[str],
    max_null_pct: float = 0.0,
) -> dict:
    """Check null rates against thresholds."""
    results = {}
    for col in required_columns:
        null_pct = df[col].null_count() / len(df) if len(df) > 0 else 0
        results[col] = {
            "null_count": df[col].null_count(),
            "null_pct": round(null_pct, 4),
            "passed": null_pct <= max_null_pct,
        }
    return results
```

### Freshness Checks

```sql
-- Check if data is stale
SELECT
    'orders' AS table_name,
    MAX(updated_at) AS last_update,
    NOW() - MAX(updated_at) AS staleness,
    CASE
        WHEN NOW() - MAX(updated_at) > INTERVAL '2 hours' THEN 'STALE'
        ELSE 'FRESH'
    END AS status
FROM orders;
```

```python
from datetime import datetime, timedelta

def check_freshness(
    df: pl.DataFrame,
    timestamp_col: str,
    max_delay: timedelta,
) -> bool:
    """Check if most recent record is within acceptable delay."""
    latest = df[timestamp_col].max()
    if latest is None:
        return False
    return datetime.now() - latest <= max_delay
```

### Referential Integrity

```python
def check_referential_integrity(
    child_df: pl.DataFrame,
    parent_df: pl.DataFrame,
    child_key: str,
    parent_key: str,
) -> dict:
    """Find orphan records in child table."""
    parent_keys = set(parent_df[parent_key].to_list())
    child_keys = set(child_df[child_key].to_list())
    orphans = child_keys - parent_keys

    return {
        "total_child_keys": len(child_keys),
        "orphan_count": len(orphans),
        "orphan_examples": list(orphans)[:10],
        "passed": len(orphans) == 0,
    }
```

---

## Great Expectations

### Setup

```bash
pip install great_expectations
great_expectations init
```

### Checkpoint Pattern

```python
import great_expectations as gx

context = gx.get_context()

# Define expectations
suite = context.add_expectation_suite("orders_suite")

# Add expectations
suite.add_expectation(
    gx.expectations.ExpectColumnValuesToNotBeNull(column="order_id")
)
suite.add_expectation(
    gx.expectations.ExpectColumnValuesToBeUnique(column="order_id")
)
suite.add_expectation(
    gx.expectations.ExpectColumnValuesToBeBetween(
        column="amount", min_value=0, max_value=100000
    )
)
suite.add_expectation(
    gx.expectations.ExpectColumnValuesToBeInSet(
        column="status",
        value_set=["pending", "shipped", "delivered", "cancelled"],
    )
)
```

### Custom Expectation

```python
from great_expectations.expectations import ExpectColumnValuesToMatchRegex

# Email validation
suite.add_expectation(
    ExpectColumnValuesToMatchRegex(
        column="email",
        regex=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$",
    )
)
```

---

## dbt Testing

### Built-in Tests

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
      - name: customer_id
        tests:
          - not_null
          - relationships:
              to: ref('dim_customers')
              field: customer_id
      - name: status
        tests:
          - accepted_values:
              values: ['pending', 'shipped', 'delivered', 'cancelled']
      - name: amount
        tests:
          - not_null
```

### Custom Singular Tests

```sql
-- tests/assert_no_negative_revenue.sql
-- Fails if any rows are returned
SELECT order_id, amount
FROM {{ ref('fct_orders') }}
WHERE amount < 0
```

```sql
-- tests/assert_orders_have_customers.sql
SELECT o.order_id
FROM {{ ref('fct_orders') }} o
LEFT JOIN {{ ref('dim_customers') }} c
    ON o.customer_id = c.customer_id
WHERE c.customer_id IS NULL
```

### Custom Generic Tests

```sql
-- macros/test_is_positive.sql
{% test is_positive(model, column_name) %}
SELECT {{ column_name }}
FROM {{ model }}
WHERE {{ column_name }} < 0
{% endtest %}
```

```yaml
# Usage in schema.yml
- name: amount
  tests:
    - is_positive
```

### dbt Source Freshness

```yaml
# models/sources.yml
sources:
  - name: raw
    freshness:
      warn_after: {count: 12, period: hour}
      error_after: {count: 24, period: hour}
    loaded_at_field: _loaded_at
    tables:
      - name: orders
      - name: customers
```

```bash
dbt source freshness
```

---

## Data Quality Metrics

### Key Metrics to Track

| Metric | Formula | Good Threshold |
|--------|---------|----------------|
| Completeness | `1 - (null_count / total_rows)` | > 99% |
| Uniqueness | `unique_count / total_rows` | 100% for keys |
| Freshness | `now() - max(updated_at)` | < SLA window |
| Validity | `valid_rows / total_rows` | > 99.9% |
| Consistency | Cross-table agreement | 100% |

### Quality Score Calculator

```python
from dataclasses import dataclass

@dataclass
class QualityScore:
    completeness: float
    uniqueness: float
    validity: float
    overall: float

def calculate_quality_score(
    df: pl.DataFrame,
    key_columns: list[str],
    required_columns: list[str],
) -> QualityScore:
    total = len(df)
    if total == 0:
        return QualityScore(1.0, 1.0, 1.0, 1.0)

    # Completeness: % of non-null values in required columns
    null_counts = sum(df[col].null_count() for col in required_columns)
    total_cells = total * len(required_columns)
    completeness = 1 - (null_counts / total_cells)

    # Uniqueness: % of unique rows by key
    unique_count = df.select(key_columns).unique().height
    uniqueness = unique_count / total

    # Validity: rows that pass all checks
    validity = completeness * uniqueness

    overall = (completeness + uniqueness + validity) / 3

    return QualityScore(
        completeness=round(completeness, 4),
        uniqueness=round(uniqueness, 4),
        validity=round(validity, 4),
        overall=round(overall, 4),
    )
```

---

## Anomaly Detection

### Statistical Bounds

```python
def detect_anomalies_zscore(
    df: pl.DataFrame,
    column: str,
    threshold: float = 3.0,
) -> pl.DataFrame:
    """Flag rows where values are beyond Z-score threshold."""
    mean = df[column].mean()
    std = df[column].std()

    return df.with_columns(
        ((pl.col(column) - mean) / std).abs().alias("z_score")
    ).filter(pl.col("z_score") > threshold)
```

### Volume Anomalies

```python
def check_volume_anomaly(
    current_count: int,
    historical_counts: list[int],
    threshold_pct: float = 0.5,
) -> bool:
    """Flag if current volume deviates from historical average."""
    if not historical_counts:
        return False

    avg = sum(historical_counts) / len(historical_counts)
    if avg == 0:
        return current_count > 0

    deviation = abs(current_count - avg) / avg
    return deviation > threshold_pct
```

### Distribution Drift

```sql
-- Compare today's distribution to last 7-day average
WITH today AS (
    SELECT status, COUNT(*) AS cnt
    FROM orders
    WHERE order_date = CURRENT_DATE
    GROUP BY status
),
baseline AS (
    SELECT status, COUNT(*) / 7.0 AS avg_cnt
    FROM orders
    WHERE order_date BETWEEN CURRENT_DATE - 7 AND CURRENT_DATE - 1
    GROUP BY status
)
SELECT
    COALESCE(t.status, b.status) AS status,
    t.cnt AS today_count,
    ROUND(b.avg_cnt) AS avg_count,
    ROUND(100.0 * (t.cnt - b.avg_cnt) / NULLIF(b.avg_cnt, 0), 1) AS pct_change
FROM today t
FULL OUTER JOIN baseline b ON t.status = b.status
ORDER BY ABS(t.cnt - b.avg_cnt) DESC;
```

---

## Quality Monitoring & Alerting

### Logging Quality Results

```python
import json
import sqlite3
from datetime import datetime

def log_quality_check(
    db_path: str,
    table_name: str,
    check_name: str,
    passed: bool,
    details: dict,
) -> None:
    """Log quality check result to monitoring table."""
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO quality_log
            (timestamp, table_name, check_name, passed, details)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                datetime.now().isoformat(),
                table_name,
                check_name,
                int(passed),
                json.dumps(details),
            ),
        )
```

### Alert Patterns

```python
import logging

logger = logging.getLogger("data_quality")

def quality_gate(checks: list[dict]) -> bool:
    """Run all checks and alert on failures."""
    all_passed = True

    for check in checks:
        if not check["passed"]:
            all_passed = False
            logger.error(
                f"QUALITY FAILURE: {check['name']} - {check['details']}"
            )
        else:
            logger.info(f"QUALITY PASS: {check['name']}")

    if not all_passed:
        # Send alert (Slack, PagerDuty, email, etc.)
        send_alert(checks)

    return all_passed
```

---

## Data Quality Framework Design

### Build vs Buy

| Approach | Pros | Cons |
|----------|------|------|
| **Custom (this library)** | Simple, tailored, no overhead | Must maintain yourself |
| **Great Expectations** | Feature-rich, community | Complex setup, learning curve |
| **dbt tests** | Integrated with transforms | SQL-only, limited to warehouse |
| **Monte Carlo/Bigeye** | Auto-anomaly detection | Expensive, SaaS dependency |

### Quality Check Pipeline

```python
def run_quality_pipeline(df: pl.DataFrame, config: dict) -> bool:
    """Run all configured quality checks."""
    results = []

    # Schema checks
    schema_errors = validate_schema(df, config["expected_schema"])
    results.append({"name": "schema", "passed": len(schema_errors) == 0})

    # Completeness checks
    completeness = check_completeness(df, config["required_columns"])
    results.append({
        "name": "completeness",
        "passed": all(c["passed"] for c in completeness.values()),
    })

    # Uniqueness checks
    for key_col in config["unique_columns"]:
        is_unique = df[key_col].is_duplicated().sum() == 0
        results.append({"name": f"unique_{key_col}", "passed": is_unique})

    # Business rules
    for rule in config.get("business_rules", []):
        passed = rule["check_fn"](df)
        results.append({"name": rule["name"], "passed": passed})

    return quality_gate(results)
```
