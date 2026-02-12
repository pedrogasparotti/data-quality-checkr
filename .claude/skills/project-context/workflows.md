# Common Workflows

## Adding a New Validation Type

1. Add method signature to `src/data_quality_checker/main.py`
2. Implement: validate inputs, perform check, log result, return bool
3. Add tests to `tests/unit/test_main.py` (pass, fail, edge cases)
4. Update README.md features table

## Running Tests

```bash
uv run pytest tests/                                          # All tests
uv run pytest tests/unit/test_main.py                         # Specific file
uv run pytest tests/ --cov=src/data_quality_checker           # With coverage
uv run pytest tests/unit/test_main.py::test_name -v           # Single test
```

## Building

```bash
uv build                    # Creates dist/ with .whl and .tar.gz
```

## Publishing

```bash
uv publish --publish-url https://test.pypi.org/legacy/    # Test PyPI
uv publish                                                 # Production PyPI
```

## Debugging Test Failures

1. Run the failing test with `-v`: `uv run pytest tests/path::test_name -v`
2. Check fixtures in `tests/conftest.py`
3. Verify package installed: `uv pip list | grep data-quality-checker`
