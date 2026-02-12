# Ideal Repository Structure for Claude Code Agents

> **Philosophy**: Make the agent autonomous. Everything it needs to understand context, make decisions, and execute should be discoverable in the repo structure.

---

## The Golden Rule

**If Claude Code needs to ask you a question, your repo structure failed.**

The repo should be self-documenting, with clear conventions that guide the agent toward correct decisions without human intervention.

---

## Core Directory Structure

```
your-project/
├── .claude/                          # Agent configuration & skills
│   ├── skills/
│   │   └── project-context/
│   │       ├── SKILL.md              # Main agent skill definition
│   │       ├── architecture.md       # System design & decisions
│   │       ├── conventions.md        # Code style, patterns, do's/don'ts
│   │       └── workflows.md          # Common tasks & how to do them
│   └── .clignore                     # Files to ignore (like .gitignore)
│
├── docs/                             # Human & agent documentation
│   ├── README.md                     # Project overview (start here)
│   ├── architecture/
│   │   ├── decisions.md              # ADRs (Architecture Decision Records)
│   │   ├── diagrams/                 # C4, sequence, ERD diagrams
│   │   └── system-context.md         # High-level system overview
│   ├── guides/
│   │   ├── setup.md                  # How to get started
│   │   ├── development.md            # Development workflow
│   │   └── deployment.md             # How to deploy
│   └── api/                          # API documentation
│       └── endpoints.md
│
├── src/                              # Source code
│   └── your_project/
│       ├── __init__.py
│       ├── config.py                 # Configuration management
│       ├── extractors/               # Data sources (if data project)
│       ├── transformers/             # Business logic
│       ├── loaders/                  # Data destinations
│       ├── validators/               # Data quality checks
│       └── utils/                    # Shared utilities
│
├── tests/                            # Test suite
│   ├── unit/                         # Fast, isolated tests
│   ├── integration/                  # Multi-component tests
│   ├── fixtures/                     # Test data
│   └── conftest.py                   # Pytest configuration
│
├── scripts/                          # Automation scripts
│   ├── setup.sh                      # Initial setup
│   ├── lint.sh                       # Run linters
│   ├── test.sh                       # Run test suite
│   └── deploy.sh                     # Deployment script
│
├── .github/                          # GitHub-specific (optional)
│   └── workflows/
│       └── ci.yml                    # CI/CD pipeline
│
├── pyproject.toml                    # Project configuration (modern Python)
├── uv.lock                           # Dependency lock file (if using uv)
├── .gitignore                        # Git ignore rules
├── .env.example                      # Environment variables template
├── README.md                         # Project entry point
└── CHANGELOG.md                      # Version history
```

---

## The `.claude/` Directory - Agent's Brain

This is where Claude Code lives. Make it comprehensive.

### `.claude/skills/project-context/SKILL.md`

The master skill that defines the agent's role and knowledge.

```markdown
---
name: project-context
description: Expert on this project's architecture, conventions, and workflows. Use for any project-specific questions.
---

# Project Context: Data Quality Checker

## What This Project Is

A Python library for validating Polars DataFrames and logging results to SQLite.

**Target Users**: Data engineers validating pipeline data
**Key Constraint**: < 100GB datasets, single-machine processing

## Your Role as Agent

You are a senior data engineer working on this codebase. You:
- Understand the architecture (see architecture.md)
- Follow our conventions (see conventions.md)
- Execute common workflows (see workflows.md)
- Make decisions consistent with ADRs in docs/architecture/decisions.md

## Quick References

- **Architecture**: `.claude/skills/project-context/architecture.md`
- **Code Conventions**: `.claude/skills/project-context/conventions.md`
- **Common Tasks**: `.claude/skills/project-context/workflows.md`
- **Tech Stack**: Polars, SQLite3, pytest, uv
- **Python Version**: 3.9+

## Decision Framework

When implementing features:
1. Check if architecture.md defines the approach
2. Follow conventions.md for code style
3. Add tests alongside code (not after)
4. Update documentation if behavior changes

## Communication Style

- Be direct and technical
- Explain tradeoffs when you make design choices
- Flag when requirements are ambiguous
- Ask specific questions if genuinely blocked
```

### `.claude/skills/project-context/architecture.md`

System design, component relationships, design patterns.

```markdown
# Architecture Overview

## System Design (C4 Model)

### System Context
[Include ASCII diagram from building-python-libraries-guide.md]

### Container Diagram
[Include component relationships]

## Design Patterns Used

### 1. Strategy Pattern (Validation)
Each validation type is a method on DataQualityChecker. Easy to extend.

### 2. Dependency Injection (Logger)
DBConnector is injected into DataQualityChecker. Can swap for different outputs.

### 3. Repository Pattern (Logging)
DBConnector abstracts data persistence. Could switch to Postgres without changing validators.

## Component Responsibilities

### DataQualityChecker
- **Purpose**: Execute validation rules on DataFrames
- **Dependencies**: DBConnector (injected)
- **Does NOT**: Handle I/O, format data, make business decisions

### DBConnector
- **Purpose**: Persist validation results
- **Dependencies**: None (only stdlib sqlite3)
- **Does NOT**: Validate data, transform results

## Data Flow

1. User creates DBConnector with database path
2. User creates DataQualityChecker with DBConnector
3. User calls validation methods (e.g., is_column_unique)
4. Validator checks data, logs result via DBConnector
5. User can query logs via print_all_logs()

## Extension Points

### Future: Multiple Input Types
Create InputReader protocol:
- S3Reader
- ParquetReader
- CSVReader
- All return pl.DataFrame

### Future: Multiple Output Types
Create LogWriter protocol:
- SQLiteWriter (current)
- PostgresWriter
- CloudWatchWriter
```

### `.claude/skills/project-context/conventions.md`

Code style, patterns, and dos/don'ts.

```markdown
# Code Conventions

## File Organization

### Module Structure
```
src/data_quality_checker/
├── __init__.py           # Public API exports
├── main.py               # DataQualityChecker class
└── connector/
    └── output_log.py     # DBConnector class
```

### When to Create New Files
- New file when > 300 lines OR logically distinct component
- Keep related functionality together
- Prefer fewer, well-organized files over many tiny files

## Python Style

### Type Hints (MANDATORY)
```python
# Good
def validate(df: pl.DataFrame, col: str) -> bool:
    pass

# Bad
def validate(df, col):
    pass
```

### Docstrings (Required for Public API)
Use Google-style docstrings:
```python
def is_column_unique(df: pl.DataFrame, column: str) -> bool:
    """
    Check if column values are unique.
    
    Args:
        df: Polars DataFrame to validate
        column: Column name to check
        
    Returns:
        True if all values are unique, False otherwise
        
    Raises:
        ValueError: If column doesn't exist
    """
```

### Error Handling
```python
# Good - Be specific
if column not in df.columns:
    raise ValueError(f"Column '{column}' not found in DataFrame")

# Bad - Generic exceptions
if column not in df.columns:
    raise Exception("Column not found")
```

## Testing Conventions

### Test File Naming
- `tests/unit/test_<module>.py`
- `tests/integration/test_<workflow>.py`

### Test Function Naming
```python
def test_<function>_<scenario>_<expected_outcome>():
    pass

# Examples:
def test_is_column_unique_with_duplicates_returns_false():
    pass

def test_is_column_unique_with_unique_values_returns_true():
    pass
```

### Fixtures Over Setup/Teardown
```python
# Good - Clear dependencies
def test_validation(db_connector, sample_df):
    checker = DataQualityChecker(db_connector)
    assert checker.is_column_unique(sample_df, "id")

# Bad - Hidden setup
def test_validation():
    # Where did db_connector come from?
    checker = DataQualityChecker(db_connector)
```

## Do's and Don'ts

### DO
- ✅ Use Polars for DataFrames (not pandas)
- ✅ Use pathlib.Path for file paths (not strings)
- ✅ Use type hints everywhere
- ✅ Write tests alongside code
- ✅ Keep functions small and focused (< 20 lines ideally)
- ✅ Use dataclasses for structured data
- ✅ Log important operations

### DON'T
- ❌ Use print() for debugging (use logging)
- ❌ Catch Exception without re-raising or handling
- ❌ Import pandas (we use Polars)
- ❌ Use mutable default arguments
- ❌ Write functions longer than 50 lines
- ❌ Skip type hints "for later"
- ❌ Leave TODO comments without GitHub issues

## Dependency Management

### Use uv
```bash
# Add dependency
uv add polars

# Add dev dependency
uv add --dev pytest

# Never manually edit pyproject.toml dependencies
```

## Git Commit Messages

Follow Conventional Commits:
```
feat: add referential integrity validation
fix: handle null values in is_column_enum
docs: update README with new validation types
test: add edge cases for unique validation
refactor: extract logging logic to DBConnector
```

## When to Update Documentation

- Architecture changes → Update architecture.md
- New public API → Update README.md and API docs
- New workflow → Update workflows.md
- Design decision → Add to docs/architecture/decisions.md
```

### `.claude/skills/project-context/workflows.md`

Step-by-step guides for common tasks.

```markdown
# Common Workflows

## Adding a New Validation Type

### 1. Define Function Signature
Edit `src/data_quality_checker/main.py`:
```python
def is_column_<validation_name>(
    self,
    df: pl.DataFrame,
    column: str,
    # ... additional params
) -> bool:
    """
    Check if column <validation description>.
    
    Args:
        df: Polars DataFrame to validate
        column: Column name to check
        # ... additional params
        
    Returns:
        True if validation passes, False otherwise
    """
    pass
```

### 2. Implement Validation Logic
```python
def is_column_<validation_name>(self, df: pl.DataFrame, column: str) -> bool:
    # 1. Validate inputs
    if column not in df.columns:
        raise ValueError(f"Column '{column}' not found")
    
    # 2. Perform validation
    result = # ... your logic here
    
    # 3. Log result
    self.db_connector.log(
        check_type="<validation_name>",
        result=result,
        additional_params={"column": column}
    )
    
    # 4. Return result
    return result
```

### 3. Write Tests
Create `tests/unit/test_main.py` if it doesn't exist:
```python
def test_is_column_<validation_name>_<scenario>():
    # Arrange
    df = pl.DataFrame({
        "col": # ... test data
    })
    checker = DataQualityChecker(mock_db_connector)
    
    # Act
    result = checker.is_column_<validation_name>(df, "col")
    
    # Assert
    assert result is True/False
    mock_db_connector.log.assert_called_once()
```

### 4. Update Documentation
- README.md: Add to feature list
- API docs: Document new function

---

## Running Tests

### Run All Tests
```bash
uv run pytest tests/
```

### Run Specific Test File
```bash
uv run pytest tests/unit/test_main.py
```

### Run With Coverage
```bash
uv run pytest tests/ --cov=src/data_quality_checker --cov-report=html
```

### Run Specific Test
```bash
uv run pytest tests/unit/test_main.py::test_is_column_unique_with_duplicates
```

---

## Releasing a New Version

### 1. Update Version
Edit `pyproject.toml`:
```toml
[project]
version = "0.2.0"  # Bump according to semver
```

### 2. Update CHANGELOG.md
```markdown
## [0.2.0] - 2024-02-11

### Added
- New validation type: is_column_range

### Fixed
- Null handling in is_column_enum
```

### 3. Commit Changes
```bash
git add pyproject.toml CHANGELOG.md
git commit -m "chore: bump version to 0.2.0"
git tag v0.2.0
git push && git push --tags
```

### 4. Build & Publish
```bash
# Build
uv build

# Test on Test PyPI
uv publish --publish-url https://test.pypi.org/legacy/

# Verify
uv pip install --index-url https://test.pypi.org/simple/ data-quality-checker

# Publish to PyPI
uv publish
```

---

## Debugging Failures

### Test Failures
1. Read the error message carefully
2. Run just that test: `uv run pytest tests/path/to/test.py::test_name -v`
3. Add print statements or use pytest's `-s` flag to see output
4. Check fixtures in conftest.py

### Import Errors
1. Verify package installed: `uv pip list | grep data-quality-checker`
2. Check PYTHONPATH: `echo $PYTHONPATH`
3. Reinstall in editable mode: `uv pip install -e .`

### Type Errors
1. Run mypy: `uv run mypy src/`
2. Check type hints match actual usage
3. Verify you're using correct Polars types

---

## Code Review Checklist

Before submitting code:
- [ ] All tests pass
- [ ] Type hints added
- [ ] Docstrings written
- [ ] README updated if needed
- [ ] CHANGELOG.md updated
- [ ] No print statements (use logging)
- [ ] No TODOs without GitHub issues
- [ ] Code follows conventions.md
```

### `.claude/.clignore`

Tell Claude what to ignore.

```
# Build artifacts
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
build/
dist/
*.egg-info/

# Virtual environments
venv/
env/
ENV/

# IDE
.vscode/
.idea/

# Test coverage
.coverage
htmlcov/
.pytest_cache/

# Logs
*.log

# Database files
*.db
*.sqlite
*.sqlite3

# Large data files
data/
*.parquet
*.csv

# Secrets
.env
*.pem
*.key
```

---

## Essential Files at Root Level

### `README.md` - The Entry Point

```markdown
# Data Quality Checker

> Validate Polars DataFrames and log results to SQLite

## Quick Start

```bash
pip install data-quality-checker
```

```python
import polars as pl
from data_quality_checker import DataQualityChecker, DBConnector

# Setup
db = DBConnector("logs.db")
checker = DataQualityChecker(db)

# Validate
df = pl.read_csv("data.csv")
checker.is_column_unique(df, "user_id")
checker.is_column_not_null(df, "email")

# View logs
db.print_all_logs()
```

## Documentation

- **Setup Guide**: [docs/guides/setup.md](docs/guides/setup.md)
- **Architecture**: [docs/architecture/system-context.md](docs/architecture/system-context.md)
- **API Reference**: [docs/api/endpoints.md](docs/api/endpoints.md)

## For Contributors

See [docs/guides/development.md](docs/guides/development.md)

## For Claude Code Agent

The `.claude/` directory contains agent-specific context:
- Start with `.claude/skills/project-context/SKILL.md`
- Review architecture, conventions, and workflows
```

### `pyproject.toml` - Single Source of Truth

```toml
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "data-quality-checker"
version = "0.1.0"
description = "Validate Polars DataFrames and log results to SQLite"
readme = "README.md"
requires-python = ">=3.9"
license = {text = "MIT"}
authors = [
    {name = "Your Name", email = "you@example.com"}
]
keywords = ["data-quality", "validation", "polars", "data-engineering"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "Topic :: Software Development :: Quality Assurance",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
]

dependencies = [
    "polars>=0.20.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-cov>=4.0",
    "pytest-mock>=3.0",
    "black>=23.0",
    "ruff>=0.1.0",
    "mypy>=1.0",
]

[project.urls]
Homepage = "https://github.com/yourusername/data-quality-checker"
Documentation = "https://github.com/yourusername/data-quality-checker/blob/main/README.md"
Repository = "https://github.com/yourusername/data-quality-checker"
Issues = "https://github.com/yourusername/data-quality-checker/issues"

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "-v --cov=src/data_quality_checker --cov-report=term-missing"

[tool.black]
line-length = 88
target-version = ['py39']

[tool.ruff]
line-length = 88
target-version = "py39"

[tool.mypy]
python_version = "3.9"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
```

### `scripts/setup.sh` - One Command Setup

```bash
#!/bin/bash
set -e

echo "🚀 Setting up data-quality-checker..."

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ uv not found. Install from https://github.com/astral-sh/uv"
    exit 1
fi

# Install dependencies
echo "📦 Installing dependencies..."
uv sync

# Install pre-commit hooks (optional)
if [ -f .git/hooks/pre-commit ]; then
    echo "✅ Git hooks already installed"
else
    echo "🪝 Installing git hooks..."
    # Add your pre-commit setup here
fi

# Run tests to verify setup
echo "🧪 Running tests..."
uv run pytest tests/

echo "✅ Setup complete! Start coding."
```

---

## Agent-Friendly Principles

### 1. **Explicit Over Implicit**
```
Bad:  "Follow our coding standards"
Good: conventions.md with concrete examples
```

### 2. **Discoverable Paths**
```
Bad:  Agent has to guess where tests go
Good: Clear tests/ structure with README
```

### 3. **Self-Contained Context**
```
Bad:  "See Slack for architecture discussion"
Good: All decisions in docs/architecture/decisions.md
```

### 4. **Runnable Examples**
```
Bad:  "Configure the database"
Good: scripts/setup.sh that does it
```

### 5. **Version Everything**
```
Bad:  "Use the latest version"
Good: uv.lock pins exact versions
```

---

## Quick Reference: Where Does X Go?

| What | Where | Why |
|------|-------|-----|
| Agent skills | `.claude/skills/` | Claude Code reads these first |
| Architecture docs | `docs/architecture/` | Humans and agents both need this |
| Code | `src/your_project/` | Python packaging standard |
| Tests | `tests/unit/` or `tests/integration/` | Pytest convention |
| Scripts | `scripts/` | Automation, not library code |
| Config | `pyproject.toml` | Modern Python standard |
| Dependencies | `pyproject.toml` + `uv.lock` | Declarative + locked |
| API docs | `docs/api/` | Reference documentation |
| Guides | `docs/guides/` | How-to tutorials |

---

## Anti-Patterns to Avoid

❌ **Scattered Documentation**
```
# Bad
README.md has some info
CONTRIBUTING.md has other info
docs/setup.txt has more
Slack has the rest
```

✅ **Centralized Knowledge**
```
# Good
README.md → High-level overview
docs/ → Comprehensive guides
.claude/ → Agent-specific context
```

❌ **Implicit Conventions**
```
# Bad
"We follow PEP 8"
(Agent has to guess specifics)
```

✅ **Explicit Rules**
```
# Good
conventions.md with examples
Linter config in pyproject.toml
```

❌ **Tribal Knowledge**
```
# Bad
"Ask John about the deployment process"
```

✅ **Documented Workflows**
```
# Good
workflows.md with step-by-step guide
scripts/deploy.sh that's runnable
```

---

## Summary: The Ideal Repo

Your repository should let Claude Code:
1. **Understand** the project by reading `.claude/skills/project-context/SKILL.md`
2. **Make decisions** using `architecture.md` and `conventions.md`
3. **Execute tasks** following `workflows.md`
4. **Verify work** with tests and scripts
5. **Never get stuck** because everything is documented

**Test**: If you onboard a new human developer using only the repo (no Slack, no calls), and they're productive in < 1 hour, your structure is good for Claude too.