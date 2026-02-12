# CLI Tools Reference

## Table of Contents
- [Database CLIs](#database-clis)
- [Cloud CLIs for Data Ops](#cloud-clis-for-data-ops)
- [Data File Tools](#data-file-tools)
- [dbt CLI](#dbt-cli)
- [Docker for Data Infrastructure](#docker-for-data-infrastructure)
- [Shell Scripting for Data Ops](#shell-scripting-for-data-ops)

---

## Database CLIs

### psql (PostgreSQL)

```bash
# Connect
psql -h localhost -U myuser -d mydb
psql "postgresql://user:pass@host:5432/dbname"

# Common flags
psql -c "SELECT COUNT(*) FROM users"          # Run single query
psql -f script.sql                             # Run SQL file
psql -A -t -c "SELECT id FROM users"           # Unaligned, tuples-only (for scripting)

# Inside psql
\dt                    # List tables
\d+ table_name         # Describe table with details
\dn                    # List schemas
\du                    # List users/roles
\l                     # List databases
\timing on             # Show query execution time
\x                     # Toggle expanded display
\copy table TO 'file.csv' CSV HEADER    # Export to CSV
\i script.sql          # Execute SQL file
```

### mysql

```bash
# Connect
mysql -h localhost -u root -p mydb

# Common flags
mysql -e "SELECT COUNT(*) FROM users" mydb     # Run single query
mysql < script.sql                              # Run SQL file

# Inside mysql
SHOW DATABASES;
SHOW TABLES;
DESCRIBE table_name;
SHOW CREATE TABLE table_name;
SHOW PROCESSLIST;                    # Active connections
```

### DuckDB CLI

```bash
# Interactive mode
duckdb warehouse.db

# Run query directly
duckdb -c "SELECT * FROM read_parquet('data.parquet') LIMIT 10"

# Query CSV/Parquet without a database
duckdb -c "SELECT COUNT(*) FROM read_csv_auto('data.csv')"
duckdb -c "DESCRIBE SELECT * FROM read_parquet('data.parquet')"

# Export results
duckdb -c "COPY (SELECT * FROM t) TO 'output.csv' (HEADER, DELIMITER ',')"
```

### Snowflake (snowsql)

```bash
# Connect
snowsql -a account_name -u username

# Run query
snowsql -q "SELECT CURRENT_WAREHOUSE(), CURRENT_DATABASE()"

# Execute file
snowsql -f load_script.sql

# Config file: ~/.snowsql/config
```

### BigQuery (bq)

```bash
# Run query
bq query --use_legacy_sql=false 'SELECT COUNT(*) FROM dataset.table'

# List datasets/tables
bq ls
bq ls dataset_name

# Show table schema
bq show --schema --format=prettyjson dataset.table

# Load data
bq load --source_format=PARQUET dataset.table gs://bucket/data.parquet

# Export
bq extract dataset.table gs://bucket/export.csv
```

---

## Cloud CLIs for Data Ops

### AWS CLI (S3 + Data Services)

```bash
# S3 Operations
aws s3 ls s3://bucket/prefix/                   # List objects
aws s3 cp file.parquet s3://bucket/data/         # Upload
aws s3 cp s3://bucket/data/file.parquet .        # Download
aws s3 sync ./local/ s3://bucket/remote/         # Sync directory
aws s3 rm s3://bucket/prefix/ --recursive        # Delete prefix

# S3 with filters
aws s3 ls s3://bucket/ --recursive --summarize   # Total size
aws s3 cp s3://bucket/ ./local/ --recursive \
    --exclude "*" --include "*.parquet"           # Only parquet files

# Glue (Data Catalog)
aws glue get-tables --database-name mydb
aws glue get-table --database-name mydb --name mytable
aws glue start-crawler --name my-crawler

# Athena
aws athena start-query-execution \
    --query-string "SELECT * FROM db.table LIMIT 10" \
    --result-configuration OutputLocation=s3://bucket/results/

# Redshift
aws redshift describe-clusters
```

### Google Cloud CLI (gcloud + gsutil)

```bash
# Storage
gsutil ls gs://bucket/
gsutil cp file.parquet gs://bucket/
gsutil -m cp -r gs://bucket/prefix/ ./local/     # Parallel download

# BigQuery via gcloud
gcloud auth application-default login
bq query --use_legacy_sql=false 'SELECT 1'

# Dataflow
gcloud dataflow jobs list
gcloud dataflow jobs show JOB_ID

# Composer (managed Airflow)
gcloud composer environments list --locations=us-central1
```

### Azure CLI

```bash
# Blob Storage
az storage blob list -c container --account-name myaccount
az storage blob upload -f file.parquet -c container -n data/file.parquet
az storage blob download -c container -n data/file.parquet -f local.parquet

# Synapse / SQL
az synapse sql pool list --workspace-name myws --resource-group myrg

# Data Factory
az datafactory pipeline list --factory-name myfactory --resource-group myrg
```

---

## Data File Tools

### jq (JSON Processing)

```bash
# Pretty print
cat data.json | jq '.'

# Extract fields
cat events.jsonl | jq '.user_id'
cat events.jsonl | jq '{user: .user_id, type: .event_type}'

# Filter
cat events.jsonl | jq 'select(.status == "active")'
cat events.jsonl | jq 'select(.amount > 100)'

# Aggregate
cat events.jsonl | jq -s 'length'                        # Count lines
cat events.jsonl | jq -s 'map(.amount) | add'            # Sum amounts
cat events.jsonl | jq -s 'group_by(.status) | map({status: .[0].status, count: length})'

# Transform to CSV
cat events.jsonl | jq -r '[.id, .name, .amount] | @csv'
```

### csvkit

```bash
# Install
pip install csvkit

# Inspect
csvstat data.csv                      # Column statistics
csvlook data.csv | head              # Pretty table view
csvcut -c 1,3,5 data.csv             # Select columns
csvgrep -c status -m "active" data.csv  # Filter rows

# Convert
in2csv data.xlsx > data.csv           # Excel to CSV
csvjson data.csv > data.json          # CSV to JSON
sql2csv --db postgresql:///mydb \
    --query "SELECT * FROM users" > users.csv

# Query CSV with SQL
csvsql --query "SELECT status, COUNT(*) FROM data GROUP BY status" data.csv
```

### parquet-tools / parquet-cli

```bash
# Install
pip install parquet-tools

# Inspect
parquet-tools show data.parquet              # Print contents
parquet-tools schema data.parquet            # Show schema
parquet-tools rowcount data.parquet          # Count rows
parquet-tools inspect data.parquet           # File metadata

# With DuckDB (often easier)
duckdb -c "DESCRIBE SELECT * FROM read_parquet('data.parquet')"
duckdb -c "SELECT COUNT(*) FROM read_parquet('data.parquet')"
```

### xsv (Fast CSV toolkit)

```bash
# Install: brew install xsv

xsv stats data.csv                    # Column statistics
xsv count data.csv                    # Row count
xsv headers data.csv                  # Column names
xsv select name,email data.csv        # Select columns
xsv search -s status "active" data.csv  # Filter
xsv sort -s amount -R data.csv        # Sort descending
xsv frequency -s status data.csv      # Value counts
```

---

## dbt CLI

### Core Commands

```bash
# Setup
dbt init my_project                    # Create new project
dbt debug                              # Test connection

# Run models
dbt run                                # Run all models
dbt run --select model_name            # Run specific model
dbt run --select +model_name           # Model + upstream dependencies
dbt run --select model_name+           # Model + downstream dependencies
dbt run --select tag:daily             # Run models with tag

# Testing
dbt test                               # Run all tests
dbt test --select model_name           # Test specific model
dbt source freshness                   # Check source freshness

# Documentation
dbt docs generate                      # Generate docs
dbt docs serve                         # Serve docs locally

# Other
dbt seed                               # Load CSV files from seeds/
dbt snapshot                           # Run snapshots (SCD Type 2)
dbt clean                              # Remove compiled files
dbt compile                            # Compile SQL without running
```

### Useful Flags

```bash
dbt run --full-refresh                 # Rebuild incremental models
dbt run --vars '{"date": "2024-01-01"}'  # Pass variables
dbt run --target prod                  # Run against production
dbt run --threads 8                    # Parallel execution
dbt run --fail-fast                    # Stop on first error
```

### Selection Syntax

```bash
# By name
dbt run --select my_model

# By path
dbt run --select models/marts/

# By tag
dbt run --select tag:nightly

# Graph operators
dbt run --select +my_model    # Model + all upstream
dbt run --select my_model+    # Model + all downstream
dbt run --select +my_model+   # Model + all upstream + downstream
dbt run --select 1+my_model   # Model + 1 level upstream

# Exclude
dbt run --exclude staging.*
```

---

## Docker for Data Infrastructure

### Common Data Services

```bash
# PostgreSQL
docker run -d --name postgres \
    -e POSTGRES_PASSWORD=secret \
    -p 5432:5432 \
    postgres:16

# MySQL
docker run -d --name mysql \
    -e MYSQL_ROOT_PASSWORD=secret \
    -p 3306:3306 \
    mysql:8

# Redis
docker run -d --name redis \
    -p 6379:6379 \
    redis:7

# MinIO (S3-compatible storage)
docker run -d --name minio \
    -p 9000:9000 -p 9001:9001 \
    -e MINIO_ROOT_USER=admin \
    -e MINIO_ROOT_PASSWORD=password \
    minio/minio server /data --console-address ":9001"
```

### Docker Compose for Local Stack

```yaml
# docker-compose.yml
version: "3.8"

services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: warehouse
      POSTGRES_USER: dataeng
      POSTGRES_PASSWORD: secret
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

  airflow-webserver:
    image: apache/airflow:2.8.0
    environment:
      AIRFLOW__CORE__SQL_ALCHEMY_CONN: postgresql://dataeng:secret@postgres/warehouse
    ports:
      - "8080:8080"
    depends_on:
      - postgres

volumes:
  pgdata:
```

### Useful Docker Commands

```bash
# Container management
docker ps                              # Running containers
docker logs -f container_name          # Follow logs
docker exec -it postgres psql -U dataeng warehouse  # Connect to DB

# Cleanup
docker system prune -a                 # Remove unused resources
docker volume prune                    # Remove unused volumes
```

---

## Shell Scripting for Data Ops

### Environment Management

```bash
#!/bin/bash
set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Load environment variables
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi
```

### Data Pipeline Script

```bash
#!/bin/bash
set -euo pipefail

DATE=${1:-$(date +%Y-%m-%d)}
LOG_FILE="logs/pipeline_${DATE}.log"

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "Starting pipeline for $DATE"

# Extract
log "Extracting data..."
psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" \
    -c "\copy (SELECT * FROM orders WHERE date='$DATE') TO '/tmp/orders_${DATE}.csv' CSV HEADER"

# Validate
ROW_COUNT=$(wc -l < "/tmp/orders_${DATE}.csv")
if [ "$ROW_COUNT" -le 1 ]; then
    log "ERROR: No data extracted"
    exit 1
fi
log "Extracted $((ROW_COUNT - 1)) rows"

# Load
log "Loading to warehouse..."
aws s3 cp "/tmp/orders_${DATE}.csv" "s3://bucket/orders/${DATE}/"

log "Pipeline complete"
```

### Cron Patterns

```bash
# Edit crontab
crontab -e

# Common schedules
0 2 * * *     /path/to/daily_pipeline.sh      # Daily at 2 AM
0 */4 * * *   /path/to/hourly_check.sh        # Every 4 hours
0 0 * * 0     /path/to/weekly_report.sh        # Sunday midnight
*/5 * * * *   /path/to/health_check.sh         # Every 5 minutes
```

### Useful One-Liners

```bash
# Count lines in all CSV files
find . -name "*.csv" -exec wc -l {} + | sort -n

# Find large files
find . -type f -size +100M -exec ls -lh {} +

# Watch file for changes
tail -f /var/log/pipeline.log | grep --line-buffered "ERROR"

# Parallel download
cat urls.txt | xargs -P 4 -I {} curl -O {}

# Quick file size check
du -sh data/*

# Compress/decompress
gzip data.csv                          # Compress
gunzip data.csv.gz                     # Decompress
tar czf archive.tar.gz data/           # Archive directory
tar xzf archive.tar.gz                 # Extract archive
```
