# Data Architecture Patterns

## Table of Contents
- [Data Modeling](#data-modeling)
- [Data Lake & Lakehouse](#data-lake--lakehouse)
- [Stream vs Batch Processing](#stream-vs-batch-processing)
- [Data Warehouse Design](#data-warehouse-design)
- [Data Mesh](#data-mesh)
- [Change Data Capture (CDC)](#change-data-capture-cdc)
- [Schema Evolution](#schema-evolution)

---

## Data Modeling

### Star Schema

The most common warehouse pattern. One fact table surrounded by dimension tables.

```
              ┌──────────────┐
              │ dim_customer │
              │              │
              │ customer_id  │
              │ name         │
              │ segment      │
              └──────┬───────┘
                     │
┌──────────────┐     │     ┌──────────────┐
│ dim_product  │     │     │ dim_date     │
│              │     │     │              │
│ product_id   │     │     │ date_key     │
│ name         ├─────┤─────┤ date         │
│ category     │     │     │ month        │
└──────────────┘     │     │ quarter      │
                     │     └──────────────┘
              ┌──────┴───────┐
              │  fct_orders  │
              │              │
              │ order_id     │
              │ customer_id  │
              │ product_id   │
              │ date_key     │
              │ quantity     │
              │ amount       │
              └──────────────┘
```

```sql
-- Fact table: measures and foreign keys
CREATE TABLE fct_orders (
    order_id BIGINT PRIMARY KEY,
    customer_id INT REFERENCES dim_customer(customer_id),
    product_id INT REFERENCES dim_product(product_id),
    date_key INT REFERENCES dim_date(date_key),
    quantity INT NOT NULL,
    amount DECIMAL(10,2) NOT NULL
);

-- Dimension table: descriptive attributes
CREATE TABLE dim_customer (
    customer_id INT PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100),
    segment VARCHAR(50),
    created_at TIMESTAMP
);
```

### Snowflake Schema

Like star schema but dimensions are normalized into sub-dimensions.

```sql
-- Normalized: product -> category -> department
CREATE TABLE dim_department (
    department_id INT PRIMARY KEY,
    department_name VARCHAR(50)
);

CREATE TABLE dim_category (
    category_id INT PRIMARY KEY,
    category_name VARCHAR(50),
    department_id INT REFERENCES dim_department(department_id)
);

CREATE TABLE dim_product (
    product_id INT PRIMARY KEY,
    product_name VARCHAR(100),
    category_id INT REFERENCES dim_category(category_id)
);
```

**When to use**: Storage is expensive, updates to dimensions are frequent.
**When to avoid**: Query performance matters more than storage (most modern warehouses).

### Data Vault

Designed for agility and auditability. Three entity types:

| Entity | Purpose | Example |
|--------|---------|---------|
| **Hub** | Business keys | `hub_customer(customer_bk)` |
| **Link** | Relationships | `link_order(customer_hk, product_hk)` |
| **Satellite** | Descriptive data + history | `sat_customer(name, email, load_date)` |

```sql
-- Hub: business key + metadata
CREATE TABLE hub_customer (
    customer_hk CHAR(32) PRIMARY KEY,  -- Hash of business key
    customer_bk VARCHAR(50) NOT NULL,   -- Business key
    load_date TIMESTAMP NOT NULL,
    record_source VARCHAR(50)
);

-- Satellite: descriptive attributes with history
CREATE TABLE sat_customer (
    customer_hk CHAR(32) REFERENCES hub_customer(customer_hk),
    load_date TIMESTAMP NOT NULL,
    name VARCHAR(100),
    email VARCHAR(100),
    segment VARCHAR(50),
    hash_diff CHAR(32),                 -- Hash of attribute values
    PRIMARY KEY (customer_hk, load_date)
);

-- Link: relationships
CREATE TABLE link_order (
    order_hk CHAR(32) PRIMARY KEY,
    customer_hk CHAR(32) REFERENCES hub_customer(customer_hk),
    product_hk CHAR(32) REFERENCES hub_product(product_hk),
    load_date TIMESTAMP NOT NULL
);
```

**When to use**: Multiple source systems, need full audit trail, schema changes frequently.

---

## Data Lake & Lakehouse

### Data Lake Layers

```
┌─────────────────────────────────────────────┐
│                 Data Lake                    │
│                                              │
│  ┌────────────┐  ┌────────────┐  ┌────────┐ │
│  │   Bronze    │  │   Silver   │  │  Gold  │ │
│  │   (Raw)     │→ │ (Cleaned)  │→ │(Curated│ │
│  │             │  │            │  │        │ │
│  │ Raw files   │  │ Validated  │  │ Marts  │ │
│  │ As-is from  │  │ Deduplied  │  │ Aggs   │ │
│  │ sources     │  │ Typed      │  │ Ready  │ │
│  └────────────┘  └────────────┘  └────────┘ │
└─────────────────────────────────────────────┘
```

| Layer | Format | Processing | Consumers |
|-------|--------|-----------|-----------|
| **Bronze** | JSON, CSV, raw | None (land as-is) | Data engineers |
| **Silver** | Parquet, Delta | Clean, dedupe, type | Data engineers, analysts |
| **Gold** | Parquet, Delta | Aggregate, join, model | Analysts, dashboards, ML |

### Delta Lake / Apache Iceberg

Open table formats that add ACID transactions to data lakes.

```python
# Delta Lake (Spark)
from delta.tables import DeltaTable

# Write with ACID transactions
df.write.format("delta").mode("overwrite").save("s3://lake/orders/")

# Time travel
df_yesterday = spark.read.format("delta") \
    .option("timestampAsOf", "2024-01-01") \
    .load("s3://lake/orders/")

# Upsert (MERGE)
delta_table = DeltaTable.forPath(spark, "s3://lake/orders/")
delta_table.alias("target").merge(
    new_data.alias("source"),
    "target.order_id = source.order_id"
).whenMatchedUpdateAll() \
 .whenNotMatchedInsertAll() \
 .execute()
```

```python
# Apache Iceberg (via DuckDB)
import duckdb

con = duckdb.connect()
con.execute("INSTALL iceberg; LOAD iceberg;")
con.execute("SELECT * FROM iceberg_scan('s3://lake/orders/')")
```

### Partitioning Strategy

```
# Partition by date (most common)
s3://lake/orders/
├── year=2024/
│   ├── month=01/
│   │   ├── day=01/
│   │   │   ├── part-00001.parquet
│   │   │   └── part-00002.parquet
│   │   └── day=02/
│   └── month=02/
```

**Rules of thumb**:
- Partition by the most common filter column (usually date)
- Target 100MB-1GB per partition file
- Avoid over-partitioning (too many small files)
- Avoid under-partitioning (files too large to scan)

---

## Stream vs Batch Processing

### When to Use Each

| Aspect | Batch | Stream |
|--------|-------|--------|
| **Latency** | Minutes to hours | Seconds to minutes |
| **Complexity** | Lower | Higher |
| **Cost** | Lower (scheduled) | Higher (always-on) |
| **Use cases** | Reports, ML training | Alerts, real-time dashboards |
| **Tools** | Spark, dbt, Airflow | Kafka, Flink, Spark Streaming |

### Batch Processing

```python
# Daily batch job
def daily_batch_pipeline(date: str):
    # Extract
    raw = extract_from_source(date)

    # Transform
    cleaned = clean_and_validate(raw)
    aggregated = compute_daily_metrics(cleaned)

    # Load
    load_to_warehouse(aggregated, f"metrics_{date}")
```

### Stream Processing Concepts

```
Producer → Kafka Topic → Consumer Group → Processing → Sink

┌──────────┐    ┌─────────┐    ┌──────────┐    ┌──────────┐
│  Source   │ →  │  Kafka  │ →  │  Flink/  │ →  │  Sink    │
│  (App,   │    │  Topic  │    │  Spark   │    │  (DB,    │
│   DB)    │    │         │    │ Streaming│    │   S3)    │
└──────────┘    └─────────┘    └──────────┘    └──────────┘
```

### Lambda Architecture (Batch + Stream)

```
                    ┌─────────────┐
         ┌────────→│ Batch Layer │──────────┐
         │          │ (Complete,  │          │
         │          │  accurate)  │          ▼
┌────────┤          └─────────────┘    ┌──────────┐
│ Source  │                            │ Serving  │
│  Data   │                            │  Layer   │
└────────┤          ┌─────────────┐    └──────────┘
         │          │ Speed Layer │          ▲
         └────────→│ (Fast,      │──────────┘
                    │  approximate│
                    └─────────────┘
```

### Kappa Architecture (Stream Only)

Simplification: treat everything as a stream. Reprocess by replaying the stream.

```
Source → Kafka (immutable log) → Stream Processor → Serving Layer
                 ↑                       │
                 └── Replay for ─────────┘
                     reprocessing
```

---

## Data Warehouse Design

### Kimball vs Inmon

| Aspect | Kimball (Bottom-Up) | Inmon (Top-Down) |
|--------|-------------------|-----------------|
| **Approach** | Build dimensional marts first | Build enterprise model first |
| **Schema** | Star schema | 3NF normalized |
| **Time to value** | Fast (weeks) | Slow (months) |
| **Best for** | Analytics, BI | Enterprise integration |

### Slowly Changing Dimensions (SCD)

**Type 1: Overwrite**
```sql
-- Just update the record (no history)
UPDATE dim_customer
SET email = 'new@email.com'
WHERE customer_id = 123;
```

**Type 2: Add new row (most common)**
```sql
-- Close current record
UPDATE dim_customer
SET end_date = CURRENT_DATE - 1, is_current = FALSE
WHERE customer_id = 123 AND is_current = TRUE;

-- Insert new version
INSERT INTO dim_customer (customer_id, name, email, start_date, end_date, is_current)
VALUES (123, 'John', 'new@email.com', CURRENT_DATE, '9999-12-31', TRUE);
```

**Type 3: Add column**
```sql
ALTER TABLE dim_customer ADD COLUMN previous_email VARCHAR(100);

UPDATE dim_customer
SET previous_email = email, email = 'new@email.com'
WHERE customer_id = 123;
```

### Materialized Views

```sql
-- Create materialized view for expensive aggregations
CREATE MATERIALIZED VIEW mv_daily_revenue AS
SELECT
    DATE_TRUNC('day', order_date) AS day,
    SUM(amount) AS total_revenue,
    COUNT(DISTINCT customer_id) AS unique_customers
FROM fct_orders
GROUP BY 1;

-- Refresh (schedule via cron or Airflow)
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_daily_revenue;
```

---

## Data Mesh

### Core Principles

1. **Domain Ownership**: Each team owns its data products
2. **Data as a Product**: Discoverable, trustworthy, self-describing
3. **Self-Serve Platform**: Infrastructure as a service
4. **Federated Governance**: Global standards, local autonomy

### Domain Data Product

```
┌─────────────────────────────────────┐
│        Orders Domain                │
│                                     │
│  ┌──────────┐  ┌──────────────────┐ │
│  │ Source    │→ │ Data Product:    │ │
│  │ Systems  │  │ fct_orders       │ │
│  └──────────┘  │                  │ │
│                │ - Schema (contract│ │
│                │ - SLA (freshness) │ │
│                │ - Quality checks  │ │
│                │ - Documentation   │ │
│                └──────────────────┘ │
└─────────────────────────────────────┘
```

### Data Contract Example

```yaml
# data-contract.yml
name: orders
version: 2.1.0
owner: order-processing-team
sla:
  freshness: 1h
  availability: 99.9%

schema:
  - name: order_id
    type: bigint
    nullable: false
    unique: true
  - name: customer_id
    type: bigint
    nullable: false
  - name: amount
    type: decimal(10,2)
    nullable: false
    constraints:
      - min: 0

quality:
  - test: row_count > 0
  - test: null_rate(customer_id) < 0.01
```

---

## Change Data Capture (CDC)

### CDC Approaches

| Method | How It Works | Latency | Impact on Source |
|--------|-------------|---------|-----------------|
| **Log-based** | Read DB transaction log | Seconds | None |
| **Trigger-based** | DB triggers write to audit table | Immediate | Moderate |
| **Timestamp-based** | Query WHERE updated_at > last_run | Minutes | Low |
| **Snapshot diff** | Compare full snapshots | Hours | High |

### Debezium (Log-Based CDC)

```json
// Debezium CDC event format
{
    "op": "u",  // c=create, u=update, d=delete, r=snapshot
    "before": {
        "id": 1,
        "name": "Old Name",
        "email": "old@test.com"
    },
    "after": {
        "id": 1,
        "name": "New Name",
        "email": "new@test.com"
    },
    "source": {
        "db": "mydb",
        "table": "users",
        "ts_ms": 1704067200000
    }
}
```

### Processing CDC Events

```python
def process_cdc_event(event: dict, target_table: str, conn) -> None:
    """Apply a CDC event to the target table."""
    op = event["op"]

    if op in ("c", "r"):  # Create or snapshot read
        insert_record(conn, target_table, event["after"])
    elif op == "u":  # Update
        update_record(conn, target_table, event["after"])
    elif op == "d":  # Delete
        delete_record(conn, target_table, event["before"]["id"])
```

### Timestamp-Based CDC

```sql
-- Simple incremental extract
SELECT *
FROM source_table
WHERE updated_at > :last_extracted_at
ORDER BY updated_at;
```

```python
def incremental_extract(conn, table: str, watermark: str) -> pl.DataFrame:
    """Extract records modified since watermark."""
    return conn.execute(
        f"SELECT * FROM {table} WHERE updated_at > ? ORDER BY updated_at",
        [watermark],
    ).pl()
```

---

## Schema Evolution

### Backward Compatible Changes (Safe)

```sql
-- Adding a column (safe: old code ignores it)
ALTER TABLE orders ADD COLUMN discount DECIMAL(10,2) DEFAULT 0;

-- Adding a table (safe: no existing consumers)
CREATE TABLE order_items (...);

-- Widening a type (safe: no data loss)
ALTER TABLE orders ALTER COLUMN name TYPE VARCHAR(200);
```

### Breaking Changes (Dangerous)

```sql
-- Renaming a column (breaks consumers)
ALTER TABLE orders RENAME COLUMN amt TO amount;

-- Dropping a column (breaks consumers)
ALTER TABLE orders DROP COLUMN legacy_field;

-- Narrowing a type (potential data loss)
ALTER TABLE orders ALTER COLUMN name TYPE VARCHAR(50);
```

### Safe Migration Pattern

```sql
-- Step 1: Add new column
ALTER TABLE orders ADD COLUMN status_v2 VARCHAR(20);

-- Step 2: Backfill
UPDATE orders SET status_v2 = CASE status_code
    WHEN 1 THEN 'pending'
    WHEN 2 THEN 'shipped'
    WHEN 3 THEN 'delivered'
END;

-- Step 3: Verify
SELECT status_code, status_v2, COUNT(*)
FROM orders GROUP BY 1, 2;

-- Step 4: Update application code to use status_v2
-- Step 5: After verification period, drop old column
ALTER TABLE orders DROP COLUMN status_code;
ALTER TABLE orders RENAME COLUMN status_v2 TO status;
```

### Avro/Parquet Schema Evolution

```python
# Parquet supports adding columns, renaming, reordering
# Use merge_schema when reading multiple files with different schemas

df = (
    pl.scan_parquet("data/**/*.parquet")
    .collect()
)

# DuckDB handles schema evolution automatically
duckdb.sql("""
    SELECT * FROM read_parquet('data/**/*.parquet', union_by_name=true)
""")
```

### Versioning Strategy

```
# Version your schemas
schemas/
├── v1/
│   └── orders.json
├── v2/
│   └── orders.json    # Added discount column
└── v3/
    └── orders.json    # Renamed amt -> amount
```

```python
# Schema registry pattern
SCHEMA_VERSIONS = {
    "orders_v1": {"id": int, "amt": float},
    "orders_v2": {"id": int, "amt": float, "discount": float},
    "orders_v3": {"id": int, "amount": float, "discount": float},
}
```
