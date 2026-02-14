# Debugging `data-quality-checker` with VS Code

A technical, hands-on guide for stepping through every layer of this project — from CLI argument parsing to SQLite persistence — using VS Code's Python debugger.

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Project Setup](#2-project-setup)
3. [VS Code Debug Configuration](#3-vs-code-debug-configuration)
4. [Sample Test Data](#4-sample-test-data)
5. [Debugging the CLI Entry Point](#5-debugging-the-cli-entry-point)
6. [Debugging the Validation Engine](#6-debugging-the-validation-engine)
7. [Debugging the Database Layer](#7-debugging-the-database-layer)
8. [Debugging Tests with pytest](#8-debugging-tests-with-pytest)
9. [Advanced Techniques](#9-advanced-techniques)
10. [Common Pitfalls](#10-common-pitfalls)

---

## 1. Architecture Overview

```
                    ┌─────────────────────────────────────┐
                    │           CLI (cli.py)               │
                    │  argparse → load_config → run_checks │
                    └──────────────┬──────────────────────┘
                                   │
                    ┌──────────────▼──────────────────────┐
                    │   DataQualityChecker (main.py)       │
                    │  is_column_unique()                  │
                    │  is_column_not_null()                │
                    │  is_column_enum()                    │
                    │  are_tables_referential_integral()   │
                    └──────────────┬──────────────────────┘
                                   │  every check calls log()
                    ┌──────────────▼──────────────────────┐
                    │   DBConnector (connector/output_log) │
                    │  _initialize_db()                    │
                    │  log()                               │
                    │  print_all_logs()                    │
                    └──────────────┬──────────────────────┘
                                   │
                    ┌──────────────▼──────────────────────┐
                    │       SQLite (validation_logs.db)    │
                    │  validation_log table                │
                    │  ┌─────┬───────────┬──────┬───────┐ │
                    │  │ id  │check_type │result│params │ │
                    │  └─────┴───────────┴──────┴───────┘ │
                    └─────────────────────────────────────┘
```

### Key architectural nuances

**Dependency injection in `DataQualityChecker`.**
The checker class does not create its own database connection. It receives a `DBConnector` instance via its constructor (`main.py:10`). This is critical for two reasons:
- It makes unit testing possible — tests inject a `MagicMock` instead of a real DB connection (`conftest.py:21-25`).
- It decouples validation logic from persistence. You could swap SQLite for PostgreSQL by writing a new connector that implements `log()`.

**Every check method is a side-effect machine.**
Each validation method (e.g., `is_column_not_null`) does two things: returns a boolean *and* writes to the database. This means debugging a "simple" boolean check also involves I/O. When stepping through code, you'll always drop into `DBConnector.log()` after the Polars operation.

**The CLI layer is a thin orchestrator.**
`cli.py:run_checks()` (line 69) is essentially a `for` loop that dispatches to checker methods based on the `type` field in the YAML config. It does not contain business logic — it maps strings to method calls. This means bugs in check behavior live in `main.py`, not `cli.py`.

**Polars expressions return scalar booleans differently than pandas.**
`df[column].is_duplicated().sum() == 0` (line 39) and `df[column].null_count() == 0` (line 62) return Python `bool` values. But `df[column].is_in(values).all()` (line 91) returns a Polars `Boolean` scalar. In the debugger, inspecting these return types is instructive — hover over `result` after each assignment to see the actual type.

**SQLite stores booleans as integers.**
`DBConnector.log()` converts `result` to `int(result)` at `output_log.py:60`. When you query the database during debugging, you'll see `1`/`0`, not `True`/`False`. The reverse conversion happens in `print_all_logs()` at line 76.

---

## 2. Project Setup

```bash
# Clone and install in editable mode
cd data-quality-checker
python -m venv .venv
source .venv/bin/activate        # macOS/Linux
# .venv\Scripts\activate         # Windows

pip install -e ".[dev]"
```

Verify the installation:

```bash
# Run the test suite
pytest

# Verify CLI is available
dqc --help
```

In VS Code, select the Python interpreter from `.venv`:
1. `Cmd+Shift+P` (macOS) or `Ctrl+Shift+P` (Windows/Linux)
2. Type "Python: Select Interpreter"
3. Choose the `.venv` interpreter

---

## 3. VS Code Debug Configuration

Create `.vscode/launch.json` in the project root:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "DQC: CLI check command",
      "type": "debugpy",
      "request": "launch",
      "module": "data_quality_checker.cli",
      "args": [
        "check",
        "sample_data/inventory.csv",
        "--config",
        "sample_data/checks_sample.yml"
      ],
      "cwd": "${workspaceFolder}",
      "console": "integratedTerminal",
      "justMyCode": true
    },
    {
      "name": "DQC: CLI logs command",
      "type": "debugpy",
      "request": "launch",
      "module": "data_quality_checker.cli",
      "args": [
        "logs",
        "validation_logs.db"
      ],
      "cwd": "${workspaceFolder}",
      "console": "integratedTerminal",
      "justMyCode": true
    },
    {
      "name": "DQC: Programmatic API",
      "type": "debugpy",
      "request": "launch",
      "program": "${workspaceFolder}/sample_data/debug_script.py",
      "cwd": "${workspaceFolder}",
      "console": "integratedTerminal",
      "justMyCode": false
    },
    {
      "name": "DQC: pytest (all tests)",
      "type": "debugpy",
      "request": "launch",
      "module": "pytest",
      "args": [
        "tests/",
        "-v",
        "--tb=short"
      ],
      "cwd": "${workspaceFolder}",
      "console": "integratedTerminal",
      "justMyCode": false
    },
    {
      "name": "DQC: pytest (single test)",
      "type": "debugpy",
      "request": "launch",
      "module": "pytest",
      "args": [
        "tests/unit/test_main.py::TestIsColumnNotNull::test_with_nulls_returns_false",
        "-v",
        "--no-header"
      ],
      "cwd": "${workspaceFolder}",
      "console": "integratedTerminal",
      "justMyCode": false
    }
  ]
}
```

### Configuration breakdown

| Config | What it does |
|--------|-------------|
| `"module": "data_quality_checker.cli"` | Runs `cli.py:main()` as `python -m data_quality_checker.cli` — this hits the argparse entry point |
| `"justMyCode": true` | Skips stepping into Polars/PyYAML internals. Set to `false` when debugging library interactions |
| `"justMyCode": false` (API/test configs) | Allows stepping into the `connector/` subpackage and test framework code |
| `"program"` (API config) | Runs a standalone script for debugging the programmatic API outside the CLI |

---

## 4. Sample Test Data

Create a `sample_data/` directory with these files. They are designed to trigger both passing and failing checks across all validation types.

### `sample_data/inventory.csv`

This CSV has intentional data quality issues for debugging:

```csv
uuid_inventario,occurrence_type,target_name,next_state_prediction,priority
INV-001,Monitoração de OAE,Bridge Alpha,stable,high
INV-002,Monitoração de OAE,Bridge Beta,degrading,medium
INV-003,,Tunnel Gamma,stable,low
INV-001,Monitoração de Drenagem Profunda,Dam Delta,improving,high
INV-005,Invalid Type,Road Epsilon,,critical
INV-006,Monitoração de Sinalização Vertical,Sign Zeta,stable,
```

**Embedded issues for debugging:**

| Row | Issue | Which check catches it |
|-----|-------|----------------------|
| 3 | `occurrence_type` is empty/null | `not_null` on `occurrence_type` |
| 4 | `uuid_inventario` = `INV-001` (duplicate of row 1) | `unique` on `uuid_inventario` |
| 5 | `occurrence_type` = `"Invalid Type"` | `accepted_values` on `occurrence_type` |
| 5 | `next_state_prediction` is empty/null | `not_null` on `next_state_prediction` |
| 6 | `priority` is empty/null | (not checked by default config but useful for experiments) |

### `sample_data/inventory_clean.csv`

A clean dataset — all checks should pass:

```csv
uuid_inventario,occurrence_type,target_name,next_state_prediction
INV-001,Monitoração de OAE,Bridge Alpha,stable
INV-002,Monitoração de Drenagem Profunda,Bridge Beta,degrading
INV-003,Monitoração de Sinalização Vertical,Tunnel Gamma,stable
```

### `sample_data/parent_table.csv`

For referential integrity debugging:

```csv
department_id,department_name
D001,Engineering
D002,Marketing
D003,Finance
```

### `sample_data/child_table.csv`

Contains an orphan foreign key (`D999`):

```csv
employee_id,name,department_id
E001,Alice,D001
E002,Bob,D002
E003,Charlie,D999
E004,Diana,D001
```

### `sample_data/checks_sample.yml`

```yaml
db: sample_data/validation_logs.db

checks:
  - type: not_null
    column: uuid_inventario

  - type: not_null
    column: occurrence_type

  - type: not_null
    column: next_state_prediction

  - type: unique
    column: uuid_inventario

  - type: accepted_values
    column: occurrence_type
    values:
      - "Monitoração de Drenagem Profunda"
      - "Monitoração de OAE"
      - "Monitoração de Sinalização Horizontal - Longitudinal e Tachas"
      - "Monitoração de Sinalização Horizontal - Marcas Viárias"
      - "Monitoração de Sinalização Horizontal - Zebrados"
      - "Monitoração de Sinalização Vertical"
      - "Monitoração de Terraplenos e Estruturas de Contenção"
```

### `sample_data/debug_script.py`

A standalone script for debugging the programmatic API:

```python
"""Debug script for stepping through the programmatic API."""

import polars as pl
from data_quality_checker import DataQualityChecker, DBConnector

# --- Setup ---
db = DBConnector("sample_data/debug_validation.db")
checker = DataQualityChecker(db)

# --- Load data ---
df = pl.read_csv("sample_data/inventory.csv")
print(f"Loaded {df.shape[0]} rows, {df.shape[1]} columns")
print(df)

# --- Run individual checks (set breakpoints on these lines) ---

# Check 1: not_null — will FAIL (row 3 has null occurrence_type)
result_not_null = checker.is_column_not_null(df, "occurrence_type")
print(f"\nnot_null on occurrence_type: {result_not_null}")

# Check 2: unique — will FAIL (INV-001 appears twice)
result_unique = checker.is_column_unique(df, "uuid_inventario")
print(f"unique on uuid_inventario: {result_unique}")

# Check 3: accepted_values — will FAIL ("Invalid Type" not in list)
accepted = [
    "Monitoração de Drenagem Profunda",
    "Monitoração de OAE",
    "Monitoração de Sinalização Vertical",
]
result_enum = checker.is_column_enum(df, "occurrence_type", accepted)
print(f"accepted_values on occurrence_type: {result_enum}")

# Check 4: referential integrity
parent_df = pl.read_csv("sample_data/parent_table.csv")
child_df = pl.read_csv("sample_data/child_table.csv")

result_ref = checker.are_tables_referential_integral(
    parent_df, child_df, "department_id", "department_id"
)
print(f"referential_integrity: {result_ref}")

# --- Inspect logs ---
print("\n--- Validation Logs ---")
db.print_all_logs()
```

---

## 5. Debugging the CLI Entry Point

### Goal: Trace a `dqc check` command from argument parsing to result output.

**Step 1: Set breakpoints in `src/data_quality_checker/cli.py`:**

| Line | Location | Why |
|------|----------|-----|
| 33 | `config = yaml.safe_load(f)` | Inspect raw YAML parse output |
| 82 | `df = _load_data(file_path)` | Inspect the loaded DataFrame |
| 88 | `check_type = check["type"]` | See which check is being dispatched |
| 91-97 | The `if/elif` chain | Step into the specific check method |
| 112 | `all_passed = all(...)` | See final aggregated result |
| 153 | `sys.exit(0 if all_passed else 1)` | Confirm exit code |

**Step 2: Launch `DQC: CLI check command`** from the Run & Debug panel (`Cmd+Shift+D`).

**Step 3: Walk through execution.**

When you hit the breakpoint at line 82, open the **Debug Console** (the REPL at the bottom of the debug panel) and type:

```python
df.shape          # (6, 5)
df.columns        # ['uuid_inventario', 'occurrence_type', ...]
df["occurrence_type"].null_count()   # See how many nulls exist
```

This is where VS Code shines — you can run arbitrary Polars expressions against the live DataFrame while paused.

**Step 4: Step into a check method.**

At line 92 (`passed = checker.is_column_not_null(df, column)`), press **F11** (Step Into). You'll land at `main.py:61`:

```python
self._validate_column_exists(df, column)   # line 61
result = df[column].null_count() == 0      # line 62
```

Hover over `result` after line 62 executes to see the boolean value. Then **F11** again into `self.db_connector.log()` to watch the SQLite write happen.

---

## 6. Debugging the Validation Engine

### Scenario: `is_column_enum` returns `False` but you don't know which values are invalid.

Set a breakpoint at `main.py:91`:

```python
result = df[column].is_in(accepted_values).all()
```

When paused, use the Debug Console to decompose the expression:

```python
# See which individual rows pass/fail the is_in check
df[column].is_in(accepted_values)
# Returns a Boolean Series: [true, true, true, true, false, true]

# Find the offending values
df.filter(~df[column].is_in(accepted_values))
# Returns rows where the value is NOT in the accepted list

# Get just the bad values
df[column].filter(~df[column].is_in(accepted_values)).unique()
# Returns: ["Invalid Type"]
```

### Scenario: `are_tables_referential_integral` returns `False` — find the orphan keys.

Set a breakpoint at `main.py:129`:

```python
result = child_keys.is_in(parent_keys).all()
```

Debug Console:

```python
# Which child keys have no parent?
child_keys.filter(~child_keys.is_in(parent_keys))
# Returns: ["D999"]

# See the full orphan rows
child_df.filter(~child_df[child_key].is_in(parent_keys))
# Returns the row for Charlie with department D999
```

### Scenario: Column validation raises `ValueError` — but which DataFrame has the issue?

For `are_tables_referential_integral`, note that `_validate_column_exists` is called twice (`main.py:124-125`):

```python
self._validate_column_exists(parent_df, parent_key)   # line 124
self._validate_column_exists(child_df, child_key)      # line 125
```

Set breakpoints on both lines. When the error fires, the call stack in the **Call Stack** panel tells you exactly which call triggered it. Check the **Variables** panel to see whether `parent_df` or `child_df` is missing the column.

---

## 7. Debugging the Database Layer

### Inspecting the SQLite database mid-session

After a check runs, the result is in the database. You can query it from the Debug Console while paused anywhere:

```python
import sqlite3, json
conn = sqlite3.connect("sample_data/validation_logs.db")
rows = conn.execute("SELECT * FROM validation_log ORDER BY id DESC LIMIT 5").fetchall()
for r in rows:
    print(f"[{r[0]}] {r[2]} | {'PASS' if r[3] else 'FAIL'} | {r[4]}")
conn.close()
```

### Watching the `log()` method

Set a breakpoint at `output_log.py:52` (the `conn.execute` INSERT statement). Each time a check completes, execution pauses here. Inspect:

- `check_type` — the string identifier
- `int(result)` — `1` or `0`
- `params_json` — the serialized JSON string

**Important nuance:** The `with sqlite3.connect(...)` context manager opens and closes a connection for every single `log()` call. This means each check writes independently. If the process crashes mid-run, you still have logs for all completed checks — they are not lost. This is a design trade-off: connection-per-write is slower but more durable.

### Using the VS Code SQLite Viewer extension

Install the **SQLite Viewer** extension (`alexcvzz.vscode-sqlite`). Then:
1. Open `validation_logs.db` from the Explorer panel
2. Click "Show Table" on `validation_log`
3. Run a check with the debugger
4. Refresh the table view to see new rows appear

---

## 8. Debugging Tests with pytest

### Running a specific test under the debugger

Use the `DQC: pytest (single test)` launch configuration. Change the test path in `args` to target any test:

```json
"args": [
  "tests/unit/test_main.py::TestIsColumnNotNull::test_with_nulls_returns_false",
  "-v"
]
```

Set a breakpoint inside the test method (`test_main.py:49`):

```python
df = pl.DataFrame({"name": ["a", None, "c"]})
checker = DataQualityChecker(mock_db_connector)
assert checker.is_column_not_null(df, "name") is False  # breakpoint here
```

Press **F11** to step into `is_column_not_null`. You're now debugging production code from within a test context. The `mock_db_connector` in the Variables panel shows the MagicMock — expand it to see that `.log` hasn't been called yet.

After stepping over the check, inspect:

```python
mock_db_connector.log.call_args
# Shows: call(check_type='not_null', result=False, additional_params={'column': 'name'})

mock_db_connector.log.call_count
# Shows: 1
```

### Understanding the fixture chain

The `conftest.py` defines three fixtures:

```
temp_db (tmp_path) → provides a Path to a temp .db file
    └──▶ db_connector (temp_db) → creates a real DBConnector with that path
mock_db_connector () → creates a MagicMock(spec=DBConnector), no real DB
```

- Tests in `test_main.py` use `mock_db_connector` — they validate Polars logic without touching SQLite.
- Tests in `test_output_log.py` use `db_connector` — they validate actual database operations.
- Tests in `test_cli.py` create their own `tmp_path`-based fixtures inline.

When debugging a test, check which fixture is injected. If you see a `MagicMock` in the Variables panel where you expected a real `DBConnector`, you're looking at a mock-based test — stepping into `log()` will step into the mock, not `output_log.py`.

### Using VS Code Test Explorer

1. Open the Testing panel (flask icon in the Activity Bar)
2. VS Code auto-discovers tests via `pyproject.toml`'s `[tool.pytest.ini_options]`
3. Click the debug icon next to any test to launch it under the debugger
4. Failed tests show inline diffs in the editor

---

## 9. Advanced Techniques

### Conditional breakpoints

Right-click a breakpoint dot in the gutter and select "Edit Breakpoint". Set a condition:

**Example 1:** Break only when a specific check type is dispatched (`cli.py:88`):

```python
check_type == "accepted_values"
```

**Example 2:** Break only when a check fails (`main.py:62`):

```python
result == False
```

This is invaluable when running a config with many checks — you skip straight to the one that fails.

### Logpoints (non-breaking breakpoints)

Right-click the gutter, select "Add Logpoint". Enter a log message with expressions in `{}`:

**At `cli.py:102`:**

```
Check {check_type} on column {column}: {status}
```

This prints to the Debug Console without pausing execution — useful for getting an overview before diving deep.

### Watch expressions

In the **Watch** panel, add:

```
df.shape
df[column].null_count()
len(results)
result
```

These update live as you step through code.

### Debug Console REPL tricks

While paused at any breakpoint, the Debug Console is a full Python REPL with access to all local variables:

```python
# Inspect DataFrame schema
df.schema
# {'uuid_inventario': String, 'occurrence_type': String, ...}

# Quick data profiling
df.describe()

# Check for nulls across all columns
df.null_count()

# Peek at specific rows
df.row(2)

# Test a Polars expression before it runs
df["occurrence_type"].value_counts()
```

---

## 10. Common Pitfalls

### Pitfall 1: Empty string vs null

In CSV files, an empty field can be read as either `""` (empty string) or `null` depending on Polars' inference. The `is_column_not_null` check catches `null` but **not** empty strings. Debug this by pausing after `_load_data` and running:

```python
df["occurrence_type"].to_list()
# Check if you see None or "" for empty fields
```

If you need to catch empty strings too, you'd need to modify the check — but first confirm what Polars actually loaded.

### Pitfall 2: `is_in` with nulls

`df[column].is_in(accepted_values).all()` returns `True` if the column contains nulls and `accepted_values` doesn't include `None`. This is because Polars' `is_in` returns `null` for null inputs, and `.all()` skips nulls by default. Set a breakpoint at `main.py:91` and test:

```python
# In Debug Console:
df[column].is_in(accepted_values)
# May show: [true, true, null, true, false, true]
#                        ^^^^ null is not False
```

### Pitfall 3: Boolean type mismatch

`is_in(...).all()` returns a Polars scalar, not a plain Python `bool`. While it behaves like a bool in most contexts, `type(result)` might surprise you. The `int(result)` conversion in `DBConnector.log()` handles this, but if you're comparing with `is True` in tests, it matters.

### Pitfall 4: Database file path is relative

`DBConnector` receives a path that may be relative (`validation_logs.db`). If you change working directories or run from a different location, the database ends up in unexpected places. Debug this by inspecting `self.db_path` in the Variables panel after `DBConnector.__init__` runs — check the absolute resolved path.

### Pitfall 5: CLI `sys.exit()` terminates the debugger

`cli.py:main()` calls `sys.exit()` at lines 147, 153, and 156. If you're debugging and hit one of these, the debugger session ends. To prevent this, set a breakpoint on the `sys.exit()` line and inspect the exit code before it fires. Alternatively, use the "Programmatic API" launch config to bypass the CLI entirely.

---

## Quick Reference: Breakpoint Cheat Sheet

| What you're debugging | File | Line(s) | What to inspect |
|----------------------|------|---------|-----------------|
| YAML config parsing | `cli.py` | 33 | `config` dict structure |
| Data file loading | `cli.py` | 82 | `df.shape`, `df.schema` |
| Check dispatch loop | `cli.py` | 88 | `check_type`, `column` |
| Column existence guard | `main.py` | 21 | `df.columns`, `column` |
| Null check logic | `main.py` | 62 | `df[column].null_count()` |
| Uniqueness check logic | `main.py` | 39 | `df[column].is_duplicated()` |
| Enum check logic | `main.py` | 91 | `df[column].is_in(accepted_values)` |
| Referential integrity | `main.py` | 127-129 | `parent_keys`, `child_keys` |
| Database INSERT | `output_log.py` | 52 | `check_type`, `int(result)`, `params_json` |
| Database SELECT | `output_log.py` | 68 | `rows` list contents |
| Test mock assertions | `test_main.py` | varies | `mock_db_connector.log.call_args` |
