# Architecture Overview

## System Design

### Components

**DataQualityChecker** (`src/data_quality_checker/main.py`)
- Executes validation rules on Polars DataFrames
- Depends on DBConnector (injected via constructor)
- Does NOT handle I/O, format data, or make business decisions

**DBConnector** (`src/data_quality_checker/connector/output_log.py`)
- Persists validation results to SQLite
- Only dependency: stdlib sqlite3
- Does NOT validate data or transform results

### Data Flow

1. User creates DBConnector with database path
2. User creates DataQualityChecker with DBConnector
3. User calls validation methods (e.g., is_column_unique)
4. Validator checks data, logs result via DBConnector
5. User can query logs via print_all_logs()

### Design Patterns

- **Dependency Injection**: DBConnector is injected into DataQualityChecker
- **Strategy Pattern**: Each validation type is a method, easy to extend
- **Repository Pattern**: DBConnector abstracts data persistence

### Extension Points

**Future Input Types**: Create InputReader protocol (S3Reader, ParquetReader, CSVReader) that all return pl.DataFrame

**Future Output Types**: Create LogWriter protocol (SQLiteWriter, PostgresWriter, CloudWatchWriter)
