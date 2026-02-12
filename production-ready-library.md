# Building Production-Ready Python Libraries
## A Data Engineer's Guide to Demonstrating Expertise

> **Source**: [Start Data Engineering - Demonstrate Python Expertise by Building Libraries](https://www.startdataengineering.com/post/demonstrate-python-expertise-building-libraries/)
> **Purpose**: Agent-friendly reference for building the data-quality-checker library
> **Status**: Active project, follow this methodology

---

## The Core Problem

**Question**: How do data engineers demonstrate Python expertise in the age of drag-and-drop tools and LLM code generation?

**Answer**: Build and publish libraries that solve real problems and that other engineers use.

---

## Project Motivation

### Why Build Libraries?

1. **Demonstrate Expertise** - Show employers you can add value before the interview
2. **Reduce Duplication** - Automate repetitive tasks across repos
3. **Career Advancement** - Build a portfolio of published, used packages
4. **Economics of Coding** - Showcase value in a changing landscape

### Example Use Cases

- **boto3 wrapper** - Enforce company-standard S3 paths, secrets management, infrastructure selection
- **Database connection manager** - Handle connections to multiple pipeline databases
- **Workflow automation** - Convert manual processes (e.g., sales validation) to CLI/webapp
- **Data quality checker** ← **THIS PROJECT**

---

## Project Scope: Data Quality Checker

### Problem Statement (From User Email)

> "I'm planning to write test scripts to make sure all the end-to-end pipeline tests are satisfied during the development phase. I was looking for a reference on which tools would be the best to use for SQL scripting or Python?"

### Who & What

- **Who**: Data Engineers validating pipeline data
- **What**: Tool to validate data quality and log results

### Features (MVP)

1. Accept input datasets
2. Validate data against rules
3. Log validation results

### Constraints & Assumptions

| Aspect | Decision | Rationale |
|--------|----------|-----------|
| **Dataset Size** | < 100GB | Small-to-medium datasets, single-machine processing |
| **Input Type** | Polars DataFrames only | Modern, fast, reduces complexity |
| **Result Storage** | SQLite3 table | Lightweight, no external dependencies |
| **Validation Types** | `unique`, `not_null`, `accepted_values`, `relationships` | Match dbt out-of-box tests (most common needs) |

### Why Not Use Existing Libraries?

- **Pandera** - Too complex for simple use cases
- **Cuallee** - API doesn't match requirements
- **Great Expectations** - Feature-rich but heavyweight

**Our Goal**: Build exactly what's needed, no more, no less.

---

## System Architecture (C4 Model)

### Level 1: System Context Diagram

```
┌─────────────────┐
│  Data Engineer  │
│    [Person]     │
│                 │
│ Validates data  │
│ using library   │
└────────┬────────┘
         │ Uses
         ▼
┌─────────────────────────┐
│ Data Quality Checker    │
│  [Software System]      │
│                         │
│ Validates Polars DFs,   │
│ logs to SQLite, returns │
│ pass/fail               │
└────────┬────────────────┘
         │ Reads/Writes
         ▼
┌─────────────────────────┐
│  SQLite Database        │
│  [External System]      │
│                         │
│  Stores validation      │
│  results                │
└─────────────────────────┘
```

### Level 2: Container Diagram

```
┌────────────────────────────────────────────────┐
│        Data Quality Checker                    │
│         [Software System]                      │
│                                                │
│  ┌──────────────────────┐                     │
│  │ DataQualityChecker   │                     │
│  │      [Class]         │                     │
│  │                      │                     │
│  │ - is_column_unique() │                     │
│  │ - is_column_not_null()│                    │
│  │ - is_column_enum()   │                     │
│  │ - are_tables_        │                     │
│  │   referential_       │                     │
│  │   integral()         │                     │
│  └──────────┬───────────┘                     │
│             │ Uses                             │
│             ▼                                  │
│  ┌──────────────────────┐                     │
│  │   DBConnector        │                     │
│  │      [Class]         │                     │
│  │                      │                     │
│  │ - log()              │                     │
│  │ - print_all_logs()   │                     │
│  └──────────┬───────────┘                     │
│             │ Logs to                          │
└─────────────┼──────────────────────────────────┘
              ▼
    ┌─────────────────────┐
    │  SQLite Database    │
    │     [.db file]      │
    │                     │
    │  log table:         │
    │  - id               │
    │  - timestamp        │
    │  - check_type       │
    │  - result           │
    │  - additional_params│
    └─────────────────────┘
```

### Design Patterns & Principles

**Key Observations**:
1. **Orthogonal Systems** - Validator and Logger are independent (can swap DBConnector for different output)
2. **Future Extensibility** - Can add InputReader class for S3, CSV, Parquet, SFTP, etc.
3. **Engineer-Defined Components** - Function signatures defined by engineer, not LLM (prevents scope creep)
4. **LLM Role** - Implementation only, not architecture

**Recommended Reading**: [Python Design Patterns](https://refactoring.guru/design-patterns/python)

---

## Implementation Workflow

### Step 1: Project Setup with uv

```bash
# Initialize library project
uv init --lib data_quality_checker
cd data_quality_checker

# Install dependencies
uv add polars 
uv add --dev pytest pytest-cov pytest-mock

# Create structure
mkdir -p ./src/data_quality_checker/connector
touch ./src/data_quality_checker/main.py 
touch ./src/data_quality_checker/connector/output_log.py 

mkdir -p ./tests/unit
touch ./tests/conftest.py
```

### Step 2: Define Function Signatures (Engineer-Led)

**File**: `./src/data_quality_checker/main.py`

```python
from typing import List, Optional
import polars as pl
from .connector.output_log import DBConnector

class DataQualityChecker:
    """Validates Polars DataFrames against data quality rules."""
    
    def __init__(self, db_connector: DBConnector):
        """
        Initialize the data quality checker.
        
        Args:
            db_connector: DBConnector instance for logging results
        """
        self.db_connector = db_connector
    
    def is_column_unique(
        self, 
        df: pl.DataFrame, 
        column: str
    ) -> bool:
        """
        Check if column values are unique.
        
        Args:
            df: Polars DataFrame to validate
            column: Column name to check
            
        Returns:
            True if all values are unique, False otherwise
        """
        pass
    
    def is_column_not_null(
        self, 
        df: pl.DataFrame, 
        column: str
    ) -> bool:
        """
        Check if column has no null values.
        
        Args:
            df: Polars DataFrame to validate
            column: Column name to check
            
        Returns:
            True if no nulls, False otherwise
        """
        pass
    
    def is_column_enum(
        self, 
        df: pl.DataFrame, 
        column: str, 
        accepted_values: List[str]
    ) -> bool:
        """
        Check if column values are in accepted list.
        
        Args:
            df: Polars DataFrame to validate
            column: Column name to check
            accepted_values: List of valid values
            
        Returns:
            True if all values are in accepted list, False otherwise
        """
        pass
    
    def are_tables_referential_integral(
        self,
        parent_df: pl.DataFrame,
        child_df: pl.DataFrame,
        parent_key: str,
        child_key: str
    ) -> bool:
        """
        Check referential integrity between parent and child tables.
        
        Args:
            parent_df: Parent table DataFrame
            child_df: Child table DataFrame
            parent_key: Primary key column in parent
            child_key: Foreign key column in child
            
        Returns:
            True if all child keys exist in parent, False otherwise
        """
        pass
```

**File**: `./src/data_quality_checker/connector/output_log.py`

```python
import sqlite3
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

class DBConnector:
    """Manages SQLite database connection and logging."""
    
    def __init__(self, db_path: Path):
        """
        Initialize database connector.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._initialize_db()
    
    def _initialize_db(self) -> None:
        """Create log table if it doesn't exist."""
        pass
    
    def log(
        self,
        check_type: str,
        result: bool,
        additional_params: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log validation result to database.
        
        Args:
            check_type: Type of validation (e.g., 'unique', 'not_null')
            result: True if validation passed, False otherwise
            additional_params: Additional context (column name, values, etc.)
        """
        pass
    
    def print_all_logs(self) -> None:
        """Print all logged validation results."""
        pass
```

### Step 3: Generate Implementation with LLM

**Instructions for LLM**:
- Implement the functions based on the signatures and docstrings
- Use Polars DataFrame operations (no pandas)
- Ensure proper error handling
- Log each validation result via DBConnector
- Keep code simple and readable

**Reference**: See [full working code](https://github.com/josephmachado/data_quality_checker)

### Step 4: Create Tests (Prevent Regression)

**Required Reading**: [Pytest Usage Documentation](https://docs.pytest.org/)

**File**: `./tests/conftest.py`

```python
import pytest
from pathlib import Path
import tempfile
from data_quality_checker.connector.output_log import DBConnector

@pytest.fixture(scope="session")
def temp_db():
    """Create temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = Path(tmp.name)
    
    yield db_path
    
    # Cleanup
    db_path.unlink()

@pytest.fixture
def db_connector(temp_db):
    """Create DBConnector instance with temporary database."""
    return DBConnector(temp_db)

@pytest.fixture
def mock_db_connector(mocker):
    """Mock DBConnector to test without actual DB writes."""
    mock = mocker.MagicMock()
    mock.log = mocker.MagicMock()
    return mock
```

**Test Structure**:
- Test DBConnector independently (using temp_db fixture)
- Test DataQualityChecker with mocked DBConnector (using mock_db_connector)
- Test all validation functions with edge cases

**Run Tests**:
```bash
uv run pytest tests/
uv run pytest tests/ --cov=src/data_quality_checker  # with coverage
```

---

## Documentation: README Structure

### Required Sections

1. **Installation**
   ```bash
   pip install data-quality-checker
   ```

2. **Quick Start Example**
   ```python
   import polars as pl
   from data_quality_checker import DataQualityChecker, DBConnector
   
   # Setup
   db = DBConnector("validation_logs.db")
   checker = DataQualityChecker(db)
   
   # Load data
   df = pl.read_csv("data.csv")
   
   # Run checks
   checker.is_column_unique(df, "user_id")
   checker.is_column_not_null(df, "email")
   
   # View results
   db.print_all_logs()
   ```

3. **Feature List**
   - Unique value validation
   - Not-null validation
   - Enum/accepted values validation
   - Referential integrity validation

4. **API Reference**
   - Full function signatures
   - Parameter descriptions
   - Return values
   - Examples

5. **Architecture Diagrams**
   - System Context (C4 Level 1)
   - Container Diagram (C4 Level 2)

6. **Development Guide**
   - How to contribute
   - How to run tests
   - How to build locally

7. **License**
   - Use MIT License for public packages

**LLM Prompt**: "Generate a README with the above sections for the data-quality-checker library. Include code examples and make it beginner-friendly."

**Reference**: [Example README](https://github.com/josephmachado/data_quality_checker/blob/main/README.md)

---

## Publishing Workflow

### Phase 1: Test PyPI (Staging)

1. **Create Account** at [test.pypi.org](https://test.pypi.org)

2. **Enable 2FA** (Required for package creation)
   - Go to Account Settings → Security

3. **Create API Token**
   - Account Settings → API tokens → Add API token
   - Scope: "Entire account"
   - **SAVE THE TOKEN** - shown only once

4. **Build & Upload**
   ```bash
   # Build distribution
   uv build
   
   # Upload to test PyPI
   uv publish --publish-url https://test.pypi.org/legacy/
   
   # When prompted:
   # Username: __token__
   # Password: <paste your API token>
   ```

5. **Test Installation**
   ```bash
   uv pip install --index-url https://test.pypi.org/simple/ data-quality-checker
   ```

6. **Verify**
   - Check your package page: `https://test.pypi.org/project/data-quality-checker/`
   - Test all functionality in a fresh environment

### Phase 2: Production PyPI

1. **Create Account** at [pypi.org](https://pypi.org)

2. **Repeat 2FA & API Token Setup**

3. **Publish**
   ```bash
   uv publish
   
   # Username: __token__
   # Password: <production API token>
   ```

4. **Verify**
   ```bash
   pip install data-quality-checker
   ```

---

## Repeatable Framework Summary

### The 5-Step Process

1. **Problem Scoping**
   - Define: Who uses it? What does it do?
   - Set clear constraints (input types, size limits, output format)
   - Start small, iterate later

2. **Design Architecture**
   - Draw C4 diagrams (System Context + Container)
   - Define function signatures and classes
   - Engineer leads, LLM implements

3. **LLM-Guided Implementation**
   - Provide detailed type hints and docstrings
   - Generate code with LLM
   - Review and refine

4. **Create Tests**
   - Unit tests for each component
   - Integration tests for workflows
   - Aim for >80% coverage

5. **Publish & Document**
   - Comprehensive README
   - Test on Test PyPI first
   - Publish to PyPI when ready

### Next Steps for Your Career

1. **Identify 3 repetitive tasks** in your current work
2. **Pick the simplest one** and apply this framework
3. **Publish to PyPI within 2 weeks**
4. **Add to resume and GitHub portfolio**

---

## Agent Instructions

When working on the data-quality-checker project or similar libraries:

1. **Follow the architecture** - Don't deviate from the defined class structure
2. **Implement one component at a time** - DBConnector first, then DataQualityChecker
3. **Write tests alongside code** - Each function needs corresponding tests
4. **Keep it simple** - Resist feature creep, stick to the defined scope
5. **Document as you go** - Update README with each new feature
6. **Use type hints everywhere** - They guide LLM generation and catch errors
7. **Test on Test PyPI first** - Always validate before production publish

---

## Key Takeaways

- **Expertise = Building, not memorizing** - Libraries demonstrate real value
- **Scope ruthlessly** - Better to ship something small and useful than nothing big and perfect
- **Architecture first, code second** - LLMs implement, humans design
- **Tests prevent regression** - Critical for library maintenance
- **Publishing matters** - It's not real until others can `pip install` it

---

## Resources

- **Article**: [Start Data Engineering - Building Libraries](https://www.startdataengineering.com/post/demonstrate-python-expertise-building-libraries/)
- **Example Repo**: [data_quality_checker on GitHub](https://github.com/josephmachado/data_quality_checker)
- **Tools**: 
  - [uv](https://github.com/astral-sh/uv) - Modern Python package manager
  - [Polars](https://pola-rs.github.io/polars/) - Fast DataFrame library
  - [pytest](https://docs.pytest.org/) - Testing framework
- **Design Patterns**: [Refactoring Guru](https://refactoring.guru/design-patterns/python)
- **C4 Model**: [c4model.com](https://c4model.com/)