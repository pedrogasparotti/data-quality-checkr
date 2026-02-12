# Code Conventions

## Module Structure

```
src/data_quality_checker/
├── __init__.py           # Public API exports
├── main.py               # DataQualityChecker class
└── connector/
    └── output_log.py     # DBConnector class
```

## Python Style

- Type hints on all functions (mandatory)
- Google-style docstrings on public API
- Specific exceptions (ValueError, not Exception)
- pathlib.Path for file paths (not strings)

## Testing

- File naming: `tests/unit/test_<module>.py`
- Function naming: `test_<function>_<scenario>_<expected_outcome>()`
- Use fixtures from conftest.py (temp_db, db_connector, mock_db_connector)
- Mock DBConnector when testing DataQualityChecker

## Do's and Don'ts

- DO: Use Polars (not pandas)
- DO: Write tests alongside code
- DO: Keep functions under 20 lines
- DON'T: Use print() for debugging (use logging)
- DON'T: Import pandas
- DON'T: Catch generic Exception

## Dependencies

- Use `uv add` to add dependencies
- Never manually edit pyproject.toml dependencies

## Commit Messages

Follow Conventional Commits: feat:, fix:, docs:, test:, refactor:, chore:
