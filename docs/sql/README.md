# SQL Commands & Best Practices

## Table of Contents
- [Common Patterns](#common-patterns)
- [Window Functions](#window-functions)
- [Performance Optimization](#performance-optimization)
- [Data Quality Queries](#data-quality-queries)
- [Schema Management](#schema-management)

---

## Common Patterns

### Deduplication
```sql
-- Keep latest record per key
WITH ranked AS (
  SELECT *,
    ROW_NUMBER() OVER (
      PARTITION BY id
      ORDER BY updated_at DESC
    ) AS rn
  FROM raw_table
)
SELECT * FROM ranked WHERE rn = 1;
```

### Incremental Load Pattern
```sql
-- Load only new/changed records
INSERT INTO target_table
SELECT s.*
FROM source_table s
LEFT JOIN target_table t ON s.id = t.id
WHERE t.id IS NULL
   OR s.updated_at > t.updated_at;
```

### SCD Type 2 (Slowly Changing Dimension)
```sql
-- Close existing record and insert new
UPDATE dim_customer
SET end_date = CURRENT_DATE - 1,
    is_current = FALSE
WHERE customer_id = :customer_id
  AND is_current = TRUE;

INSERT INTO dim_customer (customer_id, name, email, start_date, end_date, is_current)
VALUES (:customer_id, :name, :email, CURRENT_DATE, '9999-12-31', TRUE);
```

---

## Window Functions

### Running Totals
```sql
SELECT
  date,
  amount,
  SUM(amount) OVER (ORDER BY date) AS running_total,
  SUM(amount) OVER (
    ORDER BY date
    ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
  ) AS rolling_7_day
FROM transactions;
```

### Lag/Lead for Comparisons
```sql
SELECT
  date,
  revenue,
  LAG(revenue, 1) OVER (ORDER BY date) AS prev_day,
  revenue - LAG(revenue, 1) OVER (ORDER BY date) AS daily_change,
  LAG(revenue, 7) OVER (ORDER BY date) AS same_day_last_week
FROM daily_metrics;
```

### Percentiles and Rankings
```sql
SELECT
  customer_id,
  total_spend,
  NTILE(10) OVER (ORDER BY total_spend DESC) AS decile,
  PERCENT_RANK() OVER (ORDER BY total_spend) AS percentile,
  DENSE_RANK() OVER (ORDER BY total_spend DESC) AS spend_rank
FROM customer_summary;
```

---

## Performance Optimization

### Index Strategy
```sql
-- Composite index for common query patterns
CREATE INDEX idx_orders_customer_date
ON orders (customer_id, order_date DESC);

-- Partial index for active records only
CREATE INDEX idx_users_active
ON users (email)
WHERE is_active = TRUE;

-- Covering index to avoid table lookups
CREATE INDEX idx_orders_covering
ON orders (customer_id, order_date)
INCLUDE (total_amount, status);
```

### Query Optimization Checklist
1. **Check execution plan**: `EXPLAIN ANALYZE`
2. **Avoid SELECT ***: Only fetch needed columns
3. **Filter early**: Push WHERE clauses down
4. **Use appropriate JOINs**: Prefer INNER when possible
5. **Batch operations**: Process in chunks for large datasets

### Partitioning
```sql
-- Create partitioned table (PostgreSQL)
CREATE TABLE events (
  id BIGSERIAL,
  event_time TIMESTAMP NOT NULL,
  event_type VARCHAR(50),
  payload JSONB
) PARTITION BY RANGE (event_time);

-- Create monthly partitions
CREATE TABLE events_2024_01
  PARTITION OF events
  FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
```

---

## Data Quality Queries

### Null Analysis
```sql
SELECT
  COUNT(*) AS total_rows,
  COUNT(column_name) AS non_null_count,
  COUNT(*) - COUNT(column_name) AS null_count,
  ROUND(100.0 * (COUNT(*) - COUNT(column_name)) / COUNT(*), 2) AS null_pct
FROM table_name;
```

### Duplicate Detection
```sql
SELECT
  id,
  COUNT(*) AS occurrence_count
FROM table_name
GROUP BY id
HAVING COUNT(*) > 1
ORDER BY occurrence_count DESC;
```

### Referential Integrity Check
```sql
-- Find orphan records
SELECT o.order_id, o.customer_id
FROM orders o
LEFT JOIN customers c ON o.customer_id = c.customer_id
WHERE c.customer_id IS NULL;
```

### Data Freshness Check
```sql
SELECT
  table_name,
  MAX(updated_at) AS last_update,
  NOW() - MAX(updated_at) AS time_since_update,
  CASE
    WHEN NOW() - MAX(updated_at) > INTERVAL '24 hours' THEN 'STALE'
    ELSE 'FRESH'
  END AS freshness_status
FROM (
  SELECT 'orders' AS table_name, updated_at FROM orders
  UNION ALL
  SELECT 'customers', updated_at FROM customers
) t
GROUP BY table_name;
```

---

## Schema Management

### Safe Column Addition
```sql
-- Add column with default (non-blocking in modern DBs)
ALTER TABLE users
ADD COLUMN preferences JSONB DEFAULT '{}';

-- Backfill in batches
UPDATE users
SET preferences = '{"notifications": true}'
WHERE id BETWEEN :start_id AND :end_id;
```

### Migration Pattern
```sql
-- Step 1: Add new column
ALTER TABLE orders ADD COLUMN status_new VARCHAR(20);

-- Step 2: Backfill data
UPDATE orders SET status_new =
  CASE status_code
    WHEN 1 THEN 'pending'
    WHEN 2 THEN 'shipped'
    WHEN 3 THEN 'delivered'
  END;

-- Step 3: Verify
SELECT status_code, status_new, COUNT(*)
FROM orders GROUP BY 1, 2;

-- Step 4: Switch (in application code)
-- Step 5: Drop old column after verification period
ALTER TABLE orders DROP COLUMN status_code;
```

---

## Useful Snippets

### Generate Date Series
```sql
-- PostgreSQL
SELECT generate_series(
  '2024-01-01'::date,
  '2024-12-31'::date,
  '1 day'::interval
)::date AS date;

-- BigQuery
SELECT date
FROM UNNEST(
  GENERATE_DATE_ARRAY('2024-01-01', '2024-12-31')
) AS date;
```

### JSON Handling
```sql
-- PostgreSQL JSONB
SELECT
  data->>'name' AS name,
  (data->'address'->>'city') AS city,
  jsonb_array_length(data->'orders') AS order_count
FROM customers;

-- BigQuery
SELECT
  JSON_VALUE(data, '$.name') AS name,
  JSON_QUERY_ARRAY(data, '$.orders') AS orders
FROM customers;
```

### Pivot Table
```sql
SELECT
  product_id,
  SUM(CASE WHEN EXTRACT(MONTH FROM order_date) = 1 THEN amount ELSE 0 END) AS jan,
  SUM(CASE WHEN EXTRACT(MONTH FROM order_date) = 2 THEN amount ELSE 0 END) AS feb,
  SUM(CASE WHEN EXTRACT(MONTH FROM order_date) = 3 THEN amount ELSE 0 END) AS mar
FROM orders
WHERE EXTRACT(YEAR FROM order_date) = 2024
GROUP BY product_id;
```
