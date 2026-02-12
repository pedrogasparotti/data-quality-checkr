# Changelog

## [0.1.0] - 2024-02-12

### Added
- `DataQualityChecker` class with 4 validation methods:
  - `is_column_unique` - Check column uniqueness
  - `is_column_not_null` - Check for null values
  - `is_column_enum` - Check accepted values
  - `are_tables_referential_integral` - Check referential integrity
- `DBConnector` class for SQLite validation logging
- Comprehensive test suite (31 tests, 100% coverage)
- Reference documentation guides:
  - SQL commands and best practices
  - Python for data engineering
  - Pipeline patterns and orchestration
  - Data quality patterns
  - CLI tools reference
  - Data architecture patterns
